---
id: lrn-a5a52a80
type: knowledge
scope: skill:home-assistant
source: backlog
status: superseded
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:5321278fbace
    note: journal entry dated 2026-06-03
routing: null
supersedes: null
superseded_by: canon
resolution_note: overnight batch per user authorization 2026-07-14 (safe subset)
---

## Fact
An unclean host reboot can ZERO-FILL HA .storage files (seen: core.restore_state -> 134KB of NUL bytes) when the root ext4 is mounted data=writeback. HA detects the unparseable file at next startup, quarantines it as core.restore_state.corrupt.<ISO-ts>, auto-creates a fresh default, and raises a repair notification. Benign for restore_state (it is only a restart-restore cache); the fix is to acknowledge + delete the zeroed file, NOT restore from backup.

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** ext4 data=writeback + unclean reboot/power-loss: file metadata (size) is updated but data blocks are not flushed before reset, so the blocks read back as zeros. Root fs /dev/mmcblk1p1 (microSD) on the Nova is mounted writeback. restore_state is the usual victim because HA rewrites it constantly.
- **Fix:** Verify it's a host reboot not a manual-edit error: 'od -An -c <corrupt>' shows all \0, and dmesg shows a kernel boot at the corruption timestamp while the container has ExitCode=0 RestartCount=0. Click Submit on the repair notification (HA already recovered), delete the all-zeros .corrupt file. Confirm the OTHER .storage JSON (core.config_entries, *_registry) still parse via json.load. To reduce recurrence: clean reboots + consider remounting data=ordered.
- **Repro / verify:** `Unclean reboot while HA is running on data=writeback ext4 -> next boot: ERROR helpers.storage 'Unrecoverable error decoding storage core.restore_state ... unexpected character: line 1 column 1 (char 0)'.`
- **Tags:** storage, reboot, ext4
