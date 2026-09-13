#!/usr/bin/env python3
"""
ft27x-read.py — robust read-only clone capture for FT-270R / FT-277R.

Why this exists instead of just calling CHIRP's sync_in(): CHIRP's
ft7800._download() reads the 8-byte header like this:

    for i in range(30):
        chunk += pipe.read(8)
        if chunk:
            break   # <-- bug for us: breaks on ANY non-empty read, even 1 byte

If even one stray byte arrives before the real header (an aborted previous
attempt still draining out of the USB-serial chip, a keying transient, PTT
bounce), the loop stops retrying immediately and fails with
"Failed to read header (N)" -- even though the real 8-byte header is sitting
right behind it, still in transit. Confirmed on the bench: a raw sniff during
one such failure showed 17 junk bytes followed by a perfectly clean model
header a few bytes later.

This script:
  1. Waits for the line to go genuinely idle (no bytes for --quiet-for
     seconds) before arming, so leftovers from a prior aborted attempt drain
     out first.
  2. Reads the header by *accumulating* until it has the full 8 bytes (or an
     overall timeout), instead of stopping at the first non-empty read.
  3. Runs the rest of the ft7800 clone protocol (32-byte blocks, ACK each)
     the same way CHIRP does.
  4. Hands the result to CHIRP's own radio class for checksum + memory
     validation, so the pass/fail verdict is identical to what CHIRP would
     give -- this file only fixes the header race, not the protocol.

Read-only. Never writes anything but ACK (0x06), which is flow control for a
radio-initiated send.

Usage:
    python3 ft27x-read.py --port /dev/cu.usbserial-XXXX --driver Yaesu_VX-177
"""

import argparse
import datetime
import os
import re
import sys
import time

ACK = b"\x06"


def wait_for_idle(ser, quiet_for, max_wait):
    """Drain and wait until the line has been silent for quiet_for seconds."""
    print("waiting for a quiet line (up to %.0fs)..." % max_wait, flush=True)
    deadline = time.time() + max_wait
    quiet_since = None
    drained = 0
    while time.time() < deadline:
        chunk = ser.read(256)
        if chunk:
            drained += len(chunk)
            quiet_since = None
        else:
            if quiet_since is None:
                quiet_since = time.time()
            elif time.time() - quiet_since >= quiet_for:
                if drained:
                    print("  drained %d stale byte(s) before going quiet" % drained)
                print("  line quiet for %.1fs, arming" % quiet_for, flush=True)
                return
    print("  gave up waiting for quiet (drained %d bytes); arming anyway" % drained)


MODEL_RE = re.compile(rb"[A-Z]{2}\d{3}[\x20-\x7e]")


def read_header(ser, length, overall_timeout, resync_scan=32):
    """Accumulate `length` header bytes, byte-aligned to the real model ID.

    The line coming out of idle can carry a few junk/misaligned bytes before
    the UART settles -- confirmed on the bench (3 stray bytes ahead of
    'AH022U' on one capture). Taking the first `length` bytes verbatim in
    that case desyncs the whole rest of the transfer. Instead: read a bit
    more than one header's worth, find the model-ID pattern inside it, and
    treat everything before that as noise to discard.
    """
    deadline = time.time() + overall_timeout
    data = b""
    want = length + resync_scan
    while len(data) < want and time.time() < deadline:
        chunk = ser.read(want - len(data))
        if chunk:
            data += chunk
        elif len(data) >= length:
            # Nothing more arriving and we already have at least a full
            # header's worth -- stop waiting for the extra resync margin.
            break

    if not data:
        return b""

    m = MODEL_RE.search(data)
    offset = m.start() if m else 0
    if offset:
        print("  resync: discarding %d leading junk byte(s): %s"
              % (offset, data[:offset].hex(" ")), flush=True)

    aligned = data[offset:]
    while len(aligned) < length and time.time() < deadline:
        chunk = ser.read(length - len(aligned))
        if chunk:
            aligned += chunk
    return aligned[:length]


def read_body(ser, total, block_size, status_every=512):
    """Read `total` bytes in `block_size` chunks, ACKing only FULL blocks.

    This mirrors CHIRP's ft7800._download exactly: one read(block_size) call
    per block, ACK only if that call returned a complete block, stop
    (without ACKing) on any short read. ACKing a partial block -- which an
    earlier version of this script did -- desyncs the radio's block counter
    and shifts every byte after it by however many were missing. Confirmed
    on the bench: that bug produced a 1-byte-shifted, checksum-failing image
    that was otherwise a perfect match.
    """
    data = b""
    last_report = 0
    while len(data) < total:
        remaining = total - len(data)
        chunk = ser.read(min(block_size, remaining))
        if not chunk:
            break
        data += chunk
        if len(chunk) != min(block_size, remaining):
            print("  short block: got %d/%d bytes at offset %d, stopping"
                  % (len(chunk), min(block_size, remaining), len(data) - len(chunk)),
                  flush=True)
            break
        time.sleep(0.01)
        ser.write(ACK)
        ser.flush()
        if len(data) - last_report >= status_every:
            print("  ... %d/%d bytes" % (len(data), total), flush=True)
            last_report = len(data)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--driver", default="Yaesu_VX-170",
                    help="Yaesu_VX-170 (FT-270R/2m) or Yaesu_VX-177 (FT-277R/70cm)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet-for", type=float, default=1.0,
                    help="seconds of silence required before arming (default 1.0)")
    ap.add_argument("--idle-wait", type=float, default=5.0,
                    help="max seconds to wait for a quiet line (default 5.0)")
    ap.add_argument("--overall-timeout", type=float, default=90.0,
                    help="max seconds to wait for the header once armed (default 90)")
    args = ap.parse_args()

    try:
        import serial
        import gettext
        gettext.install("chirp")
        from chirp import directory, memmap
    except ImportError as e:
        sys.exit("error: CHIRP not importable (%s); use the CHIRP venv python" % e)

    directory.import_drivers()
    if args.driver not in directory.DRV_TO_RADIO:
        sys.exit("error: unknown driver %r" % args.driver)
    cls = directory.DRV_TO_RADIO[args.driver]
    header_len, body_len, tail_len = cls._block_lengths
    block_size = cls._block_size

    print("driver: %s %s (_model=%r, header=%d body=%d block=%d)"
          % (cls.VENDOR, cls.MODEL, getattr(cls, "_model", None),
             header_len, body_len, block_size))

    try:
        ser = serial.Serial(port=args.port, baudrate=cls.BAUD_RATE, timeout=1.0)
    except serial.SerialException as e:
        sys.exit("error: could not open %s: %s" % (args.port, e))

    wait_for_idle(ser, args.quiet_for, args.idle_wait)

    print("listening for %d-byte header (overall timeout %.0fs)..."
          % (header_len, args.overall_timeout), flush=True)
    header = read_header(ser, header_len, args.overall_timeout)
    if len(header) != header_len:
        ser.close()
        sys.exit("no clean header: got %d/%d bytes: %s"
                 % (len(header), header_len, header.hex(" ")))
    print("header: %s -> %r" % (header.hex(" "), header.decode("ascii", "replace")))
    ser.write(ACK)
    ser.flush()

    print("reading body (%d bytes)..." % body_len, flush=True)
    body = read_body(ser, body_len, block_size)
    tail = ser.read(tail_len) if tail_len else b""
    ser.write(ACK)
    ser.flush()
    ser.close()

    raw = header + body + tail
    print("\ncaptured: %d bytes (want %d)" % (len(raw), header_len + body_len + tail_len))

    if len(raw) != header_len + body_len + tail_len:
        print("INCOMPLETE capture -- body read stalled. Saving partial for inspection.")

    out = args.out
    if not out:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d")
        out = os.path.join("dumps", "%s-%s-read.img" % (args.driver, stamp))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as f:
        f.write(raw)
    print("saved: %s" % out)

    if len(raw) != cls._memsize:
        sys.exit("Saved partial image; not validating against CHIRP (size mismatch).")

    radio = cls(memmap.MemoryMapBytes(raw))
    try:
        radio.check_checksums()
        print("checksums: OK")
    except Exception as e:  # noqa: BLE001
        sys.exit("checksum validation FAILED: %s" % e)

    rf = radio.get_features()
    lo, hi = rf.memory_bounds
    occ = sum(1 for i in range(lo, hi + 1) if not radio.get_memory(i).empty)
    print("decodes clean: %d/%d channels occupied, bands %s" % (occ, hi, rf.valid_bands))
    print("\nVerdict: valid %s clone image." % cls.MODEL)


if __name__ == "__main__":
    main()
