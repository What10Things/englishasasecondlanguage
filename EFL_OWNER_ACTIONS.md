# EFL by Level — Owner actions required

Updated 2026-09-24 (continuation pass). Every previously-listed item that could
be resolved in-repository at zero cost has been implemented and tested — see
`CLAUDE_EFL_REVIEW.md` for details. What remains genuinely needs the owner or
an external account/service.

1. **Set a `SECRET_KEY` GoDaddy/Passenger environment variable (optional).**
   The app generates and persists its own key if none is set (unchanged from
   the previous pass), so this is not required for correctness or security —
   purely an operational-clarity preference if the owner wants one fixed value
   rather than an auto-generated one.
2. **Write real lesson/worksheet content behind the skill-hub cards**, if and
   when the owner wants to go beyond the current level. This pass replaced the
   identical placeholder sentence on every card with topic-specific
   descriptions of what each item covers (see `CLAUDE_EFL_REVIEW.md`), which
   resolves the "thin/repetitive" finding. Turning each card into an actual
   lesson page is a content-production decision for the owner/content team,
   not a code defect.
3. **No further owner action is needed for CSRF hardening, the level-test
   no-JS fallback, the sitemap, retention pruning, or structured data** — all
   were implemented and tested this pass without needing credentials, legal
   approval, payment or account access.

No DNS, billing, third-party dashboard, or credential changes were made or are
required beyond the above.
