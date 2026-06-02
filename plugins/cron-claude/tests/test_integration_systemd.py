"""Ground-truth: create a REAL user timer, see it in list-timers, remove it.
Skipped where systemd --user is unavailable (e.g. CI)."""
import shutil
import subprocess

import pytest

from cron_claude.systemd import control, timers
from cron_claude.systemd.timers import TimerSpec

pytestmark = pytest.mark.integration


def _systemd_user_available() -> bool:
    if not shutil.which("systemctl"):
        return False
    return subprocess.run(
        ["systemctl", "--user", "is-system-running"], capture_output=True, text=True
    ).returncode in (0, 1)  # 1 = degraded but usable


@pytest.mark.skipif(not _systemd_user_available(), reason="no systemd --user")
def test_real_timer_lifecycle(tmp_path):
    name = "pytest-smoke"
    spec = TimerSpec(
        name=name, on_calendar="*-*-* 04:00:00", exec_start="/bin/true",
        prompt_path="/bin/true", runner="script", description="cron-claude integration smoke",
    )
    try:
        timers.write_units(spec)
        control.daemon_reload()
        control.enable_now(timers.timer_unit(name))
        listed = subprocess.run(
            ["systemctl", "--user", "list-timers", "--all", timers.timer_unit(name)],
            capture_output=True, text=True,
        )
        assert timers.timer_unit(name) in listed.stdout
    finally:
        control.disable_now(timers.timer_unit(name))
        control.stop(timers.service_unit(name))
        timers.remove_units(name)
        control.daemon_reload()
    assert not timers.unit_paths(name)[0].exists()
