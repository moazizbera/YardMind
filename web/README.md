# YardMind React App

This app is the browser-facing YardMind presentation layer. It consumes the generated snapshot at `public/demo-data.json` and renders:

- development constructive and local-search yard layouts
- operator-level search history
- official delegated-versus-native constructive comparison
- official bay assignment views for demo-ready storytelling

## Run locally

From the repository root, refresh the Python-generated snapshot first:

```bash
python -m yardmind.demo --instance examples/sample-instance.json --output artifacts/demo/index.html
```

Then start the React app:

```bash
cd web
npm install
npm run dev
```

## Build

```bash
cd web
npm run build
```

If the app reports missing demo data, regenerate the snapshot from the repo root. `src/yardmind/demo.py` now syncs the latest JSON into `web/public/demo-data.json` automatically.
