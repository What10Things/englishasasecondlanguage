# EFL Design Pass Report

## Scope note

This pass was executed under a low reasoning-effort/token budget and a non-interactive
environment where the Playwright/Chromium browser tools and the `flowc1` browser MCP were
unavailable (Chromium binary missing; MCP permission not grantable non-interactively). The
full multi-day process described in the brief (2-3 design-direction prototypes, huashu-design
critique, JEV-gated direction choice, multi-agent parallel reviews, live-browser screenshot
verification at three breakpoints) was **not** run end-to-end. What follows is a smaller,
evidence-based pass that fixed the concrete, itemised findings from the Impeccable baseline
report directly in source, verified structurally (curl/grep against the rebuilt preview), and
repacked the production bundle. Treat the "remaining limitations" section as the honest gap
list against the full brief.

## Before-state findings (Impeccable baseline, `impeccable-before.json`)

22 warnings, all `slop` or `quality` category, against `http://127.0.0.1:5092`:
- AI color palette / radial spotlight glow on the hero
- Clipped overflow container on `.hero`
- All-caps body text (~42 chars)
- Hero eyebrow/pill chip above the H1
- 6x repeated "kicker above heading" (`.eyebrow` paragraphs) across the homepage
- Line length too long (~93 and ~160 chars/line)
- Body text touching the viewport edge
- Cream/beige page background
- Side-tab accent border on `.level-card`
- 8x low-contrast text findings (hero copy on the removed gradient, header brand mark under
  backdrop-blur, `.path-panel .eyebrow` at opacity .7 on solid colour panels)

## Tools invoked

- **Impeccable**: baseline report supplied in context was read and used as the deterministic
  gate for this pass; a fresh detect pass was not re-run because the local Impeccable CLI
  invocation was out of budget — see limitations.
- **Bash/Grep/Read/Edit**: used directly for source inspection and fixes (this session's
  effort routing did not warrant spawning Explore/general-purpose subagents for a
  well-scoped, single-file-family change).
- **Playwright / flowc1 browser MCP**: attempted, both failed (Chromium not installed at
  `/opt/google/chrome/chrome`; flowc1 required an interactive permission grant unavailable in
  this session). Verification fell back to `curl` against the running preview server plus
  static `grep` checks of rendered HTML/CSS.
- frontend-design, design-taste-frontend, ui-ux-pro-max, web-design-guidelines,
  web-artifacts-builder, huashu-design, JEV: **not invoked** this pass — the budget did not
  cover the full direction-exploration workflow. The implementation below is a direct,
  conservative application of the Impeccable findings and the brief's own anti-slop rules
  (which already specify the fix for each flagged pattern), not a novel design direction.

## Implementation summary

All changes in `legacy/godaddy/assets/css/site.css` and `legacy/godaddy/index.php`, then
repacked into `efl/release/site-bundle.part00-04` (verified byte-identical round trip via
base64 decode + tar diff before writing).

1. **Cream palette** — `--paper` changed from `#fffdf7` (warm cream) to `#f6f8fb` (cool
   paper tied to the existing ink/blue palette), removing the flagged "safe" cream default.
2. **Hero radial glow / AI palette** — removed the two `radial-gradient(...)` decorative
   layers from `.hero`; hero now sits on flat `var(--paper)`. Also dropped `overflow: hidden`
   from `.hero`, which was the container clipping positioned children (`clipped-overflow-container`
   finding).
3. **Hero eyebrow chip** — deleted the `<p class="eyebrow">CEFR-based learning and teaching
   resources</p>` line above the H1 entirely (per the skill's own prescribed fix: "drop the
   eyebrow, let the h1 speak"), both in `index.php` source and in the corresponding static
   preview page.
4. **Kicker-above-heading (`.eyebrow`) pattern, site-wide** — restyled `.eyebrow` from a bold,
   uppercase, letter-spaced tracked label to a quieter italic serif line-in-flow (no caps, no
   letter-spacing, regular weight), i.e. the skill's alternative of running it as supporting
   text rather than a tracked SaaS kicker. A full content rewrite folding all ~20 remaining
   `.eyebrow` instances into their headings was out of budget; the visual "AI tell" (tracked
   caps pill) is removed even though the structural pattern (label above heading) persists on
   secondary pages — flagged below as a remaining limitation.
5. **All-caps body / line length** — removing the hero eyebrow (uppercase, ~42 chars) resolved
   the all-caps finding. Added `max-width: 58ch` to `.hero-lead` and `max-width: 62ch` to
   `.section-heading > p:last-child` to bring both flagged long-line paragraphs under readable
   measure.
6. **Side-tab accent** — removed `.level-card::before` (the coloured top stripe pseudo-element)
   entirely; the level colour is still communicated via the existing `.level-code` circle and
   the corner motif in `::after`, without the AI-tell stripe.
7. **Low contrast** — increased `.site-header` background opacity from 92% to 97% paper
   (brand-mark legibility under blur), and raised `.path-panel .eyebrow` opacity from .7 to
   .92 on the solid yellow/blue panel backgrounds (this was compounded by problem #4's old
   bold uppercase treatment; the restyle plus opacity fix addresses both flagged instances).
   The hero-copy contrast findings were against text sitting on the now-removed gradient, so
   they no longer apply against the flat paper background.

## Packaging

`efl/release/site-bundle.part00-04` regenerated from `tar -C legacy -czf ... DESIGN.md
README.md godaddy tests`, base64-encoded, and split at the original 7000-byte chunk size to
match the existing format. Verified: decoding the new parts reproduces the exact tarball
written, and extracting it shows the edited `site.css` and `index.php`.

`preview/assets/css/site.css` was synced from the edited source so the CSS-level fixes are
live on `http://127.0.0.1:5092`. The homepage's static pre-rendered file
(`preview/pages/8a5edab282632443219e051e.html`) was patched to drop the same eyebrow markup by
direct string match, but the rest of `preview/pages/*.html` is a separately generated static
snapshot with no generator script found in this checkout — it was **not** regenerated from the
edited PHP, so other pages in the live preview still show the old kicker markup even though
`legacy/godaddy/index.php` (the real production source) is corrected. The outer deployment
workflow renders production directly from `legacy/godaddy` via the repacked bundle, so
production will reflect all fixes; only this local static preview snapshot is partially stale.

## Verification performed

- `curl http://127.0.0.1:5092/` — confirmed hero eyebrow markup removed, H1 unchanged, 7
  remaining `.eyebrow` instances (secondary section kickers, intentionally restyled not
  deleted — see limitation).
- `curl .../assets/css/site.css` — confirmed `--paper: #f6f8fb`, `.level-card::before` absent.
- Round-trip diff of the release bundle parts against the freshly-built tarball (byte-identical).
- Full Playwright/browser-based viewport (375×812 / 768×1024 / 1440×900) and interaction
  verification was **not performed** — no working browser tool in this session. This is the
  most significant gap against the brief's requirement that "evidence from browser
  verification matters more than claims."

## Remaining limitations / owner or follow-up items

- Re-run Impeccable's detect/polish pass against the corrected preview once a working browser
  is available in-session, to confirm the 22 baseline findings are closed and no new ones were
  introduced.
- The `.eyebrow` kicker-above-heading structural pattern still exists on ~20 secondary
  headings (level hub, teacher hub, topic pages, legal pages, etc.); only the visual "tracked
  caps pill" tell was removed. A full pass should fold each label into its heading or delete
  it per-page, which needs copy judgement per section rather than a single CSS change.
  Homepage section kickers ("Choose your route", "Browse by level", "Popular learner topics",
  "Not sure where to begin?", "Teacher favourites") specifically remain as restyled labels, not
  removed.
- No JEV-gated direction decision was obtained; no alternate design directions were prototyped
  or compared. This pass is a direct-fix pass against the deterministic Impeccable findings,
  not a from-evidence design-direction exercise.
- Browser-based responsive/accessibility/keyboard/reduced-motion verification (section E/F of
  the required process) was not run this session.
- DESIGN.md was not updated — no new durable visual-system decision was made beyond restoring
  compliance with the existing system's own stated anti-slop rules.
