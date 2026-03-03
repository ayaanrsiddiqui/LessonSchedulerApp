[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/F1hjDb63)


# Running locally
*written by Ayaan*

The app is setup with python dot_env to read in a file called .env with some needed environment variable

- `DJANGO_SECRET_KEY`
    - this is the only required one, and this can be any string for use in development, the production configuration is taken care of. the reason i have it setup this way is as an extra protection against accidentally pushing a real secret key to production.
    - example: `DJANGO_SECRET_KEY=insecure-dev-key-for-django`
- `DJANGO_DEBUG`
    - set to True for easier debugging
    - `DJANGO_DEBUG=True`
-  `DATABASE_URL`
    - this is optional. if you have a particular local database setup that you want to use, you put the url to it in this field. i have a postgres server setup on my computer and this field looks like `DATABASE_URL=postgres://postgres:postgres@localhost:5432/\[database name\]` but you dont need this. if not set, this will just use a sqlite db. 
    - if you use a local postgres setup, also add `DJANGO_POSTGRES_SSL_REQUIRE=False`

# initial setup
the first time you run this remember to run
`python manage.py migrate` which sets up a blank database in the correct format. youll also need to do these migrations whenever you change the models.