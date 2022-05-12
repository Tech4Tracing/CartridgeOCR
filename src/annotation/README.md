# Text Annotation Tool

This is a rudimentary tool for annotating text on headstamps + simple UI and API. We aim to develeop more or less usable API for nice custom clients. All the baked-in client code is in simple javascript.

## Starting locally

You'll need google key and secret for your oauth app; google how to issue them.

`./Dockerfile` defines a container that meets the app's dependencies.
`../../docker-compose.yml` documents how the app can be run in the container.

These are configured via environment variables using python-dotenv.
The `.env` file is .gitignored, so you will need to make your own.

1. Create `.env` file (here) based on `.env.example` - set at least Google auth credentials and probably AUTH_WHITELISTED_EMAILS
2. run `docker-compose up` (project root)
3. Wait till it's started and navigate to http://localhost:8080/ (it's important to have localhost for google to work, you have entered localhost when issuing your own google key/secrets)

By default it uses empty local MsSQL database and empty local Azure Blob storage emulator. Run `docker-compose down -v` to delete all the data and start anew, just `docker-compose down` leaves the data but removes containers.


## Usage

To highlight text, click on the headstamp center, pull the line to the top-left corner of the text and click, then click on the lower-right corner of the text.  Enter the text string into the annotation widget, and indicate what direction is 'up' for the text- outward, inward, clockwise, or counter-clocwise.

Todo tasks are in the top of app.py.
