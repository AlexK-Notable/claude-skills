# ARCHIVED — gen-1 "Self-Learning Harness" spec (2026-06-22 → 2026-07-11)

**Superseded by the gen-2 corpus at `docs/specs/self-learn/`. Do not build from these docs.**

## What this was

The first-generation design for a portable module that captured behavioral
"directives" from user corrections and re-injected them at SessionStart:
capture → classify → store → inject → promote, with a TOML manifest + 3-tier
adapter for cross-repo portability, a statistical measurement loop
(corroboration / reputation / quarantine), and an approve-before-first-use
safety queue. Three docs (design · decisions · state-of-play) plus example
host manifests, developed across three sessions with five review rounds.

## Why it was archived

A whole-plan blind review on 2026-07-11 (four agents — znote
`fKLmvUMb-jVB_u2whGiV3`, hub `cbEi6v8zmbLs7L-FMpMsa`) found the framing
itself broken, not the internals:

1. **The locked delivery mechanism (SessionStart injection) was structurally
   wrong for skill-scoped rules** — no skill is active at SessionStart, so the
   hook must preload across all skills (measurably harmful) and the
   reputation/surfaced counters measured exposure-to-noise, not causation.
2. **The scale premise was refuted by this repo's own history** — ~5–7 real
   behavioral directives (of ~58 lessons) in five weeks, zero recurrences;
   the statistical loop mathematically cannot close at that volume.
3. **The approval queue was empirically dead on arrival** — ha-note's lighter
   promotion queue was worked exactly once in its life.
4. **C7 (in-the-moment confirm) was not implementable** via Claude Code hooks.
5. **Sequential lock-in**: the C-group volume analysis invalidated premises of
   earlier-LOCKED decisions (B3/B4/E2), which their LOCKED status shielded
   from re-derivation.

The user then proposed the UI-fronted triage architecture (accumulate →
surface → route-to-canon with agent assistance) that gen 2 is built around.

## What remains valuable in here

- **The safety analysis** (E2: injection-loop risks, source-trust tiers,
  quarantine damping) — design wisdom for the v2 statistical layer.
- **The portability work** (A1 probe / A3 manifest + the example TOMLs) — the
  ready-made spec for v2 portability, gated on a second real host user.
- **The directive schema substance** (§6) — carried forward into gen 2's
  `02-schema.md` in adapted form.
- **The review methodology** — blind, altitude-stratified review beat leading
  review three times running.

Full provenance trail: znotes in project `skill-self-improvement`
(reviews `Fb7_Nvdyay6lIspcUtpsL` → `CR7l33av092VYHoN09qiu` →
`YhcvfM3KPgiLPPp8U-7BS` → `fKLmvUMb-jVB_u2whGiV3`; decisions
`YQ4644qXrprldGV5RGQCl`, `fSfJi7WzPeaDvvMzkVM2F`, `gXXgjVt_kquv75CCjtbYx`,
`c7IdjdPQVEmZtFCZ3apY5`).
