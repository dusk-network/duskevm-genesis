# DuskEVM Genesis

This repository contains the public deployment artifacts for the DuskEVM
networks:

- Mainnet: production configuration (WIP)
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
