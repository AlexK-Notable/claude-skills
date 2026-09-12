# Learnings

Reference-routed lessons, appended and retired by self-learn (newest
last). Each entry carries its record id for provenance; regenerate
nothing here — entries are added or removed only by self-learn's own
verbs (U-verbs S-54), never hand-edited in place.

## 2026-09-12 — lrn-c162fb91

**Fact:** mkinitcpio's chwd drop-in (10-chwd.conf) forces nvidia modules into every kernel preset's initramfs regardless of whether that kernel has nvidia-open-dkms installed, causing a silent (exit 0) ERROR: module not found failure and an incomplete initramfs for kernels without it (e.g. stock 'linux').
