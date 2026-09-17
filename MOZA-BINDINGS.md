# MOZA AB6 / MTQ — what every control actually does

A reference for the six MOZA profiles in `profiles/`, written 2026-09-17 by reading
the XML directly. Every binding below was extracted from the files, not guessed.

Where something is an inference rather than a fact, it says so.

## The six files, and how they pair up

MSFS 2024 keeps bindings in two separate categories per device — **airplanes
controls** (flight and systems) and **general controls** (cameras, views, UI). Both
have to be selected for a device before the profile is complete. Loading only one
half is the usual reason "half my buttons do nothing".

| Profile | Device | Airplanes | General |
| --- | --- | --- | --- |
| **GA** | AB6 FFB Base | 11 bindings | 14 bindings |
| **Airliner** | MTQ Throttle Quadrant | 21 bindings | 3 bindings |
| **Fighter** | MTQ Throttle Quadrant | 22 bindings | 3 bindings |

## Two devices, one name — read this before you troubleshoot

All six files declare `DeviceName="MOZA AB6 FFB Base"` with `ProductID="4098"`,
including the three MTQ profiles. They are still two different pieces of hardware,
distinguished only by instance GUID:

| GUID | Actually is |
| --- | --- |
| `{FAFF2A90-5A0C-11F1-8001-444553540000}` | AB6 FFB Base (the GA profiles) |
| `{5A1F4D70-7196-11F1-8001-444553540000}` | MTQ Throttle Quadrant (Airliner / Fighter) |

So if MSFS shows you two entries with the same name, that is expected. Match them by
the friendly name inside the file — the MTQ ones all end in `- throttle`.

---

# 1. AB6 FFB Base — "GA"

A self-contained general-aviation setup: stick, rudder and throttle all on the base.
No throttle quadrant needed.

## Airplanes controls

| Control | Does | Notes |
| --- | --- | --- |
| **L-Axis X** | Ailerons (roll) | |
| **L-Axis Y** | Elevator (pitch) | |
| **R-Axis Z** | Rudder (yaw) | twist axis |
| **Slider Y** | Throttle, all engines | `THROTTLE_AXIS_SET_EX1` |
| **Button 1** | Wheel brakes | held, not a toggle |
| **Button 49** | Parking brake | toggle |
| **Button 50** | Landing gear up/down | toggle |
| **Button 53** | Elevator trim — nose **down** | repeats while held |
| **Button 54** | Elevator trim — nose **up** | repeats while held |
| **Button 55** | Flaps — retract one notch | |
| **Button 56** | Flaps — extend one notch | |

## General controls

The right-hand hat drives two different things depending on whether you are inside
or outside the aircraft. Same physical directions, different result.

| Control | In the cockpit | In external/chase view |
| --- | --- | --- |
| **R-Axis Y−** (hat up) | Quick view 2 | Look up |
| **R-Axis Y+** (hat down) | Quick view 1 | Look down |
| **R-Axis X−** (hat left) | Quick view 4 | Look left |
| **R-Axis X+** (hat right) | Quick view 3 | Look right |

Quick views 1–4 are **snap views you define yourself** in MSFS — the profile only
says which hat direction fires which slot, not where each one points. If they look
wrong, it is your saved snap views, not this binding.

| Control | Does |
| --- | --- |
| **Button 2** | Cycle view mode (cockpit → external → …) |
| **Button 8** | Next cockpit camera preset |
| **Button 10** | Previous cockpit camera preset |
| **Button 29** | **Reset view** — fires three resets at once: cockpit camera, chase camera, and first-person walk-around. Whichever view you are in, this re-centres it. |

---

# 2. MTQ Throttle Quadrant — "Airliner"

## Axes and levers

| Control | Does |
| --- | --- |
| **R-Axis X** | Throttle, engine 1 |
| **R-Axis Y** | Throttle, engine 2 |
| **Slider X** | Speedbrake / spoiler, proportional |
| **Slider Y** | Flaps, proportional |

Two engines only. A four-engine aircraft will need engines 3 and 4 bound separately.

## The autopilot block — buttons 5 to 16

Twelve consecutive buttons forming a complete AP panel. The grouping is contiguous,
which strongly suggests a physical cluster on the quadrant.

| Button | Does |
| --- | --- |
| **5** | NAV1 hold — follow the navigation source (LNAV) |
| **6** | Heading hold |
| **7** | Airspeed hold (SPD) |
| **8** | Altitude hold (ALT) |
| **9** | Flight director on/off |
| **10** | **Autopilot master** — the big one |
| **11** | Selected altitude — **down** |
| **12** | Selected altitude — **up** |
| **13** | Sync selected altitude to **current** altitude |
| **14** | Heading bug — **left** |
| **15** | Heading bug — **right** |
| **16** | Sync heading bug to **current** heading |

Buttons 13 and 16 are the "set it to where I am right now" shortcuts — useful for
grabbing your present altitude or heading before engaging a hold.

## Everything else

| Button | Does |
| --- | --- |
| **25** | Landing lights toggle |
| **27** | Taxi lights toggle |
| **29** | Landing gear up/down |
| **43** | Arm ground spoilers |
| **64** | Elevator trim — see the oddity below |

## General controls — only three bindings

| Control | Does |
| --- | --- |
| **L-Axis X** | Slide the cockpit viewpoint left/right |
| **L-Axis Y** | Slide the cockpit viewpoint up/down |
| **Button 62** | Reset cockpit camera |

That is the whole general-controls profile. Cameras mostly live on the AB6 side.

---

# 3. MTQ Throttle Quadrant — "Fighter"

**The Fighter profile is the Airliner profile plus one binding.** Verified by diff:
the general-controls files are byte-for-byte identical, and the airplanes files
differ in exactly one action.

| Control | Does |
| --- | --- |
| **Button 41 + Button 42 + R-Axis X+ + R-Axis Y+**, all at once | **Afterburner toggle** |

Everything else — the whole autopilot block, the lights, the gear, the spoiler and
flap axes — is identical to Airliner.

That four-input combination is an afterburner gate. MSFS combo bindings require
**every** listed input to be active simultaneously, so this fires only when both
throttle levers are pushed fully forward *and* both detent microswitches (buttons 41
and 42) are closed. You cannot trigger it by accident at cruise power, which is the
whole point.

If it never fires, the likely cause is one lever not reaching full travel — check
axis calibration rather than the binding.

---

---

# 4. AB6 + MTQ combined — general aviation (new)

Four profiles that run both devices together with **nothing bound twice anywhere**.
Generated by `tools/generate-moza-ga-profiles.py`; re-run with `--check` to verify
the committed files still match the script.

| File | Bindings |
| --- | --- |
| `Moza Flight - AB6 + MTQ GA - AB6 Base - airplanes controls.xml` | 10 |
| `Moza Flight - AB6 + MTQ GA - AB6 Base - general controls.xml` | 14 |
| `Moza Flight - AB6 + MTQ GA - MTQ Quadrant - airplanes controls.xml` | 23 |
| `Moza Flight - AB6 + MTQ GA - MTQ Quadrant - general controls.xml` | 3 |

Load all four — one per device per category.

**Division of labour:** the stick flies the aeroplane and owns every camera; the
quadrant runs the engine, the autopilot and the systems.

## AB6 Base — airplanes

| Control | Does |
| --- | --- |
| L-Axis X / L-Axis Y | Ailerons / elevator |
| R-Axis Z | Rudder |
| Button 1 | Wheel brakes (held) |
| Button 49 | Parking brake |
| Button 50 | Strobe lights |
| Button 53 / 54 | Rudder trim left / right |
| Button 55 | Pitot heat |
| Button 56 | Electric fuel pump |

## AB6 Base — general

Unchanged from the original GA profile: hat does cockpit quick views 1–4 inside and
chase looks outside, button 2 cycles view mode, 8 / 10 step cockpit cameras, 29
resets all three camera types at once.

## MTQ Quadrant — airplanes

| Control | Does |
| --- | --- |
| R-Axis X | Throttle (all engines) |
| R-Axis Y | Propeller RPM |
| Slider X | Mixture |
| Slider Y | Flaps |
| Buttons 5–16 | Autopilot panel — unchanged from upstream |
| Button 25 / 27 | Landing / taxi lights |
| Button 29 | Landing gear |
| Button 41 / 42 | Beacon / nav lights |
| Button 43 | Avionics master |
| Button 64 | Elevator trim |

## MTQ Quadrant — general

| Control | Does |
| --- | --- |
| L-Axis X / L-Axis Y | Slide cockpit viewpoint |
| Button 62 | Cockpit quick view 5 — save it looking down at the quadrant |

## What changed from the source profiles, and why

- **Throttle moved to the quadrant.** The original GA profile put it on the base's
  Slider Y, which collided with the MTQ throttles. The stick no longer touches
  engine controls at all.
- **Elevator trim is the MTQ wheel (64), not stick buttons.** Mixing an absolute
  axis with incremental buttons means the wheel snaps trim back to its physical
  position the moment you touch it. The freed stick buttons 53/54 became rudder
  trim.
- **Flaps moved to a proportional axis** on the quadrant, so stick buttons 55/56
  became pitot heat and fuel pump.
- **Gear is the quadrant only** (29), so base button 50 became strobes.
- **Buttons 41/42 stopped being the afterburner detent pair** and **43 stopped
  being spoiler arm** — neither belongs on a GA aeroplane. They are now beacon,
  nav and avionics master.
- **The autopilot block (5–16) was left exactly as upstream had it**, on the
  assumption those are labelled physical switches. Remapping them would make the
  printing lie.
- **MTQ button 62 is no longer a second camera reset** — the AB6 already owns that.

## Scope limit, stated plainly

"All buttons available" means **every button that appears anywhere in the six
upstream profiles**, because that is the only evidence I have that a given button
exists on this hardware. I had no MOZA documentation and no web access, so if your
AB6 grip or MTQ has buttons nobody bound upstream, they are still free. The
generator makes adding them a two-line change.

# Notes, oddities and limits

**Button 64 is bound to an axis action.** `KEY_AXIS_ELEV_TRIM_SET` is an axis event,
but it is attached to a button with the axis flag set. That is most likely a trim
wheel or encoder that enumerates as a button. Treat it as "trim control of some
kind" and verify on the hardware — I could not confirm which it is from the files.

**The GA and MTQ profiles conflict on throttle if used together.** The GA profile
puts the throttle on the base's Slider Y; the MTQ profiles put throttles 1 and 2 on
R-Axis X/Y. Load both and you will have two things driving engine power. GA is
designed to be flown *without* the quadrant — pick one.

**Every bound action carries `Delay="2.000000"`.** Unbound actions have `0`. This
appears to be an artefact of how MSFS writes the file rather than a two-second delay
on every control, but it is undocumented and I could not verify it.

**Flag values are undocumented and I have not decoded them.** The files use `1`, `2`,
`4`, `132`, `2050` and `8194`. They correlate loosely with behaviour — `4` and `132`
appear on axes, `1` on the repeating trim and chase-look bindings, `8194` on
toggles and resets — but Microsoft publish no reference, so I have described what
each control *does* from its action name, which is reliable, rather than inventing
meanings for the flags.

**Physical button numbers are not physical positions.** The AB6 is a force-feedback
base; its buttons come from whichever grip is fitted, so "Button 53" means different
hardware on different grips. Where I have grouped buttons (the 5–16 autopilot block,
41/42 as detent switches) that is inference from the binding pattern, not from MOZA
documentation — I had no access to any.

## Source

Extracted from the six `Moza *.xml` files in `profiles/`, at commit `2027bf0` of
[highinthefssky/msfs-2024-controls-settings](https://github.com/highinthefssky/msfs-2024-controls-settings).
