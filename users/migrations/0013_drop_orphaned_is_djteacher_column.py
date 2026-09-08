from django.db import migrations


def drop_orphaned_column(apps, schema_editor):
    """Drop users_profile.is_djteacher if it is still physically present.

    Two earlier migrations left the database and Django's model state out of
    sync:

      * 0008 is a hand-written squash claiming to replace 0003-0006, but its
        operations omit the RemoveField that 0006 performed, so the column is
        never dropped on a database built from the squash.
      * 0011 then removes the field with SeparateDatabaseAndState and an empty
        database_operations list -- Django's state forgets the field while the
        column survives.

    The result on any freshly migrated database is a NOT NULL column with no
    default that Django no longer knows about, so every Profile insert fails
    with an IntegrityError. This drops it for real.

    Written with introspection rather than "DROP COLUMN IF EXISTS" because
    SQLite does not support the IF EXISTS clause, and local development runs
    on SQLite. Safe to run against databases where the column is already gone.
    """
    connection = schema_editor.connection
    table = "users_profile"

    with connection.cursor() as cursor:
        columns = [
            column.name
            for column in connection.introspection.get_table_description(cursor, table)
        ]

    if "is_djteacher" in columns:
        schema_editor.execute(
            "ALTER TABLE %s DROP COLUMN %s"
            % (
                schema_editor.quote_name(table),
                schema_editor.quote_name("is_djteacher"),
            )
        )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0012_alter_profile_role_and_more"),
    ]

    operations = [
        # No reverse: the column's original definition is not recoverable from
        # the current state, and re-adding a NOT NULL column with no default
        # would fail on any table with rows.
        migrations.RunPython(drop_orphaned_column, migrations.RunPython.noop),
    ]
