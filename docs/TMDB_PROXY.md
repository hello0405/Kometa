# TMDB_PROXY (this fork)

Clone `tmdb-proxy`, then `docker build`. Build wires the proxy into `modules/tmdb.py` automatically.

## Usage
```yaml
environment:
  - TMDB_PROXY=https://YOUR_PROXY_ROOT
```

Or set `TMDB_API3_BASE` / `TMDB_API4_BASE`. Unset = official API.

## Verify
Log line: `TMDb API base: v3=... v4=...`
