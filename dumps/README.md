# dumps/

Clone-mode captures and memory images from FT-270R / FT-277R radios.

All images are exactly **6057 bytes** — a raw clone image, not a CHIRP `.img`
with metadata appended. Anything else is not writable by `ft27x-write.py`.

## ⚠️ What does NOT belong in this directory

**This repo is public.** A programmed radio's clone image carries the owner's
real channel plan — private simplex frequencies, tone and DCS codes, repeater
pairs. Committing one publishes all of it in a form CHIRP decodes in seconds.

So only **near-factory reference captures** live here. Before/after images from
an actual programming session go to the local, untracked codeplug backup store
(`~/src/codeplug-backups/<radio>_<YYYYMMDD>/{before,after}.img`), which is where
the rest of the fleet's backups already live. `.gitignore` blocks the obvious
filename patterns, but the rule is the point, not the pattern.

## Naming

`<model>-<YYYY-MM-DD>-read.img`, with a nickname or serial inserted before the
date once more than one radio of a model is in play
(`ft270r-green-2026-09-13-read.img`).

Add a sibling `.md` with the same basename recording the tool, driver, cable and
SHA-256.

## Inventory

| Image | Radio | Driver | Notes |
|---|---|---|---|
| `ft270r-2026-09-13-read.img` | FT-270R | `Yaesu_VX-170` | First bench read. Near-factory, 1/200 channels (144.0000). Baseline for diffing. |
| `ft277r-2026-09-13-read.img` | FT-277R | `Yaesu_VX-177` | First bench read. Near-factory, 2/200 channels. Baseline for diffing. |

## Programming sessions

Always capture a `before.img` prior to the first write to a given radio, and keep
it — it is the restore point. Capture an `after.img` immediately following, and
`cmp` it against the image you sent. **That equality is the write verification;
a completed progress bar is not.**

Both radios were programmed and verified this way on 2026-09-13 (FT-270R 24
channels, FT-277R 31 channels, both `cmp`-identical to the image sent). Those
four images are in the backup store, not here, per the rule above.

To roll a radio back:

```bash
~/src/chirp/.venv/bin/python scripts/ft27x-write.py \
    --img ~/src/codeplug-backups/ft270_eam_20260913/before.img \
    --driver Yaesu_VX-170 --port /dev/cu.usbserial-RTWBKOPI --yes
```

## Sniff captures

`sniff-*.bin` are raw baud-sweep captures kept as evidence of what a wrong baud
rate looks like. Only the 9600 ones contain real data; see
`ft270r-2026-09-13-read.md`.
