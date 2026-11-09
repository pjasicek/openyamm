# Separate MM8 staging collection

This collection selects the 61 MM8 native families and all 198 merged descriptors from the completed coverage audit.
It contains 9,409 restored master images. Four unused Naga fidget images are excluded as requested; Earth Elemental
includes eight ESRGAN Video ×3 walk images exported at ×2, and Troll Peasant retains its approved pose substitution.
All other native poses use the latest packed whole-animation + attached OUTLINE-ONLY restoration method.

The staging exports are independent copies under `families/`. Their native palette references, masks, masters,
atlas previews and metadata use the existing acceptance viewer's format. Source restoration packages, frozen
acceptance records, shared viewer code, global ledgers and gameplay assets are unchanged.
Every family records its selected source manifest and acceptance hashes. Generated detail is measured separately
from the ×2 physical export tier; accepted sampling shortfalls remain visible in the viewer.

From the repository root:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm8_packed_outline_collection_20261002/collection.json \
  --state-dir level_generation/creatures/mm8_packed_outline_collection_20261002/review_state \
  --port 8768
```

Open <http://127.0.0.1:8768/>. The existing MM6 viewer remains on <http://127.0.0.1:8767/>.
The convenience launcher is `bash level_generation/creatures/mm8_packed_outline_collection_20261002/serve.sh`;
an optional first argument selects a different unused port.

Use the same command with `--check` to validate the collection without opening a server.
`collection.json` pins every selected manifest and the server's complete review-artifact digest.
The server rejects changed packages rather than selecting an older attempt.

Decisions and placement/size/colour proposals save only to this collection's `review_state/decisions.json` and
`review_state/frame_fixups.json`. They begin empty and do not inherit MM6 decisions. Saving proposals does not
modify the restored PNGs or install assets into gameplay. Native timing, aliases, mirrored views, fractional
placement and every native palette remain available. The master selector also exposes restored unused poses.
