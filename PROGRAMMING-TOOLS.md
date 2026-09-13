# PROGRAMMING-TOOLS.md — FT-270R / FT-277R

## Summary

**There is no OEM CPS for these radios.** Yaesu never shipped first-party
programming software for the FT-270R or FT-277R — unlike the Chinese radios in
our other `-info` repos, there is no vendor CPS to hunt down, no CPS password,
and no vendor `.dat` format to reverse. `ADMS-270` / `ADMS-277` are **RT Systems
third-party products**, not Yaesu software; the ADMS name is licensed branding.

That leaves two real paths, and on macOS it leaves exactly one.

| Path | Platform | Cost | Status |
|---|---|---|---|
| RT Systems `ADMS-270` / `ADMS-277` | Windows only | paid | Third-party, not OEM |
| CHIRP, VX-170 / VX-177 driver | macOS / Linux / Win | free | ⚠️ Model-ID check, see below |
| Radio-to-radio clone | n/a | free | Built-in, manual procedure |
| Front panel | n/a | free | 200 channels by hand. Don't. |

**On macOS, CHIRP is the path.** RT Systems ships no macOS build, so the
model-ID question below is the whole ballgame, not an academic curiosity.

## RT Systems (third-party, not OEM)

- `ADMS-270` — FT-270R. `ADMS-277` — FT-277R.
- Sold as software + cable kits. The cable is the interesting part: it plugs
  into the 4-pin waterproof mic jack.
- ⚠️ UNVERIFIED: exact cable part numbers (`USB-55` and `USB-57` are the
  candidates in the Yaesu 4-pin ecosystem — confirm before buying).
- Windows only. No macOS build. Works under Parallels/VMware with USB passthrough
  in principle — ⚠️ UNVERIFIED for this radio.

## CHIRP

CHIRP has **no `ft270` driver.** Confirmed against `kk7ds/chirp` `master`:
`chirp/drivers/` contains no FT-270/FT-277 module.

The relevant drivers are `chirp/drivers/vx170.py`:

```python
class VX170Radio(ft7800.FTx800Radio):
    MODEL = "VX-170"
    _model = "AH022$"

class VX177Radio(VX170Radio):
    MODEL = 'VX-177'
    _model = 'AH022U'
```

Two things to notice:

1. **The VX-170/VX-177 pair maps exactly onto FT-270R/FT-277R** — VHF and UHF
   siblings of the same submersible chassis. The FT-27x is widely believed to be
   the same hardware with amateur-market branding.
2. **The driver hard-checks a model ID** (`AH022$` / `AH022U`) against the clone
   image and raises `Invalid model` on mismatch.

### ✅ ANSWERED 2026-09-13 — an FT-270R reports `AH022$`

**Bench-verified on a real FT-270R. Stock CHIRP programs this radio today with
no patch, selected as `Yaesu VX-170`.**

```
$ head -c 8 dumps/ft270r-2026-09-13-read.img | xxd
00000000: 4148 3032 3224 0001                      AH022$..
```

Full verification against `Yaesu_VX-170`:

| Check | Result |
|---|---|
| Image size | 6057 bytes = driver `_memsize` exactly |
| `model[6]` field | `AH022$` — matches `_model` |
| `check_checksums()` | OK |
| `get_features().memory_bounds` | `(1, 200)` |
| Channel decode | clean (ch 1 = 144.0000) |
| SHA-256 | `afc865b2a60d9369c9cf927cc732f7c8b860e1ede34d7f6c5beb26baed1a8437` |

So the FT-270R is a rebadged VX-170 as far as the clone protocol and memory
layout are concerned. No CHIRP patch, no fork, no upstream PR needed. By
symmetry the FT-277R is expected to report `AH022U` (`Yaesu_VX-177`) — ⚠️ still
UNVERIFIED, no FT-277R on the bench yet.

### 🔴 Clone baud is 9600 — don't go chasing baud rates

The first read attempt failed with `Failed to read header (2)` and the radio
displayed `ERROR`. That looks like a baud mismatch and **is not**. Two real
causes, both operator-side:

1. The radio only transmits for a moment after PTT. If the host is not already
   listening at that instant, it catches a fragment or nothing.
2. When the driver gives up mid-header it never sends the ACK the radio is
   waiting for, so the radio itself shows `ERROR`. The radio is reporting *our*
   failure, not its own.

A baud sweep during PTT presses produced non-ASCII garbage at 4800/38400/57600
(saved in `dumps/sniff-*.bin`) purely because those were the wrong rate — at
9600 the very first successful capture began with clean `AH022$`. **9600, the
driver's own value, was correct from the start.**

Also worth knowing: the CT57B cable does **not** echo TX back to RX (verified by
writing a probe pattern and reading nothing back). So `0x06` bytes appearing in
a capture are genuinely from the radio and not your own ACKs reflected.

### Capturing an image

`scripts/ft27x-probe.py` performs a read-only capture: it runs `sync_in()`, lets
the model check fail if it's going to, scans for an `AHnnnX`-style ID, and saves
to `dumps/`.

`scripts/ft27x-sniff.py` is the fallback when a driver read fails and you need
ground truth — no driver, optional baud sweep, hexdumps whatever arrives.

**Arm the host first, then press PTT.** Not the other way around.

`scripts/ft27x-probe.py` does exactly this. It is read-only: it runs `sync_in()`,
lets the model check fail if it's going to, then scans the captured bytes for an
`AHnnnX`-style ID and saves the image to `dumps/`.

### Verified working cable

**RT Systems `CT57B Radio Cable`** — USB-A, enumerates on macOS 26 with **no
driver install**:

```
/dev/cu.usbserial-RTWBKOPI
vid=0x2100 pid=0x9e52  "CT57B Radio Cable" / "RT Systems"
```

The `/dev/cu.usbserial-<SERIAL>` node is named from the cable's USB serial
number, so the path differs per cable. Discover it, don't hardcode it.

### Bench setup (macOS, verified 2026-09-13)

CHIRP's own `chirpc` wrapper produced no output at all on this machine (exit 0,
zero bytes, even for `--help`) — unresolved. The library imports fine, so the
probe script uses the library directly and sidesteps it.

PyPI `chirp` is an **unrelated package** (it fails to build on `vitterbi.pyf`).
Install from source, without wxPython:

```bash
git clone --depth 1 https://github.com/kk7ds/chirp.git ~/src/chirp-src
cd ~/src/chirp-src
uv venv .venv
uv pip install --python .venv/bin/python pyserial requests suds yattag lark
uv pip install --python .venv/bin/python --no-deps -e .
```

Confirmed working: 556 drivers load, including `Yaesu_VX-170` (`AH022$`) and
`Yaesu_VX-177` (`AH022U`).

```bash
cd ~/src/ft270-277-info
~/src/chirp-src/.venv/bin/python scripts/ft27x-probe.py \
    --port /dev/cu.usbserial-RTWBKOPI --read-timeout 6 \
    --out dumps/ft270r-$(date +%F)-read.img
# 70cm:  ... --driver Yaesu_VX-177
```

`--read-timeout` sets the per-read serial timeout; the driver retries the header
30x, so the usable PTT window is roughly `30 x` that value. `6` gives a
comfortable ~90 s. With a bad or missing port the script lists the serial
devices that *do* exist — fastest way to tell a cable problem from a software
problem.

### Radio-side clone-out procedure (verified)

From the driver's own `pre_download` prompt, confirmed working:

1. Turn the radio **off**.
2. Connect the cable to the **MIC/SP** jack.
3. Hold **[MONI]** while turning the radio **on**.
4. Select **CLONE** in the menu, press **F**. Radio restarts in clone mode and
   shows `CLONE`.
5. Arm the host, *then* briefly hold **[PTT]**. `-TX-` appears and the image
   sends.

Press PTT **once** per attempt. A second burst mid-transfer corrupts the stream.

### Driver lineage

`VX170Radio` inherits `ft7800.FTx800Radio`, so the clone format is the
FT-7800/FT-8800 family. That gives a starting point for the memory map rather
than reversing from zero.

## Radio-to-radio cloning

Built into the radio, no computer needed. ⚠️ UNVERIFIED key combo and cable
type — pull the exact procedure from the operating manual and record it here.

## Cable troubleshooting

These radios have **no USB port**. The USB is on the computer end of a cable
whose radio end is the 4-pin waterproof mic jack. So "plugged in via USB" means
the *cable's* USB-serial chip must enumerate first — the radio is not involved
and does not need to be powered for that to happen.

```bash
ls /dev/cu.*                                        # expect a cu.usbserial-* / cu.SLAB_* / cu.usbmodem*
ioreg -p IOUSB -l -w0 | grep '"USB Product Name"'   # what actually enumerated
log show --last 5m --predicate 'subsystem == "com.apple.iokit.IOUSBHostFamily"' --style compact | tail -20
```

If `ioreg` shows only Apple hubs, the USB link is not up at all. That is
physical — dead cable, charge-only cable, unpowered hub, or a port that isn't
seated. No driver install fixes it, because a missing driver still enumerates
the device and merely fails to bind a `/dev/cu.*` node.

### Telling a blocked accessory from a dead link

macOS can *block* an accessory ("Allow accessory to connect" → denied, and the
denial is remembered). That looks superficially similar but is **not** the same
failure, and the log distinguishes them:

- **Blocked accessory** → the port still sees the electrical attach, so
  `IOUSBHostFamily` logs port/connect events, plus an authorization denial.
  Fix: System Settings → Privacy & Security → *Allow accessories to connect*.
- **Dead link** → **no `IOUSBHostFamily` events at all.** The host controller
  never saw a device. Nothing in software will help.

```bash
/usr/bin/log show --start "YYYY-MM-DD HH:MM:SS" \
  --predicate 'subsystem == "com.apple.iokit.IOUSBHostFamily"' --style compact
```

Use the **absolute path** `/usr/bin/log` — a shell alias or function named `log`
will shadow it and fail with `too many arguments`, which prints nothing and
looks exactly like "no events found." That false negative is easy to act on by
mistake.

### RT Systems cables are USB-A

RT Systems programming cables terminate in **USB-A**. Current Apple desktops and
laptops are USB-C only, so an adapter or hub is always in the path — and that
adapter is now the most likely failure point. Charge-only adapters and
unpowered/undetected hubs both produce a completely silent bus. Prefer a direct
USB-A port, or a known-good powered data hub, before debugging anything else.

## Safety rails

- **Back up before you write.** Read the radio, save the image to `dumps/`,
  confirm the file is non-trivial in size, *then* write.
- **Never write a VX-170 image to an FT-277R or vice versa.** VHF and UHF band
  data in a 70 cm radio is at best useless and at worst puts the PA somewhere it
  shouldn't be.
- Re-read after every write and diff against what you intended. Progress bars
  lie; a completed write is not a verified write.
- Extended-TX / MARS-CAP mods are a separate question from programming. Don't
  mix the two in one session.
