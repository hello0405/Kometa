# Kometa Web 控制台（本 fork）

容器内以 **Web UI 为唯一长驻进程**，通过线程锁串行执行 `kometa.py --run`，避免多次 `docker exec ... --run` 叠进程导致卡住。

> **无鉴权**：仅建议在局域网使用，不要把端口映射到公网。

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `KOMETA_WEB_PORT` | `8787` | Web 监听端口（绑定 `0.0.0.0`） |
| `KOMETA_TIME` | （空） | 每日定时，逗号分隔 `HH:MM`，如 `03:00,15:00` |
| `KOMETA_RUN_LIBRARIES` | `电视剧` | 定时要跑的媒体库，逗号分隔 |
| `TMDB_PROXY` | （空） | TMDB 反代根地址（见 `docs/TMDB_PROXY.md`） |

## 功能

- 页面 `/`：状态、上次结果、「立即运行 电视剧 / 电影」、查看 yml / 日志
- `POST /api/run`：`{"library":"电视剧"}` — 忙时返回 **409**
- `GET /api/status`：运行状态 + 日志尾部
- `GET /api/log`：完整上次运行日志（`/config/webui-last-run.log`）
- `GET /yml` 或 `/api/yml`：只读 `/config/plextmdbmatch.yml`

定时与手动共用同一把锁；CLI 仍可用：`python3 /kometa.py --run ...`（请勿与 Web 同时手动叠跑）。

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
      - KOMETA_TIME=03:00,15:00
      - KOMETA_RUN_LIBRARIES=电视剧
      - TMDB_PROXY=https://你的反代根地址
    volumes:
      - /volume1/docker/MoviePilot/config/Kometa:/config
    restart: unless-stopped
```

## 重建镜像

```bash
git clone -b tmdb-proxy https://github.com/hello0405/Kometa.git
cd Kometa
docker build -t hello0405/kometa:tmdb-proxy .
docker compose up -d
```

浏览器打开：`http://NAS_IP:8787`
