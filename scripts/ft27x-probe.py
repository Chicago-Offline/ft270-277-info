#!/usr/bin/env python3
"""
ft27x-probe.py — read an FT-270R / FT-277R in clone mode via CHIRP's VX-170
family driver, save the raw image, and report the model ID the radio actually
sends.

This answers the open question in PROGRAMMING-TOOLS.md: does an FT-270R report
`AH022$` (VX-170) / does an FT-277R report `AH022U` (VX-177)? If yes, stock
CHIRP works today. If no, we need a small subclass with the real _model.

It deliberately does NOT patch out the model check. It lets the check fail,
then inspects the bytes that came off the radio. Read-only — never writes.

Usage:
    python3 ft27x-probe.py --port /dev/cu.usbserial-XXXX
    python3 ft27x-probe.py --port /dev/cu.usbserial-XXXX --driver Yaesu_VX-177

Requires the CHIRP source tree on sys.path, e.g.:
    cd ~/src/chirp-src && .venv/bin/python /path/to/ft27x-probe.py --port ...
"""

import argparse
import datetime
import os
import re
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True,
                    help="serial device, e.g. /dev/cu.usbserial-A1B2C3")
    ap.add_argument("--driver", default="Yaesu_VX-170",
                    help="CHIRP driver key (default: Yaesu_VX-170; "
                         "use Yaesu_VX-177 for the 70cm FT-277R)")
    ap.add_argument("--out", default=None,
                    help="output .img path (default: dumps/<driver>-<date>.img)")
    args = ap.parse_args()

    try:
        import serial  # noqa: F401
        from chirp import directory, errors
    except ImportError as e:
        sys.exit("error: CHIRP not importable (%s).\n"
                 "Run this with the CHIRP source venv, e.g.\n"
                 "  cd ~/src/chirp-src && .venv/bin/python %s --port ..."
                 % (e, os.path.basename(__file__)))

    directory.import_drivers()
    if args.driver not in directory.DRV_TO_RADIO:
        sys.exit("error: unknown driver %r" % args.driver)
    cls = directory.DRV_TO_RADIO[args.driver]

    print("driver:   %s %s (expects _model=%r)"
          % (cls.VENDOR, cls.MODEL, getattr(cls, "_model", None)))
    print("port:     %s" % args.port)
    print()
    print("Put the radio in CLONE mode and start the SEND/clone-out step,")
    print("then this read will complete. Read-only; nothing is written.")
    print()

    import serial
    try:
        ser = serial.Serial(port=args.port, baudrate=cls.BAUD_RATE,
                            rtscts=getattr(cls, "HARDWARE_FLOW", False),
                            timeout=1)
    except serial.SerialException as e:
        print("error: could not open %s: %s" % (args.port, e))
        print("\nAvailable serial ports:")
        from serial.tools import list_ports
        found = list(list_ports.comports())
        if found:
            for p in found:
                print("  %s  %s" % (p.device, p.description))
        else:
            print("  (none) — no USB-serial adapter is enumerating at all.")
            print("  Check the cable/port before blaming software:")
            print("    ioreg -p IOUSB -l -w0 | grep 'USB Product Name'")
        sys.exit(1)
    radio = cls(ser)

    err = None
    try:
        radio.sync_in()
        print("sync_in: OK — model check PASSED")
    except errors.RadioError as e:
        err = e
        print("sync_in: RadioError: %s" % e)
    except Exception as e:  # noqa: BLE001
        err = e
        print("sync_in: %s: %s" % (type(e).__name__, e))
    finally:
        try:
            ser.close()
        except Exception:  # noqa: BLE001
            pass

    mmap = getattr(radio, "_mmap", None)
    if not mmap:
        sys.exit("\nNo data captured. Nothing came off the radio — check the "
                 "cable, the port, and that clone-out was actually started.")

    raw = mmap.get_packed() if hasattr(mmap, "get_packed") else bytes(mmap)
    print("\ncaptured: %d bytes" % len(raw))

    # Yaesu model IDs in this family look like AH022$ / AH022U.
    hits = [(m.start(), m.group().decode("ascii", "replace"))
            for m in re.finditer(rb"[A-Z]{2}\d{3}[\x20-\x7e]", raw)]
    if hits:
        print("candidate model IDs found in image:")
        for off, s in hits[:10]:
            print("  offset 0x%04x: %r" % (off, s))
    else:
        print("no AHnnnX-style model string found — dump the head manually:")
        print("  %s" % raw[:64].hex(" "))

    out = args.out
    if not out:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d")
        out = os.path.join("dumps", "%s-%s-read.img" % (args.driver, stamp))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as f:
        f.write(raw)
    print("\nsaved:    %s" % out)

    if err:
        print("\nVerdict: stock CHIRP will NOT accept this as %s." % cls.MODEL)
        print("Compare the model ID above against %r. If it differs, the fix is"
              % getattr(cls, "_model", None))
        print("a subclass overriding _model — an upstreamable CHIRP patch.")
    else:
        print("\nVerdict: stock CHIRP reads this radio as %s today." % cls.MODEL)


if __name__ == "__main__":
    main()
