# Paperdoll and fitted equipment handoff

## Current: accepted and installed — 2026-09-26

[The runtime cutover record](../runtime_install_20260926/README.md) supersedes the pending-installation notes below.
**9,920 exact-2× icons are accepted and installed**, with all 726 active offsets and 79 inventory fits imported.
All 13,854 original MM6–MM8 icon files are preserved under `assets_legacy/icons_20260926/`, outside runtime mounts.
MM9's 881 native files remain unchanged. The canonical ledger and export manifest contain the approvals.
Runtime icon package policy selects restored roots without native fallback; world NPC namespaces remain distinct.

The active browser scripts are `../runtime_install_20260926/review.js` and `inventory_fit.js`. All 1,260 decisions
and 728 placement records are preserved. All reviewed queues are empty. Use port **8899** and Ctrl+Shift+R.
Existing release ZIPs are not rebuilt; launch the current build with `assets_dev` to use this installation.

The following sections retain the earlier session history.

## Current canonical acceptance and full icon audit — 2026-09-26

The user accepted the final repairs and authorized ledger integration. [The finalization record](../finalization_20260926/README.md)
imports and stages **2,216 distinct images**: 1,349 equipment/jewelry targets plus 770 inventory targets,
minus 369 shared images, plus 466 already-approved doll/body-part sprites. All 1,260 review decisions and 728
placement records are preserved. All 63 jewelry image groups are accepted; main, held-armor, jewelry and repair
queues are empty. The active overlay is `../finalization_20260926/review.js` and accepted-only mode loads its
canonical exports. The canonical checkpoint now records these approvals. Runtime installation is pending.

**The entire icons folder is not finished.** The full audit found seven unapproved doll backgrounds and one
inventory coverage omission: Shadow's Mask `7item344.bmp` (its equipped variants are accepted).
[Inspect the eight gaps](http://127.0.0.1:8899/level_generation/ui/hud_inventory/finalization_20260926/remaining.html).
The native folders remain in place. The finalization README records the required placement/sizing integration,
restored-only lookup and archive work before originals can be retired.

## Previous jewelry feedback repairs — 2026-09-26

[Jewelry repairs and staging](jewelry_repairs_20260926/README.md) fix the Shadow Sect Medallion's metal color,
recover the complete Fine Ring from its retained master, and reduce the displayed sizes of Paladin Gauntlets,
Ethereal Ring and Scarab Ring (also Igraine/Athena). The three size corrections preserve their approved PNGs.
All **1,260 decisions, 1,258 staged approvals and 728 placement records** from the 15:49:48 UTC capture are
preserved. The previous approved Fine Ring remains archived while its repaired crop awaits review.

**61 of 63 jewelry image groups are accepted; only two replacements need review.**
[Open latest repairs](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=latest&hide_accepted=1&item=150)
and Ctrl+Shift+R. Main equipment and held-armor queues remain complete. The active scripts are
`jewelry_repairs_20260926/review.js` and `jewelry_repairs_20260926/inventory_fit.js`.
Isolated browser checks cover all five fixes, shared aliases, slot fitting, keyboard movement and preservation
of current/newer feedback. No ledger or runtime installation; display scales and offsets are staged proposals.

## Earlier jewelry classification and inventory fit — 2026-09-26

[Coverage, shared-image classification and staged sizing](jewelry_inventory_20260926/README.md) account for every
gauntlet/amulet/ring table row: **79 items, 63 distinct images**, with 16 duplicate images in twelve families.
The review queue/selectors now show each normal underlying image once and list its artifact/relic/special aliases.
Igraine is a Scarab Ring alias, not an unseen design. The captured review has **58 accepted groups and five flagged
groups**, with no unreviewed groups. All 1,260 saved decisions and 728 placement records remain preserved.

The browser shows an inventory-cell preview: rings 1×1, gauntlets 1×2, five amulets 1×1 and fifteen amulets 1×2.
Uniform inventory-only fitting contains the whole canvas without cropping and leaves paperdoll artwork/offsets
unchanged. Six table footprint changes and the common-image mappings are staged as CSV/JSON proposals. Final
ledger acceptance and runtime integration remain deferred. The five flagged image groups remain flagged.
The same update repairs the already-imported twelve offset approval snapshots using their prior explicit receipt;
only exact unchanged old decisions at the authorized positions are updated. Cleared/newer work is protected.

## Gloves/jewelry browser repair — 2026-09-26

The screenshot `test_img/2046.png` correctly showed native fallback: eight gloves and 25 jewelry icons had no
browser-ready candidate. [Jewelry preparation](jewelry_prepared/README.md) connects 33 retained restorations;
all **18 glove icons and 61 jewelry icons** now have exact-2× art. Existing accepted images, 1,225 staged decisions,
726 placement records and the canonical ledger are preserved. The separate `backhand` panel remains native.

**Selection mode** now includes Gloves, Amulet and Ring 1–6. Space advances, Shift+Space accepts, and arrows move
the current slot. Next/previous buttons, direct item selection and body-type cycling keep the jewelry overlay
visible. F1–F9 return to the corresponding doll equipment slot. Jewelry icons are included in the review queue.
Ctrl+Shift+R loads the updated catalog and controls; no newly connected image was automatically accepted.

## Earlier snapshot — held armor accepted and offset notes applied, 2026-09-26

The latest [acceptance/offset snapshot](acceptance_snapshot_20260926_1411/README.md) captures the user's complete
held-armor web review and applies all twelve notes requesting matching offsets on the empty-hand variants.
**1,225 approvals are staged, zero flags remain, and all 726 saved placement records are preserved exactly.**
The twelve paired empty-hand approval snapshots now confirm the requested positions; their artwork is unchanged.
See [the applied offset CSV](acceptance_snapshot_20260926_1411/armor_offset_updates.csv) and the complete
[placement proposals](acceptance_snapshot_20260926_1411/placement_proposals.csv).

All **270 held variants** are accepted (266 staged, four already canonical), and all **270 empty-hand variants**
remain accepted. Main equipment, held armor, and latest repairs each have zero remaining targets.
At this snapshot, **8 gloves and 28 jewelry images** remained unreviewed in this equipment scope. Its overlay
**`acceptance_snapshot_20260926_1411/review.js`** is retained as history; the jewelry repair pass above supersedes it.
All twelve changed pairs were checked in empty/one-hand/two-hand poses. The ledger, artwork, and runtime tables
remain unchanged; final ledger acceptance/installation is still deferred.

## Historical preparation — held armor from accepted bases, 2026-09-26

[Held-armor preparation and validation](held_armor_20260926/README.md) implements the accepted-base workflow:
**270 held candidates, zero imagegen calls**. There are 188 exact copies, 44 local sleeve trims, and 38 arm
transfers. All pixels outside the recorded right-arm edit regions match the accepted empty-hand bases exactly.
All 964 staged files/decisions and 724 placement records remain intact; the ledger and runtime assets are unchanged.

[Open held-weapon armor review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=held&hide_accepted=1&target=engine--icons--7item078v1.bmp).
Ctrl+Shift+R refreshes. Use **Review → Held-weapon armor to review**, F6 for armor, Space for next, Tab for body
type, Shift+Space to accept. The preparation overlay **`held_armor_20260926/review.js`** is retained as history.

At preparation, **266 held images needed approval**: the earlier 256 pending images plus ten replacements of older
held approvals. Those prior approved files remain preserved; four held approvals still match exactly.
All 270 empty-hand armor approvals stayed valid. Browser checks covered all 82 edited arms and all five types
across three poses. No new image was automatically accepted at preparation; the user subsequently approved them,
as recorded in the current snapshot above.

## Preserved acceptance snapshot — main equipment complete, 2026-09-26

The user explicitly approved the three round-3 repairs with "ok accepted". Their exact repaired image hashes
and reviewed placements are recorded in [approval.json](acceptance_snapshot_20260926_1322/approval.json).
**964 approvals are staged, zero current flags remain, and all 724 placement records are preserved exactly.**
The saved browser state was read from an isolated copy before applying this scoped chat approval; prior flags,
notes, images and browser values remain archived. No ledger acceptance or runtime installation.
See [the current acceptance snapshot](acceptance_snapshot_20260926_1322/README.md).

Weapons, bows, shields and wands (332 images), empty-hand armor, helmets, boots, belts and **all 72 cloak variants**
are complete. At this snapshot, both **Latest feedback repairs** and **Remaining main equipment** were empty with
accepted images hidden. The two sleeve repairs and recovered dwarf hat are staged. This snapshot had **256 pending
held-weapon armor variants, 8 gloves and 28 jewelry images**; the active held-armor pass above replaces that held
queue. The earlier body/limb acceptance remains unchanged.

The active held-armor overlay carries all approvals/placements from `acceptance_snapshot_20260926_1322/review.js`
and preserves newer local work.
The [round-3 repair evidence](review_pass_20260926_round3/README.md) is retained as a historical snapshot.

## Historical held-weapon armor feasibility study — 2026-09-26

The [accepted-base pose study](armor_pose_study_20260926/README.md) audits all 270 pairs and records a proposed
workflow with exact RGBA preservation outside a small right-arm edit region. Of the 256 pending held variants,
177 have identical native poses and can reuse the accepted empty-hand file exactly; 79 require local arm work.
Nine isolated probes demonstrate preservation and identify seam problems in a naive donor splice. No imagegen,
approval changes, artwork installation or active-browser changes were made for this study. The previously
accepted images, including all 14 already-approved held variants, remain intact.

## Equipment repair pass — round 2, 2026-09-26

See [the current repair/staging handoff](review_pass_20260926_round2/README.md) and
[open the latest 51 replacements](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=latest&hide_accepted=1).
The latest export (07:54:45 UTC) preserves **916 decisions, 838 approvals staged, and 714 placement records**.
All **38 new/revised flags** are covered, along with matching-sprite variants and ten additional crop repairs
found among staged approvals. Four automatically inherited wand offsets now follow the newer first-wand adjustment.
Original records and the exact approved files remain archived; replacements await review. **No ledger acceptance.**

Use **Review → Latest feedback repairs** for this round, or **All repairs to re-review** for the remaining older
repairs too. **Hide accepted / staged** filters the queue and item selectors; Space and the item arrows skip
accepted artwork. Changed candidates remain visible until re-approved. Older decisions, notes and manual offsets
survive the one-time import, with newer browser edits taking precedence. Ctrl+Shift+R refreshes the page.
The [first repair pass](review_pass_20260926/README.md) remains an immutable historical record.

Current decision: **2026-09-24 — accept native-based Real-ESRGAN for every available doll body and limb.**
The user selected this modest improvement to keep the original placement and avoid further repaint/fitting cost.
Painted restoration is deferred future work, not an active completion gate.

## Accepted dolls

**466 sprites: 75 bodies and 391 limbs/hand overlays**, covering all 75 available doll sets, are accepted
in `checkpoint/state.json`. The main [equipment browser](index.html?doll=1) now selects their canonical
accepted copies in both candidate and accepted-only artwork modes. The PC01 painted-trial toggle was removed.
The native-original checkbox remains available for comparison.

Acceptance provenance, exact hashes, source validation and scope live in
[the acceptance record](identity_workflow/esrgan_acceptance_20260924/README.md).
`identity_workflow/accept_esrgan.py` is the explicit, scope-limited user-decision import; it does not fabricate
imagegen review results or accept dependent equipment. It uses the canonical checkpoint lock and preserves
other cells. The earlier generation manifest remains a historical comparison-stage record; current acceptance
is owned by the checkpoint and the immutable decision record.

Recipe: `realesrgan-x4plus`, native RGB with transparent-area color extension and four pixels of padding,
4× inference, original-source alpha, premultiplied Lanczos export to exactly 2×, clipped to the native footprint.
No source canvas, equipment table, hand anchor, or draw order changed. This adds no equipment offset work.
It also does not repair preexisting bad equipment candidates or prove every independently generated armor fits.

Missing source art remains missing: character #30 references absent pieces; #31 lacks its body.
Six body-only originals contain their own full-canvas scenery, retained by this faithful upscale.
Separate doll backgrounds and head/beard metadata, avatars, equipment, and jewelry panel `backhand` are outside
this body/limb acceptance. The originals and all painted attempts are preserved. Runtime installation is separate;
this task accepted assets and selected them in the review browser, without changing `assets_dev`.

## Comparison / acceptance GUI (2026-09-24)

The browser now shows **native doll + native items** beside **accepted ESRGAN doll + candidate equipment**,
with per-slot Accept/Flag/Clear and movement buttons to the right. Five equipment body-type shortcuts plus the
non-equipping dragon type avoid traversing all characters. The full selector remains available.

Acceptance is per exact image/hash, including separate armor body-type and arm-pose files. Shared base weapon
images keep one decision across dolls. Moves are one native game pixel (two pixels at 2×), save locally, and are
included in **Export review JSON**. Body equipment moves map to per-item/per-type complex points. Weapon, shield,
bow and jewelry corrections are now scoped to **item + doll type + slot**, in screen coordinates, and exported as
preview proposals requiring later runtime placement support. The native tables combine global item grip points
with doll-type anchors; neither can express individual per-item/type/slot corrections by itself. Old global
`grip:*` / `preview:*` proposals remain preserved but explicitly inactive, and decisions tied to them are stale.
Runtime tables remain unchanged.
A changed reviewed placement makes its decision stale. See [controls, ownership, export and checks](README.md#side-by-side-acceptance-and-placement).

The UI queue includes the 332 base icons as well as the 930 remaining fitted/doll targets (**1,262 pending**).
Browser acceptance remains a local/exported review decision; it does not automatically change the canonical
checkpoint. No equipment was accepted or installed by implementing this GUI.

## Keyboard controls and retained work (2026-09-25)

F1–F9 select main-hand / two-hand / shield / bow / cloak / armor / helm / boots / belt.
Space advances that mode; Shift+Space accepts its currently displayed image without advancing. Arrows nudge
its offset by one game pixel. Tab cycles the five equipment body types, excluding dragons (Shift+Tab reverses).
Notes and dropdowns retain normal typing/navigation; Escape resumes shortcuts. The toolbar identifies the active
mode and image. Existing local storage keys are unchanged; the first updated load makes an additional verbatim
snapshot under `openyamm-paperdoll-before-shortcuts-v1`. Export JSON remains the portable backup.

## Inline flag notes (2026-09-25)

Each manually flagged or automatically flagged equipment row now has an inline notes field. Clicking Flag
focuses it immediately. Notes autosave per exact image and are included in the existing decision JSON export
and import. Inspector and row notes stay synchronized; editing a note does not revalidate stale acceptance.

## Automatic magenta screen (2026-09-25)

[Scan results and method](magenta_scan/README.md): all 1,262 pending selected targets and 1,319 total
candidate/alternative records checked. The GUI pre-flags **70 suspected spill** candidates and separates
**14 purple-material checks**. Use **Review → No magenta detected** for the remaining **1,178** targets,
or the two automatic-check filters to inspect findings. No pixels, acceptance decisions or placements changed.
Findings are candidate/source-hash-bound and exported separately from manual decisions. Run `scan_magenta.py`
after new candidate preparation; “no spill detected” is only a screening result, not quality approval.

## Remaining review

The active pending queue now contains **930 targets**: **906 fitted equipment variants**, **7 separate doll
backgrounds**, and **17 head/beard metadata sprites**. The latter are not composited by the current renderer.
The updated [pending snapshot](APPROVAL_SCOPE_AFTER_ESRGAN_20260924.csv) is distinct from the historical
1,396-target snapshot. Weapons/shields/base icons belong to `inventory_items`, outside this queue.
They remain at their existing approval states; none was accepted by the doll decision.
All **332 base weapon/bow/shield/wand icons now have exact-2× browser candidates**: 244 melee, 35 missile,
38 shield, 15 wand. The [inventory preparation](inventory_prepared/README.md) adds 229 retained-sheet
extractions and 37 exact-source donor copies to the existing 66 candidates. Use the
[inventory gallery](inventory_prepared/index.html) or candidate artwork mode in the main browser.
These are unapproved previews with extraction/registration findings, not accepted equipment.

The browser resolves items from game tables and labels each drawn layer accepted, pending, or native.
Accepted artwork is checkpoint art, not the original `assets_dev/engine/icons` BMPs.
Candidate equipment remains selectable over the accepted dolls. Accepted-only mode intentionally uses
native fallback for weapon/shield icons without accepted art.

Useful commands from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/accept_esrgan.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/build.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/verify.py
python3 -m http.server 8899 --bind 127.0.0.1
```

The first command verifies the exact acceptance scope; no `--apply` is needed again. The server is already
running during this session. Open `http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1`.

## Deferred painted restoration

Do not resume generation or treat paint-quality rejection notes as rejection of the accepted ESRGAN files.
A future user-requested pass may improve anatomy, hands, portrait identity and materials, subject to original
placement. Preserve the current accepted set until replacements are explicitly approved.
The [previous handoff](HANDOFF_BEFORE_ESRGAN_ACCEPTANCE_20260924.md), retained raw masters, prompts and PC01
comparisons document the attempted methods and unresolved issues for that future work.
