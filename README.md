# neumes-playground

## Frontend development

The Vite dev server proxies `/api/*` requests to the Python backend to avoid browser CORS issues during development.

By default the proxy target is:

```bash
http://127.0.0.1:8000
```

You can override it with an environment variable:

```bash
VITE_HTR_PROXY_TARGET=http://134.2.227.44:8000
```

You can also bypass the proxy entirely and point the frontend directly at a backend:

```bash
VITE_HTR_BASE_URL=http://134.2.227.44:8000
```

`VITE_HTR_BASE_URL` takes precedence over the dev proxy.
