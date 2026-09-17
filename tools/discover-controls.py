#!/usr/bin/env python3
"""
Discover exactly what buttons, axes and hats your controllers expose, and which
physical control maps to which number in MSFS.

Run this on the PC the sim lives on, with the MOZA gear plugged in.

    pip install pygame
    python tools/discover-controls.py            # inventory, then live press-to-identify
    python tools/discover-controls.py --inventory-only

MSFS numbers buttons from 1; the underlying HID layer numbers from 0. This script
prints the MSFS number, which is what the profile XML uses.
"""

from __future__ import annotations

import sys
import time

try:
    import pygame
except ImportError:
    sys.exit("pygame not installed.  Run:  pip install pygame")


def main() -> int:
    pygame.init()
    pygame.joystick.init()

    n = pygame.joystick.get_count()
    if n == 0:
        return int(bool(print("No controllers detected. Check they are plugged in "
                              "and not captured by another program.")))

    sticks = []
    print(f"\n{n} controller(s) detected\n" + "=" * 64)
    for i in range(n):
        j = pygame.joystick.Joystick(i)
        j.init()
        sticks.append(j)
        print(f"\n[{i}] {j.get_name()}")
        print(f"      GUID    : {j.get_guid()}")
        print(f"      buttons : {j.get_numbuttons():>3}   (MSFS calls these "
              f"'Joystick Button 1' .. 'Joystick Button {j.get_numbuttons()}')")
        print(f"      axes    : {j.get_numaxes():>3}")
        print(f"      hats    : {j.get_numhats():>3}   "
              f"(each hat is 4-8 more inputs in MSFS)")

    print("\n" + "=" * 64)
    if "--inventory-only" in sys.argv:
        print("Paste the block above back to continue.\n")
        return 0

    print("""
Now the useful part. Press each physical control you actually use in flight and
this will tell you its MSFS number. Move levers and hats too.

Say out loud (or note down) what the control IS as you press it, e.g.
    "Button 17 = red pinkie trigger"
    "Button 33 = left hat up"

Ctrl-C when done, then paste the log back.
""")
    print("-" * 64)

    seen: dict[tuple[int, str], int] = {}
    axis_rest = {(i, a): s.get_axis(a)
                 for i, s in enumerate(sticks) for a in range(s.get_numaxes())}

    try:
        while True:
            pygame.event.pump()
            for i, s in enumerate(sticks):
                tag = s.get_name()[:26]
                for b in range(s.get_numbuttons()):
                    if s.get_button(b):
                        key = (i, f"btn{b}")
                        if not seen.get(key):
                            print(f"  [{tag}]  Joystick Button {b + 1}")
                        seen[key] = 1
                    else:
                        seen.pop((i, f"btn{b}"), None)
                for a in range(s.get_numaxes()):
                    v = s.get_axis(a)
                    if abs(v - axis_rest[(i, a)]) > 0.45:
                        key = (i, f"ax{a}")
                        if not seen.get(key):
                            print(f"  [{tag}]  axis {a} moved "
                                  f"(rest {axis_rest[(i, a)]:+.2f} -> {v:+.2f})")
                        seen[key] = 1
                    else:
                        seen.pop((i, f"ax{a}"), None)
                for h in range(s.get_numhats()):
                    hv = s.get_hat(h)
                    if hv != (0, 0):
                        key = (i, f"hat{h}{hv}")
                        if not seen.get(key):
                            print(f"  [{tag}]  hat {h} -> {hv}")
                        seen[key] = 1
                    else:
                        for k in [k for k in seen if k[0] == i
                                  and k[1].startswith(f"hat{h}")]:
                            seen.pop(k, None)
            time.sleep(0.03)
    except KeyboardInterrupt:
        print("\n" + "-" * 64 + "\nDone.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
