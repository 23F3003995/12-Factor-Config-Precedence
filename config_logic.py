import os
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Fallback copy of config.development.yaml, used only if the file is missing.
EMBEDDED_YAML = {"port": 8762, "workers": 14, "debug": True}

# The assigned OS-level layer. Real APP_* variables on the host (if any)
# are merged on top, as a real process environment would be.
ASSIGNED_OS_ENV = {
    "APP_PORT": "8667",
    "APP_WORKERS": "13",
    "APP_LOG_LEVEL": "info",
    "APP_API_KEY": "key-bkcyariyib",
}

ALIASES = {"num_workers": "workers"}
INT_KEYS = {"port", "workers"}
TRUTHY = {"true", "1", "yes", "on"}
MASK = "****"


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in TRUTHY


def normalize_key(k, strip_prefix=False):
    k = str(k).strip().lower()
    if strip_prefix and k.startswith("app_"):
        k = k[4:]
    return ALIASES.get(k, k)


def load_yaml_layer(env=None):
    env = env or os.environ.get("CONFIG_ENV", "development")
    path = BASE / f"config.{env}.yaml"
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except FileNotFoundError:
        data = dict(EMBEDDED_YAML) if env == "development" else {}
    return {normalize_key(k): v for k, v in data.items()}


def parse_dotenv(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[normalize_key(k, strip_prefix=True)] = v
    return out


def load_dotenv_layer():
    path = BASE / ".env"
    try:
        return parse_dotenv(path.read_text())
    except FileNotFoundError:
        return {}


def load_os_layer():
    env = dict(ASSIGNED_OS_ENV)
    env.update({k: v for k, v in os.environ.items() if k.startswith("APP_")})
    return {
        normalize_key(k, strip_prefix=True): v
        for k, v in env.items()
        if k.startswith("APP_")
    }


def parse_overrides(items):
    out = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"override must be key=value, got {item!r}")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"empty key in override {item!r}")
        out[k.lower()] = v  # later duplicates win
    return out


def coerce(cfg):
    out = {}
    for k, v in cfg.items():
        if k in INT_KEYS:
            try:
                out[k] = int(str(v).strip()) if not isinstance(v, bool) else int(v)
            except ValueError:
                raise ValueError(f"{k} must be an integer, got {v!r}")
        elif k == "debug":
            out[k] = to_bool(v)
        else:
            out[k] = v if isinstance(v, str) else str(v)
    return out


def effective_config(overrides=(), *, yaml_layer=None, dotenv_layer=None, os_layer=None):
    cfg = dict(DEFAULTS)
    cfg.update(load_yaml_layer() if yaml_layer is None else yaml_layer)
    cfg.update(load_dotenv_layer() if dotenv_layer is None else dotenv_layer)
    cfg.update(load_os_layer() if os_layer is None else os_layer)
    cfg.update(parse_overrides(overrides))
    cfg = coerce(cfg)
    cfg["api_key"] = MASK
    return cfg
