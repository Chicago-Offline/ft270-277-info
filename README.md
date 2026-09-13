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

## Status

Early scaffold. Most sections are TODO and explicitly marked as such.

**Rule for this repo:** anything not verified against a manual, a live radio, or
source code gets tagged `⚠️ UNVERIFIED`. Don't launder a forum post into a fact.

## Open questions

- [ ] Does the CHIRP VX-170/VX-177 driver read/write these without patching?
      (Driver enforces a model-ID check — see `PROGRAMMING-TOOLS.md`.)
- [ ] Clone-mode protocol and image size — is it the `ft7800`-family format?
- [ ] Exact memory map for channel entries
- [ ] MARS/CAP / extended-TX mod procedure for each model
- [ ] Firmware version string location and known revisions
