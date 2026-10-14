# Multilingual learning and digital resources — 14 October 2026

## Shipped source

- First-visit accessible native dialog with English, Spanish, French and Polish;
  one-year language preference, always available in the header, no-JS selection page.
- Native-language study landing page, six practice levels, resource shop, product
  samples and instructions. English exercise sentences/options are preserved.
- Server-rendered 24-question level check with translated explanations after
  submission. Works without JavaScript; CSRF protected. This is a limited grammar
  and vocabulary check, not a validated all-skills CEFR assessment.
- Six focused £3.99 practice products, A1–C2. Each contains 12 original questions,
  two English writing tasks, teacher notes, answers and explanations, and a usage
  licence. Every purchase includes all four language editions. HTML files are
  printable through a browser; native PDF/DOCX/PPTX files are not included.
- Product compiler creates 24 language editions and 72 printable HTML documents,
  packaged into six deterministic ZIPs. Edition hashes prevent silent changes to
  sold versions. Build reports and browser evidence are retained by Actions.
- Weekly Monday 05:17 UTC rebuild/validation/deployment plus ordinary push deploys.
  This is an authored-bank compiler, NOT autonomous creation of new topics. It
  makes no paid API calls and does not relabel reordered exercises as new products.
- Stripe Checkout adapter with CSRF, explicit digital consent, fixed server prices,
  idempotency, verified payment/amount/currency/edition and refund/dispute checks.
  Paid files are outside Flask public assets and denied by Apache .htaccess.

## Important remaining work

1. Full translation of older informational/topic/legal pages. Their shared navigation
   translates; the body remains English and is explicitly labelled. Main translated
   study, practice, level-check and product journeys are available now.
2. New-content generation: integrate the existing UrbanSky EFL pack-factory design
   through its canonical state/QA contracts when that implementation is available.
   An existing MainBuyer workflow `efl-claude-pack-factory-design.yml` was discovered;
   its target `automation/efl_pack_factory/` was absent from main during this work.
   This release does not interrupt or overwrite that work.
3. Payments: configure EFL_STRIPE_SECRET_KEY in the Passenger environment, verify a
   test checkout/download/refund and the account's receipt/tax/business settings,
   then verify the live connection and set EFL_SALES_ENABLED=1. Do not paste keys
   into chat or commit them. Checkout stays visibly unavailable until enabled.
   Stripe transaction fees apply on sales; the compiler has no API usage cost.
4. Human/native-language pedagogical review is still valuable before expanding the
   range. Automated checks validate structure, not certified educational quality.

## Validation and release

- `PYTHONPATH=flask_app python flask_app/test_learning.py`
- Full legacy build followed by `python validate.py` and `python test_learning.py`
- `python browser_learning.py` against the fully built app (Chromium required)
- Live checks for English existing routes, Spanish landing, Polish C2 practice,
  French shop, runtime identity, and direct paid-file denial.

## Operational details

The normal build copies the `learning` module and compiles `private_products`.
Keep production `storage/` and its secret key across deployments. Do not expose
private products via a CDN or copy them into `public/` or `assets/`.

Purchase access uses a private Stripe checkout-session URL. Treat it as a bearer
link. Downloads revalidate Stripe each time, are not cached, and send no referrer.
There is no webhook-based email fulfilment/recovery yet; the confirmation page
contains the download and the customer is asked to keep its private link.

To add a language: add a name in LANGUAGES, every UI row, every rule explanation,
validate the complete coverage and create new immutable product versions. To add
new exercises/topics, extend the authored bank and review educational ambiguity;
never edit a published edition without incrementing its version.

## Asian-language expansion — 14 October 2026

Added Hindi (`hi`), Urdu (`ur`), Pashto (`ps`), Simplified Chinese (`zh-Hans`)
and Traditional Chinese (`zh-Hant`). The Chinese options are written-script
variants, not spoken Mandarin/Cantonese audio courses. Nine language choices
now cover the translated study/shop/test UI and all 18 explanation rules across
A1–C2. Questions and writing prompts remain English.

Urdu and Pashto use RTL page/dialog layout; English questions, answers and inline
grammar terms retain LTR direction. The scrollable picker works on small screens.
Print editions preserve direction too. There are no external translation API calls.

Version 2 products include all nine language editions (54 level/language editions,
162 HTML documents). Version 1 remains reproducible byte-for-byte via frozen source,
so previous purchase hashes/downloads continue to work; archived listings redirect
to the current edition. Prices remain £3.99. Sales activation remains unchanged.
Legacy-page English-only disclosures still apply; these additions do not claim
that every older informational page has been translated.

Validation: complete locale/rule keys, all 54 customer route combinations,
English exercise direction, deterministic ZIP coverage, preserved v1 hashes,
Chromium mobile/RTL/picker checks for each added locale, print checks, and live
checks for all five new options in the deployment gate.
