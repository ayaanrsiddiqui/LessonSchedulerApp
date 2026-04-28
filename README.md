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
Fhe first time you run this remember to run:
`python manage.py migrate` which sets up a blank database in the correct format. You will also need to do these migrations whenever you change the models.

# Our Application
We built this application for UVA's Hip Hop Organization. As of last semester, the organization has added DJ and Producer lessons which are hosted by a handful of experienced executive members for any interested club members. Previously, they were scheduling lessons via text message or Instagram DM. With our app, we hope to streamline lesson scheduling by allowing DJ and Producer teachers to post lesson offering with date, time, capacity, skill level, location, and lesson type. In response, DJ and Producer students can sign up for lessons fitting their schedules and needs.

# Using our App

# As a DJ/Producer Teacher
Our application's first user type is a DJ/Producer Teacher. This user is able to post lessons by clicking "Post Lessons" in the top menu bar. Upon clicking, the user we will be redirected to a lesson form on which they can fill out their lesson's details. Once filled out, the user can click "Submit".

# As a DJ/Producer Student
Our application's second user type is a DJ/Producer student. This user can sign up for any posted classes by clicking on a class's "Sign Up" button. 

# Both students and 
Both users are able to send/receive messages. A user can view their messages by clicking "Messages" in the top menu bar. From the inbox, a user can start a new conversation with any existing teacher/student user or continue an existing chat. Furthermore, both of these user types can view their own and other's profiles. Their own profile can be navigated to by clicking the profile icon in the top right corner.

# As Admin
Our application's third user type is the User Administrator. This user can view all existing users, view/accept/deny user role change requests (student requesting teacher role).

