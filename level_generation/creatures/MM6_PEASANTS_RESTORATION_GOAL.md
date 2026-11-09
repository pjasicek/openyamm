# Goal: restore all eight MM6 peasant sprite families

## Objective

Complete enhanced 2D sprite packages for the eight native MM6 peasant families below, covering all original
actions, stored directions, mirrored/reused views, and palette variants. Target the quality and practical workflow
of the accepted goblin and `pmn2` restorations: coherent detailed materials, recognizable original characters,
clean transparent contours, stable animation placement, compact atlases and selective recoloring.

The intended result is **eight base-art families with three palette appearances each**, not 24 independent AI
restorations. Reuse completed accepted work. This goal authorizes generation and reversible offline processing;
it does not authorize engine installation, gameplay changes, replacing native art, or regenerating accepted
families merely to make them new. Guards (`gua*.bmp`) are outside this goal.

## Families and initial lookup hints

These are actual sprite-file prefixes, not necessarily the names of their animation groups. Sources currently
live in `assets_dev/engine/sprites/`; palette files are under `assets_dev/worlds/mm6/textures/`.

| Family label in merged descriptors | Native pattern | Palette IDs | Merged descriptor IDs | Working directory |
| --- | --- | --- | --- | --- |
| Female 1 | `pfem*.bmp` | 786–788 | 595–597 | `level_generation/creatures/mm6_pfem/` |
| Female 2 | `fmp*.bmp` | 789–791 | 598–600 | `level_generation/creatures/mm6_fmp/` |
| Female 3 | `mfp*.bmp` | 792–794 | 601–603 | `level_generation/creatures/mm6_mfp/` |
| Female 4 | `natf*.bmp` | 795–797 | 604–606 | `level_generation/creatures/mm6_natf/` |
| Male 1 | `pman*.bmp` | 798–800 | 607–609 | `level_generation/creatures/mm6_pman/` |
| Male 2 | `pmn2*.bmp` | 801–803 | 610–612 | **Existing:** `level_generation/creatures/mm6_pmn2/` |
| Male 3 | `mep*.bmp` | 804–806 | 613–615 | `level_generation/creatures/mm6_mep/` |
| Male 4 | `natm*.bmp` | 795–797 | 616–618 | `level_generation/creatures/mm6_natm/` |

Treat these values as lookup hints and verify current descriptors → animation groups → actual files. Group names
and capitalization vary: for example, Female 2 uses `fmA*` groups pointing at `fmp*` images, and all three Male 2
variants use `pmn2*` images. Shared palette numbers between male/female families do not make their geometry or
masks interchangeable. Descriptor labels also need not be the creature's displayed gameplay name: `pmn2` is the
staff-carrying mage family. Restore each source character's actual clothing, anatomy, accessories and equipment.

## Required workflow

Use the [creature-restore skill](../../.agents/skills/creature-restore/SKILL.md) for each family, following
[Sprite Atlas and Variants Pipeline](SPRITE_ATLAS_VARIANTS_PIPELINE.md) and the relevant parts of
[Direct Sprite Workflow](DIRECT_SPRITE_WORKFLOW.md). Use the available imagegen skill and **built-in imagegen**;
do not switch to a separately billed API. This is direct sprite restoration, with no Blender or rigged-model phase.

1. **Inventory and resume once.** Inspect existing family folders, manifests, accepted outputs and provenance before
   generating. Resolve source files case-insensitively and exclude unrelated wildcard matches. Record dimensions,
   transparent indices, original palette appearances, per-variant timing/scale, anchor flags, native image aliases
   and unused source artwork. Do not assume every family has identical frame counts or canvases.
2. **Calibrate identity and regions.** Inspect a compact native multi-view/palette contact per family. Select one
   correctly paletted appearance as the enhanced base. Identify which skin, clothes, hair or equipment colors vary
   and which details remain protected. Start with a compact standing-view restoration, adding an action reference
   only if it reveals important hidden equipment. Review it and continue autonomously.
3. **Generate missing base art.** Use compact action/direction batches, normally 4–8 useful poses. Native frames
   control poses, camera angles, handedness, equipment visibility and foot contacts; accepted enhanced references
   control identity and materials. Carry the same face, body proportions, clothing construction, tonal weight and
   baked-light direction through the entire family. Retain original differences between the eight families.
4. **Clean and register.** Preserve real alpha if the generator supplies it; otherwise use the established matte
   extraction and edge-RGB unmixing workflow. Inspect actual output dimensions and empty gutters before cutting.
   Preserve thin fingers, hair, staffs, blades and garment tips. Apply only demonstrated local repairs. Use shared
   anatomical scale per batch and native landmarks/baselines; preserve collapse/prone proportions, crop offsets,
   variable canvases and original frame/actor scale. Export at 2 physical pixels per logical pixel.
5. **Author selective variants.** Generate each base once. Create the smallest sufficient set of soft coverage masks
   on enhanced pixels, guided by native palette differences. Use fixed per-region recolor parameters across all
   poses, with exact base bypass and unchanged alpha. Bake other appearances deterministically for review. Do not
   substitute a whole-character tint or resize native masks onto changed anatomy. Do not force a single mask when
   independent regions need different colors; document any engine extension required by the chosen operation.
6. **Package and review.** Export base/matching mask atlas pages, versioned placement/animation/variant JSON,
   aligned masters, compact crops, deterministic previews and an offline native/enhanced animation viewer.
   Preserve native sequence reuse, pixel aliases, mirror flags and per-palette timing/scale. Assemble full action
   sheets as review artifacts, not as giant sparse runtime textures. Review every frame through compact contacts,
   mask overlays and representative playback; repair specific faults without restarting accepted work.

## Reuse and efficiency

- `mm6_pmn2/` is already complete and installed separately as custom monsters 904–906. Read its
  [README](mm6_pmn2/README.md), validation and current accepted outputs. Count it as completed after a brief coverage
  and checkpoint review. Do not rerun its ten AI requests or alter its runtime installation. Only repair a concrete
  asset fault if one is found, keeping installed content unchanged during this goal.
- Use the [complete goblin package](mm6_goblin/direct_complete/README.md) as an example of native pixel reuse,
  per-palette timing and multi-region masks. Its scripts are creature-specific examples, not a universal exporter.
  Do not copy its skin/material assumptions into human peasants.
- Save each accepted raw sheet and exact submitted prompt immediately. Record source/reference/output hashes,
  selected versions, dimensions, cleanup parameters, registration and masks. Resume from these checkpoints after
  interruption. Complete one family through review/export before treating it as done in the overall index.
- Normally use one AI request per useful missing batch. Regenerate only demonstrated bad cells/sheets. Fix matte,
  color, crop or registration faults deterministically from saved raw art when possible. After repeated failure,
  change the batch/reference/extraction approach instead of repeating the same prompt indefinitely.
- Do not build a generic asset framework, run engine builds or gameplay scenarios, or audit every NPC in a map.
  The important checks are visual quality and the small offline export checks below.
- Proceed through routine authorized steps without driver approval checkpoints. If a tool-enforced permission is
  actually required, report the real blocker; do not claim that this document bypasses tool permissions. Use
  [the approved local HTML capture helper](../../tools/CAPTURE_LOCAL_HTML.md) directly rather than constructing new
  headless Chrome commands. Never use a paid API as an unattended fallback.

## Completion checks per family

- All expected native source filenames are represented or explicitly excluded with a verified reason. Exact native
  duplicate images share enhanced tiles; aliases and repeated sequence entries retain original timing and placement.
- No clipped accepted silhouettes. Tight crops reconstruct aligned RGBA, and atlas extraction matches base and masks
  exactly. The 2× export changes physical resolution, not logical size or feet-on-ground placement.
- Mask coverage is valid, channel weights do not exceed one, protected zero-mask pixels are unchanged, variant alpha
  matches base alpha, and the base preset is an exact bypass. Inspect **all** frames' masks, not only standing.
- Run automatic residual-spill checks on **every cleaned and final atlas-extracted frame**. Review a compact
  worst-edge contact on light/dark backgrounds. Correct confirmed contamination locally while preserving alpha and
  thin details. A low chroma score alone does not establish clean contours; protect intended pink/purple materials.
- Inspect native/enhanced size and pose comparison, all-frame contacts and representative viewer playback. Retain
  coherent faces, materials and light across frames; record specific unresolved visible approximations honestly.
- Report actual generated dimensions separately from the 2× export tier, plus decoded base, masks, packing and
  intended upload formats. Do not multiply shared atlas memory by actor count or claim measured FPS from byte counts.

## Final deliverables and stop condition

Create `level_generation/creatures/mm6_peasants/README.md` as the overall index. Link each of the eight family
packages, its viewer, validation, native patterns, palette mappings, reuse status and runtime compatibility.
Include a concise status table and total shipping/decoded footprint, distinguishing staged assets from the existing
`pmn2` installation. Keep this index useful for resuming work; do not mark partially generated families complete.

Create one compact labeled contact comparing all eight families' three enhanced appearances, alongside native
references at matching logical size. Each family's viewer remains the detailed animation/mask review tool.

Finish when all eight families meet the checks, with all native views/actions and 24 deterministic palette
appearances available through their packages. The expected new work is seven families, plus brief verification and
reuse of `pmn2`; adjust only if the initial inventory finds additional valid accepted checkpoints.
The final response should link the overall index and contact, give coverage and validation results, and identify
remaining visible limitations or required future shader support. **Do not install or spawn these families in-game.**
