import sys
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_settings import (
    ConfigConflict, config_changes, matches_search, normalize_profile_access, profile_settings, read_profiles,
    revision, write_config, write_portal_cache, write_profiles,
)


class SettingsTest(unittest.TestCase):
    def test_two_sessions_cannot_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            backup = Path(directory) / "backup.json"
            config.write_bytes(b'{"version": 1}')
            lock = threading.Lock()
            base = revision(config.read_bytes())

            def update(raw):
                try:
                    return write_config(config, backup, base, raw, lock)
                except ConfigConflict:
                    return None

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(update, [b'{"version": 2}', b'{"version": 3}']))
            self.assertEqual(results.count(None), 1)
            self.assertIn(revision(config.read_bytes()), results)
            self.assertEqual(backup.read_bytes(), b'{"version": 1}')

    def test_missing_configuration_can_be_created(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            backup = Path(directory) / "backup.json"
            raw = b'{"version": 1}'
            lock = threading.Lock()
            self.assertEqual(write_config(config, backup, None, raw, lock), revision(raw))
            self.assertEqual(write_config(config, backup, None, raw, lock), revision(raw))
            self.assertFalse(backup.exists())

    def test_search_ignores_accents_and_term_order(self):
        self.assertTrue(matches_search("EXIBICAO paineis", "Painéis e ordem de exibição"))
        self.assertFalse(matches_search("exibicao backup", "Painéis e ordem de exibição"))

    def test_portal_sync_keeps_manual_revision_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            backup = Path(directory) / "backup.json"
            lock = threading.Lock()
            initial = {"name": "Suporte", "ticker": {"portal_enabled": True, "portal_cache": {"last_sync": "2026-11-19T14:00:00"}}}
            raw = json.dumps(initial).encode()
            base = write_config(config, backup, None, raw, lock)
            fresh_cache = {"last_sync": "2026-11-19T14:05:00", "news": [{"titulo": "Aviso"}]}
            write_portal_cache(config, base, fresh_cache, lock)
            self.assertEqual(revision(config.read_bytes()), base)
            self.assertFalse(backup.exists())
            proposed = {**initial, "name": "Coordenação"}
            write_config(config, backup, base, json.dumps(proposed).encode(), lock)
            saved = json.loads(config.read_bytes())
            self.assertEqual(saved["name"], "Coordenação")
            self.assertEqual(saved["ticker"]["portal_cache"], fresh_cache)
            write_portal_cache(config, base, {"last_sync": "2026-11-19T14:10:00"}, lock)
            self.assertEqual(json.loads(config.read_bytes()), saved)

    def test_preview_detects_added_modified_and_removed_panels(self):
        def config(items):
            return {"profiles": {"support": {"nome": "Suporte", "paineis": items}}}

        old = config([{"id": "1", "nome": "SIM", "tempo": 10}, {"id": "2", "nome": "Portais"}])
        new = config([{"id": "1", "nome": "SIM", "tempo": 20}, {"id": "3", "nome": "G4Flex"}])
        self.assertEqual(config_changes(old, new), {
            "Adicionados": ["Suporte › G4Flex"],
            "Alterados": ["Suporte › SIM"],
            "Removidos": ["Suporte › Portais"],
        })


class PersistentProfilesTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "profiles": {"suporte": {"nome": "Suporte"}, "gestao": {"nome": "Gestão"}},
            "default_profile_id": "gestao",
            "ticker": {"enabled": True},
        }
        self.settings = profile_settings(self.config)

    def test_profile_access_preserves_legacy_access_and_validates_explicit_roles(self):
        self.assertIsNone(normalize_profile_access(None))
        self.assertEqual(normalize_profile_access([]), [])
        self.assertEqual(normalize_profile_access("suporte"), [])
        self.assertEqual(
            normalize_profile_access(["desenvolvimento", "suporte", "suporte", "desconhecido"]),
            ["suporte", "desenvolvimento"],
        )

    def test_first_save_preserves_both_profiles_and_default_in_new_session(self):
        request = Mock(return_value=[])
        self.assertEqual(read_profiles(request), (None, None))
        request.return_value = [{"revision": "saved"}]
        saved_revision = write_profiles(request, None, None, None, self.settings)
        method, path, payload = request.call_args.args
        self.assertEqual((method, path), ("POST", "monitor_profiles"))
        self.assertEqual(payload, {"id": 1, "revision": saved_revision, "settings": self.settings})
        self.assertNotIn("ticker", payload["settings"])
        new_session = Mock(return_value=[payload])
        self.assertEqual(read_profiles(new_session), (saved_revision, self.settings))

    def test_stale_edit_cannot_replace_profiles(self):
        request = Mock()
        with self.assertRaises(ConfigConflict):
            write_profiles(request, "old", "current", {}, self.settings)
        request.assert_not_called()

    def test_save_uses_revision_filter_and_detects_simultaneous_update(self):
        request = Mock(return_value=[])
        with self.assertRaises(ConfigConflict):
            write_profiles(request, "current", "current", {}, self.settings)
        method, path, _ = request.call_args.args
        self.assertEqual(method, "PATCH")
        self.assertEqual(path, "monitor_profiles?id=eq.1&revision=eq.current")

    def test_simultaneous_first_save_is_a_conflict(self):
        def request(*args):
            raise RuntimeError("Conflict") from HTTPError("", 409, "Conflict", {}, None)

        with self.assertRaises(ConfigConflict):
            write_profiles(request, None, None, None, self.settings)

    def test_retry_after_success_is_idempotent(self):
        request = Mock()
        self.assertEqual(write_profiles(request, None, "current", self.settings, self.settings), "current")
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
