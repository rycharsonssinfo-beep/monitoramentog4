"""Storage and navigation helpers for the monitor settings."""

import hashlib
import os
import tempfile
import unicodedata
from pathlib import Path


class ConfigConflict(Exception):
    """Another session saved a newer revision."""


def read_config(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def revision(raw):
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def atomic_write(path, raw):
    fd, name = tempfile.mkstemp(prefix=".monitoramento-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def write_config(path, backup, expected_revision, raw, lock):
    with lock:
        previous = read_config(path)
        if previous == raw:
            return revision(raw)
        if revision(previous) != expected_revision:
            raise ConfigConflict
        if previous is not None:
            atomic_write(backup, previous)
        atomic_write(path, raw)
        return revision(raw)


def matches_search(query, text):
    def fold(value):
        return "".join(
            char for char in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(char)
        )

    haystack = fold(text)
    return all(term in haystack for term in fold(query).split())


def config_changes(before, after):
    """Return added, modified and removed profile/panel names."""
    def entries(config):
        profiles = config.get("profiles", {})
        return {
            **{(pid, None): ("Perfil: " + p["nome"], {k: v for k, v in p.items() if k != "paineis"})
               for pid, p in profiles.items()},
            **{(pid, panel["id"]): (p["nome"] + " › " + (panel.get("nome") or "Painel sem nome"), (i, panel))
               for pid, p in profiles.items() for i, panel in enumerate(p.get("paineis", []))},
        }

    old, new = entries(before), entries(after)
    return {
        "Adicionados": [label for key, (label, _) in new.items() if key not in old],
        "Alterados": [label for key, (label, value) in new.items() if key in old and value != old[key][1]],
        "Removidos": [label for key, (label, _) in old.items() if key not in new],
    }
