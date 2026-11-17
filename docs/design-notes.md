# Design notes (from collabstr.com/design-system)

Tokens copied into `briefs/static/briefs/css/app.css` (names kept so they map 1:1 to the DS):

- **Font:** Inter, fallbacks `-apple-system, system-ui, Segoe UI, Roboto, sans-serif`. Body 16px/#222.
- **Text:** default `#333` (`--bw-black`), subtle `--gray-600 #535862`, subtlest `--gray-500 #717680`,
  placeholder `--gray-400 #A4A7AE`.
- **Brand pink:** `--pink-500 #FB669D` (brand-500, focus borders, text-brand), `--pink-600 #FF4C8E` (brand button),
  `--pink-100 #FFE7E6` (brand badge bg) with `--pink-700 #FF2A79` text.
- **Surfaces:** white; secondary `--gray-100 #F5F5F5`; borders default `--gray-300 #D5D7DA`, subtle `--gray-200 #E9EAEB`.
- **Semantic:** success `--green-700 #027A48` (bg at 8%), error `--red-600 #D92D20` (bg at 8%).
- **Buttons (`ds-btn`):** 14px/600, padding 12px 24px, radius 8px, shadow-sm. Primary = `#333` bg, white text.
  Secondary = white bg, gray border. Ghost = transparent.
- **Inputs:** 16px, padding 12px 16px, radius 8px, 1px `--gray-300` border, focus border `--color-brand-500`.
- **Labels:** 14px/500 #333. Helper text subtlest.
- **Cards (`ds-card`):** white, radius 12px, shadow-md `rgba(120,120,170,.15) 0 2px 16px 0`.
- **Option card:** radius 12px, 2px border; selected = 2px `#333` border + `0 0 0 3px rgba(51,51,51,.08)` ring;
  icon tile tinted brand-500 at 12%.
- **Tag (`ds-tag`):** pill, `--gray-100` bg, `--gray-200` border, 12px/500 `--gray-700` text.
- **Badge brand:** `--pink-100` bg, `--pink-700` text, 10–12px/600.
- **Toast:** white, radius 4px, shadow-xl, success text green-700.
- **Alert:** 16px padding, radius 4px, semantic bg at 8%.
- **Spacing:** 4/8/12/16/24/32/40/48. **Radii:** 4/8/12/16/20/9999.
- **Motion:** fast 150ms, normal 300ms; `ease-out cubic-bezier(0,0,.2,1)`; shimmer for skeletons; respect reduced motion.
- **Platform colours:** Instagram `#D756FF`, TikTok `#FF5FA3`.
- **Icons:** Lucide (inline SVG, `aria-hidden`).
