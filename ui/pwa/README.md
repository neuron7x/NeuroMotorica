# NeuroMotorica Progressive Web App

This folder hosts a production-ready starter for the NeuroMotorica PWA. It
implements the offline-first strategy described in the system plan:

- **IndexedDB replica** for session data via [`idb`](https://github.com/jakearchibald/idb).
- **ONNX Runtime Web** worker to keep inference off the main thread.
- **Workbox** service worker pre-cache for installability and offline access.

## Development

```bash
pnpm install
pnpm dev
```

The app exposes reusable primitives (`src/lib/`, `src/workers/`) that can be
consumed by mobile wrappers (React Native / Capacitor) with minimal changes.
