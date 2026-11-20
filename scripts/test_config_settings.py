import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_settings import ConfigConflict, config_changes, matches_search, revision, write_config


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


if __name__ == "__main__":
    unittest.main()
