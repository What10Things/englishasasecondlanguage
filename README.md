# EFL by Level

Production source for **englishasaforeignlanguage.com**.

The rebuilt site is a GoDaddy-friendly PHP application with:

- separate learner and teacher journeys
- A1–C2 CEFR level hubs
- grammar, vocabulary, listening, reading, writing, speaking, Business English and IELTS routes
- teacher lesson-plan, worksheet, game, PowerPoint, placement-test and classroom-management routes
- a 24-question English level test
- consent-aware lead capture
- shop, product and bundle foundations
- responsive navigation, accessibility states, cookie choices, sitemap and legal pages
- automated PHP linting, JavaScript checks, route smoke tests, FTPS deployment and live verification

## Production source

The complete production tree is stored in `release/site-bundle.part00` through `release/site-bundle.part04`. GitHub Actions reconstructs the bundle before every test and deployment.

To unpack it locally:

```bash
cat release/site-bundle.part* | base64 -d > /tmp/efl-site-bundle.tar.gz
tar -xzf /tmp/efl-site-bundle.tar.gz
```

The deployable website is then available in `godaddy/`.

## Required GitHub Actions secrets

Add these repository secrets before running the deployment:

- `FTP_SERVER` — the FTP/FTPS hostname, not a filesystem path
- `FTP_USERNAME`
- `FTP_PASSWORD`
- `FTP_SERVER_DIR` — the directory visible to that FTP login which maps to the document root for `englishasaforeignlanguage.com`; use `./` only when the FTP account is already rooted in that folder

Every push to `main` then runs the checks, uploads `godaddy/` by FTPS and verifies the live homepage, level test, A1 hub and teacher hub.

## Lead data

Live submissions are written to `godaddy/storage/leads.csv`. The directory is denied by `.htaccess`, and the CSV is excluded from future deployments so collected data is not overwritten.
