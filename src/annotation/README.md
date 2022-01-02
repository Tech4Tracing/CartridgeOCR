## Text Annotation Tool

This is a rudimentary tool for annotating text on headstamps.
It's a basic flask app with a sqlite3 database. It relies on a local copy of the image set.  All the client code is in simple javascript.

Setup:

`python build_db.py --img_home [path to images]`

Then run:

`python -m flask run`

To highlight text, click on the headstamp center, pull the line to the top-left corner of the text and click, then click on the lower-right corner of the text.  Enter the text string into the annotation widget, and indicate what direction is 'up' for the text- outward, inward, clockwise, or counter-clocwise.

Todo tasks are in the top of app.py.