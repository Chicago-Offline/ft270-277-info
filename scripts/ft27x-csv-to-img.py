#!/usr/bin/env python3
"""
ft27x-csv-to-img.py — build an FT-270R / FT-277R clone image from a CHIRP CSV.

Fills the gap between a codeplug source (CSV) and `ft27x-write.py`, which only
speaks clone images. Everything happens offline; the radio is not touched.

The base image supplies everything the CSV does not describe: menu settings,
squelch, the model ID header. So the base should be a **fresh read of the radio
you are about to write**, not a stale dump from another session.

Usage:
    python3 ft27x-csv-to-img.py \\
        --base dumps/ft277r-2026-09-13-read.img \\
        --csv  codeplug.csv \\
        --driver Yaesu_VX-177 \\
        --out  dumps/ft277r-new.img

Interlocks, all of which must pass before an image is written:

1. The base image's model field must equal the driver's `_model`. Same
   cross-band guard as ft27x-write.py — a 2 m base with a 70 cm driver would
   silently produce an image that writes 2 m data to a 70 cm radio.
2. The base image must be exactly the driver's `_memsize` and pass
   `check_checksums()`.
3. Every CSV row must land inside the driver's `memory_bounds`, and every
   frequency inside its `valid_bands`.

Channels not named by the CSV are erased unless --keep-extra is passed, so the
resulting image is a faithful picture of the CSV and not a merge with whatever
happened to be on the radio.
"""

import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True,
                    help="baseline clone image to start from (ideally a fresh "
                         "read of the target radio)")
    ap.add_argument("--csv", required=True, help="CHIRP CSV to import")
    ap.add_argument("--driver", default="Yaesu_VX-170",
                    help="CHIRP driver key (Yaesu_VX-170 = FT-270R / 2m, "
                         "Yaesu_VX-177 = FT-277R / 70cm)")
    ap.add_argument("--out", required=True, help="image to write")
    ap.add_argument("--keep-extra", action="store_true",
                    help="leave channels the CSV does not mention alone "
                         "(default is to erase them)")
    args = ap.parse_args()

    try:
        from chirp import directory, import_logic
        from chirp.drivers import generic_csv
    except ImportError as e:
        sys.exit("error: CHIRP not importable (%s); use the CHIRP venv python" % e)

    import gettext
    gettext.install("chirp")
    directory.import_drivers()

    if args.driver not in directory.DRV_TO_RADIO:
        sys.exit("error: unknown driver %r" % args.driver)
    cls = directory.DRV_TO_RADIO[args.driver]
    expect = getattr(cls, "_model", None)

    for path in (args.base, args.csv):
        if not os.path.exists(path):
            sys.exit("error: no such file: %s" % path)

    raw = open(args.base, "rb").read()
    print("base:   %s (%d bytes)" % (args.base, len(raw)))
    print("csv:    %s" % args.csv)
    print("driver: %s %s (_model=%r, _memsize=%s)"
          % (cls.VENDOR, cls.MODEL, expect, cls._memsize))
    print()

    if len(raw) != cls._memsize:
        sys.exit("REFUSING: base is %d bytes, driver expects %d."
                 % (len(raw), cls._memsize))
    print("[ok] base size %d == _memsize" % len(raw))

    found = raw[:6].decode("ascii", "replace")
    if expect and found != expect:
        print("\n" + "!" * 66)
        print("REFUSING: base image model ID mismatch.")
        print("  base says:    %r" % found)
        print("  driver wants: %r" % expect)
        print("Cross-band guard — pick the matching --driver or base image.")
        print("!" * 66)
        sys.exit(2)
    print("[ok] base model %r == driver _model" % found)

    dst = cls(args.base)
    try:
        dst.check_checksums()
    except Exception as e:  # noqa: BLE001
        sys.exit("REFUSING: base checksum validation failed: %s" % e)
    print("[ok] base checksums valid")

    src = generic_csv.CSVRadio(args.csv)
    src_features = src.get_features()
    rf = dst.get_features()
    lo, hi = rf.memory_bounds

    rows = []
    for i in range(*src.get_features().memory_bounds):
        try:
            mem = src.get_memory(i)
        except Exception:  # noqa: BLE001
            continue
        if not mem.empty:
            rows.append(mem)
    if not rows:
        sys.exit("REFUSING: no non-empty channels in %s" % args.csv)

    for mem in rows:
        if not lo <= mem.number <= hi:
            sys.exit("REFUSING: CSV row %d is outside memory bounds %d-%d"
                     % (mem.number, lo, hi))
        if not any(b_lo <= mem.freq <= b_hi for b_lo, b_hi in rf.valid_bands):
            sys.exit("REFUSING: channel %d (%s) at %.4f MHz is outside %s"
                     % (mem.number, mem.name, mem.freq / 1e6, rf.valid_bands))
    print("[ok] %d CSV channels, all in bounds and in band" % len(rows))

    name_cap = rf.valid_name_length
    used = set()
    print()
    for mem in rows:
        converted = import_logic.import_mem(dst, src_features, mem)
        dst.set_memory(converted)
        used.add(mem.number)
        # The radio charset has no lowercase and no '.', so names can come back
        # altered rather than rejected.
        flag = "" if converted.name.strip() == mem.name.strip() else \
            "  <-- name changed from %r" % mem.name
        print("  %3d  %-*s %10.4f  %-1s%s"
              % (mem.number, name_cap, converted.name, mem.freq / 1e6,
                 mem.duplex, flag))

    erased = 0
    if not args.keep_extra:
        for i in range(lo, hi + 1):
            if i in used:
                continue
            if dst.get_memory(i).empty:
                continue
            dst.erase_memory(i)
            erased += 1
    print("\n[ok] %d channels set, %d erased" % (len(used), erased))

    dst.update_checksums()
    # Not dst.save(): CHIRP appends its own metadata blob, and ft27x-write.py
    # (rightly) refuses anything that is not exactly _memsize bytes.
    packed = dst._mmap.get_packed()
    if len(packed) != cls._memsize:
        sys.exit("REFUSING: built image is %d bytes, expected %d"
                 % (len(packed), cls._memsize))
    with open(args.out, "wb") as fh:
        fh.write(packed)

    verify = cls(args.out)
    verify.check_checksums()
    occupied = sum(0 if verify.get_memory(i).empty else 1
                   for i in range(lo, hi + 1))
    out_raw = open(args.out, "rb").read()
    print("[ok] wrote %s (%d bytes, model %r, %d/%d occupied, checksums valid)"
          % (args.out, len(out_raw),
             out_raw[:6].decode("ascii", "replace"), occupied, hi))
    print("\nNext: ft27x-write.py --img %s --driver %s   (dry run first)"
          % (args.out, args.driver))


if __name__ == "__main__":
    main()
