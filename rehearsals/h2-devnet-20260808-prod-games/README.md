# H2 Devnet Production-Game Rehearsal

This immutable artifact set defines the isolated DuskEVM deployment used to
validate the H2 Kubernetes topology against Dusk devnet. It does not replace
the public `devnet/` deployment.

- Dusk L1 chain ID: `3`
- DuskEVM L2 chain ID: `1310`
- L1 origin block: `526452`
- Adapter compatibility base: `testnet-2026-07-27`
- Adapter maintenance commit: `42f7b36fb574f399e837f3b0b63a51421918c367`
- Adapter image: `ghcr.io/dusk-network/dusk-duskevm-adapter@sha256:a50377461dfd8058c5bdf08f7202ed4bedace5846fc5753e5177795c7172efe4`
- Contracts tag: `testnet-2026-07-27`
- Fault-proof game type: `8`
- Fault-proof maximum depth: `73`
- Fault-proof split depth: `30`
- Bond curve: OP Big Bonds, scaled to Dusk by `33,333 LUX/gas`
- Rehearsal maximum game clock: `1,200 seconds`

The genesis, rollup, L1 chain, address-book, and prestate files form one atomic
deployment set. `prestate.bin.gz` is the matching Cannon-Kona absolute prestate
used by the type-8 challenger; `prestate-proof.json` records its commitment and
proof. Do not combine these files with artifacts from another network or reuse
an existing adapter, op-reth, op-node, challenger, or Blockscout data directory
with this set.

## SHA-256

```text
02c42e7cd973ca87f12742e95d6344140fd426e46081e09dd23d13dfc3169e49  genesis.json
ffe6d5432e177522717faafe349cfbce130cb6fe1c417b483add90841cdb4330  l1-addresses.json
ad532475cbacd1d617f3e91b0df534bfc0f4934f248db75294a1e467bc8bfb72  l1-genesis.json
9c3f294a1783291c58d6037512de7af726d80618428ca7957f23be64183d5c7a  prestate-proof.json
8b64ee56eda2461609f0996b1f0916b4aba5ba48a0b76012a3fe8336b14abbae  prestate.bin.gz
e4adfdea6a8b1e9c382c74dff1f1851f24e0fd740db6418988aa62e06f41f076  rollup.json
```
