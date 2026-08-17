#!/usr/bin/env python3

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validate_release_bundle import BundleError, validate_bundle


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "rehearsals" / "h2-devnet-20260813-fresh-l1"


class ReleaseBundleValidationTest(unittest.TestCase):
    def test_existing_h2_rehearsal_is_internally_consistent(self) -> None:
        warnings = validate_bundle(FIXTURE)
        self.assertTrue(any("source revision" in warning for warning in warnings))

    def test_tampered_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            with (bundle / "rollup.json").open("a", encoding="utf-8") as handle:
                handle.write("\n")
            with self.assertRaisesRegex(BundleError, "SHA-256 mismatch for rollup.json"):
                validate_bundle(bundle)

    def test_rehearsal_cannot_pass_as_release_candidate(self) -> None:
        with self.assertRaisesRegex(BundleError, "source revision"):
            validate_bundle(FIXTURE, strict_release=True)

    def test_cross_file_origin_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            manifest_path = bundle / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["network"]["origin"]["block"] += 1
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BundleError, "rollup origin block"):
                validate_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
