"""Diagnose the media-storage configuration end to end.

    python manage.py check_s3

Reports which storage backend is actually active, then -- if it is S3 --
performs a real write, read-back, URL signing and delete against the bucket,
printing the precise error code when a step fails. Run it on the dyno:

    heroku run python manage.py check_s3 --app <app>

The settings fall back to local filesystem storage when any of
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY or AWS_STORAGE_BUCKET_NAME is
missing. That fallback is silent by design (so the project runs from a clean
clone with no AWS account), which means a half-configured production
environment looks like it is working until the dyno restarts and every upload
disappears. This command makes that state loud.
"""

import traceback
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management.base import BaseCommand

PROBE_PATH = "s3-healthcheck/probe.txt"
PROBE_BODY = b"storage healthcheck\n"


def mask(value):
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]} (len {len(value)})"


class Command(BaseCommand):
    help = "Check that media storage is configured and actually reachable."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Leave the probe object in the bucket instead of deleting it.",
        )

    def handle(self, *args, **options):
        ok = self.style.SUCCESS
        bad = self.style.ERROR
        warn = self.style.WARNING

        # django.core.files.storage.default_storage is a LazyObject proxy --
        # type() on it returns the wrapper (DefaultStorage), not the backend it
        # wraps. Go through the storages registry to get the real instance.
        self.storage = storages["default"]
        backend = type(self.storage)

        self.stdout.write("")
        self.stdout.write(f"DEBUG                   {settings.DEBUG}")
        self.stdout.write(f"Active media backend    {backend.__module__}.{backend.__name__}")
        self.stdout.write("")

        self.stdout.write("Environment as Django sees it:")
        self.stdout.write(f"  AWS_ACCESS_KEY_ID     {mask(getattr(settings, 'AWS_ACCESS_KEY_ID', None))}")
        self.stdout.write(f"  AWS_SECRET_ACCESS_KEY {mask(getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))}")
        self.stdout.write(f"  AWS_STORAGE_BUCKET_NAME {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None) or '(not set)'}")
        self.stdout.write(f"  AWS_S3_REGION_NAME    {getattr(settings, 'AWS_S3_REGION_NAME', None) or '(not set)'}")
        self.stdout.write("")

        if "s3" not in backend.__module__:
            missing = [
                name
                for name in (
                    "AWS_ACCESS_KEY_ID",
                    "AWS_SECRET_ACCESS_KEY",
                    "AWS_STORAGE_BUCKET_NAME",
                )
                if not getattr(settings, name, None)
            ]
            self.stdout.write(bad("S3 is NOT active. Uploads are going to the dyno filesystem,"))
            self.stdout.write(bad("which is wiped on every restart and every deploy."))
            self.stdout.write("")

            if missing:
                self.stdout.write(f"Missing config vars: {', '.join(missing)}")
                self.stdout.write("")
                self.stdout.write("Set them with:")
                for name in missing:
                    self.stdout.write(f"  heroku config:set {name}=... --app <app>")
            else:
                self.stdout.write(
                    warn(
                        "All three credentials are present, so settings.py should have "
                        "selected S3. Something else is overriding STORAGES -- check for "
                        "a local settings override, and confirm django-storages is "
                        "installed (import storages.backends.s3boto3)."
                    )
                )
            return

        # ------------------------------------------------------------ live checks
        try:
            client = self.storage.connection.meta.client
            self.stdout.write(f"Resolved endpoint       {client.meta.endpoint_url}")
            self.stdout.write(f"Signature version       {client.meta.config.signature_version}")
            self.stdout.write("")
        except Exception:
            self.stdout.write(warn("Could not introspect the boto3 client; continuing.\n"))

        steps = [
            ("write", self._write),
            ("exists", self._exists),
            ("read back", self._read),
            ("sign url", self._url),
        ]

        failed = False
        try:
            for label, fn in steps:
                try:
                    detail = fn()
                except Exception as exc:  # noqa: BLE001 -- we want every failure mode
                    failed = True
                    self.stdout.write(bad(f"  {label:<10} FAILED"))
                    self.stdout.write("")
                    self.stdout.write(self._explain(exc))
                    self.stdout.write("")
                    self.stdout.write(traceback.format_exc())
                    break
                self.stdout.write(ok(f"  {label:<10} ok    {detail}"))
        finally:
            # Cleanup runs even when a step failed, so a bad run does not leave
            # probe objects behind. AWS_S3_FILE_OVERWRITE is False, so each
            # orphan would otherwise accumulate under a new suffixed name.
            saved = getattr(self, "_saved_name", None)
            if saved and not options["keep"]:
                try:
                    self.storage.delete(saved)
                    self.stdout.write(ok(f"  {'cleanup':<10} ok    probe removed"))
                except Exception as exc:  # noqa: BLE001
                    self.stdout.write(warn(f"  {'cleanup':<10} could not remove {saved}: {exc}"))

        self.stdout.write("")
        if failed:
            self.stdout.write(bad("Storage is misconfigured. See the error above."))
        else:
            self.stdout.write(ok("S3 is configured correctly and reachable."))

    # ---------------------------------------------------------------- the steps

    def _write(self):
        self._saved_name = self.storage.save(PROBE_PATH, ContentFile(PROBE_BODY))
        return self._saved_name

    def _exists(self):
        found = self.storage.exists(self._saved_name)
        if not found:
            raise RuntimeError(
                "The object was written but exists() says it is absent. This is the "
                "classic symptom of an IAM policy without s3:ListBucket -- S3 answers "
                "HeadObject with 403 instead of 404, and boto3 reports it as missing."
            )
        return "object is present"

    def _read(self):
        with self.storage.open(self._saved_name, "rb") as handle:
            body = handle.read()
        if body != PROBE_BODY:
            raise RuntimeError(f"Read back {body!r}, expected {PROBE_BODY!r}")
        return f"{len(body)} bytes match"

    def _url(self):
        url = self.storage.url(self._saved_name)
        self.stdout.write(f"             url   {url}")

        # Two valid presigning formats. SigV4 uses X-Amz-* query parameters;
        # SigV2 -- still accepted by buckets in regions that predate 2014, such
        # as us-east-1 -- uses AWSAccessKeyId/Signature/Expires. Matching only
        # the first would flag a working URL as broken.
        if "X-Amz-Signature" in url:
            style = "SigV4"
        elif "AWSAccessKeyId=" in url and "Signature=" in url:
            style = "SigV2 (legacy)"
        elif "?" not in url:
            raise RuntimeError(
                "The URL carries no query string, so it is not presigned at all. "
                "Against a private bucket the browser will get 403. Check that "
                "AWS_QUERYSTRING_AUTH is True."
            )
        else:
            style = "unrecognised signature format"

        # Recognising the format only proves a signature is present, not that S3
        # accepts it. Fetch the object the way a browser would, which is the
        # thing we actually care about.
        try:
            with urlopen(Request(url, headers={"User-Agent": "check_s3"}), timeout=20) as response:
                body = response.read()
                status = response.status
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:600]
            raise RuntimeError(
                f"S3 rejected the presigned URL with HTTP {exc.code}. Response body:\n{detail}"
            ) from exc

        if body != PROBE_BODY:
            raise RuntimeError(f"Fetched {body!r} from the signed URL, expected {PROBE_BODY!r}")

        return f"{style}, fetched OK (HTTP {status})"

    # --------------------------------------------------------------- diagnosis

    def _explain(self, exc):
        """Turn the common boto3 error codes into something actionable."""
        code = None
        response = getattr(exc, "response", None)
        if isinstance(response, dict):
            code = response.get("Error", {}).get("Code")

        hints = {
            "InvalidAccessKeyId": (
                "The access key does not exist in AWS. Either it was deleted, or the "
                "value in Heroku has a typo or a stray newline. Re-set it."
            ),
            "SignatureDoesNotMatch": (
                "The secret key is wrong for that access key. Secrets often contain "
                "'+' and '/', so re-set it with quotes:\n"
                "  heroku config:set AWS_SECRET_ACCESS_KEY='...' --app <app>"
            ),
            "AccessDenied": (
                "Credentials are valid but the IAM user is not allowed this action. "
                "The policy needs BOTH resources -- the object ARN with /* for "
                "GetObject/PutObject/DeleteObject, and the bucket ARN without /* for "
                "ListBucket. A policy missing the bucket ARN fails exactly here."
            ),
            "NoSuchBucket": (
                "No bucket by that name exists. Check AWS_STORAGE_BUCKET_NAME against "
                "the S3 console -- it is the bare name, not a URL and not an ARN."
            ),
            "PermanentRedirect": (
                "The bucket lives in a different region than AWS_S3_REGION_NAME. Find "
                "the real region in the S3 console and set AWS_S3_REGION_NAME to it."
            ),
            "AuthorizationHeaderMalformed": (
                "Region mismatch. The error text names the region S3 expects -- set "
                "AWS_S3_REGION_NAME to that."
            ),
            "AccessControlListNotSupported": (
                "The bucket has ACLs disabled (the modern default). AWS_DEFAULT_ACL "
                "must be None, not 'public-read'."
            ),
            "ExpiredToken": "The credentials are temporary and have expired. Use a long-lived IAM user key.",
        }

        lines = []
        if code:
            lines.append(f"AWS error code: {code}")
            if code in hints:
                lines.append("")
                lines.append(hints[code])
        else:
            lines.append(f"{type(exc).__name__}: {exc}")
            text = str(exc).lower()
            if "could not connect" in text or "endpoint" in text:
                lines.append("")
                lines.append(
                    "This looks like a network or endpoint problem rather than a "
                    "permissions one -- check AWS_S3_REGION_NAME."
                )
        return "\n".join(lines)
