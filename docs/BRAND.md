# AFTERLIGHT brand and thumbnail

The **Sun Receipt** combines a coral sunset, a violet torn receipt, two ledger lines, and a check cut out of the paper. It connects the project's solar source to its inspectable evidence. The wordmark uses custom spacing and outlined Bricolage Grotesque glyphs; the SVG does not require a font installation.

## Deliverables

- `artifacts/brand/afterlight-logo-primary.svg` — editable horizontal logo, outlined lettering.
- `artifacts/brand/afterlight-logo-primary.png` — high-resolution transparent logo.
- `artifacts/brand/afterlight-icon-primary.svg` and `.png` — standalone transparent symbol.
- `artifacts/brand/afterlight-logo-reversed.*` — coral/lime/white for dark backgrounds.
- `artifacts/brand/afterlight-logo-mono.*` — one-color ink logo.
- `artifacts/brand/afterlight-logo-white.*` — white logo for solid dark backgrounds.
- `artifacts/brand/afterlight-app-icon.png` — 1024 px square violet avatar.
- `artifacts/brand/afterlight-brand-board.png` — visual identity overview.
- `artifacts/thumbnail/afterlight-youtube.jpg` — lightweight YouTube thumbnail, 1672 × 941.
- `artifacts/thumbnail/afterlight-youtube.png` — original full-resolution generated thumbnail, under 2 MB.
- `artifacts/afterlight-media-kit.zip` — logos, thumbnail, this guide, the generation brief and font license.

The website uses the primary SVG and a matching favicon. The motion film uses the same logo and refreshed actual interface captures.

## Use

Keep at least half the sunset's diameter as clear space around the symbol. Preserve its proportions and negative-space check. Use the reversed version on dark violet; use the mono version when only one ink is available. Keep the wordmark's coral terminal dot.

Palette: ink `#2b1845`, violet `#713ce4`, coral `#ff784f`, lime `#c7ff74`, yellow `#ffdd65`. Typography is Bricolage Grotesque; its SIL Open Font License is included.

## Provenance and reproduction

The logo is original repo-native vector artwork generated with `scripts/brand.py`. PNGs preserve transparency. To reproduce the logo exports, install FontTools, make it available on the Python path (or under `.tooling/python`), and run that script. Pillow is also required. The supplied SVG files contain paths rather than live font text.

The thumbnail was generated using the built-in imagegen tool, with the brand board as the visual reference. Its exact prompt is recorded in `docs/THUMBNAIL-PROMPT.md`. The JPEG is a format-only export of the generated image at unchanged pixel dimensions; the composition has not been cropped or altered.
