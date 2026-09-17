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
| `Moza Flight - AB6 + MTQ GA - AB6 Base - airplanes controls.xml` | 28 |
| `Moza Flight - AB6 + MTQ GA - AB6 Base - general controls.xml` | 17 |
| `Moza Flight - AB6 + MTQ GA - MTQ Quadrant - airplanes controls.xml` | 27 |
| `Moza Flight - AB6 + MTQ GA - MTQ Quadrant - general controls.xml` | 6 |

**78 bindings**, built against the real button map read from MOZA Cockpit on
2026-09-17 — every button number below is confirmed to exist on this rig.

Load all four — one per device per category.

**Division of labour:** the stick flies the aeroplane and owns every camera; the
quadrant runs the engine, the autopilot and the systems.

## AB6 Base + MHG grip — airplanes

| Control | Physical | Does |
| --- | --- | --- |
| L-Axis X / Y | base gimbal | Ailerons / elevator |
| R-Axis Z | grip twist | Rudder |
| **1** | trigger, stage 2 | Wheel brakes |
| **6** | trigger, stage 1 | Carb heat |
| **3** | nosewheel steering lock | Tailwheel lock |
| **4** | Launch (guarded) | Landing gear |
| **5** | head button, lower right | Electric fuel pump |
| **7 / 9** | Hat A up / down | **Elevator trim** |
| **8 / 10** | Hat A right / left | Aileron trim |
| **11** | Hat A push | Rudder trim reset |
| **17 / 19** | Hat C up / down | **Altimeter baro** |
| **18** | Hat C right | COM radio swap |
| **20 / 21** | Hat C left / push | Rudder trim left / right |
| **23 / 24** | 3-pos switch up / down | Master battery / alternator |
| **49–56** | base button columns | Cabin lights, alternate static, nav, beacon, strobe, pitot heat, parking brake, starter |

## AB6 Base + MHG grip — general

| Control | Physical | Does |
| --- | --- | --- |
| R-Axis X / Y | mini stick | Quick views 1–4 inside, chase looks outside |
| **2** | head button, left | Cycle view mode |
| **12 / 14** | Hat B up / down | Cockpit camera next / previous |
| **13 / 15** | Hat B right / left | Zoom in / out |
| **16** | Hat B push | **Reset all cameras** |
| Slider X | base thumbwheel | Cockpit camera zoom |

## MTQ + TQF — airplanes

| Control | Physical | Does |
| --- | --- | --- |
| R-Axis X / Y | throttle levers 1 / 2 | Throttle / propeller RPM |
| Slider X | speedbrake lever | Mixture |
| Slider Y | flap lever (detented 0/1/2/3/FULL) | Flaps |
| **1–4** | A1–A4 annunciators | APR hold, VS hold, VS up / down |
| **5–10** | 2×3 grid | NAV, HDG, SPD, ALT, flight director, **AP master** |
| **11 / 12 / 13** | rotary encoder | Altitude down / up / sync to current |
| **14 / 15 / 16** | rotary encoder | Heading bug left / right / sync to current |
| **25 / 27 / 29** | 2-pos toggles | Avionics master, magnetos up / down |
| **53 / 54** | TQF right hat | Flaps up / down |
| **55 / 56** | TQF right hat | Landing / taxi lights |

## MTQ + TQF — general

| Control | Physical | Does |
| --- | --- | --- |
| L-Axis X / Y | TQF left thumb stick | Slide cockpit viewpoint |
| **62** | thumb stick push | Quick view 5 |
| **63 / 64 / 65** | left-module buttons | ATC menu, EFB, aircraft labels |

## Deliberately left free

- **31–43** — lever detent virtual buttons. **41 and 42 are the afterburner pair**
  and assert whenever a lever crosses the detent, which on a GA aeroplane is just
  full power for takeoff. An earlier revision had beacon and nav lights there,
  which would have flipped both on every departure.
- **17–21** — the 5-position rotary. Ideal for a magneto selector, but the events
  are aircraft-specific.
- **22–24, 49–51, 57–61** — remaining MTQ toggle and TQF right-module switches.
- **AB6 22, Dial (Slider Y) and its detents 57–62** — spare.

## Two upstream bindings that never worked

Both found by checking the profiles against the real button map:

- **AB6 button 29** (camera resets). The grip stops at 24 and the base starts at
  49 — **there is no button 29 on this hardware**, so that binding never fired.
  Resets now live on Hat B push (16).
- **MTQ button 64** (`KEY_AXIS_ELEV_TRIM_SET`). 64 is an ordinary button on the
  TQF left module, not a trim wheel, so binding an axis action to it did nothing.
  Elevator trim is now Hat A up/down on the grip.

## Confirmed hardware inventory

Verified 2026-09-17 against MOZA's own user manuals and support knowledge base —
not inferred from the profiles.

**AB6 FFB Base** — Windows enumerates it as `MOZA AB6 FFB Base`, which is why the
XML says that.

- **8 RGB-backlit buttons**
- **2 axis sliders**, switchable between Button / Axis / **Mixed** mode
- Pitch and roll from the force-feedback gimbal
- Takes MH16, MHG, MA3X and third-party grips

**MHG Flightstick** — the grip in the AB6 bundle.

- **Mini stick**, 2-axis analog *(this is what the view bindings use, not a hat)*
- **Four management hats**: Sensor, Navigation, Target, Countermeasure
- **Dual-stage trigger** (two signals), **Launch**, **Mode Cycle**,
  **Nosewheel Steering Lock**
- **Z-axis** twist — the rudder axis
- Warning Button Light is an indicator, not an input

The arithmetic closes exactly: 4 hats × 4 directions = 16, plus Launch, Mode
Cycle, both trigger stages and the nosewheel lock = 21, plus the base's 8 = **29**,
which is the "29 programmable signals" MOZA advertise for the bundle.

**MTQ — Multi-function Throttle Quadrant.**

- Four axes: throttle 1, throttle 2, flaps, speedbrake
- **Rotary encoders**, which MOZA themselves recommend for "HDG, ALT, SPD, V/S"
- **Toggle switches** bottom right, 2- and 3-position, "suitable for engine start,
  fuel cutoff, or master switches"
- Detents generate **six virtual buttons** for the Cutoff / Idle / Afterburner zones
- Flaps and speedbrake levers also support Button / Axis / Mixed mode
- Three interchangeable handles: **TQA** (Airbus, idle+climb detents, reverse
  thrust lock), **TQF** (fighter, afterburner detent, grip speedbrake button,
  thumb stick), **TQB** (general aviation, smooth travel, no detents)

## Tuned for the TQF handle

These profiles assume a **TQF** fighter handle on the MTQ, which is what this rig
has. That drives one deliberate omission:

**Buttons 41 and 42 are left unbound on purpose.** They are the afterburner-zone
virtual buttons. On the TQF they assert whenever a throttle lever crosses the
afterburner detent — which in a GA aeroplane just means "full power for takeoff".
Anything bound there fires on every departure and every go-around. An earlier
revision of this file had beacon and nav lights on them, which would have flipped
both lights during every takeoff roll.

If you remove the detent mechanically — MOZA document how — those two become safe
to use. Until then they stay empty, and beacon and nav lights are waiting for a
home.

## Claimed since the button map arrived

All three pools that were idle in the first revision are now in use:

- **The MHG grip hats.** Hat A is the trim cluster, Hat B the camera hat, Hat C
  altimeter and radio. Only the mini stick was bound before.
- **The MTQ toggle switches** — avionics master and magnetos, which is what MOZA
  recommend them for.
- **The TQF modules** — the left thumb stick and its three buttons, and the right
  hat for flaps and the lights you want on the takeoff roll.

What remains free is listed under *Deliberately left free* above, and is free for
a reason rather than by omission.

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

**Button numbers shift with the fitted hardware.** The AB6's buttons come partly
from the base and partly from whichever grip is attached, and the MTQ's change with
the handle — MOZA's software explicitly redraws its button diagram when you swap
handles. So these numbers are correct for an **AB6 + MHG + MTQ/TQF** rig and should
not be assumed on a different combination.

Two earlier inferences in this document have since been **confirmed** against MOZA's
manuals and support pages: buttons 41/42 really are the afterburner detent pair, and
the 5–16 block really is a labelled physical cluster — MOZA's own guidance points
the MTQ's rotary encoders at exactly the HDG / ALT / SPD / V/S functions bound there.

## Source

Extracted from the six `Moza *.xml` files in `profiles/`, at commit `2027bf0` of
[highinthefssky/msfs-2024-controls-settings](https://github.com/highinthefssky/msfs-2024-controls-settings).
