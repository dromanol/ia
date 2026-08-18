---
name: signed-commit-troubleshooting
description: 1Password signing failures are transient (locked agent) — retry, never --no-gpg-sign; and "No signature" from git log is misleading without allowedSignersFile.
type: gotcha
---

## `1Password: failed to fill whole buffer`

```
error: 1Password: failed to fill whole buffer
fatal: failed to write commit object
```

The commit did **not** happen (staged changes survive). This is the 1Password SSH/GPG agent needing to be
unlocked, or an approval prompt that timed out — it is **transient**, not a misconfiguration.

**Retry the same commit** once the agent is unlocked. Do **not** work around it with `--no-gpg-sign`,
`-c commit.gpgsign=false`, or `--no-verify`: the user configured signing deliberately, and an unsigned
commit can fail branch protection or need rewriting later. If a retry still fails, say so and let the
user unlock rather than bypassing.

## `git log --show-signature` says "No signature" on a signed commit

```
error: gpg.ssh.allowedSignersFile needs to be configured and exist for ssh signature verification
No signature
```

This is a **verification-side** gap: git cannot check an SSH signature without an allowed-signers file.
It says nothing about whether the commit carries a signature, and `%G?` returns `N` for the same reason.

To check whether the signature is actually present, look at the raw object:

```bash
git cat-file commit HEAD | grep -c gpgsig
```

A `gpgsig -----BEGIN SSH SIGNATURE-----` header means it is signed and will verify on the forge, which
has the public keys. Don't report a commit as unsigned based on `--show-signature` alone.
