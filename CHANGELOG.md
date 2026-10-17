# Changelog

All notable changes to this project will be documented in this file.

## v3 (2026-10-17)

Fixes found by publishing a project with Mobirise 6.1.12:

- Padding options (Top / Bottom) now go from 0 to 4 in steps of 45 px, default 2 (90 px). Mobirise resets padding options to 2 when a block is added, which gave 30 px sections with the previous 0-9 scale
- Images in blocks no longer break on publish (a data URI in an img tag was rewritten as a relative path); blocks use the extension's own placeholder image
- The contact form's Send button was invisible (the theme sets font-size: 0 on button containers); buttons now have a fallback font size
- The demo site is generated from the current block sources and uses smaller theme text sizes

## v2 (2026-10-17)

- Blocks now appear in the "Add Block" menu, in a "Skyline" group (native components: template.html, style.less, thumb.png)
- Shared stylesheet loaded through a plugin
- Fixed button variants (outline, primary, sky, light) being overridden by the base button rule of a later block
- Added a demo site (examples/demo-site) and the tools to generate and check it

## v1 (2026-10-17)

- First version: gallery button in the Mobirise top bar with 21 blocks in 13 groups (menu, hero, text, venue, notice, cards, goodies, perks, teams, steps, pricing, support levels, rates table, programme, gallery, FAQ, contact form, call to action, two footers)
