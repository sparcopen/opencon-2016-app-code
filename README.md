## Installation

- install Pillow prerequisites: `apt-get install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk`
- `virtualenv -p python3 venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`
- `pip install -r requirements.devel.txt` # not needed in production
- add `.env` file to the directory where manage.py is
- `.env` file: add `SECRET_KEY`
- `.env` file: add path to `DJANGO_SETTINGS_MODULE` (default is `opencon_project.settings.developer`)
- on a new machine (with empty database): `./manage.py add_airports`, `./manage.py add_institutions`, `./manage.py add_organizations`
- note: `./manage.py add_countries` is not needed (because autocomplete was removed & countries are now in a dropdown menu)
- `./manage.py migrate`
- `./manage.py collectstatic` (needed in production for static file serving using WhiteNoise)
- `./manage.py runserver`

## Working with the app

- before accessing the admin interface: `./manage.py createsuperuser`
- add rating users: http(s)://server:port/admin/rating/user/ -- then check UUIDs
- log in as rating user: http(s)://server:port/rate/login/11112222333344445555666677778888/

Note: Be absolutely sure to install up-to-date requirements from requirements.txt. For example, as of 2016-05-15, this project requires *modified* `django-bootstrap-form` forked by @ZoltanOnody (otherwise on forms, the sequence "verbose_name -> help_text -> form field" will not be displayed in the correct order). If a different version of `django-bootstrap-form` is already installed, uninstall and re-install it to display form fields correctly.

## Modifying the app

After changing the `recalculate_ratings` function (in `application/models.py`), e.g. when the the logic of moving ratings between round 1 and round 2 is modified, it's necessary to recalculate the values already stored in the database using `./manage.py recalculate_ratings`.
