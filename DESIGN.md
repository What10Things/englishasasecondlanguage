# EFL by Level design system

## Direction: "graded reader"

A calm, reading-first education brand. The CEFR scale itself is the signature device: the homepage hero is the
A1–C2 ladder (six linked rows with a can-do line each), and every level page carries the same scale as a
clickable meter. Decoration must be navigation or data; if it is neither, it goes.

Chosen in September 2026 over two prototyped alternatives ("workbook" gap-fill hero; "route map" transit line)
after browser comparison and a Jev decision. The workbook gap-fill survives in one place only: the level test
writes the chosen answer into the sentence gap.

## Tokens (assets/css/site.css `:root`)

- Colour: ink `#15263a`, ink-soft `#44566b`, paper `#f7f8fa`, surface `#ffffff`, rule `#d6dde6`,
  action blue `#1f56c9` (links/buttons only), yellow `#ffd166` (brand mark, selection, focus on dark),
  learner tint `#edf3fd`, teacher tint `#fff6dc`, night `#0d1b2b` (footer and CTA bands).
- Level colours (content.php) are used only for level codes, the ladder and the level meter.
- Type: **Newsreader** (display, optical sizes) + **Atkinson Hyperlegible Next** (body/UI), both OFL and
  self-hosted in `assets/fonts/` because the CSP only allows `'self'`. Do not reintroduce Google Fonts.
  Newsreader was chosen over Literata because Literata's figure one is indistinguishable from "l" ("A1" read as "Al").
  Atkinson Hyperlegible is designed for letterform distinction, which suits people reading in a second language.
- Scale: h1 `clamp(2.35rem … 4.25rem)`, h2 `clamp(1.7rem … 2.6rem)`; body 17px (16px on phones); measure ≤ 62ch.
- Radius: 4px controls, 8px panels. No hard offset shadows; elevation is a 1px rule, not a shadow.

## Principles

1. **Two routes are always visible:** the hero has the learner CTA, a teacher link and all six levels.
2. **Level is the navigation system:** the ladder and meter link to every level; codes use a stable colour.
3. **Lists before cards:** topics, teaching areas and lessons are ruled index rows. Cards are only for
   selectable products.
4. **No kicker labels above headings.** Put dates and small facts in flow as `.meta` text after the heading.
5. **One authored motion moment:** the hero ladder rows enter in sequence (CSS, visible by default,
   disabled under `prefers-reduced-motion`). Everything else is state feedback only.
6. **Honest commerce copy:** never imply checkout, stock or prices are live when they are not.

## Quality requirements

- keyboard-visible focus (blue ring on light, yellow on dark sections), skip link, `scroll-padding` for the sticky header
- minimum 44px interactive targets; the "Find my level" button stays outside the collapsed mobile menu
- no grey text over saturated backgrounds; body text ≥ 4.5:1
- mobile-first navigation and wrapping; no horizontal overflow at 320px
- no decorative dependency on external images or third-party requests
- clear error, consent and empty-state copy
