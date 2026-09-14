# ft270-277-info

Reference and reverse-engineering notes for the **Yaesu FT-270R** (2 m) and
**FT-277R** (70 cm) submersible FM handhelds.

Same radio, two bands. Everything except the RF deck and band limits is shared:
chassis, 16-key layout, menu tree, clone protocol, accessories.

| | FT-270R | FT-277R |
|---|---|---|
| Band | 2 m VHF | 70 cm UHF |
| TX (US ham) | 144–148 MHz | 430–450 MHz |
| RF out | 5 W max | 5 W max |
| Memories | 200 | 200 |
| Water rating | IPX7 | IPX7 |
| Audio out | 800 mW | 800 mW |
| Status | Legacy / discontinued | Legacy / discontinued |

## ⚠️ Model-number collision — read this first

Yaesu **reused `FT-270R`**. There are two unrelated radios with that exact name:

- **FT-270R (HT, ~2007)** — the 5 W 2 m submersible handheld this repo documents.
- **FT-270R / FT-270RH (mobile, 1980s)** — a 25 W / 3 W 2 m mobile, 144–146 MHz,
  13.8 VDC. Completely different radio, different manual, different everything.

Manual sites, parts listings, and rig databases mix these up constantly. If a
spec sheet mentions 25 W or 13.8 VDC, you are looking at the mobile, not the HT.

`FT-277R` has a similar hazard — the number was used on much older gear too.
Assume "FT-277R" means the modern 70 cm HT only when the context is a 5 W IPX7
handheld.

## Repo map

| File | Contents |
|---|---|
| `SPECS.md` | Hardware specs, band limits, accessories, known-good vs TODO |
| `PROGRAMMING-TOOLS.md` | ADMS-270/277, cloning, cable, CHIRP status |
| `FIRMWARE.md` | Version strings, service menus, alignment notes |
| `REFERENCES.md` | Manuals, product pages, community threads |
| `scripts/` | Headless probe / build / write / sniff tools |
| `dumps/` | Clone-mode captures and memory images |
| `cps/` | Vendor/RT Systems software artifacts (no redistribution of licensed binaries) |

## ✅ Programming: solved for both radios

**There is no OEM CPS for these radios**, and RT Systems is Windows-only — but
**stock CHIRP programs both today with no patch:**

| Radio | Select in CHIRP | Model ID | Verified |
|---|---|---|---|
| FT-270R | `Yaesu VX-170` | `AH022$` | ✅ 2026-09-13 |
| FT-277R | `Yaesu VX-177` | `AH022U` | ✅ 2026-09-13 |

Bench-verified against both physical radios: 6057-byte clone images, checksums
validate, 200 channels decode, model IDs byte-identical to what
`chirp/drivers/vx170.py` expects. Both are rebadged VX-17x radios at the
protocol level.

⚠️ **Match driver to band.** The two images are the same size and differ by one
byte in the model ID — they look interchangeable and are not. CHIRP's model
check is what prevents a cross-band write.

Cable: **RT Systems `CT57B`**, no driver install needed on macOS 26.
Clone baud is **9600**.

### Headless end-to-end write — verified on both radios

**2026-09-13: both radios were programmed from a codeplug source with no GUI,
and each read back byte-identical to the image sent.** `CHIRP.app`'s GUI upload
also works and remains a fine option; it is no longer the only one.

```bash
PY=~/src/chirp/.venv/bin/python
PORT=/dev/cu.usbserial-RTWBKOPI
DRV=Yaesu_VX-177                      # Yaesu_VX-170 for the FT-270R
BAK=~/src/codeplug-backups/ft277_eam_20260913   # NOT dumps/ — see below

$PY scripts/ft27x-probe.py      --port $PORT --driver $DRV \
      --read-timeout 6 --out $BAK/before.img        # 1. back up, always
$PY scripts/ft27x-csv-to-img.py --base $BAK/before.img --csv codeplug.csv \
      --driver $DRV --out new.img                   # 2. CSV + base -> image
$PY scripts/ft27x-write.py      --img new.img --driver $DRV
$PY scripts/ft27x-write.py      --img new.img --driver $DRV --port $PORT --yes
$PY scripts/ft27x-probe.py      --port $PORT --driver $DRV \
      --read-timeout 6 --out $BAK/after.img         # 3. verify
cmp new.img $BAK/after.img                          # must be silent
```

| | FT-270R | FT-277R |
|---|---|---|
| Channels written | 24 | 31 |
| Read-back SHA-256 | `f290bff3bf7c…b94aaf9c` | `8a94fba316ad…8457c3be` |
| `cmp` vs sent image | identical | identical |

CSVs came from `codeplugger`’s `--output-format chirp-csv`
(`muehlstein-codeplugger-profiles`, radio ids `yaesu_ft270_mars` /
`yaesu_ft277_mars`), but any CHIRP-format CSV works.

⚠️ **Keep real codeplugs out of this repo.** It is public, and a programmed
radio's image carries the owner's actual channel plan — private frequencies,
tone and DCS codes — which CHIRP decodes in seconds. Session backups belong in a
private store; `dumps/` holds only near-factory reference captures. See
[`dumps/README.md`](dumps/README.md).

⚠️ **Clone direction reverses the operator order.** This is the single easiest
thing to get wrong, and it cost one failed read on 2026-09-13:

- **Read** — radio shows `CLONE`, **arm the host first**, *then* press PTT once.
- **Write** — radio shows `CLONE` → `[MONI]` → `-RX-`, *then* run the host.

⚠️ **Match driver to band.** The two clone images are the same size and differ by
one byte in the model ID — they look interchangeable and are not. CHIRP's model
check is what prevents a cross-band write, and `ft27x-write.py` re-checks it
independently before sending a byte (bench-tested: it refuses).

## Status

Programming solved for both models, read and write, GUI and headless. Hardware
specs still thin — most `SPECS.md` rows are vendor marketing copy, not bench
measurements.

**Rule for this repo:** anything not verified against a manual, a live radio, or
source code gets tagged `⚠️ UNVERIFIED`. Don't launder a forum post into a fact.

## Open questions

- [x] ~~Does the CHIRP VX-170/VX-177 driver read these without patching?~~
      **Yes for FT-270R** — reports `AH022$`, verified 2026-09-13.
- [x] ~~Clone-mode protocol and image size~~ — `ft7800`-family, 6057 bytes
      (8-byte header + 6048 data + 1), 32-byte blocks, 9600 baud.
- [x] ~~Does an FT-277R report `AH022U` (i.e. `Yaesu_VX-177`)?~~ **Yes** —
      verified 2026-09-13.
- [x] ~~Verify a *write* back to a radio, not just a read~~ **Yes** — CHIRP.app
      GUI upload confirmed on a physical FT-277R, 2026-09-13.
- [x] ~~Headless write, end to end, verified by read-back~~ **Yes** — both
      radios, 2026-09-13, `cmp`-identical. See "Headless end-to-end write".
- [x] ~~`codeplugger` support for FT-270R/FT-277R export~~ **Yes** — radio ids
      `yaesu_ft270` / `yaesu_ft277` plus MARS variants; `scripts/ft27x-csv-to-img.py`
      bridges its CHIRP CSV to a clone image. HA2 export is still open.
- [ ] Fix `scripts/ft27x-read.py` for reliable headless full-image
      verification. Not a blocker any more — `ft27x-probe.py` does a correct
      full read and is what the verified pipeline uses — but the two scripts
      should be reconciled or one retired.
- [ ] Exact memory map for channel entries beyond what `vx170.py` models
- [ ] MARS/CAP / extended-TX mod procedure for each model. Both bench radios
      arrived already modded, so the procedure is unknown and the post-mod
      transmit span is unmeasured — see `FIRMWARE.md`.
- [ ] Firmware version string location and known revisions
