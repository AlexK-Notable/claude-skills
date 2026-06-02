# Encryption (age)

Chezmoi can encrypt files in the source repo so they can safely live in a public/shared git remote. **Recommended for this user** — no encryption is currently configured (no `[age]` block in `~/.config/chezmoi/chezmoi.toml`).

## Table of Contents

- [Why age](#why-age)
- [Setup](#setup)
- [Adding encrypted files](#adding-encrypted-files)
- [Daily workflow](#daily-workflow)
- [What to encrypt](#what-to-encrypt)
- [Recovery / key safety](#recovery--key-safety)

## Why age

[age](https://github.com/FiloSottile/age) is a modern, simple file encryption tool. Single key. No web of trust. Encrypted files end up in source as `<name>.age`, which is just a base64 blob — git-friendly and reviewable.

Alternatives: GPG (more complex, more compatible) and [rage](https://github.com/str4d/rage) (Rust impl of age). Stick with age unless you have a specific reason.

## Setup

```bash
# Install age (user must run this; never sudo from Claude)
# CachyOS / Arch:    sudo pacman -S age
# macOS:             brew install age

# Generate a key pair
age-keygen -o ~/.config/chezmoi/key.txt
chmod 600 ~/.config/chezmoi/key.txt
```

The key file contains both the private key and the public key (as a comment). Extract the public key:

```bash
grep "public key" ~/.config/chezmoi/key.txt
# # public key: age1xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Edit `~/.config/chezmoi/chezmoi.toml`:

```toml
encryption = "age"

[age]
    identity = "~/.config/chezmoi/key.txt"
    recipient = "age1xxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Verify: `chezmoi doctor` should show `ok` for the age section.

## Adding encrypted files

```bash
chezmoi add --encrypt --private ~/.ssh/id_ed25519
```

Result in source dir:
```
~/.local/share/chezmoi/encrypted_private_dot_ssh/private_id_ed25519.age
```

On `apply`:
- Chezmoi reads the encrypted blob
- Decrypts using the configured identity (`key.txt`)
- Writes plaintext to destination with mode 0600

## Daily workflow

Encrypted files behave identically to normal managed files for `add`, `re-add`, `edit`, `apply`. Chezmoi handles encryption/decryption transparently.

```bash
chezmoi edit ~/.ssh/config       # decrypts, opens in $EDITOR, re-encrypts on save
chezmoi cat ~/.ssh/config        # decrypt + show
chezmoi diff                     # diff renders decrypted content
```

## What to encrypt

Strong candidates:

- `~/.ssh/` private keys (`id_rsa`, `id_ed25519`, `*.pem`)
- API tokens — Anthropic, GitHub PAT, OpenAI, etc. Often in `.config/<app>/secrets.json` or similar.
- `.npmrc`, `.netrc` with auth tokens
- `~/.aws/credentials`, `~/.kube/config` (depending on threat model)
- Browser session/cookie files
- `.gnupg/` (often easier to back up the keyring directly)

**Don't encrypt:**

- Files that are public anyway (shell rc, editor config, theme files) — encryption adds opaque diffs and slows reviews.
- Files that change frequently and are non-sensitive — every diff becomes a re-encrypted blob, polluting git history.

## Recovery / key safety

**Critical: back up `~/.config/chezmoi/key.txt` to a separate location** — password manager, hardware key, encrypted USB stick. Without it, every encrypted file in the git repo is unrecoverable.

If the key is lost:

1. Encrypted source files cannot be decrypted
2. They must be re-added from a machine where they still exist as plaintext destinations
3. Old encrypted versions in git history are also lost

Mitigations:

- Store key in a password manager (Bitwarden, 1Password, etc.)
- Store key on a YubiKey using `age-plugin-yubikey` (advanced)
- Keep a printed paper backup of the key file (it's short)
- For extreme paranoia: configure age with multiple recipients (identity + backup key)
