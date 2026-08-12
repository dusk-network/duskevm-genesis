# DuskEVM testnet artifacts

These files define the existing DuskEVM testnet chain. Changing `genesis.json`,
`l1-genesis.json`, or `rollup.json` is a chain-breaking operation and requires a
fresh testnet genesis.

The Cannon-Kona challenger uses `prestate.bin.gz`. Its commitment is recorded
in both `absolute-prestate.txt` and `l1-addresses.json`:

```text
0x0323bc27b4764a4c1d292b5949c6d860763454fecec31b8155f15872ae918b28
```

`prestate-proof.json` is retained beside the binary so operators can verify the
step-zero commitment. Deployment configuration must also pin the downloaded
files by SHA-256; artifact names alone are not an integrity boundary.
