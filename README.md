# ANKLE360 storefront prototype

Visual direction: sports performance, in the lane of Hyperice, Therabody, and Peloton.
Black header and dark full-bleed sections, spotlit media behind condensed uppercase
headlines, big stat callouts, and ANKLE360 orange as the single accent.

Mobile-first prototype of the ANKLE360 Shopify theme, US market first. Built to deploy to
GitHub Pages for stakeholder review, and written so the HTML, CSS, and JS port into a Shopify
Online Store 2.0 theme with minimal change.

## Deploy to GitHub Pages

1. Create a new GitHub repo and push the contents of this folder to the `main` branch.
2. In the repo: Settings > Pages > Build and deployment > Source: **GitHub Actions**.
3. Every push to `main` runs `.github/workflows/pages.yml`, which runs `python build.py`
   and publishes the `site/` folder. The URL appears in the Actions run and in Settings > Pages.

GitHub Pages is free for public repos; a private repo needs a paid GitHub plan.

## Build process

There's one small build step, and GitHub runs it for you. `build.py` uses only the Python
standard library (no npm, no installs). It:

- assembles each page from `layout/theme.html` + `partials/` + `pages/` (like Shopify's layout and sections),
- generates the illustrations in `assets/img/`,
- writes the deployable site to `site/` and single-file review copies to `preview/`.

`site/` and `preview/` are build output and are git-ignored. Edit the source folders, not `site/`.

Run it locally to check changes before pushing:

```
python3 build.py
python3 -m http.server 8000 --directory site
# open http://localhost:8000
```

Serve through `http.server` rather than double-clicking the HTML file: some browsers and in-app
viewers block scripts or video on `file://` pages.

**Only needed when you change the video:** `tools/build_montage.py` and `tools/prepare_hero_video.sh`
need ffmpeg. The rendered videos are already in `assets/video/`, so deployment doesn't need ffmpeg.

## Repo layout

```
.github/workflows/pages.yml   deploys site/ to GitHub Pages
assets/                       CSS, JS, images, video (copied as-is to site/assets)
layout/theme.html             page shell        → Shopify layout/theme.liquid
partials/                     header, footer, consent → Shopify sections/snippets
pages/                        page bodies       → Shopify templates + sections
tools/                        video scripts (optional, need ffmpeg)
build.py                      assembles site/ and preview/
```

## Pages

| Page | File | Shopify template |
|---|---|---|
| Home | `index.html` | `templates/index.json` |
| Product | `product.html` | `templates/product.json` |
| Training plan | `training.html` | `templates/page.training.json` |
| Customer stories | `stories.html` | `templates/page.stories.json` |
| Cart | `cart.html` | `templates/cart.json` (checkout stays Shopify's) |
| Contact | `contact.html` | `templates/page.contact.json` |
| Policies | `policies.html` | Shopify-generated `/policies/*` |
| Not found | `404.html` | `templates/404.json` |
| Device preview | `devices.html` | Prototype only |

## Foundations

### Breakpoints (mobile first, `min-width`)

| Name | Min width | Devices | Grid columns |
|---|---|---|---|
| base | 0 | Phones, 360–479px | 4 |
| sm | 30em / 480px | Large and landscape phones | 4 |
| md | 48em / 768px | Tablets, portrait | 8 |
| lg | 64em / 1024px | Tablets landscape, small laptops | 12 |
| xl | 80em / 1280px | Laptops, desktops | 12 |
| 2xl | 90em / 1440px | Large desktops | 12 |

Media queries use `em` (resolved against the 16px browser default). CSS variables can't be
used inside media queries, so these values are the canonical list.

### Units and sizing

- Root font size is the browser default, 16px (`html { font-size: 100% }`), so **1rem = 16px** and user font-size settings are respected.
- All type, spacing, padding, margins, radii, and controls are in `rem`. Hairline borders stay `1px` so they never blur.
- Tokens step up per breakpoint in `tokens.css`: type scale, section spacing, page gutter, grid columns, and grid gap. Components never hard-code sizes.

| Token | base | md | lg | xl |
|---|---|---|---|---|
| `--text-base` | 1rem | 1.0625rem | | |
| `--text-2xl` (h2) | 2.25rem | 3rem | 3.75rem | |
| `--text-3xl` (page h1) | 3rem | 4rem | 5rem | |
| `--text-display` (hero h1) | 3.5rem (4 at sm) | 5.5rem | 7rem | 8.5rem |
| `--section-gap` | 3.5rem | 5rem | 6.5rem | 8rem |
| `--gutter` | 1.25rem (1.5 at sm) | 2rem | 2.5rem | 3rem |
| `--grid-gap` | 1rem | 1.5rem | 2rem | |

### Grid skeleton (`assets/layout.css`)

Every page is `section.section > .container > .grid > children`.

- `.grid` has 4 / 8 / 12 columns by breakpoint.
- Children are full width by default. Add spans per breakpoint: `span-2` (phones), `md-span-4` (tablets), `lg-span-6` (laptops and up), `lg-start-7` to offset.
- A span class with no smaller partner stays full width below its breakpoint, so `md-span-4 lg-span-3` reads as "full on phones, half on tablets, quarter on laptops."
- Vertical rhythm comes only from `.section` padding and `.stack` gaps, never component margins.

### CSS files, in load order

`reset.css` → `tokens.css` → `layout.css` → `theme.css`. Swap a brand by editing `tokens.css` only.

## Requirements covered

**Semantic HTML:** landmarks, one `h1` per page, ordered headings, `ol` only for real sequences, `dl` for specs and story fields, `table` with `caption`/`scope`, `fieldset`/`legend`, native `details` and `dialog`.

**Accessibility baseline:** skip link, visible focus, AA contrast, 44px touch targets, labeled controls, live-region announcements for cart and forms, reduced-motion support, meaningful alt text on every image.

**Cookie consent (US + California):** opt-out model, Global Privacy Control honored, "Your privacy choices" in the footer, choices forwarded to Shopify's Customer Privacy API, and consent-gated scripts via `<script type="text/plain" data-consent="analytics">`. Compare against Shopify's native banner before launch, and have counsel review.

## Illustrative content to replace before launch

This content is realistic so stakeholders can review the site as the MVP, but it isn't real:

- **Customer stories, quotes, and reviews** (names, results, "4.8 from 126 reviews"). Publishing invented testimonials or ratings on a live store violates FTC rules, so these must be real before launch.
- **Unconfirmed product facts:** weight (1.4 lb), 1-year warranty, ship-from location, 30-day return terms, free shipping, team pricing at 10+.
- **Difficulty mechanism:** assumed base only, then add one ring per level.
- **Images:** flat illustrations in `assets/img/` stand in for product photography and the hero video.
- **Contact emails and hours.**
- **Variant IDs** `40000000000001`–`4`.

The prototype sets `noindex` and shows a "Prototype for review" line in the footer. Remove both in the Shopify theme.
