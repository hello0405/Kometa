# TMDB_PROXY (this fork)

Default `Dockerfile` builds **from source** with `python:3.13-slim` — no `kometateam/kometa:base` pull.

```bash
git clone -b tmdb-proxy https://github.com/hello0405/Kometa.git kometa-src
cd kometa-src
docker build -t hello0405/kometa:tmdb-proxy .
```

## Env
```yaml
environment:
  - TMDB_PROXY=https://YOUR_PROXY_ROOT
```
Or `TMDB_API3_BASE` / `TMDB_API4_BASE`. Unset = official API.

## Verify
Log: `TMDb API base: v3=... v4=...`

Optional: `Dockerfile.official-base` if you already have official base locally.
