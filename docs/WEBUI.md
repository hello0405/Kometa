# Kometa Web 控制台（本 fork）

容器内以 **Web UI 为唯一长驻进程**，通过线程锁串行执行 `kometa.py --run`，避免多次 `docker exec ... --run` 叠进程导致卡住。

> **无鉴权**：仅建议在局域网使用，不要把端口映射到公网。

## 与 MoviePilot 插件的对齐

PlexTmdbMatch 只写 `/config/plextmdbmatch.yml`。插件触发的 **默认 mode 是 `metadata`**：

```text
python3 /kometa.py --run --metadata-only --ignore-schedules --run-libraries 电视剧
```

不要用插件去打全量 `--run`（会把 collection/overlay/整库 operations 跑一遍）。夜里全量走定时 `KOMETA_SCHEDULE_MODE=full`。

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `KOMETA_WEB_PORT` | `8787` | Web 监听端口 |
| `KOMETA_WEB_DEFAULT_MODE` | `metadata` | 手动/API 默认：`metadata` / `full` / `overlays` / `collections` / `operations` |
| `KOMETA_SCHEDULE_MODE` | `full` | 定时任务模式 |
| `KOMETA_TIME` | （空） | 每日定时，逗号分隔 `HH:MM` |
| `KOMETA_RUN_LIBRARIES` | `电视剧` | 定时库，逗号或 `\|` 分隔 |
| `TMDB_PROXY` | （空） | TMDB 反代根地址 |

## API

```http
POST /api/run
{"library":"电视剧"}
{"library":"电视剧","mode":"metadata"}
{"library":"电视剧","mode":"full"}
```

兼容字段：`preset` 等同 `mode`，`libraries` 等同 `library`。忙时 **409**。

- `GET /api/status`
- `GET /api/log`
- `GET /yml`

## docker-compose 示例

```yaml
services:
  kometa:
    image: hello0405/kometa:tmdb-proxy
    container_name: kometa
    ports:
      - "8787:8787"
    environment:
      - TZ=Asia/Shanghai
      - KOMETA_WEB_PORT=8787
      - KOMETA_WEB_DEFAULT_MODE=metadata
      - KOMETA_SCHEDULE_MODE=full
      - KOMETA_TIME=03:00
      - KOMETA_RUN_LIBRARIES=电视剧
      - TMDB_PROXY=https://你的反代根地址
    volumes:
      - /volume1/docker/MoviePilot/config/Kometa:/config
    restart: unless-stopped
```

重建镜像后生效。浏览器：`http://NAS_IP:8787`
