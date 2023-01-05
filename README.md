# Daily fire tally visualization app

## Structure

 * `application.py` contains the main app loop code.
 * `gui.py` has most user interface elements.
 * `luts.py` has shared code & lookup tables and other configuration.
 * `assets/` has images and CSS (uses [Bulma](https://bulma.io))

## Local development

After cloning this template, run it this way:

```
pipenv install
export FLASK_APP=application.py
export FLASK_DEBUG=True
pipenv run flask run
```

The project is run through Flask and will be available at [http://localhost:5000](http://localhost:5000).

Other env vars that can be set:

 * `DASH_LOG_LEVEL` - sets level of logger, default INFO
 * `DASH_CACHE_EXPIRE` - Has sane default (1 day), override if testing cache behavior.
 * `TALLY_DATA_URL` - URL to source data CSV, has a sane working default baked in
 * `TALLY_DATA_ZONES_URL` - URL to source data CSV, has a sane working default baked in


## Deploying to AWS Elastic Beanstalk:

Apps run via WSGI containers on AWS.

Before deploying, make sure and run `pipenv run pip freeze > requirements.txt` to lock current versions of everything.

```
eb init
eb deploy
```

The following env vars must be set:

 * `DASH_REQUESTS_PATHNAME_PREFIX` - URL fragment so requests are properly routed.

For local development, set `FLASK_DEBUG` to `True`.  This will use a local file for source data and enable other debugging tools.
