#!/usr/bin/env python3
"""
ft27x-write.py — write a clone image back to an FT-270R / FT-277R.

THIS WRITES TO THE RADIO. Unlike the probe and sniff scripts, this one is not
read-only.

Safety interlocks, all of which must pass before a single byte goes out:

1. The image's `model[0:6]` field must equal the selected driver's `_model`.
   This is the cross-band guard. FT-270R and FT-277R images are both 6057 bytes
   and differ by ONE byte in that field, so they look interchangeable and are
   not. Writing 2m data into a 70cm radio puts out-of-band frequencies in front
   of the PA.
2. The image must be exactly the driver's `_memsize`.
3. `check_checksums()` must pass.
4. `--yes` must be passed explicitly.

Usage:
    # dry run: validate the image, write nothing
    python3 ft27x-write.py --img dumps/x.img --driver Yaesu_VX-177

    # actually write
    python3 ft27x-write.py --port /dev/cu.usbserial-XXXX \\
        --img dumps/x.img --driver Yaesu_VX-177 --yes

Radio side (do this BEFORE arming the host, opposite of a read):
    1. Radio off.
    2. Cable to MIC/SP jack.
    3. Hold [MONI] while turning on.
    4. Select CLONE, press F. Radio shows "CLONE".
    5. Press [MONI] -- "-RX-" appears. The radio is now waiting to receive.
    6. THEN run this with --yes.
"""

import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--img", required=True, help="clone image to write")
    ap.add_argument("--driver", default="Yaesu_VX-170",
                    help="CHIRP driver key (Yaesu_VX-170 = FT-270R / 2m, "
                         "Yaesu_VX-177 = FT-277R / 70cm)")
    ap.add_argument("--port", default=None, help="serial device")
    ap.add_argument("--yes", action="store_true",
                    help="actually write. Without this it is a dry run.")
    args = ap.parse_args()

    try:
        import serial
        from chirp import directory, errors  # noqa: F401
    except ImportError as e:
        sys.exit("error: CHIRP not importable (%s); use the CHIRP venv python" % e)

    import gettext
    gettext.install("chirp")
    directory.import_drivers()

    if args.driver not in directory.DRV_TO_RADIO:
        sys.exit("error: unknown driver %r" % args.driver)
    cls = directory.DRV_TO_RADIO[args.driver]
    expect = getattr(cls, "_model", None)

    if not os.path.exists(args.img):
        sys.exit("error: no such image: %s" % args.img)
    raw = open(args.img, "rb").read()

    print("image:  %s" % args.img)
    print("driver: %s %s (_model=%r, _memsize=%s)"
          % (cls.VENDOR, cls.MODEL, expect, getattr(cls, "_memsize", "?")))
    print()

    # --- interlock 2: size ---
    memsize = getattr(cls, "_memsize", None)
    if memsize and len(raw) != memsize:
        sys.exit("REFUSING: image is %d bytes, driver expects %d."
                 % (len(raw), memsize))
    print("[ok] size %d == _memsize" % len(raw))

    # --- interlock 1: model ID (the cross-band guard) ---
    found = raw[:6].decode("ascii", "replace")
    if expect and found != expect:
        print("\n" + "!" * 66)
        print("REFUSING TO WRITE: model ID mismatch.")
        print("  image says:   %r" % found)
        print("  driver wants: %r" % expect)
        print()
        print("This is the cross-band guard. FT-270R (AH022$, 2m) and FT-277R")
        print("(AH022U, 70cm) images are the same size and differ by one byte.")
        print("Writing the wrong one puts out-of-band frequencies on the PA.")
        print("Pick the matching --driver, or use the matching image.")
        print("!" * 66)
        sys.exit(2)
    print("[ok] model %r == driver _model" % found)

    # --- interlock 3: checksums ---
    radio = cls(args.img)
    try:
        radio.check_checksums()
    except Exception as e:  # noqa: BLE001
        sys.exit("REFUSING: checksum validation failed: %s" % e)
    print("[ok] checksums valid")

    rf = radio.get_features()
    occupied = 0
    lo, hi = rf.memory_bounds
    for i in range(lo, hi + 1):
        if not radio.get_memory(i).empty:
            occupied += 1
    print("[ok] decodes: %d/%d channels occupied, bands %s"
          % (occupied, hi, rf.valid_bands))

    if not args.yes:
        print("\nDRY RUN — all interlocks passed. Nothing written.")
        print("Re-run with --port <dev> --yes to write.")
        return

    if not args.port:
        sys.exit("error: --yes requires --port")

    print("\n" + "=" * 66)
    print("WRITING to %s. Radio must already show '-RX-'." % args.port)
    print("=" * 66, flush=True)

    ser = serial.Serial(port=args.port, baudrate=cls.BAUD_RATE, timeout=3)
    radio.set_pipe(ser)
    try:
        radio.sync_out()
        print("\nWRITE COMPLETE.")
        print("Now re-read the radio and diff against this image to confirm.")
    except Exception as e:  # noqa: BLE001
        print("\nWRITE FAILED: %s: %s" % (type(e).__name__, e))
        print("The radio may be mid-clone; power-cycle it before retrying.")
        sys.exit(1)
    finally:
        try:
            ser.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
