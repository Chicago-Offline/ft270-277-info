# PROGRAMMING-TOOLS.md — FT-270R / FT-277R

## Summary

There is **no official Yaesu programming software** for these radios. The
practical options are RT Systems (paid, Windows) or CHIRP via the VX-170 family
driver (free, cross-platform, with a caveat).

| Path | Platform | Cost | Status |
|---|---|---|---|
| RT Systems `ADMS-270` / `ADMS-277` | Windows | paid | Vendor-supported |
| CHIRP, VX-170 / VX-177 driver | macOS / Linux / Win | free | ⚠️ Model-ID check, see below |
| Radio-to-radio clone | n/a | free | Built-in, manual procedure |
| Front panel | n/a | free | 200 channels by hand. Don't. |

## RT Systems

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
   image and raises `Invalid model` on mismatch. If the FT-270R reports a
   different ID, a stock CHIRP will refuse the image even if the format is
   otherwise identical.

### The open question

Does an FT-270R report `AH022$`? Two possible outcomes:

- **It matches** → CHIRP works today with the radio set to VX-170. Document it,
  done.
- **It doesn't** → the fix is a subclass with the real `_model` string, which is
  a small, upstreamable CHIRP patch.

**To answer it:** put the radio in clone-out mode, capture the image, and read
the model field. Save the capture to `dumps/`. Do not skip straight to patching
out the check — the check is what stops you writing a VX-170 image into
something that isn't one.

### Driver lineage

`VX170Radio` inherits `ft7800.FTx800Radio`, so the clone format is the
FT-7800/FT-8800 family. That gives a starting point for the memory map rather
than reversing from zero.

## Radio-to-radio cloning

Built into the radio, no computer needed. ⚠️ UNVERIFIED key combo and cable
type — pull the exact procedure from the operating manual and record it here.

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
