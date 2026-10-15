# Automatic teacher-resource release

Owner authority: 15 October 2026 — quality-check produced items and publish passing products for sale.

Mainbuyer2's EFL factory remains authoritative. The final gate checks the English core and every declared language review, review/content hashes, exact rendered files and ZIP contents. A policy approval and durable outbox precede delivery. Failed checks cannot upload. New daily A1–C2 briefs require nine editions; older resources disclose their actual languages.

The price is £3.99 GBP per complete language bundle, matching existing practice packs. Factory resources have immutable product IDs and ZIP hashes, actual titles, durations, objectives and original samples. Sold editions are unchanged.

Validated FTPS delivers files into `storage/factory_products/`, protected by Apache and Flask URL denial. ZIP upload and verification precede an atomic listing commit. App deployments exclude this persistent directory. Listings are read at request time. A public `resources/<id>/release.json` receipt verifies hash and price without paid content. Downloads require Stripe payment, exact edition/amount/currency and no refund/dispute; tampered ZIPs block checkout and download.

`provision-factory-transport.yml` seals the existing site FTPS credentials to Mainbuyer2's committed public key with RSA-4096 OAEP/SHA256. Only ciphertext enters a one-day artifact. The private key and decrypted 0600 delivery file remain on Mainbuyer2, never in source or logs.

Publishing does not enable payments. Existing `EFL_SALES_ENABLED` and `EFL_STRIPE_SECRET_KEY` requirements remain. Until live checkout/delivery are verified, listings show payments unavailable. Publication is not proof of a real payment.

Validation: run `flask_app/test_learning.py` and `flask_app/test_factory_sales.py` with `PYTHONPATH=flask_app`. The normal full build, validation and browser journey gate run before deployment. Live evidence is recorded in the MainBuyer factory implementation report.
