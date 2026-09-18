#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kometa Web 控制台（fork 增强）

- 唯一长驻进程；用线程锁串行化 kometa --run，避免 docker exec 叠进程卡死
- 可选按 KOMETA_TIME 定时跑（同一把锁）
- 无鉴权，仅建议局域网使用
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

try:
    import schedule
except ImportError:  # pragma: no cover
    schedule = None

WEB_PORT = int(os.environ.get("KOMETA_WEB_PORT") or "8787")
KOMETA_PY = os.environ.get("KOMETA_PY") or "/kometa.py"
CONFIG_DIR = Path(os.environ.get("KOMETA_CONFIG") or "/config")
LOG_PATH = CONFIG_DIR / "webui-last-run.log"
YML_PATH = CONFIG_DIR / "plextmdbmatch.yml"
RUN_LIBRARIES_DEFAULT = "电视剧"

_run_lock = threading.Lock()
_state = {
    "running": False,
    "library": None,
    "started_at": None,
    "last_finished_at": None,
    "last_library": None,
    "last_returncode": None,
    "last_ok": None,
    "last_error": None,
}
_state_lock = threading.Lock()

app = Flask(__name__, template_folder="templates")


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_libraries(raw: str | None) -> list[str]:
    text = (raw or "").strip() or RUN_LIBRARIES_DEFAULT
    return [x.strip() for x in text.split(",") if x.strip()]


def _tail_log(max_chars: int = 8000) -> str:
    try:
        if not LOG_PATH.exists():
            return ""
        data = LOG_PATH.read_text(encoding="utf-8", errors="replace")
        if len(data) > max_chars:
            return data[-max_chars:]
        return data
    except Exception as e:
        return f"(读日志失败: {e})"


def _do_run(library: str) -> int:
    """在已持有 _run_lock 的前提下执行一次 kometa。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    started = _now_str()
    with _state_lock:
        _state["running"] = True
        _state["library"] = library
        _state["started_at"] = started
        _state["last_error"] = None

    header = (
        f"===== Kometa Web 运行 =====\n"
        f"开始: {started}\n"
        f"媒体库: {library}\n"
        f"命令: python3 {KOMETA_PY} --run --run-libraries {library}\n"
        f"===========================\n\n"
    )
    try:
        with open(LOG_PATH, "w", encoding="utf-8") as logf:
            logf.write(header)
            logf.flush()
            proc = subprocess.Popen(
                ["python3", KOMETA_PY, "--run", "--run-libraries", library],
                cwd="/",
                stdout=logf,
                stderr=subprocess.STDOUT,
                text=True,
            )
            rc = proc.wait()
            finished = _now_str()
            logf.write(f"\n\n===== 结束 {finished} returncode={rc} =====\n")
    except Exception as e:
        finished = _now_str()
        rc = -1
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as logf:
                logf.write(f"\n\n===== 异常 {finished}: {e} =====\n")
        except Exception:
            pass
        with _state_lock:
            _state["last_error"] = str(e)

    with _state_lock:
        _state["running"] = False
        _state["library"] = None
        _state["last_finished_at"] = finished
        _state["last_library"] = library
        _state["last_returncode"] = rc
        _state["last_ok"] = rc == 0
    return rc


def try_start_run(library: str, *, wait: bool = False) -> tuple[bool, str]:
    """尝试启动一次运行。wait=False 时忙则失败；wait=True 时阻塞等锁。"""
    library = (library or "").strip() or RUN_LIBRARIES_DEFAULT
    acquired = _run_lock.acquire(blocking=wait)
    if not acquired:
        return False, "busy"

    def worker():
        try:
            _do_run(library)
        finally:
            _run_lock.release()

    threading.Thread(target=worker, name=f"kometa-run-{library}", daemon=True).start()
    return True, "started"


def _scheduled_job():
    libs = _parse_libraries(os.environ.get("KOMETA_RUN_LIBRARIES"))
    for lib in libs:
        # 定时任务同步持锁执行，与手动 API 共用同一把锁
        _run_lock.acquire(blocking=True)
        try:
            _do_run(lib)
        finally:
            _run_lock.release()


def _setup_schedule():
    raw = (os.environ.get("KOMETA_TIME") or "").strip()
    if not raw:
        print("[webui] KOMETA_TIME 未设置，不定时运行", flush=True)
        return
    if schedule is None:
        print("[webui] 缺少 schedule 包，无法定时", flush=True)
        return
    times = [t.strip() for t in raw.split(",") if t.strip()]
    libs = _parse_libraries(os.environ.get("KOMETA_RUN_LIBRARIES"))
    for t in times:
        try:
            schedule.every().day.at(t).do(_scheduled_job)
            print(f"[webui] 已安排每日 {t} 运行库: {libs}", flush=True)
        except Exception as e:
            print(f"[webui] 无效时间 {t!r}: {e}", flush=True)

    def loop():
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                print(f"[webui] schedule error: {e}", flush=True)
            time.sleep(20)

    threading.Thread(target=loop, name="kometa-scheduler", daemon=True).start()


@app.get("/")
def index():
    with _state_lock:
        st = dict(_state)
    return render_template(
        "index.html",
        running=st["running"],
        library=st["library"],
        started_at=st["started_at"],
        last_finished_at=st["last_finished_at"],
        last_library=st["last_library"],
        last_returncode=st["last_returncode"],
        last_ok=st["last_ok"],
        last_error=st["last_error"],
        schedule_time=os.environ.get("KOMETA_TIME") or "（未设置）",
        run_libraries=os.environ.get("KOMETA_RUN_LIBRARIES") or RUN_LIBRARIES_DEFAULT,
    )


@app.post("/api/run")
def api_run():
    data = request.get_json(silent=True) or {}
    library = (data.get("library") or "").strip() or RUN_LIBRARIES_DEFAULT
    ok, msg = try_start_run(library, wait=False)
    if not ok:
        return jsonify({"ok": False, "error": "正在运行中，请稍后再试", "code": "busy"}), 409
    return jsonify({"ok": True, "message": f"已开始运行：{library}", "library": library})


@app.get("/api/status")
def api_status():
    with _state_lock:
        st = dict(_state)
    return jsonify(
        {
            "running": st["running"],
            "library": st["library"],
            "started_at": st["started_at"],
            "last_finished_at": st["last_finished_at"],
            "last_library": st["last_library"],
            "last_returncode": st["last_returncode"],
            "last_ok": st["last_ok"],
            "last_error": st["last_error"],
            "log_tail": _tail_log(4000),
            "schedule_time": os.environ.get("KOMETA_TIME") or "",
            "run_libraries": os.environ.get("KOMETA_RUN_LIBRARIES") or RUN_LIBRARIES_DEFAULT,
        }
    )


@app.get("/api/log")
def api_log():
    text = ""
    try:
        if LOG_PATH.exists():
            text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        text = f"(读日志失败: {e})"
    return Response(text, mimetype="text/plain; charset=utf-8")


@app.get("/yml")
@app.get("/api/yml")
def api_yml():
    try:
        if not YML_PATH.exists():
            body = f"# 文件不存在: {YML_PATH}\n"
        else:
            body = YML_PATH.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        body = f"# 读取失败: {e}\n"
    return Response(body, mimetype="text/plain; charset=utf-8")


def main():
    print(f"[webui] Kometa Web 控制台启动 0.0.0.0:{WEB_PORT}", flush=True)
    print(f"[webui] 无鉴权（仅局域网）；日志 {LOG_PATH}", flush=True)
    _setup_schedule()
    app.run(host="0.0.0.0", port=WEB_PORT, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
