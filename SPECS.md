# SPECS.md — FT-270R / FT-277R

Confirmed items cite a source. Everything else is `⚠️ UNVERIFIED` until checked
against the operating manual or a radio on the bench.

## General

| Item | FT-270R | FT-277R | Source |
|---|---|---|---|
| Type | 2 m FM handheld | 70 cm FM handheld | Yaesu product pages |
| RF output (max) | 5 W | 5 W | Yaesu product page |
| Power steps | ⚠️ UNVERIFIED (likely 5 / 2 / 0.5 W) | ⚠️ UNVERIFIED | — |
| Modulation | FM (F3E) | FM (F3E) | — |
| Memory channels | 200 | 200 | eHam listing |
| Audio output | 800 mW | 800 mW | Yaesu product page |
| Water rating | IPX7 (30 min @ 3 ft) | IPX7 | Yaesu product page |
| Keypad | 16-key, backlit, DTMF | 16-key, backlit, DTMF | Yaesu product page |
| Display | Backlit LCD | Backlit LCD | Yaesu product page |

## Frequency coverage

⚠️ UNVERIFIED — fill from the operating manual, per market variant
(`R` = Americas, `E` = Europe, plus AU/Asia versions).

| | TX | RX | Notes |
|---|---|---|---|
| FT-270R | 144–148 MHz (US ham) | ~137–174 MHz wideband RX (⚠️ UNVERIFIED) | |
| FT-277R | 430–450 MHz (US ham) | ⚠️ UNVERIFIED | AU version reportedly receives UHF CB (80 ch, post-Apr 2011) — eHam review, ⚠️ UNVERIFIED |

## Features

- CTCSS / DCS encode + decode
- DTMF autodialer — ⚠️ UNVERIFIED memory count
- ARTS (Auto Range Transponder System) — ⚠️ UNVERIFIED
- WIRES-II one-touch internet key (Yaesu product page)
- Enhanced Paging and Code Squelch (EPCS) — eHam listing
- PMS (Programmable Memory Scan) pairs — ⚠️ UNVERIFIED count
- Home channels, memory banks — ⚠️ UNVERIFIED

## Physical

⚠️ UNVERIFIED — dimensions, weight, antenna connector.
Antenna is believed to be **SMA (female on radio)**; the `CN-3` SMA→BNC adapter
is listed as an accessory on the Yaesu product page, which is consistent but not
proof of gender.

## Power / battery

| Part | Description | Source |
|---|---|---|
| `FNB-83` | 1400 mAh Ni-MH battery pack (supplied) | Yaesu product page |
| `FBA-25A` | Alkaline battery tray | Yaesu product page |
| `CD-26` | Charging cradle | Yaesu product page |
| `SAD-24B` | AC charger (replaces PA-48B) | Yaesu product page |
| `SBH-13` | Desktop rapid charger, ~4 h; requires `SAD-25B` | Yaesu product page |
| `E-DC-6` | DC cable, plug + wire only | Yaesu product page |
| `SDD-13` | DC cable with cigarette-lighter plug | Yaesu product page |

## Audio accessories

| Part | Description | Source |
|---|---|---|
| `MH-73A4B` | Waterproof speaker microphone | Yaesu product page |
| `SSM-17H` | Compact speaker mic (replaces `MH-57A4B`) | Yaesu product page |
| `CT-91` | Microphone adapter | Yaesu product page |
| `CN-3` | SMA → BNC antenna adapter | Yaesu product page |

The mic/speaker jack is the **4-pin waterproof Yaesu/Vertex style** shared with
the VX-170 family — ⚠️ UNVERIFIED, but it is what the shared accessory list
implies and what the programming cable ecosystem assumes.

## Known-good vs assumed

Nothing in this file has been checked against a physical radio yet. The Yaesu
product-page rows are vendor marketing copy; treat dimension, current-drain, and
sensitivity figures as missing rather than guessing them.
