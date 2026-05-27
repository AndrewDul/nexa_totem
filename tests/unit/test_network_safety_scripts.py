import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.network import rollback_nexa_ap, setup_nexa_ap


REPO_ROOT = Path(__file__).resolve().parents[2]


class NetworkSafetyScriptTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_setup_defaults_to_dry_run(self):
        summary = setup_nexa_ap.dry_run_summary()
        self.assertTrue(summary["dry_run"])
        self.assertFalse(summary["changed_network"])
        self.assertTrue(summary["apply_required"])

    def test_setup_requires_apply_and_warning_flag(self):
        source = self.read(REPO_ROOT / "scripts/network/setup_nexa_ap.py")
        self.assertIn("--apply", source)
        self.assertIn("--i-understand-this-may-disconnect-wifi", source)
        self.assertIn("missing_warning_flag", source)

    def test_setup_requires_force_when_wlan0_is_internet_route(self):
        with patch.object(setup_nexa_ap, "collect_network_state", return_value={}), patch.object(
            setup_nexa_ap,
            "analyze_network_state",
            return_value={"wlan0_is_default_route": True, "warning": "WARNING: wlan0 appears to be your current internet route."},
        ), patch.object(setup_nexa_ap, "_write_backup") as backup, patch.object(setup_nexa_ap.subprocess, "run") as run:
            result = setup_nexa_ap.apply_profile("wlan0", False)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "wlan0_is_default_route")
        self.assertFalse(result["changed_network"])
        backup.assert_not_called()
        run.assert_not_called()

    def test_rollback_defaults_to_dry_run(self):
        summary = rollback_nexa_ap.dry_run_summary()
        self.assertTrue(summary["dry_run"])
        self.assertFalse(summary["changed_network"])
        self.assertIn("nmcli connection delete NeXa-ToTem", "\n".join(summary["commands"]))

    def test_rollback_requires_apply_and_warning_flag(self):
        source = self.read(REPO_ROOT / "scripts/network/rollback_nexa_ap.py")
        self.assertIn("--apply", source)
        self.assertIn("--i-understand-this-changes-network", source)
        self.assertIn("missing_warning_flag", source)

    def test_tests_do_not_run_real_nmcli_apply(self):
        setup_source = self.read(REPO_ROOT / "scripts/network/setup_nexa_ap.py")
        rollback_source = self.read(REPO_ROOT / "scripts/network/rollback_nexa_ap.py")
        self.assertIn("if not args.apply", setup_source)
        self.assertIn("elif not args.i_understand_this_may_disconnect_wifi", setup_source)
        self.assertIn("if not args.apply", rollback_source)
        self.assertIn("elif not args.i_understand_this_changes_network", rollback_source)


if __name__ == "__main__":
    unittest.main()
