"""ha_lib — shared live-access helpers for ha-api / ha-doctor.

Centralizes the three things both tools need and that were per-call friction
before: loading the skill's config.sh, fetching the HA admin token (via bws),
and making REST/WS calls. The token is held in memory only and is NEVER written
to stdout/stderr by this module — keep it that way.

Token resolution order:
  1. $HA_LLAT            (an explicit long-lived token in the env; wins)
  2. bws secret get $HA_TOKEN_BWS_ID, with BWS_ACCESS_TOKEN sourced from
     $HA_BWS_TOKEN_ENV if it isn't already in the environment.
"""
import os
import re
import json
import subprocess
import urllib.request
import urllib.error


def _load_config():
    """Seed HA_* env defaults from the skill's config.sh (env still wins).

    Same parser ha-inventory uses, so the config seam stays single-source."""
    here = os.path.dirname(os.path.realpath(__file__))
    cfg = os.path.join(os.path.dirname(here), "skills", "home-assistant", "config.sh")
    if not os.path.exists(cfg):
        return
    pat = re.compile(r'^\s*(?:export\s+)?(HA_[A-Z_]+)=["\']?([^"\'\n#]*)["\']?')
    for line in open(cfg):
        m = pat.match(line)
        if m and m.group(1) not in os.environ:
            os.environ[m.group(1)] = m.group(2).strip()


_load_config()

HA_URL = os.environ.get("HA_URL", "http://192.168.1.232:8123").rstrip("/")
HA_SSH = os.environ.get("HA_SSH", "komi@192.168.1.232")
HA_CONTAINER = os.environ.get("HA_CONTAINER", "homeassistant")
HA_TOKEN_BWS_ID = os.environ.get("HA_TOKEN_BWS_ID", "74edad23-6bd2-4617-a1d8-b45d016db173")
HA_BWS_TOKEN_ENV = os.path.expanduser(
    os.environ.get("HA_BWS_TOKEN_ENV", "~/.config/bws/token.env"))

_token = None  # process-lifetime cache; fetched once, never logged


def get_token():
    """Return the HA long-lived access token (cached). Never prints it."""
    global _token
    if _token:
        return _token
    if os.environ.get("HA_LLAT"):
        _token = os.environ["HA_LLAT"].strip()
        return _token
    env = os.environ.copy()
    if not env.get("BWS_ACCESS_TOKEN") and os.path.exists(HA_BWS_TOKEN_ENV):
        m = re.search(r'BWS_ACCESS_TOKEN=["\']?([^"\'\s]+)', open(HA_BWS_TOKEN_ENV).read())
        if m:
            env["BWS_ACCESS_TOKEN"] = m.group(1)
    try:
        out = subprocess.run(["bws", "secret", "get", HA_TOKEN_BWS_ID],
                             capture_output=True, text=True, env=env, timeout=30)
    except FileNotFoundError:
        raise SystemExit("ha_lib: `bws` not found — set $HA_LLAT or install bws")
    if out.returncode != 0:
        raise SystemExit("ha_lib: could not fetch the HA token via bws. Set $HA_LLAT, "
                         f"or check BWS_ACCESS_TOKEN / {HA_BWS_TOKEN_ENV}.")
    _token = json.loads(out.stdout)["value"].strip()
    return _token


def _req(method, path, data=None):
    url = HA_URL + "/api/" + path.lstrip("/")
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Bearer " + get_token())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ha_lib: HTTP {e.code} on {method} {path}: {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"ha_lib: cannot reach {HA_URL} ({e.reason})")
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw  # e.g. /api/template returns plain text


def api_get(path):
    return _req("GET", path)


def api_post(path, data=None):
    return _req("POST", path, {} if data is None else data)


def config_entries():
    """All config entries via the WS API (domain/title/state/reason). The one
    diagnostic the REST API can't give. Needs the `websockets` lib."""
    import asyncio
    try:
        import websockets
    except ImportError:
        raise SystemExit("ha_lib: config-entry check needs the `websockets` lib "
                         "(pip install websockets)")
    tok = get_token()
    ws_url = re.sub(r'^http', 'ws', HA_URL) + "/api/websocket"

    async def _go():
        async with websockets.connect(ws_url, max_size=None) as ws:
            await ws.recv()
            await ws.send(json.dumps({"type": "auth", "access_token": tok}))
            await ws.recv()
            await ws.send(json.dumps({"id": 1, "type": "config_entries/get"}))
            return json.loads(await ws.recv())["result"]

    return asyncio.run(_go())
