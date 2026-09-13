#!/usr/bin/env python3
"""
ft27x-sniff.py — dumb serial sniffer for FT-270R / FT-277R clone-out.

Use this when a CHIRP driver fails with a short/garbled header and you need
ground truth about what the radio is actually sending, and at what baud rate.

Makes no assumptions about the driver. Sweeps baud rates, and for each one
listens for clone-out traffic, ACKs the header the way the Yaesu clone protocol
expects, and reports exactly what arrived.

Read-only with respect to radio memory: it only ever sends ACK (0x06), which is
flow control for a radio-initiated send. It never initiates a write.

Usage:
    # sweep, pressing PTT repeatedly while it runs
    python3 ft27x-sniff.py --port /dev/cu.usbserial-XXXX

    # single baud, longer listen
    python3 ft27x-sniff.py --port /dev/cu.usbserial-XXXX --baud 9600 --dwell 30
"""

import argparse
import os
import sys
import time

ACK = b"\x06"


def hexdump(data, limit=64):
    out = []
    for i in range(0, min(len(data), limit), 16):
        chunk = data[i:i + 16]
        hexs = " ".join("%02x" % b for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append("  %04x  %-47s  |%s|" % (i, hexs, text))
    if len(data) > limit:
        out.append("  ... (%d more bytes)" % (len(data) - limit))
    return "\n".join(out)


def listen(port, baud, dwell, ack=True):
    """Listen at one baud rate. Returns captured bytes."""
    import serial
    ser = serial.Serial(port=port, baudrate=baud, timeout=0.2)
    try:
        ser.reset_input_buffer()
        data = b""
        acked = False
        deadline = time.time() + dwell
        last_rx = None
        while time.time() < deadline:
            chunk = ser.read(256)
            if chunk:
                data += chunk
                last_rx = time.time()
            elif data and last_rx and (time.time() - last_rx) > 0.4:
                # Sender paused. If this is a real clone header it is waiting
                # on our ACK before streaming the body.
                if ack and not acked:
                    ser.write(ACK)
                    ser.flush()
                    acked = True
                    last_rx = time.time()
                    deadline = max(deadline, time.time() + 5)
                elif ack and acked:
                    ser.write(ACK)
                    ser.flush()
                    last_rx = time.time()
        return data
    finally:
        ser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=None,
                    help="single baud rate; omit to sweep")
    ap.add_argument("--sweep", default="9600,19200,38400,4800,57600",
                    help="comma-separated baud rates to try in order")
    ap.add_argument("--dwell", type=float, default=12.0,
                    help="seconds to listen per baud rate (default 12)")
    ap.add_argument("--outdir", default="dumps")
    args = ap.parse_args()

    try:
        import serial  # noqa: F401
    except ImportError:
        sys.exit("error: pyserial not available; use the CHIRP venv python")

    bauds = [args.baud] if args.baud else [int(b) for b in args.sweep.split(",")]

    print("port:  %s" % args.port)
    print("bauds: %s" % ", ".join(str(b) for b in bauds))
    print("dwell: %.0fs each  (total ~%.0fs)" % (args.dwell, args.dwell * len(bauds)))
    print()
    print("Press PTT to send the clone image, and keep re-sending every few")
    print("seconds for the whole sweep. Each baud gets its own listen window.")
    print("=" * 66)

    os.makedirs(args.outdir, exist_ok=True)
    results = []

    for baud in bauds:
        print("\n[%s] listening at %d baud ..." % (time.strftime("%H:%M:%S"), baud),
              flush=True)
        try:
            data = listen(args.port, baud, args.dwell)
        except Exception as e:  # noqa: BLE001
            print("  error: %s" % e, flush=True)
            continue

        results.append((baud, data))
        if not data:
            print("  nothing received", flush=True)
            continue

        print("  received %d bytes" % len(data), flush=True)
        print(hexdump(data), flush=True)

        path = os.path.join(args.outdir, "sniff-%d-%s.bin"
                            % (baud, time.strftime("%Y%m%d-%H%M%S")))
        with open(path, "wb") as f:
            f.write(data)
        print("  saved %s" % path, flush=True)

        printable = sum(1 for b in data[:16] if 32 <= b < 127)
        if len(data) >= 6 and printable >= 4:
            print("  >>> looks like real ASCII header at this baud <<<", flush=True)
            print("  >>> first 6 bytes = %r <<<"
                  % data[:6].decode("ascii", "replace"), flush=True)

    print("\n" + "=" * 66)
    print("summary:")
    for baud, data in results:
        note = ""
        if data:
            note = " first6=%r" % data[:6].decode("ascii", "replace")
        print("  %6d baud: %5d bytes%s" % (baud, len(data), note))
    if not any(d for _, d in results):
        print("\nNothing at any baud. The radio never sent, or TX/RX is not")
        print("reaching the cable. Re-check that '-TX-' actually appeared.")


if __name__ == "__main__":
    main()
