"""Loads machine-specific settings (cluster address, node names, accounts) from main/.env.

main/.env is git-ignored; copy main/.env.example and fill in the values.
Config/manifest YAML may reference these values as ${VAR} or ${VAR:-default}.
"""
import os
import re

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
_VAR_PATTERN = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")


def load(path=ENV_FILE):
    if not os.path.exists(path):
        return
    with open(path) as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[len("export "):].strip()
            os.environ.setdefault(key, value.strip().strip("\"'"))


def env(name, default=None):
    value = os.environ.get(name)
    if value:
        return value
    if default is None:
        raise KeyError(f"{name} is not set. Add it to {ENV_FILE} (see .env.example)")
    return default


def expand(text):
    return _VAR_PATTERN.sub(
        lambda m: os.environ.get(m.group(1)) or (m.group(2) or ""), text
    )


load()
