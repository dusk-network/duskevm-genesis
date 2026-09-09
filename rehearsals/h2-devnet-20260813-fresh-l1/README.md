# H2 Fresh-L1 Devnet Rehearsal

This immutable artifact set replaces the obsolete H2 rehearsal after the
underlying Dusk devnet was recreated. It is intended for the disposable H2
Kubernetes rehearsal only and does not replace the public `devnet/` artifacts.

- Dusk L1 chain ID: `3`
- Dusk genesis hash: `a8874591964bcb8ac6dc1a7d427984e51d474b83e8db1afb47768e6f54480d7a`
- DuskEVM L2 chain ID: `1310`
- L1 origin block: `280`
- Sequencing window: `4000` L1 blocks (devnet recovery allowance)
- Contracts tag: `testnet-2026-07-27`
- Contracts commit: `a3302939506f35c89b1f012f250e59f904b869bb`
- Adapter compatibility tag: `testnet-2026-07-27`
- Adapter image: `ghcr.io/dusk-network/dusk-duskevm-adapter@sha256:7fde4423b3aedee186a93cb7b29d6dd2e7313403b2e5b5b485114c8a496d52dc`
- Fault-proof game type: `8`
- Fault-proof maximum depth: `73`
- Fault-proof split depth: `30`
- Game maximum clock: `302400` seconds
- Game clock extension: `10800` seconds
- Bond curve: OP Big Bonds, scaled to Dusk by `33333 LUX/gas`

The genesis, rollup, L1 chain, address-book, and prestate files form one atomic
deployment set. Do not mix them with another network or reuse an adapter,
op-reth, op-node, challenger, or Blockscout data directory created from the
previous H2 rehearsal.

The sequencing window is intentionally 400 blocks wider than the original
deployment. The H2 operator lost its unsafe chain after an outage longer than
the original 3,600-block window; the extra margin lets the first recovery
channel land without resetting the otherwise canonical L2 history. This is a
disposable devnet recovery setting, not a mainnet recommendation.

`release-manifest.json` records the exact immutable images and chart versions
observed on H2 and binds them to this artifact set. It also records which
source revisions and activation heights were not captured by this historical
rehearsal. Those omissions deliberately prevent this bundle from passing the
stricter release-candidate validation; this remains rehearsal evidence, not a
mainnet candidate.

`SHA256SUMS` authenticates every generated file in this directory. The two
origin-parent files bind adapter synchronization to the Dusk and projected
Ethereum views of block `279`. `l2-genesis-output-root.txt` records the output
root used to initialize the AnchorStateRegistry. This repository intentionally
contains no wallet, seed, JWT, private key, or Kubernetes Secret.

## Local validation

The set was exercised from empty state against the fresh six-node Dusk devnet:

- all 21 L1 contracts deployed and were wired successfully;
- op-reth and op-node initialized from the generated files;
- op-batcher published a blob in projected L1 block `309` and op-node derived
  it to safe L2 block `127`;
- the proposer created and confirmed a type-8 dispute game;
- the final captured heads were unsafe `274`, safe `127`, and finalized `0`;
- the DisputeGameFactory reported one game.

The blob transaction was
`0x8d7931a6c285ec347455d87cc61e30a0236bf3bcfd79c314f9374c84e2234ac1`.
The proposer transaction was
`0x5a81f7ea78ebd97be9751f67c29323489f0b94b18a7724538ee2d12efd95edf5`
and was included in projected L1 block `316`. `local-validation.json` records
the machine-readable result, including the L2 genesis output root.

Before the H2 rollout, both independently rebuilt adapters repeatedly resolved
origin block `280` to canonical projected hash
`0x1d3832b95282c9d11e10954fb6cb644f034b4050017ea9fe63e5445857147a2c`.
The rollup origin was corrected from the transient hash captured during the
ceremony; no other generated artifact depends on that projected block hash.

Fresh deployments must fund both operational fee paths: the adapter's Dusk
relayer account for wrapper transactions and the proposer's EVM router credit
for the type-8 game bond.
