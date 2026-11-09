# Paperdoll equipment context review

For continuation of this approval slice, start with the [paperdoll and fitted equipment handoff](HANDOFF.md)
and its [current pending target snapshot](APPROVAL_SCOPE_AFTER_ESRGAN_20260924.csv).

**Current acceptance:** the final two repairs are approved. **2,216 distinct equipment, inventory and doll
images are now accepted and staged in the canonical icon ledger**, preserving all 1,260 decisions and 728 offsets.
All 63 jewelry groups are accepted; the main, held-armor, jewelry and latest-repair queues are empty. Accepted-only
mode loads the canonical staged files. See [acceptance and full icon audit](../finalization_20260926/README.md).
Ctrl+Shift+R loads the update. Runtime integration remains pending: the audit found seven unapproved backgrounds
and a previously omitted Shadow's Mask inventory sprite. [Inspect these eight gaps](../finalization_20260926/remaining.html).

The approved jewelry repairs include silver/white metal on the Shadow Sect Medallion, the recovered Fine Ring top,
and smaller Paladin Gauntlets, Ethereal Ring and Scarab Ring displays (also Igraine/Athena). Inventory previews
fit rings into 1×1, gauntlets into 1×2, and amulets into 1×1 or 1×2 cells. The [repair provenance](jewelry_repairs_20260926/README.md)
retains the earlier pending-review snapshot; the canonical acceptance above supersedes its status.

**Gloves and jewelry:** [open Fleetfingers in the overlay](index.html?item=517&art=candidate&hide_accepted=1).
All 18 glove icons and 61 jewelry icons now have 2× artwork; 33 missing candidates were connected from retained
restorations. Choose **Gloves**, **Amulet**, or **Ring 1–6** in Selection mode to use Space / Shift+Space and the
arrow keys. Item arrows and body-type cycling retain the overlay. The separate panel background stays native.
See [preparation and verification](jewelry_prepared/README.md). Existing decisions and offsets are preserved.

**Earlier armor acceptance, 2026-09-26:** [held armor complete](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=held&hide_accepted=1).
All 270 held variants are accepted/staged. The [armor snapshot](acceptance_snapshot_20260926_1411/README.md)
preserves **1,225 approvals and all 726 saved placement records** and applies twelve notes requesting matching
offsets for the empty-hand armor variants. Both poses retain their approvals and use the corrected positions.
Main equipment and held armor remain complete. The then-pending jewelry review is superseded by the repair pass
above; ledger acceptance and runtime installation remain deferred.

The [accepted-base preparation](held_armor_20260926/README.md) produced 188 exact copies, 44 sleeve trims, and
38 local arm transfers without imagegen; every pixel outside the arm edit masks is preserved.

**Preserved acceptance state:** [main equipment review complete](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=main&hide_accepted=1).
The [acceptance snapshot](acceptance_snapshot_20260926_1322/README.md) includes the user's explicit approval
of all three round-3 repairs. All 964 approvals are staged and all 724 placement records preserved.
Weapons/bows/shields/wands, empty-hand armor, helmets, boots, belts and all 72 cloak variants are complete.
The current acceptance snapshot carries these earlier records forward.
Final ledger acceptance and runtime installation remain deferred.
The previous repair batch is retained in the
[round-2 handoff](review_pass_20260926_round2/README.md).

Open [index.html](index.html) directly in a browser. The page loads local image files and a generated `catalog.js`;
it does not need a server. Chrome's local-file policy can vary, so use
`python3 -m http.server 8899 --bind 127.0.0.1` from the repository root if images are blocked.

The browser presents all 77 `character_data.txt` dolls, including alternate races and conditional characters.
It shows each doll's assigned original avatar portrait beside the stage, using the same `facePicturesPrefix + 01`
mapping as the game. A separate 2× portrait candidate is labeled with its approval state. The original portrait
is the identity reference while those portrait candidates remain under review. The
[portrait-linked doll preparation and pilot](identity_workflow/README.md) records 75 available doll/portrait
reference packs. Its [in-place PC01 arm comparison](identity_workflow/in_situ_preview.html) includes one
registration-passing open-hand trial and a shared-bracer shield-hand trial. Neither is loaded by this browser's
normal artwork mode.
Each doll has its table-selected background, which can be hidden. Two synchronized canvases show the selected pose: originals enlarged on the left, selected restored art on the right. Available poses are empty hands,
a one-hand main weapon with optional off-hand item, or a two-hand main weapon. Changing a hand item selects its
pose; the Pose selector also switches directly. A jewelry toggle shows the `backhand` overlay
with its gauntlet, amulet and ring anchors. The item selectors cover the merged item table's visual equipment slots.
To check restored equipment against the original figure, open
[original doll with candidate equipment](index.html?doll=1&originalDoll=1), or check **Use original doll (body + hands)**
and set **Artwork** to **2× candidates, native fallback**. This keeps the native body, hand, finger and background
sprites while equipment follows the Artwork selector. Item positions remain table-driven.

**Accepted doll artwork, 2026-09-24:** all 466 available body/limb sprites (75 bodies and 391 hand/limb
layers) now use the native-based Real-ESRGAN set, following the user's explicit budget/quality decision.
Both candidate and accepted-only artwork modes select the canonical accepted files. The PC01 painted-trial
control has been retired; its artwork remains archived as deferred future work. See the
[acceptance record](identity_workflow/esrgan_acceptance_20260924/README.md).
The exports preserve exact 2× canvases, original-source alpha within the native footprint, and all table
coordinates. No equipment placement adjustment is introduced. Existing equipment restoration problems remain
separate from doll acceptance. Use **Use original doll (body + hands)** for a native comparison.

Equipment still follows the Artwork selector independently. Accepted art comes from checkpoint/HUD signoff
files; originals come from `assets_dev/engine/icons`. No weapon, bow or shield icon is currently accepted in
the catalog, so these slots use native art in accepted-only mode. Doll acceptance does not accept equipment,
backgrounds, avatars or head/beard metadata. No runtime installation was performed.
Use the asset queue to jump to a remaining fitted variant or paperdoll part; `[` and `]` move through filtered
targets. Arrow keys move the selected equipped image when no text/select input is focused; use the doll buttons
or body-type shortcuts to switch characters. A direct link can use
`?target=engine--icons--6chain1v3.bmp` or `?doll=50`.

## Side-by-side acceptance and placement

Use [the comparison reviewer](index.html?doll=1&pose=one&item=1) on port **8899**. The left canvas always uses
native originals at unchanged table coordinates. The right canvas defaults to accepted ESRGAN bodies/hands and
prepared equipment. The existing Artwork and original-doll controls still allow additional comparisons.
Both canvases use the same loadout, pose, background setting and display size.

The right-hand section has one row per visible equipment slot, with **Accept**, **Flag**, **Clear**, movement
arrows and **Reset**. **Flag** opens and focuses a notes field directly in that equipment row. Automatic
magenta/purple findings also expose notes without opening the inspector. Notes save as you type, remain scoped
to the exact image, and travel with the decision in Export/Import JSON. Adding a note to an automatic finding
records your own flag; editing an existing note does not re-approve a stale decision. The row and detailed
inspector share the same note.
Click the item filename to select it and open its detailed inspector below the comparison.
Each click moves **one native game pixel**, which is **two physical pixels at 2×**. Directional keyboard keys
move the selected visible equipment too. Accept/move are disabled when the candidate is not the displayed art.
The original canvas is never shifted.

**Acceptance scope is the exact image and hash**, not the item family: `item084v1`, `item084v1a` and `item084v2`
are separate decisions. Weapon/shield/bow/wand artwork is shared across body types, so its image decision follows
it across dolls. Changing an image or its reviewed placement marks the saved decision stale. Shared cloak files
likewise have one image decision even where several doll types resolve the same file.

Quick switches cover all six `doll_types.txt` entries: **male, female, minotaur, troll, dwarf, dragon**.
The first five support equipment; dragons support none. Existing slot restrictions remain active, including
minotaur helmet/boot exclusions. The full character dropdown remains available for individual checks.

Placement proposals follow actual table ownership:

- Worn equipment: `complex_item_pictures.txt`, item id + doll type. Both arm-pose variants share this point,
  so moving one updates the other pose's placement but does not accept its artwork.
- Weapons/shields/bows and centered jewelry: fitting adjustments belong to **item id + doll type + slot**.
  A male main-hand change does not move the female version or the off-hand item. Different characters sharing
  the same body type reuse the adjustment. Arrows remain screen-relative for rotated off-hand weapons.
  These are **preview proposals**, with `table: null`, requiring per-item/type/slot runtime placement support later.
  Original weapon placement still combines the global `items.txt` Equip X/Y grip point with the body-type hand
  anchors from `doll_types.txt`. Editing either existing component would affect other dolls or other items,
  so the reviewer does not misrepresent these individual fitting adjustments as edits to those shared fields.

Older `grip:*` and `preview:*` global proposals are retained in browser storage and exports as inactive reference
records. They are never applied, are listed in `inactive_legacy_placement_keys`, and old decisions tied to them
are stale. Recheck those items using the new body-type controls; old global shifts are not silently copied to each type.

Decisions and adjustments are saved in this browser's local storage. **Export review JSON** includes exact
asset/source/candidate hashes, per-image decisions, the reviewed placement snapshot, table row/type/fields,
original coordinates, deltas and proposed coordinates (or explicitly scoped screen-fit proposals). **Import JSON** restores them; the existing v1 decision-only
exports remain readable. A changed source/candidate or original table point disables a stale placement proposal.
These controls do not write the canonical acceptance checkpoint, change runtime tables, or install artwork.
The exported file is the handoff for the later acceptance/table application pass after review is complete.

Focused checks:

```sh
node level_generation/ui/hud_inventory/paperdoll_review/test_placement.mjs
node level_generation/ui/hud_inventory/paperdoll_review/test_gui.mjs
```

The GUI check requires the repository HTTP server on 8899 and local `google-chrome`. It uses a separate temporary
Chrome profile, tests variant isolation, body-type/hand isolation including rotated weapons, unchanged original pixels,
local persistence and JSON round-trip, and writes its screenshot/report under `/tmp`.

## Keyboard review

The toolbar shows the current selection mode and exact visible image. Shortcuts:

| Key | Action |
| --- | --- |
| F1 / F2 / F3 | Main-hand weapon / two-hand weapon / shields only |
| F4 / F5 / F6 | Bow / cloak / armor |
| F7 / F8 / F9 | Helm / boots / belt |
| Space | Next item in the selected mode; wraps and skips None |
| Shift+Space | Accept the visible item in that mode, without advancing |
| Arrow keys | Move that mode's item by one native game pixel |
| Tab / Shift+Tab | Next / previous equipment body type, excluding dragons |

F1–F3 also select the corresponding hand pose. Unavailable slots (e.g. minotaur boots) cannot advance or accept.
Keys retain their normal behavior inside notes, search fields and dropdowns; **Escape** leaves the field and
resumes shortcuts. Held Space/Tab/function keys do not repeatedly advance or accept; arrow repeat can nudge.
A loading, absent or native-only image cannot be accepted using Shift+Space.

Existing decision, attempt and placement storage keys are unchanged. On the first updated load with saved data,
`openyamm-paperdoll-before-shortcuts-v1` stores an additional, verbatim snapshot of those three local-storage
values. It does not replace the live records. Continue using the same browser and origin (127.0.0.1:8899), and
use **Export review JSON** for an external backup of your decisions, notes and placement changes.
`test_shortcuts.mjs` checks preservation, the backup, all modes, shield-only cycling, per-variant acceptance,
five-type cycling, movement and note-field keyboard behavior using a separate Chrome profile.

## Automatic magenta screening

The [2026-09-25 scan](magenta_scan/README.md) covers all pending selected candidates and retained alternatives.
**70 likely spill cases** are automatically flagged; **14 possible purple-material cases** remain separate.
Use **Review → No magenta detected** to classify the other **1,178** selected candidates first, or choose
**Auto: magenta spill** / **Auto: purple material check**. Equipment rows and the inspector show findings too.
The scan does not alter pixels or your decisions. Automatic findings are included separately in exports.
Run `python3 -B level_generation/ui/hud_inventory/paperdoll_review/scan_magenta.py` after rebuilding changed art.

## Scope and selection

The catalog contains 1,757 engine paperdoll/fitted-equipment targets. The browser also adds 332 distinct base
weapon/bow/shield/wand icons to the searchable queue. Its default filter shows **1,262 active unapproved targets**:
906 fitted variants, 24 background/head/beard assets, and 332 shared inventory/equipment icons.
The 466 ESRGAN bodies and limbs have left the pending queue. All remaining targets have exact-2× candidates.

The remaining candidates comprise 839 prepared raw returns, 65 existing audited candidates, four repaired
candidates and 22 new sheet returns. Preparation and registration measurements do not approve these files.
The original stays beside each candidate in the inspector. Selecting a target picks its doll/item context.
A **forced preview** means the current resolver or doll type does not normally select that variant.
There are 815 resolver-selected pending targets and 115 manual/metadata-only targets (98 fitted variants
and 17 head fields). The previous 1,396-target preparation history is preserved in the
[historical handoff](HANDOFF_BEFORE_ESRGAN_ACCEPTANCE_20260924.md).
Some historical item rows have lowercase `armor` or `cloak` values, and some variant suffixes are bypassed by the
current selector. Seventeen active head assets are table fields that the current paperdoll renderer does not
composite; their inspector shows original and
candidate art without inventing a head placement. Character #30 references seven doll images absent from the icon
inventory. Four dwarf beard field names are also absent; neither set is silently substituted with other art.

Weapons, bows, shields, and base item icons belong to the separate `inventory_items` family. The browser now
includes the 332 weapon/bow/shield/wand targets in its combined review queue. All **332 weapon/bow/shield/wand icons** now have exact-2× candidates:
244 melee weapons, 35 missile weapons, 38 shields and 15 wand icons. See the
[searchable original/candidate gallery](inventory_prepared/index.html), whose **Try on doll** links select the
item in context. The [preparation record](inventory_prepared/README.md) describes 229 retained-sheet extractions,
37 exact-source donor copies and the 66 existing candidates, including unresolved registration/crop findings.
Use **2× candidates, native fallback** to see them; accepted-only mode continues to show native weapon/shield
art until those candidates are approved. Each layer and inspector link identifies the actual selected artifact.
Other context families may still use native fallback. The browser never draws raw master sheets directly.

The catalog favors the canonical accepted artifact, then the HUD signoff image, then an exact-2× candidate from the
second-pass replacement audit (using a prepared border repair for eight opaque images), then a prepared raw or new
return. The original audited art remains selectable for each repaired image. If none exists, it uses a native PNG
preview for context assets outside the pending queue. Candidate art shown here is **not** installed in
`assets_dev/*/icons_x2`; this is a review preview, not a capture of current runtime artwork. Flags and approvals
stay in browser storage until **Export review JSON** is used. Each decision records the source and
candidate hashes and selected raw attempt, so a changed image makes an imported decision stale. Selected attempts
and decisions persist across reloads. Browser decisions do not modify the canonical restoration checkpoint.
`7item344` uses the frozen 50×55 native override because its current runtime BMP
is a contact sheet; that one native preview is deliberately different from the unfixed runtime file.

The prepared returns are **unclassified artwork**. The inspector shows the raw sheet, measured crop, extraction
method, sampling, and technical findings; the attempt selector exposes retained alternatives. The selected prepared
images include 731 registration flags and 617 measured-cell-boundary flags. These are prompts for visual inspection,
not automatic rejection or acceptance. All 35 donor destinations need their own review; two chainmail destinations
retain known geometry holds. Eighteen newly generated capes carry prior family-quality holds. Approve or flag each
target from its assembled view, then export the review JSON. No prepared candidate was silently accepted.

## Engine geometry used

The catalog reads the current `character_data.txt`, `doll_types.txt`, `items.txt`,
`complex_item_pictures.txt`, and `gameplay/character.yml` directly. The browser follows the game rules in
`GameplayPartyOverlayRenderer.cpp`, `GameplayScreenRuntime.cpp` and `CharacterDollTable.cpp`:

- The 640×480 reference layout has a 175×378 logical doll canvas. It is composited at 2× physical resolution.
  Native layers use nearest-neighbor
  enlargement; exact-2× candidates use their full pixels. Drawing order comes from `character.yml` z indices.
- Body X is copied from the character table, while Body Y is sign-flipped on load. Doll-type Y coordinates are
  sign-flipped. The table's matching background is selected per character.
- Armor uses `vN` when a main-hand weapon exists, otherwise `vNa` first. Cloaks use `vNa`; doll types 2 and 3
  select `v1a`. Other body equipment uses `vN`. Missing variants fall back to the item icon.
- Worn-item positions use the per-item, per-doll point in `complex_item_pictures.txt`. Main-hand grip, shield,
  off-hand weapon rotation, bow centering, fingers and open/closed hand layers use the same offsets and order as
  the renderer. Off-hand weapons rotate counterclockwise; the right-hand fingers layer draws over the weapon.

The viewer preserves the game's geometry and native logical dimensions. It uses browser Canvas alpha blending for
the picture; the engine uses BGRA integer blending, so subtle semitransparent pixels can differ. The equipment
selectors let you assemble review loadouts; class, race, skill and inventory legality beyond the doll-type flags
are not simulated. The Spear mastery control covers the renderer's left-hand pose change at Master rank.

## Preparation and refresh

From the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/prepare_raw_candidates.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/prepare_missing_returns.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/repair_existing_borders.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/build.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/verify.py
```

The first preparer crops retained raw sheets using their recorded layouts, extracts transparency where needed, and
exports exact-2× target PNGs under `raw_prepared/`. Its manifest records all 1,028 alternatives and the source,
crop, alpha treatment, and registration findings. The second preparer splits the eight new genuine-alpha sheets in
`new_returns/raw/` into 22 exact-2× PNGs. Their source contact sheets, layouts and draft prompts are in
`new_returns/input/`; `new_returns/submitted_prompts.json` records the prompts actually submitted to imagegen.
The border preparer removes isolated one-pixel magenta sheet seams from eight older opaque candidates and records
both the original and repaired hashes under `edge_repaired/`. All manifests preserve source and output hashes. The
builder verifies frozen source hashes and exact-2× dimensions, checks that every active target has a character or
item context, and regenerates the file-friendly catalog plus native PNG previews. It reuses unchanged native
previews. The final verifier checks that the 930 remaining paperdoll/fitted targets and 332 base equipment icons
have nonempty, hash-matched, exact-2× RGBA candidates. None of these commands accepts artwork or installs it in the
game.
