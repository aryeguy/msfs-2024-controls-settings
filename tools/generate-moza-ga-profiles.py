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

# --------------------------------------------------------------------------
# AB6 device = MOZA AB6 FFB Base + MHG flightstick, one HID device.
# Layout read off MOZA Cockpit's Button Number panel, 2026-09-17:
#
#   MHG grip   1  trigger stage 2      6  trigger stage 1
#              2  head button (left)   5  head button (lower right)
#              3  nosewheel steering lock
#              4  Launch (guarded)
#              7/8/9/10/11    Hat A  up/right/down/left/push
#              12/13/14/15/16 Hat B  up/right/down/left/push
#              17/18/19/20/21 Hat C  up/right/down/left/push
#              22/24/23       3-position switch  up/centre/down
#              mini stick = R-Axis X/Y, twist = R-Axis Z
#   AB6 base   49-52 left button column, 53-56 right button column
#              57/58/59 Slider detents, 60/61/62 Dial detents
#
# There is NO button 29 on this hardware - grip stops at 24, base starts at 49.
# The upstream profile bound camera resets to 29, which simply never fired.
# --------------------------------------------------------------------------

AB6_AIRPLANES = [
    # Primary flight controls. The quadrant never touches these.
    ("KEY_AXIS_AILERONS_SET",       F_AXIS,   ["L-Axis X"]),
    ("KEY_AXIS_ELEVATOR_SET",       F_AXIS,   ["L-Axis Y"]),
    ("KEY_AXIS_RUDDER_SET",         F_AXIS,   ["R-Axis Z"]),

    # Trigger. Stage 2 is the firm squeeze, so it gets the brakes.
    ("KEY_BRAKES",                  F_BUTTON, ["btn:1"]),
    ("KEY_ANTI_ICE_TOGGLE_ENG1",    F_BUTTON, ["btn:6"]),   # carb heat

    ("KEY_TOGGLE_TAILWHEEL_LOCK",   F_BUTTON, ["btn:3"]),   # nosewheel lock
    ("KEY_GEAR_TOGGLE",             F_TOGGLE, ["btn:4"]),   # guarded = good for gear
    ("KEY_TOGGLE_ELECT_FUEL_PUMP",  F_BUTTON, ["btn:5"]),

    # Hat A - trim cluster. The single most-used control in GA flight.
    ("KEY_ELEV_TRIM_UP",            F_REPEAT, ["btn:7"]),
    ("KEY_ELEV_TRIM_DN",            F_REPEAT, ["btn:9"]),
    ("KEY_AILERON_TRIM_RIGHT",      F_REPEAT, ["btn:8"]),
    ("KEY_AILERON_TRIM_LEFT",       F_REPEAT, ["btn:10"]),
    ("KEY_RUDDER_TRIM_RESET",       F_BUTTON, ["btn:11"]),

    # Hat C - altimeter and radio, the other two things touched constantly.
    ("KEY_KOHLSMAN_INC",            F_REPEAT, ["btn:17"]),
    ("KEY_KOHLSMAN_DEC",            F_REPEAT, ["btn:19"]),
    ("KEY_COM_RADIO_SWAP",          F_BUTTON, ["btn:18"]),
    ("KEY_RUDDER_TRIM_LEFT",        F_REPEAT, ["btn:20"]),
    ("KEY_RUDDER_TRIM_RIGHT",       F_REPEAT, ["btn:21"]),

    # 3-position switch on the grip head.
    ("KEY_TOGGLE_MASTER_BATTERY",   F_BUTTON, ["btn:23"]),
    ("KEY_TOGGLE_MASTER_ALTERNATOR", F_BUTTON, ["btn:24"]),

    # Base buttons - lights and set-and-forget systems.
    # Landing and taxi lights are NOT here: they live on the TQF right-module
    # hat, which you can reach on the takeoff roll without releasing the
    # throttle. Binding them in both places would double-toggle.
    ("KEY_TOGGLE_CABIN_LIGHTS",     F_BUTTON, ["btn:49"]),
    ("KEY_TOGGLE_ALTERNATE_STATIC", F_BUTTON, ["btn:50"]),
    ("KEY_TOGGLE_NAV_LIGHTS",       F_BUTTON, ["btn:51"]),
    ("KEY_TOGGLE_BEACON_LIGHTS",    F_BUTTON, ["btn:52"]),
    ("KEY_STROBES_TOGGLE",          F_BUTTON, ["btn:53"]),
    ("KEY_PITOT_HEAT_TOGGLE",       F_BUTTON, ["btn:54"]),
    ("KEY_PARKING_BRAKES",          F_TOGGLE, ["btn:55"]),
    ("KEY_TOGGLE_STARTER1",         F_BUTTON, ["btn:56"]),
]

AB6_GENERAL = [
    # Mini stick: cockpit snap views inside, chase-camera looks outside.
    ("KEY_COCKPIT_QUICKVIEW1", F_BUTTON, ["R-Axis Y+"]),
    ("KEY_COCKPIT_QUICKVIEW2", F_BUTTON, ["R-Axis Y-"]),
    ("KEY_COCKPIT_QUICKVIEW3", F_CYCLE,  ["R-Axis X+"]),
    ("KEY_COCKPIT_QUICKVIEW4", F_CYCLE,  ["R-Axis X-"]),
    ("KEY_CHASE_LOOK_DOWN",    F_REPEAT, ["R-Axis Y+"]),
    ("KEY_CHASE_LOOK_UP",      F_REPEAT, ["R-Axis Y-"]),
    ("KEY_CHASE_LOOK_RIGHT",   F_REPEAT, ["R-Axis X+"]),
    ("KEY_CHASE_LOOK_LEFT",    F_REPEAT, ["R-Axis X-"]),

    ("KEY_VIEW_MODE",          F_CYCLE,  ["btn:2"]),

    # Hat B is the camera hat. Push re-centres whichever view you are in -
    # this is what upstream tried to put on the non-existent button 29.
    ("KEY_COCKPIT_CYCLE",      F_CYCLE,  ["btn:12"]),
    ("KEY_COCKPIT_BACKCYCLE",  F_CYCLE,  ["btn:14"]),
    ("KEY_ZOOM_IN",            F_REPEAT, ["btn:13"]),
    ("KEY_ZOOM_OUT",           F_REPEAT, ["btn:15"]),
    ("KEY_COCKPIT_RESET",      F_TOGGLE, ["btn:16"]),
    ("KEY_CAMERACHASE_RESET",  F_TOGGLE, ["btn:16"]),
    ("KEY_PC_FPV_LOOK_RESET",  F_BUTTON, ["btn:16"]),

    # The base thumbwheels. MOZA suggest these for view zoom.
    ("KEY_COCKPIT_CAMERA_ZOOM_AXIS", F_AXIS, ["Slider X"]),
]

# --------------------------------------------------------------------------
# MTQ + TQF handles. Layout from MOZA Cockpit's Button Number panel, 2026-09-17:
#
#   Panel   1-4    A1-A4 annunciator buttons
#           5-10   2x3 button grid
#           11/12/13  rotary encoder  CCW/CW/push
#           14/15/16  rotary encoder  CCW/CW/push
#           17-21  5-position rotary selector
#           22/23/24  3-position toggle
#           25/26, 27/28, 29/30  2-position toggles
#   Levers  speedbrake detents 31,43 | throttle-1 detents 32,33,41
#           throttle-2 detents 34,35,42 | flap detents 36,37,38,39,40
#   TQF R   49/50/51 3-position switch | 52-56 hat | 57-61 hat
#   TQF L   62 thumb-stick push (L-Axis X/Y) | 63,64,65 buttons
#
#   Axes    R-Axis X throttle 1 | R-Axis Y throttle 2
#           Slider X "Dial" speedbrake lever | Slider Y "Slider" flap lever
#           L-Axis X/Y = TQF left-module thumb stick
#
# Upstream bound KEY_AXIS_ELEV_TRIM_SET to button 64. 64 is an ordinary button
# on the left module, not a trim wheel, so that binding never worked. Elevator
# trim now lives on the MHG's Hat A where it belongs.
# --------------------------------------------------------------------------

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
    # A1-A4 annunciators: the autopilot modes the 2x3 grid has no room for.
    ("KEY_AP_APR_HOLD",             F_BUTTON, ["btn:1"]),
    ("KEY_AP_VS_HOLD",              F_BUTTON, ["btn:2"]),
    ("KEY_AP_VS_VAR_INC",           F_BUTTON, ["btn:3"]),
    ("KEY_AP_VS_VAR_DEC",           F_BUTTON, ["btn:4"]),

    # 2-position toggles, bottom right. MOZA point these at exactly this job.
    ("KEY_TOGGLE_AVIONICS_MASTER",  F_BUTTON, ["btn:25"]),
    ("KEY_MAGNETO1_INCR",           F_BUTTON, ["btn:27"]),
    ("KEY_MAGNETO1_DECR",           F_BUTTON, ["btn:29"]),

    # TQF right-module hat, under the throttle hand: lights you reach for on
    # the roll without letting go of the throttle.
    ("KEY_TOGGLE_TAXI_LIGHTS",      F_BUTTON, ["btn:56"]),
    ("KEY_LANDING_LIGHTS_TOGGLE",   F_BUTTON, ["btn:55"]),
    ("KEY_FLAPS_UP",                F_BUTTON, ["btn:53"]),
    ("KEY_FLAPS_DOWN",              F_BUTTON, ["btn:54"]),

    # DELIBERATELY UNBOUND on the TQF, and this matters:
    #
    #   31-43  lever detent virtual buttons. MOZA's detent feature emits six of
    #          these for the Cutoff / Idle / Afterburner zones (32/33/41 on
    #          throttle 1, 34/35/42 on throttle 2), plus flap and speedbrake
    #          position buttons. On the TQF, 41 and 42 assert whenever a lever
    #          crosses the afterburner detent - which for a GA aeroplane is
    #          just "full power for takeoff". An earlier revision had beacon
    #          and nav lights there, which would have flipped both lights on
    #          every departure. Remove the detent mechanically and they become
    #          safe; until then, leave them alone.
    #
    #   17-21  5-position rotary. Ideal for a magneto selector
    #          (OFF/R/L/BOTH/START) but the events are aircraft-specific.
    #   22-24  3-position toggle, free.
    #   49-51, 57-61  remaining TQF right-module switch and hat, free.
]

MTQ_GENERAL = [
    ("KEY_COCKPIT_CAMERA_TRANSLATION_X", F_AXIS_EX, ["L-Axis X"]),
    ("KEY_COCKPIT_CAMERA_TRANSLATION_Y", F_AXIS_EX, ["L-Axis Y"]),
    # Thumb-stick push. Not another camera reset - the MHG's Hat B owns that.
    ("KEY_COCKPIT_QUICKVIEW5",           F_BUTTON,  ["btn:62"]),
    # Left-module buttons, all within reach of the throttle hand.
    ("KEY_ATC_MENU_OPEN",                F_BUTTON,  ["btn:63"]),
    ("KEY_MENU_SR_EFB_TOGGLE",           F_BUTTON,  ["btn:64"]),
    ("KEY_TOGGLE_AIRCRAFT_LABELS",       F_BUTTON,  ["btn:65"]),
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
