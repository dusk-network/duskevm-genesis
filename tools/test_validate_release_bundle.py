#!/usr/bin/env python3

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validate_release_bundle import BundleError, validate_bundle


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "rehearsals" / "h2-devnet-20260813-fresh-l1"


def update_artifact_digest(bundle: Path, relative: str) -> None:
    manifest_path = bundle / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][relative] = hashlib.sha256((bundle / relative).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


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
        with self.assertRaisesRegex(BundleError, "compatible adapter chart"):
            validate_bundle(FIXTURE, strict_release=True)

    def test_release_candidate_requires_source_revisions_after_chart_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            manifest_path = bundle / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["charts"].update(
                {
                    "adapter": "0.1.3",
                    "aggregate": "0.0.39",
                    "blockscout": "0.1.18",
                    "postgresql": "16.3.5",
                }
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BundleError, "source revision"):
                validate_bundle(bundle, strict_release=True)

    def test_release_candidate_requires_consume_gas_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            manifest_path = bundle / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["charts"].update(
                {
                    "adapter": "0.1.3",
                    "aggregate": "0.0.39",
                    "blockscout": "0.1.18",
                    "postgresql": "16.3.5",
                }
            )
            for component in ("contracts", "adapter", "rusk", "piecrust"):
                manifest["components"][component]["sourceRevision"] = "1" * 40
            manifest["network"]["dusk"]["activationHeights"].update(
                {"blobCall": 1, "nativeCurves": 1}
            )
            manifest["stage0"]["executionProfile"] = "constrained-v1"
            manifest["stage0"]["calldataLimits"] = {
                "bn254PairingBytes": 112_704,
                "bls12381G1MultiExpBytes": 156_672,
                "bls12381G2MultiExpBytes": 307_456,
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(BundleError, "activationHeights.consumeGas"):
                validate_bundle(bundle, strict_release=True)

            manifest["network"]["dusk"]["activationHeights"]["consumeGas"] = 1
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            validate_bundle(bundle, strict_release=True)

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

    def test_projected_origin_hash_drift_is_rejected_after_rehash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            rollup_path = bundle / "rollup.json"
            rollup = json.loads(rollup_path.read_text(encoding="utf-8"))
            rollup["genesis"]["l1"]["hash"] = "0x" + "1" * 64
            rollup_path.write_text(json.dumps(rollup), encoding="utf-8")
            update_artifact_digest(bundle, "rollup.json")
            with self.assertRaisesRegex(BundleError, "rollup origin hash"):
                validate_bundle(bundle)

    def test_l2_genesis_attestation_drift_is_rejected_after_rehash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            validation_path = bundle / "local-validation.json"
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            validation["l2_genesis_hash"] = "0x" + "1" * 64
            validation_path.write_text(json.dumps(validation), encoding="utf-8")
            update_artifact_digest(bundle, "local-validation.json")
            with self.assertRaisesRegex(BundleError, "L2 genesis block hash"):
                validate_bundle(bundle)

    def test_rollup_contract_address_drift_is_rejected_after_rehash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            shutil.copytree(FIXTURE, bundle)
            addresses_path = bundle / "l1-addresses.json"
            addresses = json.loads(addresses_path.read_text(encoding="utf-8"))
            addresses["contracts"]["optimism_portal"]["evm_address"] = "0x" + "1" * 40
            addresses_path.write_text(json.dumps(addresses), encoding="utf-8")
            update_artifact_digest(bundle, "l1-addresses.json")
            with self.assertRaisesRegex(BundleError, "deposit_contract_address"):
                validate_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
