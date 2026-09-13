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
| `dumps/` | Clone-mode captures and memory images |
| `cps/` | Vendor/RT Systems software artifacts (no redistribution of licensed binaries) |

## ✅ Programming: solved for the FT-270R

**There is no OEM CPS for these radios**, and RT Systems is Windows-only — but
**stock CHIRP programs the FT-270R today with no patch.** Select `Yaesu VX-170`.

Bench-verified 2026-09-13 against a real FT-270R: the clone image is 6057 bytes,
checksums validate, 200 channels decode, and the `model[6]` field reads `AH022$`
— byte-identical to what `chirp/drivers/vx170.py` expects. The FT-270R is a
rebadged VX-170 at the protocol level.

Cable: **RT Systems `CT57B`**, no driver install needed on macOS 26.
Clone baud is **9600**. Full procedure and pitfalls: `PROGRAMMING-TOOLS.md`.

## Status

Programming path solved; hardware specs still thin. Most `SPECS.md` rows are
vendor marketing copy, not bench measurements.

**Rule for this repo:** anything not verified against a manual, a live radio, or
source code gets tagged `⚠️ UNVERIFIED`. Don't launder a forum post into a fact.

## Open questions

- [x] ~~Does the CHIRP VX-170/VX-177 driver read these without patching?~~
      **Yes for FT-270R** — reports `AH022$`, verified 2026-09-13.
- [x] ~~Clone-mode protocol and image size~~ — `ft7800`-family, 6057 bytes
      (8-byte header + 6048 data + 1), 32-byte blocks, 9600 baud.
- [ ] Does an FT-277R report `AH022U` (i.e. `Yaesu_VX-177`)? Expected by
      symmetry, **unverified** — no FT-277R on the bench.
- [ ] Verify a *write* back to the radio, not just a read
- [ ] Exact memory map for channel entries beyond what `vx170.py` models
- [ ] MARS/CAP / extended-TX mod procedure for each model
- [ ] Firmware version string location and known revisions
