# EFL by Level design system

## Direction: independent language workbook

October 2026 redesign requested by the site owner. Warm paper, strong sans-serif typography,
cobalt ink and ruled indexes replace the previous generic education styling.

- Identity: custom lower-case efl. wordmark with “by level” and a square progression mark.
  Source SVG: flask_app/learning/assets/logo.svg; also used as the favicon.
- Site-wide override: flask_app/learning/assets/identity.css, loaded after legacy styles.
- Colours: paper #f5f3ed, surface #fffefa, ink #202321, cobalt #263bd5.
- Typography: self-hosted Atkinson Hyperlegible Next, with native-script system fallbacks.
- Compact level indexes and clear English exercises. Muted book covers identify A1–C2 resources.
- Sharp rules, small control radii, generous whitespace. No decorative gradients or card walls.
- Nine-language picker, persistent preference, native names and RTL layout for Urdu/Pashto.
- English questions retain LTR direction. Existing downloadable editions remain immutable.

## Quality requirements

Keyboard focus, accessible labels, visible language control, mobile menu, no horizontal overflow
at 320px, and reduced-motion support. Browser release checks capture desktop and mobile versions,
including native scripts and RTL. Commerce copy must reflect the actual checkout state.
