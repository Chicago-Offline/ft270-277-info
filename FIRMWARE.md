# FIRMWARE.md — FT-270R / FT-277R

## Status: unknown

Nothing verified yet. These are ~2007-era Yaesu handhelds; there is **no known
user-flashable firmware path** and no public firmware images. Assume the MCU
firmware is factory-only unless proven otherwise.

## TODO

- [ ] Firmware/version string — is there a display combo that shows it?
      (Typical Yaesu HT pattern: hold a key or key pair during power-on.)
- [ ] Service / alignment menu entry sequence, per model
- [ ] Hard reset procedure (restore factory defaults)
- [ ] Soft reset / microprocessor reset, if distinct from hard reset
- [ ] Extended TX (MARS/CAP) modification — jumper, solder, or key sequence?
      Record it per model; VHF and UHF versions are usually different.
      **Both bench radios arrived already modded** (owner-reported 2026-09-13),
      so the procedure cannot be recovered by inspection here. What the mod
      *does* is partly observed: the FT-277R stored and accepted a 462.5500 MHz
      channel through the normal clone path. The actual transmit span has **not**
      been measured on either radio — do not assume it matches the CHIRP
      driver's `valid_bands` (137–174 / 420–470 MHz), which is only the upper
      bound the programming path will accept.
- [ ] Whether any authorized-dealer firmware update ever existed

## Rules

- Do not record an unlock or extended-TX procedure here from a single forum
  post. Two independent sources, or a confirmed bench result, or it stays a TODO.
- If a procedure is destructive or irreversible, say so on the same line as the
  procedure, not in a footnote.
- Alignment / service mode is **RF calibration**. Photograph or record every
  screen before changing anything, and never load another radio's values.
