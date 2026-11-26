"""Storage and navigation helpers for the monitor settings."""

import hashlib
import json
import os
import tempfile
import unicodedata
from uuid import uuid4
from pathlib import Path


class ConfigConflict(Exception):
    """Another session saved a newer revision."""


def read_config(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def revision(raw):
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("ticker"), dict):
            data["ticker"].pop("portal_cache", None)
        raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (UnicodeError, ValueError):
        # A backup can still replace a corrupt file if it hasn't changed since reading.
        pass
    return hashlib.sha256(raw).hexdigest()


def _with_latest_portal_cache(previous, proposed):
    if previous is None:
        return proposed
    try:
        current = json.loads(previous)
        target = json.loads(proposed)
        old_ticker, new_ticker = current.get("ticker"), target.get("ticker")
        if not isinstance(old_ticker, dict) or not isinstance(new_ticker, dict):
            return proposed
        portal_keys = ("portal_enabled", "portal_agenda_days", "source_mode")
        if any(old_ticker.get(key) != new_ticker.get(key) for key in portal_keys):
            return proposed
        old_cache = old_ticker.get("portal_cache") or {}
        new_cache = new_ticker.get("portal_cache") or {}
        if old_cache.get("last_sync", "") > new_cache.get("last_sync", ""):
            new_ticker["portal_cache"] = old_cache
            return json.dumps(target, ensure_ascii=False, indent=2).encode("utf-8")
    except (AttributeError, UnicodeError, ValueError, TypeError):
        pass
    return proposed


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
        previous_revision, next_revision = revision(previous), revision(raw)
        if previous_revision not in (expected_revision, next_revision):
            raise ConfigConflict
        raw = _with_latest_portal_cache(previous, raw)
        if previous == raw:
            return next_revision
        if previous is not None and previous_revision != next_revision:
            atomic_write(backup, previous)
        atomic_write(path, raw)
        return next_revision


def write_portal_cache(path, expected_revision, cache, lock):
    """Update only the generated cache, without writing a new settings revision."""
    with lock:
        raw = read_config(path)
        if raw is None or revision(raw) != expected_revision:
            return
        data = json.loads(raw)
        ticker = data.get("ticker")
        if not isinstance(ticker, dict):
            return
        updated = _with_latest_portal_cache(raw, json.dumps({
            **data, "ticker": {**ticker, "portal_cache": cache},
        }, ensure_ascii=False, indent=2).encode("utf-8"))
        if updated != raw:
            atomic_write(path, updated)


def profile_settings(config):
    return {key: config[key] for key in ("profiles", "default_profile_id")}


def read_profiles(request):
    rows = request("GET", "monitor_profiles?id=eq.1&select=revision,settings")
    if rows == []:
        return None, None
    row, = rows
    return row["revision"], profile_settings(row["settings"])


def write_profiles(request, expected_revision, current_revision, current_settings, settings):
    if current_settings == settings:
        return current_revision
    if current_revision != expected_revision:
        raise ConfigConflict
    next_revision = str(uuid4())
    payload = {"revision": next_revision, "settings": settings}
    if current_revision is None:
        try:
            rows = request("POST", "monitor_profiles", {**payload, "id": 1})
        except RuntimeError as exc:
            if getattr(exc.__cause__, "code", None) == 409:
                raise ConfigConflict from exc
            raise
    else:
        rows = request("PATCH", f"monitor_profiles?id=eq.1&revision=eq.{current_revision}", payload)
    if not rows:
        raise ConfigConflict
    return next_revision


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
