"""TMDB reverse-proxy helpers (fork enhancement).

Env (priority):
  TMDB_API3_BASE / TMDB_API4_BASE (or TMDB_API3_URL / TMDB_API4_URL)
  TMDB_PROXY — reverse-proxy root; becomes {proxy}/3 and {proxy}/4
Unset → official api.themoviedb.org.

Wired at Docker build via scripts/wire_tmdb_proxy.py into modules/tmdb.py.
"""

from __future__ import annotations

import os

from modules import util

logger = util.logger


def apply_tmdb_proxy_from_env():
    import tmdbapis.api3 as api3
    import tmdbapis.api4 as api4

    def _base(ver):
        explicit = os.environ.get("TMDB_API%s_BASE" % ver) or os.environ.get("TMDB_API%s_URL" % ver)
        if explicit:
            return explicit.rstrip("/")
        proxy = (os.environ.get("TMDB_PROXY") or "").rstrip("/")
        if not proxy:
            return None
        if proxy.endswith("/3") or proxy.endswith("/4"):
            root = proxy[:-2].rstrip("/")
            return "%s/%s" % (root, ver)
        return "%s/%s" % (proxy, ver)

    b3 = _base("3")
    b4 = _base("4")
    if b3:
        api3.base_url = b3
    if b4:
        api4.base_url = b4
    logger.info(
        "TMDb API base: v3=%s v4=%s%s"
        % (api3.base_url, api4.base_url, "" if (b3 or b4) else " (official)")
    )
