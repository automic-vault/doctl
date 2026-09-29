# Automic Vault signed doctl releases

This fork repacks upstream doctl executables with Automic Vault's Developer ID.
It does not patch executable code or add a credential protocol. The AV Hardener
owns protected installation, native token routing, verification and migration.

Follow the canonical [domain language](https://github.com/automic-vault/automic-vault/blob/main/docs/domain-language.md),
[architecture](https://github.com/automic-vault/automic-vault/blob/main/docs/architecture.md)
and [positioning](https://github.com/automic-vault/automic-vault/blob/main/docs/positioning.md).

Download the arm64 and amd64 archives from DigitalOcean's **v1.175.0** release as
`inputs/arm64.tgz` and `inputs/amd64.tgz`. The script checks pinned input hashes,
extracts only a bounded regular executable, signs with Hardened Runtime and no
entitlements, verifies the AV Developer ID and packages the license.

```sh
python3 av/repackage.py --inputs inputs --output artifacts --identity CERTIFICATE_SHA1
```

`manifest-1.175.0-av.1.json` records the actual reviewed outputs. Timestamped
signatures make rebuilds produce different output digests: never replace a
published pinned artifact. Use a new release revision and update the AV and tap
pins together. Upstream executables are not run by this packaging script.
No separate notarization assessment is claimed.

Prepare a **draft** release `v1.175.0-av.1` containing the two signed archives
and manifest. Publish only after reviewing the dependent AV and tap PRs and
finishing signed end-to-end installation/credential-delivery validation.

`catalog.go` walks the actual upstream Cobra tree, including aliases, while
excluding local commands, plugins, apps dev, serverless support and new command
families pending review. Against upstream commit
`776faec72dd6e13556f37340f068fd76b16ad575`, it emits the 470 lines used by AV:

```sh
go run -mod=vendor av/catalog.go > doctl-commands.txt
```

Other credential-consuming commands require explicit review before gaining
access to the protected token. See the AV PR for policy and boundary tests.
