#!/usr/bin/env python3
"""Wire TMDB_PROXY support into modules/tmdb.py at image build time."""
from pathlib import Path

p = Path("/modules/tmdb.py")
if not p.exists():
    p = Path("modules/tmdb.py")
t = p.read_text(encoding="utf-8")
if "apply_tmdb_proxy_from_env" in t:
    print("tmdb.py already wired")
    raise SystemExit(0)
old_imp = "from modules import util\nfrom modules.util import Failed, ServiceError\n"
new_imp = (
    "from modules import util\n"
    "from modules.tmdb_proxy import apply_tmdb_proxy_from_env\n"
    "from modules.util import Failed, ServiceError\n"
)
if old_imp not in t:
    raise SystemExit("import block not found in tmdb.py")
t = t.replace(old_imp, new_imp, 1)
old = (
    "        logger.secret(self.apikey)\n"
    "        try:\n"
    "            self.TMDb = TMDbAPIs(self.apikey, language=self.language, session=self.requests.session)\n"
)
new = (
    "        logger.secret(self.apikey)\n"
    "        try:\n"
    "            apply_tmdb_proxy_from_env()\n"
    "            self.TMDb = TMDbAPIs(self.apikey, language=self.language, session=self.requests.session)\n"
)
if old not in t:
    raise SystemExit("init block not found in tmdb.py")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("wired apply_tmdb_proxy_from_env into", p)
