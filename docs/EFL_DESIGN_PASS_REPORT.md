# EFL design pass report: high-effort completion pass (24 September 2026)

This report replaces the earlier partial pass. That pass fixed a handful of Impeccable findings. It did not use
the design skills, JEV, sub-agents or a real browser. This pass treated every limitation it listed as backlog.
Tool evidence is itemised in `docs/EFL_DESIGN_TOOL_EVIDENCE.json`.

## 1. Before-state findings

Playwright baseline: 11 routes at 375×812, 768×1024 and 1440×900. Routes: home, level test, learner hub, A1,
B2, grammar, teacher hub, lesson plans, shop, starter pack, product.

- **The brand fonts never rendered in production.** The live `Content-Security-Policy` (`style-src 'self'`)
  blocks `fonts.googleapis.com`. Every page logged a CSP error and fell back to Georgia and the system sans
  (confirmed against the live site with `curl -I`).
- **Generic neobrutalist template.** Isolated Impeccable critique sub-agent (Assessment A): the site fails the
  design-specificity test. Evidence: hard 4px offset shadows on every button and card, a rotated sticker brand
  mark, a decorative blob-and-orbit hero with floating "15 min / 2 paths" notes, a Fraunces/DM Sans template
  pairing, and 8+ competing calls to action in the first viewport. The only subject-specific device was the
  CEFR meter on level pages.
- **Card walls.** The teacher hub on mobile was 5,351px of eight identical cards, each with a redundant "TEACHER" pill.
- **Detector (Assessment B, isolated sub-agent): 61 findings across 5 routes.** 33 low-contrast (brand text
  under the backdrop-blur header), 12 body-text-viewport-edge (the unstyled company disclosure injected by the
  Flask build), 5 line-length, 2 text-occlusion (hero stickers), an oversized 102px H1, radial glow,
  gradient product covers and the overused Fraunces font.
- **Internal developer copy shown to customers:** "The shop framework is ready for product files and checkout
  integration" and "Connect your chosen payment/download service before accepting orders". The homepage also
  called the fixed-order test "adaptive".
- **Kicker labels above almost every heading** (14 `.eyebrow` instances in the templates, plus one in the build script).

## 2. Skills and tools actually used

Each skill was loaded from its installed `SKILL.md`. This session exposes no `Skill` tool, so the files were read
directly and their commands and scripts run.

| Tool | What it did in this pass |
|---|---|
| impeccable | Ran `impeccable context`. Loaded the craft floor and the critique method. Ran the critique as two isolated sub-agents (A: design review; B: detector over 5 routes plus the source). The detector was re-run after implementation as the quality gate: 61 → 10 → fixes (§7). |
| frontend-design | Two-pass method. Wrote a token/type/wireframe plan for three directions, then reviewed it against the generic-default list (cream + serif, tracked kickers, SaaS card kit, single-word accents). Result: the `<em>` accent in the H1 was dropped, the eyebrows removed and the card walls replaced with index rows. |
| design-taste-frontend | Its AI-tells list drove removing the oversized H1s (6.8rem → 4.25rem max), the "3 equal cards" rows (topics, lessons, levels) and the section numbering on About. Its React/Tailwind/Framer defaults were overridden by the no-build-chain constraint. |
| ui-ux-pro-max | `--design-system` query for the product. It returned indigo `#4F46E5`, a testimonials carousel and Baloo/Comic Neue, all rejected (AI-purple, fabrication ban, adult audience). Targeted `typography` and `ux` queries kept the 65–75ch measure, progress-indicator and line-height rules, and surfaced Newsreader ("News Editorial") as the fallback display face. |
| huashu-design | Direction and critique only. Three differentiated directions rendered as real visuals. Its anti-slop table (no geometric masks, no filler data, iconography slop) was used to reject the orbit hero. JEV made the choice instead of a human stop, as the brief directs. |
| web-artifacts-builder | `init-artifact.sh` and `bundle-artifact.sh` (React + Tailwind + shadcn, in `/tmp/efl-proto`). One temporary prototype of the homepage hero and routes in all three directions (`?d=a|b|c`), screenshotted at 1440 and 375, then translated back into PHP/CSS. The prototype and its server were deleted. |
| Playwright | Node Playwright (Chromium) scripts: baseline and after screenshots of 11 routes × 3 viewports, font-load and console checks, a glyph test that caught Literata's ambiguous "1", and interaction runs (§6). |
| web-design-guidelines | Fetched the current Vercel `command.md` and reviewed the changed templates and CSS against it (§7). |
| JEV | `jev_check_research` decision on the direction (§3). |
| Sub-agents | 2 critique assessments, 4 post-implementation reviews (§5). All Sonnet, read-only, with no nested spawning and at most two concurrent. |

## 3. JEV decision

- Initial advisory (routing, supplied with the brief): `opus-medium`, confidence 0.58.
- **Direction decision (after evidence gathering, before implementation):** `jev_check_research` on the claim
  "Direction A 'Graded reader' site-wide, B's gap-fill only inside the level test, C rejected". Seven evidence
  items were supplied (baseline, both critique assessments, CSP finding, prototype screenshots, UI/UX Pro Max
  output, font rationale).
  **Result: `decision: accept`, confidence 0.63 (accept 0.75 / verify_more 0.22 / reject 0.03).**
- `jev_decide` (custom choice question) was attempted first. It rejected every option schema tried ("provide 2–255
  choice options"), so no result from it is claimed. The accepted decision above is the genuine JEV decision used.
- Completion review: see §9.

## 4. Chosen direction: "graded reader", and why

Three directions were prototyped on the real content:

- **A, Graded reader:** calm reading-first system. The real CEFR ladder is the hero.
- **B, Workbook:** a gap-fill headline ("I want to learn English at ___ level") with level chips, on ruled
  paper. Memorable, but costume-like. The headline wrapped badly and teachers were pushed below the fold.
- **C, Route map:** a transit line. Its idioms ("board at your level", "change at any station") are hard for A1
  readers, and the line collapsed on mobile.

A won because every prominent element is also navigation. At 1440 the learner CTA, a teacher route and all six
levels sit above the fold; at 375 the CTA and the first levels do. B's gap-fill survives where it is native: the
level test writes the chosen answer into the sentence.

Typography: **Newsreader** (display) + **Atkinson Hyperlegible Next** (body), both OFL and self-hosted.
Literata was implemented first, but a Playwright glyph test showed its figure one is identical to "l", so
"A1" read as "Al". That is unacceptable on a site navigated by level codes, and Newsreader's footed 1 fixed it.
Atkinson Hyperlegible is built for letterform distinction, which suits second-language readers.

## 5. Implementation summary

Source edited: `legacy/godaddy/index.php`, `assets/css/site.css` (a token-based rewrite of the system),
`assets/js/level-test.js`, new `assets/fonts/` (two woff2 files, about 166KB, plus OFL licences),
`efl/flask_app/build_from_legacy.py`, `DESIGN.md` (both copies). The bundle was repacked as
`release/site-bundle.part00–37`.

- **Fonts:** Google Fonts removed. Fonts are self-hosted and preloaded, so the CSP stays strict and there are no
  third-party requests. The privacy notice now says fonts are served from this website, and "font delivery" was
  removed from its list of recipients.
- **Header:** the announcement bar is gone, the header is solid (no backdrop blur), and "Find my level" stays
  outside the collapsed mobile menu. The brand mark is no longer rotated or shadowed. The drawer is positioned
  from the header, not a magic offset.
- **Home:** H1 plus lead plus one primary CTA and an "I teach English" route, with the six-row CEFR ladder
  (`level_ladder()` helper, can-do line per level) as the hero. Then a ruled skill index, then a teacher block
  (free starter pack as the teacher's primary action, shop secondary, four teaching areas plus "All teaching
  areas"), then one closing test band. The path panels, the duplicate 3×2 level card grid and the trust row were removed.
- **Level pages:** the CEFR meter is now a six-link level switcher with `aria-current`, labelled "level n of 6".
  It no longer uses the flagged 5px top-border tab.
- **Hubs:** the learner hub uses the ladder with summaries. The teacher hub, topic lists and lesson lists are
  two-column ruled index rows (the teacher hub on mobile went from 5,351px to 3,065px). No audience pills.
- **Level test:** the chosen answer fills the blank. The progress bar animates `transform` instead of `width`.
  Flat card, no hard shadow. The result heading reads "Estimated level: B1 Intermediate".
- **Shop and product:** flat covers (level code plus format), no gradients. The copy is now honest ("Checkout is
  not open yet", "Not on sale yet") and routes to the free starter pack instead of a dead "Coming soon" button.
- **Global:** all 15 kicker labels removed (dates are now `.meta` after the H1), About's non-sequential 01/02/03
  numbering removed, the grain overlay removed, one authored motion moment (the ladder rows enter in sequence,
  visible by default, off under reduced motion), themed `::selection`, caret and `accent-color`, blue focus ring
  on light and yellow on dark, `scroll-padding-top` for the sticky header, 44px targets, the footer disclosure styled.

## 6. Sub-agent review findings and fixes

| Review | Finding | Disposition |
|---|---|---|
| Regression / deploy (reproduced CI) | `validate.py` asserted the removed copy "Two clear journeys" and "Teacher hub". **CI would have failed.** | Fixed: the assertions now check stable new copy. `validate.py` exits 0 (`{"pages": 91, "status": "ok"}`). |
| Regression / deploy | The 404 page skipped `apply_compliance_updates`/`add_company_disclosure`, so the cookie banner leaked and there was no disclosure (pre-existing). | Fixed in `build_from_legacy.py`. 0 pages now contain the banner, and 404 has the disclosure. |
| Regression / deploy | Round trip, `php -l`, smoke test (12 routes), consent fields, CSP/no external origins, no temp files. | Pass. |
| A11y / responsive (Playwright) | Footer links and the brand link were 37–39px tall at 375. | Fixed: 44px minimum. |
| A11y / responsive | Non-current level-meter link contrast reported at 2.77:1. | Fixed defensively (full ink colour). |
| A11y / responsive | Menu `aria-expanded`, skip link first, visible focus, gap-fill, 24-question completion, reduced motion, no overflow at 320px. | Pass. |
| Anti-slop / type | "`/learn-english/` never migrated" (P0). | **Rejected after verification:** the rendered HTML has the ladder and no orbit, eyebrow or pill markup, and the screenshot hashes differ. It was a misread. |
| Anti-slop / type | Three different labels for the level-test CTA. | Fixed: "Take the free level test" everywhere except the compact header "Find my level". |
| Anti-slop / type | Test card shadow. | Removed earlier by the detector gate. |
| Anti-slop / type | Product cards; green can-do ticks. | Kept: `DESIGN.md` reserves cards for selectable products, and the ticks mean "achievement". |
| Journeys (Playwright) | The result screen went straight into an email form, with the study link buried below it. | Fixed: "Study A2 English" is the primary action, with "Take the test again". The form is headed "Email yourself this result (optional)", and focus moves to the result heading. |
| Journeys | "Start studying" was vague (its #study anchor works; the reviewer caught the page mid-scroll). | Relabelled "See B2 grammar and vocabulary". |
| Journeys | Level pages link to level-agnostic grammar/vocabulary hubs. | Not changed: this is content architecture, not design (see limitations). |

## 7. Browser verification (Playwright, Chromium)

- **Viewports:** 375×812, 768×1024, 1440×900 (plus 320px overflow checks by the a11y reviewer).
- **Routes screenshotted before and after:** `/`, `/english-level-test/`, `/learn-english/`,
  `/learn-english/a1/`, `/learn-english/b2/`, `/learn-english/grammar/`, `/teach-english/`,
  `/teach-english/lesson-plans/`, `/shop/`, `/shop/product/a1-grammar-worksheet-pack/`, `/teacher-starter-pack/`.
  Final: both self-hosted fonts loaded on 33/33 renders, 0 console errors (baseline had a CSP error on every
  page), no horizontal overflow.
- **Interactions at all three sizes:**
  - the mobile/tablet menu opens and closes, with `aria-expanded` updating
  - hero ladder → B1 page; level meter → B2 with `aria-current`
  - header "Find my level" → test; choosing an answer fills the sentence gap and enables Next
  - all 24 questions → result screen with the study CTA and the optional form
  - "I teach English" → teacher hub → Worksheets → shop → product → "Get the free starter pack" → form
  - the form's HTML5 validation blocks an empty or invalid email; the form was not submitted
- **Keyboard and motion:** skip link first, then the header links in order, each with a visible 3px focus ring.
  With reduced motion there are 0 running animations.
- Page height at 375: teacher hub 5,351 → 3,065px. At 1440: home 6,180 → 2,786px, with every original route
  still reachable.

## 8. Impeccable and Vercel audit outcomes

- **Impeccable detector (same routes as the baseline):** 61 → 10 → **1**. The remaining finding is `cramped-padding`
  on the shop tab strip, a false positive: the active underline sits on the rule by design. Source scan: 1 → 0.
  The 10 intermediate findings were fixed: padding transition on the ladder, thin border with a wide shadow,
  disabled-button contrast, and footer measure.
- **Vercel web-interface guidelines** (fetched fresh). Applied: `scroll-padding-top` for the sticky header,
  `touch-action: manipulation` and an intentional tap highlight, `spellcheck="false"` on email inputs,
  `translate="no"` on the brand, `theme-color` matching the page, font preload with `swap`, transitions
  listing explicit properties, visible `:focus-visible` everywhere, `aria-live` on form status (already present).
  Not applicable or declined: Title Case (the site uses British sentence case), `Intl` date formatting (the dates
  are static legal text).

## 9. Remaining limitations

- **JEV:** `jev_decide` rejected every custom-question schema tried, so the direction decision came from
  `jev_check_research` (accept, 0.63). The final `jev_review_completion` was attempted three times with 60–75s
  back-off and returned "Too many requests" each time, so **no completion review from JEV is claimed**. The
  remaining two retries allowed by the brief were not used because of the job's turn cap.
- **Skills:** this session exposes no `Skill` tool. Every required skill was loaded by reading its installed
  `SKILL.md` and running its bundled scripts (Impeccable CLI, UI/UX Pro Max search, the artifact
  init/bundle scripts).
- **Browsers:** only Chromium was tested. Safari/iOS and Firefox rendering of the variable fonts and `color-mix()`
  was not verified. `color-mix()` needs Safari 16.2+ and is used only for tints.
- **Content, not design:** level pages link to level-agnostic grammar and vocabulary hubs, and topic lesson rows
  all point to the level test. Level-filtered content pages would improve the learner journey.
- **Commerce:** checkout, product files and prices are still not live. The site now says so plainly and routes
  teachers to the free starter pack. Nothing was fabricated.
- **Payload:** the fonts add about 166KB (woff2, preloaded, cached for a day by Flask). The Google Fonts CSS and
  third-party connections are gone.
- **Size:** the release bundle is now 38 base64 parts (it was 5) because of the font binaries. CI's
  `cat release/site-bundle.part*` handles this unchanged, and the round trip was verified byte for byte.
- Nothing was committed, pushed or deployed. Temporary screenshots and prototypes live only under `/tmp`.
