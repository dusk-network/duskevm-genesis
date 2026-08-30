# DuskEVM deployment bundles

This repository contains the public deployment artifacts for the DuskEVM
networks:

- Mainnet: generated only from an approved immutable release candidate
- Testnet: public testing environment (WIP)
- Devnet: testing environment

Each network directory contains:

- `genesis.json`: op-reth L2 genesis
- `rollup.json`: op-node rollup configuration
- `l1-genesis.json`: Dusk L1 chain configuration used by op-node

Rust-adapter deployments additionally require `l1-addresses.json`, containing
the EVM addresses and Dusk contract IDs from the matching contract deployment.
A network directory without that file is not a complete current deployment
set.

Treat all files in a complete network directory as an atomic set. Reusing an
op-reth or adapter database with artifacts from another set is unsupported and
should fail startup policy checks.

## Release manifest

Every new rehearsal or release bundle must include `release-manifest.json`.
It binds the network identity, activation heights, Stage 0 execution profile,
source revisions, immutable images, chart versions, artifact digests and local
validation evidence. The schema is documented in
`release-manifest.schema.json`.

Validate a bundle with:

```sh
python3 tools/validate_release_bundle.py path/to/bundle
```

Bundles marked `release-candidate` or `release` are checked more strictly than
historical rehearsals. They must pin the contracts, adapter, Rusk and Piecrust
source revisions, record BlobCall, native-curve and explicit-gas-consumption
activation heights, use the `constrained-v1` profile and declare all three
Stage 0 calldata ceilings.

The validator also checks artifact hashes and cross-file invariants: chain IDs,
genesis time, L1 origin, `SystemConfig.startBlock()`, origin-parent hashes,
the projected origin and L2 genesis hashes, OP contract addresses, absolute
prestate and the attested L2 genesis output root. Release candidates must also
use the exact chart versions in the validator's reviewed Stage 0 compatibility
matrix; a chart version is part of the release contract, not a deployment-time
choice.

`release-manifest.json` contains no secret values. Relayer, proposer,
challenger, Engine JWT and database credentials remain in the deployment
environment's secret manager or Kubernetes Secrets.
