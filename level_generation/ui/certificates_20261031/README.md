# Completion certificates

Certificates for finishing a world's story, requested 2026-10-31: one per continent, given the first time its story is
finished (a party that plays only MM6 receives Enroth's), and an OpenYAMM certificate once Enroth, Antagarich and
Jadame are all finished. Each is saved automatically as a PNG.

The user's direction (second pass, 2026-10-31): the continent certificates use the ORIGINAL games' certificate art,
restored at x2, with the OpenYAMM mark added; only the composite certificate is OpenYAMM's own design.

## How it works

- A world declares its certificate in `world.yml` `completion`: the qbit that marks its story finished, the art, the
  headline and the ending text, variants chosen by a qbit set at that moment (MM7's path of the Dark, qbit 1606), and
  a `layout` in the art's 640 x 480 units: the zone the text is centred in and where the OpenYAMM mark (the seal and
  wordmark) goes. MM6 uses qbit 784 (`hive_mmmerge.lua`, good ending), MM7 783 (either path), MM8 228.
- With a layout the certificate looks like the originals: the background icon (`6winbg`, `7winbg`, `winbg`), the
  ENDGAME font, "Congratulations!", "Name the Level N Class", "Total Time" and "Your score" (the originals' formula,
  the party's experience over the days played). MM8 keeps its original ending text; MMerge replaced MM7's original
  ending strings (global 675/676) with its own, and MM6's are not in the repository, so MM6 and MM7 have new texts.
- The composite certificate is `assets_dev/engine/ui/certificates.yml` with OpenYAMM's 1536 x 1024 art; it is offered
  only when every world it names is mounted and declares a completion.
- `game/content/CompletionCertificates.cpp` records a completion the first frame its qbit is set with no record (the
  record keeps the game time, the score and the real date, in the party's save), after any ending movie. A save from
  before version 143 first gets untimed records, without certificates, for stories it had already finished.
- A game played by a ruleset names it beside the OpenYAMM wordmark (`certificateRulesetLabel`): "OpenYAMM - MAW
  (Beyond Madness)", the challenge mode, else the difficulty ("MAW (Hell)"), both for Austerity ("MAW (Austerity,
  Hard)"), and Randomizer when on; a Standard game shows "OpenYAMM" alone. It is the ruleset at the moment of
  completion (Austerity's difficulty can change during a game).
- `WinGameScreen` draws the certificate fitted to the frame. On its second frame the game saves the certificate's part
  of the frame to `certificates/openyamm_<id>_<date>_<time>.png` in the user data folder (beside `saves/`).
- The old pseudo-house win (EnterHouse 600/601) is gone: in the merged house table those are Crane Cottage and Bith
  Estate, and no script used them as endings any more.

## Art

| Certificate | Art | Source |
| --- | --- | --- |
| mm6 | `engine/icons_x2/6winbg.png` | `original_x2/raw/6winbg_b.png`: keeps the original's (R) mark |
| mm7 | `engine/icons_x2/7winbg.png` | `original_x2/raw/7winbg_a.png` |
| mm8 | `engine/icons_x2/winbg.png` | the x2 restoration accepted in the 2026-09-26 icon migration |
| grand | `engine/hud_x2/certificates/grand.png` | `raw/grand_b.png`: its medallions stay below the text |

- `original_x2/`: Codex restorations of the native 640 x 480 backgrounds (`BRIEF.md`, `scripts/prepare.py` places each
  in a 1536 x 1024 canvas between grey bars, `scripts/run_codex.py`). The middle 1365 x 1024 is resized to exactly
  1280 x 960; brought back to 640 x 480 every candidate differs from the native by 4-9 levels on average, and the
  title lettering was checked against the native.
- OpenYAMM design: `briefs/`, `guide_*.png` (`scripts/make_guides.py`), `scripts/run_codex.py`. `raw/enroth_*`,
  `antagarich_*` and `jadame_*` were the first pass's OpenYAMM continent certificates, superseded by the originals.
  The grand painting's seal recess sits at (768, 130), radius about 63 (`scripts/measure_recess.py`); its text zone is
  x 330-1206, y 236-750, above the medallion ornaments (y 766). A new painting must keep these, or `WinGameScreen`'s
  constants change with it.

## Review

`review/tour.yml` finishes all three worlds at once (MM7 on the path of the Dark) and steps through the four
certificates; `review/01`-`05` are its captures on a five-member party (a 2026-10-25 save), the last one back in the
game with the "Certificate saved" status.
