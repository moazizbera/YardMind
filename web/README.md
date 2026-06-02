# YardMind React App

This app is the browser-facing YardMind presentation layer. It consumes the generated snapshot at `public/demo-data.json` and renders:

- development constructive and local-search yard layouts
- operator-level search history
- official delegated-versus-native constructive comparison
- official bay assignment views for demo-ready storytelling

## Run locally

From the repository root, refresh the Python-generated snapshot first:

```bash
python -m yardmind.demo --instance examples/realistic-improvement-instance.json --output artifacts/demo/index.html
```

Then start the React app:

```bash
cd web
npm install
npm run dev -- --host=127.0.0.1 --port=5173
```

From the repo root you can also use:

```bash
./scripts/open-react-demo.ps1
```

The launcher prints the exact local URL it selected and will move to the next free port automatically when `5173` is already in use.

Useful variants:

```bash
./scripts/open-react-demo.ps1 -View judge
./scripts/open-react-demo.ps1 -View story
./scripts/open-react-demo.ps1 -View walkthrough
./scripts/open-react-demo.ps1 -Foreground
```

To export the current demo screenshots from the repo root, run:

```bash
./scripts/capture-react-demo.ps1
```

The first run installs the Playwright Chromium browser used for headless capture.

## Build

```bash
cd web
npm run build
```

If the app reports missing demo data, regenerate the snapshot from the repo root. `src/yardmind/demo.py` now syncs the latest JSON into `web/public/demo-data.json` automatically. The default snapshot favors the stronger `realistic-improvement-instance` development yard and the `official-search-quality-instance` official comparison.

## Deploy to Cloudflare Pages

This frontend is ready to deploy as a static Cloudflare Pages project.

Use these settings when creating the Pages project:

- Repository: the main YardMind GitHub repository
- Root directory: `web`
- Build command: `npm run build`
- Build output directory: `dist`
- Node version: `22`

The app currently uses static data from `public/demo-data.json`, so no runtime secrets are required for a basic deployment.

## Deploy to Cloudflare Workers Static Assets

If you deploy with `wrangler deploy` instead of Cloudflare Pages, do not publish the raw `web` folder.

This repository includes a root `wrangler.jsonc` configured to:

- build the frontend with `npm --prefix web ci && npm --prefix web run build`
- publish the built output from `web/dist`

That avoids the broken production case where Cloudflare serves `web/index.html` directly and the browser receives `/src/main.tsx` instead of compiled assets.
