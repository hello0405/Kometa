# 怎么改 TMDB 代理（hello0405/Kometa）

## 原理
在 TMDbAPIs 初始化前，用环境变量改掉 tmdbapis 的 base_url。

## 环境变量
- TMDB_PROXY=https://你的反代（根地址，不要末尾 /；自动变成 /3 和 /4）
- 或直接：TMDB_API3_BASE / TMDB_API4_BASE

## 代码
分支 tmdb-proxy 已包含 modules/tmdb_proxy.py。

在 modules/tmdb.py 改两处：

1) import 区增加：
from modules.tmdb_proxy import apply_tmdb_proxy_from_env

2) TMDb.__init__ 里，创建 TMDbAPIs(...) 之前加：
apply_tmdb_proxy_from_env()

## docker-compose
environment:
  - TZ=Asia/Shanghai
  - KOMETA_TIME=03:00
  - TMDB_PROXY=https://你的反代根地址

## 验证
日志出现：TMDb API base: v3=https://.../3 v4=https://.../4
