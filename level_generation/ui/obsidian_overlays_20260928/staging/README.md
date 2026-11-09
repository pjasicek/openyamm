# Approved Obsidian UI — staged integration package

**Approved 28 September 2026: extended overlays revision 03.** This approval includes the latest item footer, blue skill
rows, native skill spacing, rest blocks, stat borders, wider quick-reference column, colours, dark surfaces and buff art.
It builds on the approved **Carved Obsidian revision 06** full-screen frame and **Obsidian refinement 04** gameplay HUD.

[Review the staged assets](http://127.0.0.1:8899/level_generation/ui/obsidian_overlays_20260928/staging/index.html) ·
[Approved interactive collection](http://127.0.0.1:8899/level_generation/ui/obsidian_overlays_20260928/index.html) ·
[Runtime integration notes](INTEGRATION.md) · [Validation](validation.json)

The subsequent [journal/map/quest/autonote revision 01](../../obsidian_journal_20260928/README.md) is also approved.
Its [companion staging package](../../obsidian_journal_20260928/staging/README.md) holds the journal graphics,
native reading fonts, Fondamento controls and layout draft.

| Directory/file | Contents |
| --- | --- |
| `engine/icons_x2/` | Content-free page skins, button plates/states, frame slices, shared chrome, approved icons/banners, 22 glyph-free buff illustrations and plain aggro diamonds. |
| `engine/ui/gameplay/` | Eleven draft YAMLs preserving current IDs and binding points. New hooks are annotated. |
| `engine/fonts/` | Five faithful MM FNT/TTF pairs/descriptors; Fondamento outline file and OFL license. |
| `design/` | Exact palette, font roles, interaction rules, frame construction and font-registration requirements. These are specifications, not live layout schema. |
| `masters/` | Original transparent frame, cuts/crop provenance, material and carved-frame source artwork. |
| `reference_layouts/` | Pinned current layout snapshots, for rebasing before integration. |
| `manifest.json`, `asset_receipts.json` | File/source hashes, intended destinations, dimensions, alpha and dependency inventory. |
| `review_geometry.json` | Measured approved browser geometry in review and 640×480 logical space; sample text is reference only. |

The package is **unmounted**. No runtime assets, code, game settings or saves were changed. “Staged” here means prepared
for integration, not added to Git's index. The layout drafts parse with the existing loader, but renderer work is needed
for Fondamento registration, repeated/cropped frames, semantic colours, dynamic layout and the responsive gameplay HUD.
Read [INTEGRATION.md](INTEGRATION.md) before using the drafts.

The accepted default is engraved inventory cells, dark obsidian, ivory/native reading faces and native 17px skills.
Earlier vellum/Source-font variants and the smaller skill-font comparison remain historical review options.
Original approval captures remain under [../previews/r03/](../previews/r03/) and unchanged inspector examples under
[../previews/r02/](../previews/r02/); source hashes are recorded in the manifest.
