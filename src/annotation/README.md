## Text Annotation Tool

This is a rudimentary tool for annotating text on headstamps.
It's a basic flask app with a sqlite3 database. It relies on a local copy of the image set.  All the client code is in simple javascript.

Setup:

`python build_db.py --img_home [path to images]`

Then run:

`python app.py`

NOTE: Don't use `python -m flask run` as this will fail to launch the app with https enabled, preventing Google OAUTH from working.

To highlight text, click on the headstamp center, pull the line to the top-left corner of the text and click, then click on the lower-right corner of the text.  Enter the text string into the annotation widget, and indicate what direction is 'up' for the text- outward, inward, clockwise, or counter-clocwise.

Todo tasks are in the top of app.py.


# Running in Docker (Compose)

`./Dockerfile` defines a container that meets the app's dependencies.
`../../docker-compose.yml` documents how the app can be run in the container.

These are configured via environment variables using python-dotenv.
The `.env` file is .gitignored, so you will need to make your own.

Do this by `cp .env.example .env` then inspect `.env`
(more configuration may be added here later).

When you have a .env file then you will be able to run `docker-compose up`
from the repository root (`../../`) to run the app in docker container.

Then acess it on http://localhost:8080

Notes:
* (for now) this composition mounts the data directory and sqlite database
  in the same way as the above instructions (for running locally without containerization).
* the composition includes database and object store services,
  which will eventually be used to replace sqlite (see #21)
  and the local filesystem media storage (see #13).
* production-like setups will have the container behind an SSL-terminating gateway (reverse proxy).
  This is not currently working quite right (see bug #23)
* production-like setups will need changes to how the flask container is run,
  (i.e. not as a development server, see #24)