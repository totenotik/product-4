# SOUWERS formulary

- Current release: Formulary 2.7.0 and account iframe bridge 1.0.3.
- Editable sources live in `src/`. Run `npm ci` and `npm run build` to regenerate the versioned assets in `scripts/`.
- Installation blocks for Tilda live in `tilda/`. Preserve the existing Premium gate and template mounting.
- `npm run build` also refreshes the separately downloadable, versioned files and numbered T123 text snippets in `files/`.
- Original files supplied on 2026-11-03 are preserved in `archive/input-2026-11-03/`.
- Work in a task branch. A local file or local commit is not a remote backup; report the pushed branch and commit when saving to GitHub.
- Browser checks: `npm run test:browser` (Python Playwright and Chromium required). All browser network requests are intercepted by the test harness. Never use the live checkout to test purchases.
- Do not change formula calculations, IFRA handling, material matching or mixing order as a side effect of UI edits.
- See `README.md` and `docs/verification.md` for installation and the limits of validation. Source commits do not deploy to Tilda or object storage.
