# World of Xeen completion certificate (A4, 2026-11-21; decider D-56)

World of Xeen has no certificate page of its own (its ending is the endgame movie; the extracted images hold no
certificate or score background), so this is a new painting in the originals' layout, a third of the MM6/MM7 family:
the gold knotwork border, "Might and Magic" at the top, a "WORLD OF XEEN" plaque at the bottom, and a faded sepia
picture of the joined flat world under one sun with the wedding of Roland and Kalindra on a balcony at the lower right
(subjects from the endgame frames `eg270001`, `eg280001`, `eg140001`). The rest follows
`level_generation/ui/certificates_20261031/README.md`.

- `scripts/make_guide.py`: `guide.png` (640 x 480 layout on the 1536 x 1024 canvas: title, text zone x 100-540,
  y 80-410 as MM6's, the mark at (320, 422), the plaque) and `refs/`.
- `BRIEF.md`, `scripts/run_codex.py`: one Codex worker, two candidates, raw returns in `raw/` (log kept).
- Chosen: `raw/xeen_cert_a.png` (the paler text zone: mean 226, std 8.6 against b's 220 and 13.2). Its middle
  1365 x 1024 resized to 1280 x 960 is `assets_dev/worlds/xeen/icons_x2/xeenwinbg.png`; `xeenwinbg_640.png` is the
  native-size view.
- `completion_block.yml`: the `completion` block for `worlds/xeen/world.yml` (the orchestrator adds it): qbit 111840
  (`m42.done`), art `xeenwinbg`, headline "Congratulations!", the ending text, layout as MM6's.
- Checked in game on a scratch root with the block (`output/xeen_a4/s12/cert/`, build-xeen 02:31): `qbit set 111840`
  shows the certificate with the text, party, time, score and the OpenYAMM mark in place
  (`output/xeen_a4/s12/cert/shots/01_xeen_certificate.png`).
