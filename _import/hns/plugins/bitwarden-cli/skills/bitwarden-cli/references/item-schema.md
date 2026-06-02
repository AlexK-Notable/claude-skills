# Item Schema Reference

Bitwarden CLI items are JSON documents. Every item shares a common envelope; type-specific fields go in a nested object keyed by the item type name.

## Table of Contents

- [Item Type Table](#item-type-table)
- [Common Envelope](#common-envelope)
- [Custom Field Types](#custom-field-types)
- [Type 1 — Login](#type-1--login)
- [Type 2 — Secure Note](#type-2--secure-note)
- [Type 3 — Card](#type-3--card)
- [Type 4 — Identity](#type-4--identity)
- [Folders](#folders)
- [Common Patterns](#common-patterns)

## Item Type Table

| `type` | Name | Key object | Primary use |
|---|---|---|---|
| 1 | Login | `login` | Username/password/URI/TOTP |
| 2 | Secure Note | `secureNote` | Free-form text, restore instructions, backups |
| 3 | Card | `card` | Payment cards |
| 4 | Identity | `identity` | Address book, government IDs |

## Common Envelope

Every item has these fields:

```json
{
  "type": 2,
  "name": "Display name in vault",
  "notes": "Free-form notes body. Markdown-friendly.",
  "folderId": null,
  "organizationId": null,
  "favorite": false,
  "reprompt": 0,
  "fields": [],
  "collectionIds": []
}
```

| Field | Meaning |
|---|---|
| `name` | Required. Title shown in vault list. |
| `notes` | Optional free-text body. Same on every item type. |
| `folderId` | UUID of containing folder, or `null` for root |
| `organizationId` | UUID for shared org vaults, or `null` for personal |
| `favorite` | Pin to favorites list |
| `reprompt` | `0` = no master-password re-prompt, `1` = require re-prompt on view |
| `fields` | Custom fields — see below |
| `collectionIds` | Org-vault collection memberships (empty for personal items) |

## Custom Field Types

```json
{"name": "label", "value": "content", "type": 0, "linkedId": null}
```

| `type` | Name | Behavior in UI |
|---|---|---|
| 0 | Text | Visible plaintext |
| 1 | Hidden | Masked by default, click to reveal |
| 2 | Boolean | Renders as checkbox; `value` is `"true"` or `"false"` |
| 3 | Linked | References another field on this item (`linkedId` filled) |

Use **type 1 (hidden)** for things like API keys, fingerprints, or short tokens you want masked at a glance. Use **type 0 (text)** for metadata like machine name, repo URL, generation date.

## Type 1 — Login

```json
{
  "type": 1,
  "name": "GitHub — alexkechichian1",
  "login": {
    "username": "alexkechichian1@gmail.com",
    "password": "...",
    "totp": "otpauth://totp/...",
    "uris": [
      {"uri": "https://github.com", "match": null}
    ],
    "passwordRevisionDate": null
  },
  "notes": "Recovery codes filed in .../<other-item-id>",
  "fields": []
}
```

`login.uris[].match`:
- `null` = base domain match (default)
- `0` = base domain
- `1` = host (subdomain-sensitive)
- `2` = starts with
- `3` = exact
- `4` = regex
- `5` = never

`login.totp` accepts either the otpauth URI or a bare base32 seed.

## Type 2 — Secure Note

The most common type for "store this info" requests.

```json
{
  "type": 2,
  "name": "Note name — host/context",
  "notes": "Markdown-friendly body.\n\nUse \\n for newlines in JSON.",
  "secureNote": {"type": 0},
  "fields": [
    {"name": "label", "value": "value", "type": 0}
  ]
}
```

`secureNote.type` is always `0` (the only valid value — a vestigial enum). Always include it.

**When to put data in `notes` vs `fields`:**
- `notes`: free-form prose, multi-line content, code blocks, restore instructions, anything that benefits from formatting
- `fields`: discrete labeled values (machine name, key fingerprint, generation date, repo URL) — these become indexed metadata visible alongside the body

## Type 3 — Card

```json
{
  "type": 3,
  "name": "Chase Visa — primary",
  "card": {
    "cardholderName": "Alex Kechichian",
    "brand": "Visa",
    "number": "4111111111111111",
    "expMonth": "12",
    "expYear": "2030",
    "code": "123"
  },
  "notes": "...",
  "fields": []
}
```

`card.brand` values: `"Visa"`, `"Mastercard"`, `"Amex"`, `"Discover"`, `"Diners Club"`, `"JCB"`, `"Maestro"`, `"UnionPay"`, `"RuPay"`, `"Other"`.

## Type 4 — Identity

```json
{
  "type": 4,
  "name": "Primary identity",
  "identity": {
    "title": "Mr",
    "firstName": "Alex",
    "middleName": null,
    "lastName": "Kechichian",
    "address1": "...",
    "address2": null,
    "address3": null,
    "city": "...",
    "state": "...",
    "postalCode": "...",
    "country": "US",
    "company": null,
    "email": "alexkechichian1@gmail.com",
    "phone": "...",
    "ssn": null,
    "username": null,
    "passportNumber": null,
    "licenseNumber": null
  }
}
```

## Folders

Folders are themselves API objects, simpler than items:

```json
{"name": "Dotfiles backups"}
```

Create with: `echo '{"name":"foo"}' | bw encode | bw create folder`. Then use the returned `id` as `folderId` on items.

List existing: `bw list folders | jq '.[] | {id, name}'`.

## Common Patterns

### Get the JSON template Bitwarden ships

`bw get template item` prints a blank item with all fields populated. Useful sanity check when you're unsure about a field name:

```bash
bw get template item
bw get template item.field
bw get template item.login
bw get template item.login.uris
bw get template item.card
bw get template item.identity
bw get template folder
```

These never require an unlocked vault — pure CLI-side templates.

### Convert template to specific item

The fastest "give me a valid skeleton" recipe:

```bash
bw get template item | jq '.type = 2 | .name = "My note" | .notes = "Body here" | .secureNote = {type: 0}' | bw encode | bw create item
```

### Add custom fields after creation

```bash
ITEM_ID="<uuid>"
bw get item "$ITEM_ID" | \
  jq '.fields += [{"name":"new_field","value":"new_value","type":0}]' | \
  bw encode | bw edit item "$ITEM_ID"
```
