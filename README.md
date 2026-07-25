# EFL by Level

Production source for **englishasaforeignlanguage.com**.

The live site is a GoDaddy-compatible **Flask application running through CloudLinux Passenger**. It includes:

- separate learner and teacher journeys
- A1–C2 CEFR level hubs
- grammar, vocabulary, listening, reading, writing, speaking, Business English and IELTS routes
- teacher lesson-plan, worksheet, game, PowerPoint, placement-test and classroom-management routes
- a 24-question English level test
- Flask-based form and lead handling
- shop, product and bundle foundations
- responsive navigation, accessibility states, cookie choices, sitemap and legal pages
- automated Flask validation, JavaScript checks, FTPS deployment, Passenger restart and live verification

## Flask application

The Python runtime is stored in `flask_app/`:

- `app.py` — Flask application and route dispatcher
- `passenger_wsgi.py` — cPanel Passenger entry point
- `build_from_legacy.py` — preserves the existing rendered design and routes while generating Flask-served page snapshots
- `remote_deploy.py` — removes the previous PHP entry files and verifies the Passenger deployment
- `validate.py` — route, health and form tests

The earlier PHP release bundle remains under `release/` only as the verified content/design source used during the migration build. It is not the production runtime.

## Deployment

Every push to `main`:

1. reconstructs the existing EFL content
2. renders all sitemap and linked routes
3. assembles a Flask/Passenger application in `deploy/`
4. validates the homepage, level test, A1 hub, teacher hub, health endpoint and form handling
5. removes the previous PHP runtime from GoDaddy
6. deploys the Flask application by FTPS
7. uploads `tmp/restart.txt` to restart Passenger
8. verifies that live responses include `X-EFL-Runtime: Flask`

The Passenger application root is:

```text
/home/uak0tydpqj02/public_html/englishasaforeignlanguage.com
```

It uses the existing Python 3.11 environment already proven by the What10Things Flask application:

```text
/home/uak0tydpqj02/virtualenv/flask_app/3.11/bin/python
```

## Required GitHub Actions secrets

- `FTP_USERNAME`
- `FTP_PASSWORD`
- `FTP_SERVER_DIR` — normally `./` because the dedicated FTP account is rooted in the EFL document directory

## Submission data

Live form submissions are stored in `storage/submissions.csv`. That file is excluded from later deployments so collected data is not overwritten.
