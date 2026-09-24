# EFL by Level — Owner actions required

These items genuinely need the owner or access to an external account/service.
Nothing in this list can be safely completed from inside the repository.

1. **Write real content for the seven/eight "skill hub" pages** (Business
   English, grammar, IELTS, listening, reading, speaking, vocabulary, writing
   under `/learn-english/...`). Every topic card currently repeats the same
   placeholder sentence and links only to the level test. Claude will not
   invent lesson content, teacher claims, or examples on the owner's behalf —
   this needs real subject-matter input.
2. **Decide the level-test no-JavaScript fallback experience.** The test is
   currently a dead end without JavaScript. Fixing this well requires a
   product decision (e.g. "show a static first question and a link to enable
   JS" vs "show a short explanatory message") before it's built.
3. **Set a `SECRET_KEY` GoDaddy/Passenger environment variable** (optional
   but recommended). The app now generates and persists its own key if none is
   set, so this is not required for correctness, but the owner may prefer to
   set `SECRET_KEY` explicitly via cPanel's Python app environment variables
   for operational clarity.
4. **Add a scheduled GoDaddy cron job to prune old submissions** independent
   of new form activity, so the published 24-month retention promise in the
   privacy policy holds even during quiet periods with no new leads. This
   needs access to the GoDaddy cPanel cron interface.
5. **Review and approve the sitemap/SEO build-pipeline changes** flagged in
   `CLAUDE_EFL_REVIEW.md` (full sitemap regeneration from crawled routes,
   JSON-LD/canonical validation) before they are implemented — these touch the
   generated HTML for all 91+ live pages and should not ship without a look at
   a rendered sample first.
6. **Review the CSRF-hardening approach** for the lead form before it's built:
   because pages are pre-rendered at build time rather than per-request, a
   proper fix means changing how forms are rendered (a build-time nonce
   refreshed periodically, or moving to per-request rendering for pages with
   forms). Either has trade-offs worth an owner decision before implementation.

No DNS, billing, third-party dashboard, or credential changes were made or are
required beyond the above.
