#!/usr/bin/env python3
"""
Generate a conflict-free MOZA AB6 + MTQ general-aviation control set for MSFS 2024.

Four output profiles, one per (device, category):

    AB6 Base        airplanes  -> flight controls, brakes, trim, systems on the stick
    AB6 Base        general    -> all camera and view handling
    MTQ Quadrant    airplanes  -> engine levers, autopilot panel, lights, gear
    MTQ Quadrant    general    -> seat position, one quadrant snap view

Design rule: one sim function is bound on exactly one control, on exactly one
device, in exactly one category. Nothing is bound twice anywhere.

The generator works by text surgery on the upstream profiles rather than
re-serialising XML, so everything it does not touch stays byte-identical -
including the non-standard multi-root document structure MSFS writes.

Usage:  python3 tools/generate-moza-ga-profiles.py [--check]
        --check verifies the committed outputs match what this script produces.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROFILES = Path(__file__).resolve().parent.parent / "profiles"

# Templates supply the device block (name, GUID, product id) and the full action
# list. We keep the GUIDs so MSFS still recognises each physical device.
TPL_AB6_AIR = "Moza Flight - 6 ABS FFB - GA - airplanes controls.xml"
TPL_AB6_GEN = "Moza Flight - 6 ABS FFB - GA - general controls.xml"
TPL_MTQ_AIR = "Moza Flight - MTQ Throttle Quadrant - Airliner - airplanes controls.xml"
TPL_MTQ_GEN = "Moza Flight - MTQ Throttle Quadrant - Airliner - general controls.xml"

# --------------------------------------------------------------------------
# Control encoding
#
# Buttons encode as N-1. Axes have a base code; base+0 is the negative
# direction, base+1 the positive, base+2 the whole axis. Whole-axis
# Information strings carry a trailing space, directional ones do not. Both
# rules were derived from every KEY element in the upstream repository.
# --------------------------------------------------------------------------

AXIS_BASE = {
    "L-Axis X": 1024, "L-Axis Y": 1040, "L-Axis Z": 1056,
    "R-Axis X": 768,  "R-Axis Y": 784,  "R-Axis Z": 800,
    "Slider X": 512,  "Slider Y": 528,
}


def control(spec: str) -> tuple[str, int]:
    """'btn:29' -> ('Joystick Button 29', 28);  'R-Axis X' -> (..., 770)"""
    if spec.startswith("btn:"):
        n = int(spec[4:])
        return f"Joystick Button {n}", n - 1
    if spec[-1] in "+-":
        name, sign = spec[:-1].strip(), spec[-1]
        return f"Joystick {name}{sign}", AXIS_BASE[name] + (1 if sign == "+" else 0)
    return f"Joystick {spec} ", AXIS_BASE[spec] + 2


# Flag values are undocumented by Microsoft. These mirror what MSFS itself wrote
# for the same action types in the upstream profiles, so behaviour matches.
F_BUTTON, F_REPEAT, F_AXIS, F_AXIS_EX, F_CYCLE, F_TOGGLE = 2, 1, 4, 132, 2050, 8194

# --------------------------------------------------------------------------
# The bindings. (action, flag, [controls]) - multiple controls means MSFS
# requires all of them simultaneously.
# --------------------------------------------------------------------------

AB6_AIRPLANES = [
    # Primary flight controls - the stick owns these, the quadrant never touches them.
    ("KEY_AXIS_AILERONS_SET",      F_AXIS,   ["L-Axis X"]),
    ("KEY_AXIS_ELEVATOR_SET",      F_AXIS,   ["L-Axis Y"]),
    ("KEY_AXIS_RUDDER_SET",        F_AXIS,   ["R-Axis Z"]),
    # Stop-and-go.
    ("KEY_BRAKES",                 F_BUTTON, ["btn:1"]),
    ("KEY_PARKING_BRAKES",         F_TOGGLE, ["btn:49"]),
    # Rudder trim, not elevator trim: elevator trim lives on the MTQ wheel
    # (button 64) and mixing an absolute axis with incremental buttons makes the
    # wheel yank the trim back to its physical position.
    ("KEY_RUDDER_TRIM_LEFT",       F_REPEAT, ["btn:53"]),
    ("KEY_RUDDER_TRIM_RIGHT",      F_REPEAT, ["btn:54"]),
    # Systems you want under your thumb, not across the cockpit.
    ("KEY_PITOT_HEAT_TOGGLE",      F_BUTTON, ["btn:55"]),
    ("KEY_TOGGLE_ELECT_FUEL_PUMP", F_BUTTON, ["btn:56"]),
    ("KEY_STROBES_TOGGLE",         F_BUTTON, ["btn:50"]),
]

AB6_GENERAL = [
    # The hat does cockpit snap views inside, chase-camera looks outside.
    ("KEY_COCKPIT_QUICKVIEW1", F_BUTTON, ["R-Axis Y+"]),
    ("KEY_COCKPIT_QUICKVIEW2", F_BUTTON, ["R-Axis Y-"]),
    ("KEY_COCKPIT_QUICKVIEW3", F_CYCLE,  ["R-Axis X+"]),
    ("KEY_COCKPIT_QUICKVIEW4", F_CYCLE,  ["R-Axis X-"]),
    ("KEY_CHASE_LOOK_DOWN",    F_REPEAT, ["R-Axis Y+"]),
    ("KEY_CHASE_LOOK_UP",      F_REPEAT, ["R-Axis Y-"]),
    ("KEY_CHASE_LOOK_RIGHT",   F_REPEAT, ["R-Axis X+"]),
    ("KEY_CHASE_LOOK_LEFT",    F_REPEAT, ["R-Axis X-"]),
    ("KEY_VIEW_MODE",          F_CYCLE,  ["btn:2"]),
    ("KEY_COCKPIT_CYCLE",      F_CYCLE,  ["btn:8"]),
    ("KEY_COCKPIT_BACKCYCLE",  F_CYCLE,  ["btn:10"]),
    # One button re-centres whichever view you happen to be in.
    ("KEY_COCKPIT_RESET",      F_TOGGLE, ["btn:29"]),
    ("KEY_CAMERACHASE_RESET",  F_TOGGLE, ["btn:29"]),
    ("KEY_PC_FPV_LOOK_RESET",  F_BUTTON, ["btn:29"]),
]

MTQ_AIRPLANES = [
    # Four levers, the classic GA quadrant.
    ("KEY_THROTTLE_AXIS_SET_EX1",   F_AXIS_EX, ["R-Axis X"]),
    ("KEY_PROP_PITCH_AXIS_SET_EX1", F_AXIS_EX, ["R-Axis Y"]),
    ("KEY_AXIS_MIXTURE_SET",        F_AXIS,    ["Slider X"]),
    ("KEY_AXIS_FLAPS_SET",          F_AXIS,    ["Slider Y"]),
    # Autopilot block, buttons 5-16. Left exactly as upstream had it, because
    # these are almost certainly a labelled physical cluster on the quadrant and
    # remapping them would make the printing lie.
    ("KEY_AP_NAV1_HOLD",            F_BUTTON, ["btn:5"]),
    ("KEY_AP_HDG_HOLD",             F_BUTTON, ["btn:6"]),
    ("KEY_AP_AIRSPEED_HOLD",        F_BUTTON, ["btn:7"]),
    ("KEY_AP_ALT_HOLD",             F_BUTTON, ["btn:8"]),
    ("KEY_TOGGLE_FLIGHT_DIRECTOR",  F_BUTTON, ["btn:9"]),
    ("KEY_AP_MASTER",               F_BUTTON, ["btn:10"]),
    ("KEY_AP_ALT_VAR_DEC",          F_BUTTON, ["btn:11"]),
    ("KEY_AP_ALT_VAR_INC",          F_BUTTON, ["btn:12"]),
    ("KEY_AP_ALT_CURRENT_ALT_SET",  F_TOGGLE, ["btn:13"]),
    ("KEY_HEADING_BUG_DEC",         F_BUTTON, ["btn:14"]),
    ("KEY_HEADING_BUG_INC",         F_BUTTON, ["btn:15"]),
    ("KEY_AP_HDG_CURRENT_HDG_SET",  F_TOGGLE, ["btn:16"]),
    # Lights and gear.
    ("KEY_LANDING_LIGHTS_TOGGLE",   F_BUTTON, ["btn:25"]),
    ("KEY_TOGGLE_TAXI_LIGHTS",      F_BUTTON, ["btn:27"]),
    ("KEY_GEAR_TOGGLE",             F_TOGGLE, ["btn:29"]),
    # Buttons 41 and 42 are DELIBERATELY LEFT UNBOUND on the TQF handle.
    #
    # They are the afterburner-zone virtual buttons that the MTQ's detent
    # feature generates (MOZA support: the detent function "adds six virtual
    # buttons" for the Cutoff / Idle / Afterburner zones). On the TQF they
    # assert whenever a throttle lever crosses the afterburner detent - which
    # in a GA aeroplane is simply "full power for takeoff". Anything bound
    # here fires on every departure and go-around.
    #
    # An earlier revision had beacon and nav lights on them, which would have
    # flipped both lights on every takeoff roll.
    #
    # If you remove the detent mechanically (MOZA document this) these become
    # free, but they are unsafe to use while the afterburner detent is fitted.
    #
    # 43 was spoiler arm, which GA aircraft do not have.
    ("KEY_TOGGLE_AVIONICS_MASTER",  F_BUTTON, ["btn:43"]),
    ("KEY_AXIS_ELEV_TRIM_SET",      F_AXIS,   ["btn:64"]),
]

MTQ_GENERAL = [
    ("KEY_COCKPIT_CAMERA_TRANSLATION_X", F_AXIS_EX, ["L-Axis X"]),
    ("KEY_COCKPIT_CAMERA_TRANSLATION_Y", F_AXIS_EX, ["L-Axis Y"]),
    # Deliberately NOT another camera reset - the AB6 already owns that on
    # button 29. Save a snap view looking down at the quadrant instead.
    ("KEY_COCKPIT_QUICKVIEW5",           F_BUTTON,  ["btn:62"]),
]

OUTPUTS = [
    ("Moza Flight - AB6 + MTQ GA - AB6 Base - airplanes controls.xml",
     TPL_AB6_AIR, "GA combined - AB6 - airplanes controls", AB6_AIRPLANES),
    ("Moza Flight - AB6 + MTQ GA - AB6 Base - general controls.xml",
     TPL_AB6_GEN, "GA combined - AB6 - general controls", AB6_GENERAL),
    ("Moza Flight - AB6 + MTQ GA - MTQ Quadrant - airplanes controls.xml",
     TPL_MTQ_AIR, "GA combined - MTQ - airplanes controls", MTQ_AIRPLANES),
    ("Moza Flight - AB6 + MTQ GA - MTQ Quadrant - general controls.xml",
     TPL_MTQ_GEN, "GA combined - MTQ - general controls", MTQ_GENERAL),
]

BOUND_BLOCK = re.compile(
    r'<Action ActionName="([^"]+)"[^>]*>\s*'
    r'(?:<(?:Primary|Secondary)>.*?</(?:Primary|Secondary)>\s*)+'
    r'</Action>',
    re.DOTALL,
)


def build(template: str, friendly: str, bindings) -> str:
    text = (PROFILES / template).read_text(encoding="utf-8")

    # Every action name must already exist, or MSFS silently ignores it.
    existing = set(re.findall(r'ActionName="([^"]+)"', text))
    missing = sorted({a for a, _, _ in bindings if a not in existing})
    if missing:
        raise SystemExit(f"{template}: action(s) not in this profile: {missing}")

    # No control may drive two different actions, except the deliberate
    # cockpit/chase pairs which are mutually exclusive by camera mode.
    dual_ok = {"KEY_COCKPIT_QUICKVIEW1", "KEY_COCKPIT_QUICKVIEW2",
               "KEY_COCKPIT_QUICKVIEW3", "KEY_COCKPIT_QUICKVIEW4",
               "KEY_CHASE_LOOK_UP", "KEY_CHASE_LOOK_DOWN",
               "KEY_CHASE_LOOK_LEFT", "KEY_CHASE_LOOK_RIGHT",
               "KEY_COCKPIT_RESET", "KEY_CAMERACHASE_RESET",
               "KEY_PC_FPV_LOOK_RESET"}
    seen: dict[str, str] = {}
    for action, _, ctrls in bindings:
        for c in ctrls:
            if c in seen and not (action in dual_ok and seen[c] in dual_ok):
                raise SystemExit(f"{template}: {c} double-bound "
                                 f"({seen[c]} and {action})")
            seen[c] = action

    # Clear every binding the template came with.
    text = BOUND_BLOCK.sub(
        lambda m: f'<Action ActionName="{m.group(1)}" ValueEvent="0.000000" '
                  f'Delay="0.000000" Flag="2"/>',
        text)

    # Apply ours.
    for action, flag, ctrls in bindings:
        keys = "".join(
            f"\n{{i}}\t\t<KEY Information=\"{n}\">{v}</KEY>"
            for n, v in (control(c) for c in ctrls))
        pattern = re.compile(
            r'([ \t]*)<Action ActionName="' + re.escape(action) + r'"[^>]*/>')
        def repl(m, action=action, flag=flag, keys=keys):
            i = m.group(1)
            body = keys.replace("{i}", i)
            return (f'{i}<Action ActionName="{action}" ValueEvent="0.000000" '
                    f'Delay="2.000000" Flag="{flag}">\n'
                    f'{i}\t<Primary>{body}\n{i}\t</Primary>\n'
                    f'{i}</Action>')
        text, n = pattern.subn(repl, text, count=1)
        if n != 1:
            raise SystemExit(f"{template}: could not place {action}")

    text = re.sub(r'(<FriendlyName[^>]*>)[^<]*(</FriendlyName>)',
                  lambda m: m.group(1) + friendly + m.group(2), text, count=1)
    return text


def main() -> int:
    check = "--check" in sys.argv
    failures = 0
    for name, tpl, friendly, bindings in OUTPUTS:
        produced = build(tpl, friendly, bindings)
        dest = PROFILES / name
        if check:
            current = dest.read_text(encoding="utf-8") if dest.exists() else ""
            state = "ok" if current == produced else "DRIFTED"
            failures += state == "DRIFTED"
            print(f"  [{state}] {name}")
        else:
            dest.write_text(produced, encoding="utf-8")
            print(f"  wrote {name}  ({len(bindings)} bindings)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
