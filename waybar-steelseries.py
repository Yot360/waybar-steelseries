#!/usr/bin/env python3
"""Waybar custom module: SteelSeries mouse (rivalcfg) and headset (headsetcontrol) battery."""

import argparse
import fcntl
import json
import os
import re
import subprocess
import time

MOUSE_ICON = "󰍽"
HEADSET_ICON = "󰋋"
CHARGING_ICON = "󱐋"

# Several bars (one per monitor) run this at the same moment, but the devices can
# only be opened by one process at a time. Serialise queries with a lock and let
# the other instances reuse a fresh result.
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
LOCK_FILE = os.path.join(RUNTIME_DIR, "waybar-steelseries.lock")
CACHE_FILE = os.path.join(RUNTIME_DIR, "waybar-steelseries.json")
CACHE_SECONDS = 5


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def mouse_battery():
    """Return (level, charging) or None. Parses e.g. 'Discharging [========  ] 80 %'."""
    out = run(["rivalcfg", "--battery-level"])
    if not out:
        return None
    m = re.search(r"(\d+)\s*%", out)
    if not m:
        return None
    return int(m.group(1)), out.strip().lower().startswith("charging")


def headset_battery():
    """Return (level, charging) or None."""
    out = run(["headsetcontrol", "-b", "-o", "json"])
    if not out:
        return None
    try:
        devices = json.loads(out).get("devices", [])
    except json.JSONDecodeError:
        return None
    for dev in devices:
        battery = dev.get("battery") or {}
        status = battery.get("status")
        level = battery.get("level")
        if status in ("BATTERY_AVAILABLE", "BATTERY_CHARGING") and isinstance(level, int) and level >= 0:
            return level, status == "BATTERY_CHARGING"
    return None


def batteries():
    """Return (mouse, headset), querying the devices at most once per CACHE_SECONDS."""
    with open(LOCK_FILE, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if time.time() - os.path.getmtime(CACHE_FILE) < CACHE_SECONDS:
                with open(CACHE_FILE) as f:
                    mouse, headset = json.load(f)
                return mouse and tuple(mouse), headset and tuple(headset)
        except (OSError, ValueError):
            pass
        mouse, headset = mouse_battery(), headset_battery()
        with open(CACHE_FILE, "w") as f:
            json.dump([mouse, headset], f)
        return mouse, headset


def fmt(icon, battery):
    if battery is None:
        return None
    level, charging = battery
    return f"{icon} {CHARGING_ICON if charging else ''}{level}%"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warning", type=int, default=30, help="warning threshold in %% (default: 30)")
    parser.add_argument("--critical", type=int, default=15, help="critical threshold in %% (default: 15)")
    args = parser.parse_args()

    mouse, headset = batteries()

    parts = [p for p in (fmt(MOUSE_ICON, mouse), fmt(HEADSET_ICON, headset)) if p]
    tooltip = "\n".join([
        f"Mouse: {mouse[0]}%{' (charging)' if mouse[1] else ''}" if mouse else "Mouse: not connected",
        f"Headset: {headset[0]}%{' (charging)' if headset[1] else ''}" if headset else "Headset: not connected",
    ])

    # Colour by the lowest battery that is not charging.
    discharging = [b[0] for b in (mouse, headset) if b and not b[1]]
    lowest = min(discharging) if discharging else None
    classes = []
    if lowest is not None and lowest <= args.critical:
        classes.append("critical")
    elif lowest is not None and lowest <= args.warning:
        classes.append("warning")
    if any(b and b[1] for b in (mouse, headset)):
        classes.append("charging")
    if not parts:
        classes.append("disconnected")

    levels = [b[0] for b in (mouse, headset) if b]
    print(json.dumps({
        "text": "  ".join(parts),
        "tooltip": tooltip,
        "class": classes,
        "percentage": min(levels) if levels else 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
