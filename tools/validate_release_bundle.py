#!/usr/bin/env python3
"""Validate a DuskEVM deployment bundle without external dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


HEX_32 = re.compile(r"^(?:0x)?[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
IMAGE_DIGEST = re.compile(r"^.+@sha256:[0-9a-f]{64}$")
REQUIRED_ARTIFACTS = {
    "genesis.json",
    "l1-addresses.json",
    "l1-genesis.json",
    "l2-genesis-output-root.txt",
    "local-validation.json",
    "origin-parent-dusk-hash.txt",
    "origin-parent-eth-hash.txt",
    "prestate-proof.json",
    "prestate.bin.gz",
    "rollup.json",
}
REQUIRED_COMPONENTS = {
    "contracts",
    "adapter",
    "rusk",
    "piecrust",
    "opReth",
    "opNode",
    "opBatcher",
    "opProposer",
    "opChallenger",
    "blockscoutBackend",
    "blockscoutFrontend",
}
SOURCE_PINNED_COMPONENTS = {"contracts", "adapter", "rusk", "piecrust"}
RELEASE_CHART_COMPATIBILITY = {
    "adapter": {"0.1.4"},
    "aggregate": {"0.0.40"},
    "blockscout": {"0.1.18"},
    "postgresql": {"16.3.5"},
}


class BundleError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleError(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise BundleError(f"{path.name} must contain a JSON object")
    return value


def nested(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise BundleError(f"release-manifest.json is missing {'.'.join(keys)}")
        current = current[key]
    return current


def normalize_hash(value: str) -> str:
    return value.removeprefix("0x")


def require_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX_32.fullmatch(value):
        raise BundleError(f"{field} must be a lowercase 32-byte hash")
    return value


def require_positive_int(value: Any, field: str, *, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BundleError(f"{field} must be an integer >= {minimum}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_bundle(bundle_dir: Path, strict_release: bool = False) -> list[str]:
    manifest_path = bundle_dir / "release-manifest.json"
    manifest = load_json(manifest_path)
    warnings: list[str] = []

    if manifest.get("schemaVersion") != 1:
        raise BundleError("schemaVersion must be 1")
    kind = manifest.get("kind")
    if kind not in {"rehearsal", "release-candidate", "release"}:
        raise BundleError("kind must be rehearsal, release-candidate or release")
    strict = strict_release or kind in {"release-candidate", "release"}

    network_name = nested(manifest, "network", "name")
    if not isinstance(network_name, str) or not network_name:
        raise BundleError("network.name must be non-empty")
    dusk_chain_id = require_positive_int(
        nested(manifest, "network", "dusk", "chainId"), "network.dusk.chainId"
    )
    l2_chain_id = require_positive_int(
        nested(manifest, "network", "l2", "chainId"), "network.l2.chainId"
    )
    genesis_time = require_positive_int(
        nested(manifest, "network", "l2", "genesisTime"),
        "network.l2.genesisTime",
    )
    origin_block = require_positive_int(
        nested(manifest, "network", "origin", "block"), "network.origin.block"
    )
    require_hash(nested(manifest, "network", "dusk", "genesisHash"), "network.dusk.genesisHash")
    parent_dusk = require_hash(
        nested(manifest, "network", "origin", "parentDuskHash"),
        "network.origin.parentDuskHash",
    )
    parent_eth = require_hash(
        nested(manifest, "network", "origin", "parentEthHash"),
        "network.origin.parentEthHash",
    )
    projected_origin_eth = require_hash(
        nested(manifest, "network", "origin", "projectedEthHash"),
        "network.origin.projectedEthHash",
    )
    l2_genesis_hash = require_hash(
        nested(manifest, "network", "l2", "genesisHash"),
        "network.l2.genesisHash",
    )

    stage0 = nested(manifest, "stage0")
    if stage0.get("settlement") != "permissioned-respected-game":
        raise BundleError("stage0.settlement must be permissioned-respected-game")
    if stage0.get("gameType") != 8:
        raise BundleError("stage0.gameType must be 8")

    components = nested(manifest, "components")
    missing_components = REQUIRED_COMPONENTS.difference(components)
    if missing_components:
        raise BundleError(f"components missing: {', '.join(sorted(missing_components))}")
    for name, component in components.items():
        if not isinstance(component, dict):
            raise BundleError(f"components.{name} must be an object")
        image = component.get("image")
        if image is not None and not IMAGE_DIGEST.fullmatch(image):
            raise BundleError(f"components.{name}.image must use an immutable sha256 digest")

    artifacts = nested(manifest, "artifacts")
    if not isinstance(artifacts, dict):
        raise BundleError("artifacts must be an object")
    missing_artifacts = REQUIRED_ARTIFACTS.difference(artifacts)
    if missing_artifacts:
        raise BundleError(f"artifacts missing: {', '.join(sorted(missing_artifacts))}")
    for relative, expected in artifacts.items():
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise BundleError(f"unsafe artifact path: {relative}")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise BundleError(f"invalid SHA-256 for {relative}")
        artifact = bundle_dir / relative
        if not artifact.is_file():
            raise BundleError(f"artifact does not exist: {relative}")
        actual = sha256(artifact)
        if actual != expected:
            raise BundleError(f"SHA-256 mismatch for {relative}: expected {expected}, got {actual}")

    genesis = load_json(bundle_dir / "genesis.json")
    rollup = load_json(bundle_dir / "rollup.json")
    l1_genesis = load_json(bundle_dir / "l1-genesis.json")
    addresses = load_json(bundle_dir / "l1-addresses.json")
    validation = load_json(bundle_dir / "local-validation.json")
    prestate = load_json(bundle_dir / "prestate-proof.json")

    if nested(genesis, "config", "chainId") != l2_chain_id:
        raise BundleError("genesis.json chain ID differs from release manifest")
    if rollup.get("l2_chain_id") != l2_chain_id:
        raise BundleError("rollup.json L2 chain ID differs from release manifest")
    if rollup.get("l1_chain_id") != dusk_chain_id:
        raise BundleError("rollup.json L1 chain ID differs from release manifest")
    if nested(l1_genesis, "config", "chainId") != dusk_chain_id:
        raise BundleError("l1-genesis.json chain ID differs from release manifest")
    if nested(rollup, "genesis", "l1", "number") != origin_block:
        raise BundleError("rollup origin block differs from release manifest")
    if normalize_hash(nested(rollup, "genesis", "l1", "hash")) != normalize_hash(
        projected_origin_eth
    ):
        raise BundleError("rollup origin hash differs from release manifest")
    if normalize_hash(nested(rollup, "genesis", "l2", "hash")) != normalize_hash(
        l2_genesis_hash
    ):
        raise BundleError("rollup L2 genesis hash differs from release manifest")
    if nested(addresses, "metadata", "system_config_start_block") != origin_block:
        raise BundleError("SystemConfig start block differs from release manifest")
    if nested(rollup, "genesis", "l2_time") != genesis_time:
        raise BundleError("rollup genesis time differs from release manifest")
    if int(str(genesis.get("timestamp")), 16) != genesis_time:
        raise BundleError("L2 genesis timestamp differs from release manifest")

    dusk_file = (bundle_dir / "origin-parent-dusk-hash.txt").read_text(encoding="utf-8").strip()
    eth_file = (bundle_dir / "origin-parent-eth-hash.txt").read_text(encoding="utf-8").strip()
    if normalize_hash(dusk_file) != normalize_hash(parent_dusk):
        raise BundleError("Dusk origin-parent hash differs from release manifest")
    if normalize_hash(eth_file) != normalize_hash(parent_eth):
        raise BundleError("Ethereum origin-parent hash differs from release manifest")

    output_root = (bundle_dir / "l2-genesis-output-root.txt").read_text(encoding="utf-8").strip()
    require_hash(output_root, "l2-genesis-output-root.txt")
    if validation.get("l2_genesis_output_root") != output_root:
        raise BundleError("local validation attests a different L2 genesis output root")
    if normalize_hash(validation.get("l2_genesis_hash", "")) != normalize_hash(l2_genesis_hash):
        raise BundleError("local validation attests a different L2 genesis block hash")
    if nested(addresses, "metadata", "absolute_prestate") != prestate.get("pre"):
        raise BundleError("address book and prestate proof use different absolute prestates")

    address_checks = {
        "deposit_contract_address": "optimism_portal",
        "l1_system_config_address": "system_config",
        "protocol_versions_address": "protocol_versions",
    }
    for rollup_field, contract_name in address_checks.items():
        configured = rollup.get(rollup_field)
        deployed = nested(addresses, "contracts", contract_name, "evm_address")
        if not isinstance(configured, str) or configured.lower() != str(deployed).lower():
            raise BundleError(
                f"rollup {rollup_field} differs from address book {contract_name}"
            )

    attestation = nested(manifest, "attestations", "localValidation")
    if attestation != "local-validation.json":
        raise BundleError("attestations.localValidation must reference local-validation.json")

    if strict:
        charts = nested(manifest, "charts")
        for chart, supported_versions in RELEASE_CHART_COMPATIBILITY.items():
            version = charts.get(chart)
            if version not in supported_versions:
                supported = ", ".join(sorted(supported_versions))
                raise BundleError(
                    f"release candidate requires compatible {chart} chart ({supported}); got {version!r}"
                )
        for component_name in SOURCE_PINNED_COMPONENTS:
            revision = components[component_name].get("sourceRevision")
            if not isinstance(revision, str) or not REVISION.fullmatch(revision):
                raise BundleError(
                    f"release candidate requires a full source revision for {component_name}"
                )
        activations = nested(manifest, "network", "dusk", "activationHeights")
        require_positive_int(activations.get("blobCall"), "activationHeights.blobCall", allow_zero=True)
        require_positive_int(
            activations.get("nativeCurves"), "activationHeights.nativeCurves", allow_zero=True
        )
        require_positive_int(
            activations.get("consumeGas"), "activationHeights.consumeGas", allow_zero=True
        )
        if stage0.get("executionProfile") != "constrained-v1":
            raise BundleError("release candidate must use executionProfile constrained-v1")
        limits = stage0.get("calldataLimits")
        if not isinstance(limits, dict):
            raise BundleError("release candidate must record constrained calldata limits")
        for name in (
            "bn254PairingBytes",
            "bls12381G1MultiExpBytes",
            "bls12381G2MultiExpBytes",
        ):
            require_positive_int(limits.get(name), f"stage0.calldataLimits.{name}")
    else:
        charts = nested(manifest, "charts")
        for chart, supported_versions in RELEASE_CHART_COMPATIBILITY.items():
            if charts.get(chart) not in supported_versions:
                warnings.append(
                    f"rehearsal uses {chart} chart {charts.get(chart)!r}, outside the Stage 0 release matrix"
                )
        for component_name in SOURCE_PINNED_COMPONENTS:
            if components[component_name].get("sourceRevision") is None:
                warnings.append(f"rehearsal did not record {component_name} source revision")
        if stage0.get("executionProfile") != "constrained-v1":
            warnings.append("rehearsal predates the final constrained-v1 execution profile")

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--strict-release",
        action="store_true",
        help="apply release-candidate completeness checks to a rehearsal bundle",
    )
    args = parser.parse_args()
    try:
        warnings = validate_bundle(args.bundle.resolve(), args.strict_release)
    except BundleError as exc:
        print(f"release bundle validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"release bundle valid: {args.bundle}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
