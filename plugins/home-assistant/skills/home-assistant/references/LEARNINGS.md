# Learnings

Reference-routed lessons, appended by self-learn (newest last). Each
entry carries its record id for provenance; regenerate nothing here —
this file is append-only.

## 2026-07-13 — lrn-e2e4026b

**Fact:** HA Core debounces .storage registry writes (delayed save): after a registry mutation, the on-disk .storage file can lag live state for seconds to minutes, so a file read or backup taken immediately after a change may be stale.

**Context:** Mechanism behind the existing verify-via-live-API rule in SKILL.md; surfaced during self-learn fixture-C absence-proofing (2026-07-13), which confirmed the causal fact appears on no loaded surface.
