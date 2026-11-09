# MM6 New Sorpigal characters: 3D stage 1

**Ready for Meshy base geometry generation.** Four body reference sets are complete, reviewed against preserved
native sprites, and accompanied by anatomy and motion guides. Each has five transparent, weapon-free images:
one three-quarter submission plus front/back/left/right correction references. Actual generated resolution is
1024 × 1536 per image; selected files are unresized, byte-identical imagegen returns.

[Complete package](mm6_new_sorpigal_stage1_meshy_and_studies.zip)

| Character | Meshy submission | Reviewed views | Anatomy | All native animations |
| --- | --- | --- | --- | --- |
| Staff-carrying mage, `pmn2` | [Primary](pmn2/submission/00_smart_topology_three_quarter.png) | [Five views](pmn2/guides/selected_views_review.png) | [Guide](pmn2/ANATOMY_GUIDE.md) | [Study](pmn2/ANIMATION_STUDY.md) |
| Male peasant, `pman` | [Primary](pman/submission/00_smart_topology_three_quarter.png) | [Five views](pman/guides/selected_views_review.png) | [Guide](pman/ANATOMY_GUIDE.md) | [Study](pman/ANIMATION_STUDY.md) |
| Female peasant, `pfem` | [Primary](pfem/submission/00_smart_topology_three_quarter.png) | [Five views](pfem/guides/selected_views_review.png) | [Guide](pfem/ANATOMY_GUIDE.md) | [Study](pfem/ANIMATION_STUDY.md) |
| New Sorpigal guard, `gua` | [Primary](gua/submission/00_smart_topology_three_quarter.png) | [Five views](gua/guides/selected_views_review.png) | [Guide](gua/ANATOMY_GUIDE.md) | [Study](gua/ANIMATION_STUDY.md) |

## Identity and native evidence

The New Sorpigal `oute3` initial actor list contains 21 female peasants (595–597), 17 male peasants (607–609)
and five Guard A actors (553). It contains no `pmn2` mage placement. The requested mage is included as an
additional character: MM6 Apprentice/Journeyman/Mage (610–612), whose descriptor-internal labels say
`PeasantM2`; use its native `pmn2` sprites, not another game's mage or generic MM6 spellcaster art.

Selected palettes: mage 802 green, male 798 green, female 786 green, guard 748 navy sleeves/teal trousers/warm mail.
All three original palettes and standing variant evidence are retained per family. Guard lieutenant/captain
554–555 are palette variants of this geometry; their original palettes are retained even though only Guard A
is placed in the town. Color variants do not require separate base bodies.

The original 236 BMPs were found in the retired-native archive and hash-verified against the pre-restoration
inventories. All 236 aligned decoded PNGs match the existing native references exactly. Current runtime
restored atlases were not used as native animation evidence. The current frame table's timing and known
family atlas routing were checked against the original bindings. Each `source_inventory.json` retains hashes,
frame offsets, logical canvas, pivot, palettes, descriptor rows, playback order and source placement records.

| Family | Original files | Used files | Temporal anchors | Hit duration | Unused art retained separately |
| --- | --- | --- | --- | --- | --- |
| `pmn2` | 59 | 58 | 31 | 750 ms | `pmn2fib0` |
| `pman` | 59 | 57 | 30 | 625 ms | `pmanfib0`, `pmanwif0` |
| `pfem` | 59 | 58 | 31 | 750 ms | `pfemfib0` |
| `gua` | 59 | 59 | 31 | 750 ms | None; unrelated `guardang.bmp` excluded |

All seven native states are covered: standing, walking, attack, hit, death, corpse, fidget. `attack2` is an
alias of attack, not another animation. Native walking/fidget use six 125 ms entries and loop at 750 ms.
Death has five entries and reaches the separately held corpse at 625 ms. Standing/corpse metadata durations
do not limit how long the pose is held. Repeated native entries remain repeated holds; unused images are not
inserted into playback. There is no native run sequence in these families.

Only standing/walking have five genuine views. Other states reuse frontal images in every direction.
Mirrored directions add no depth evidence. Guides identify visible observations separately from inferred
3D angles, wrist/palm planes, hidden joints, contacts and corpse transitions.

## What to do in Meshy

For each family, upload **only `submission/00_smart_topology_three_quarter.png`** to the single-image
Smart Topology route. Request **15000 target triangles, A-pose, geometry without textures**, then download
the **unrigged GLB**. Keep the job/settings receipt and actual triangle count. The target is approximate,
not proof of the selected generation mode. The current documented API route uses `model_type: smart-topology`,
`ai_model: meshy-t2`, `target_polycount: 15000`, `pose_mode: a-pose`, `should_texture: false`; Smart Topology
already returns triangles and ignores the ordinary topology/remesh options.
See [Meshy Image to 3D documentation](https://docs.meshy.ai/en/api/image-to-3d).

The four other images are separate modeling/correction references. Do not upload the contact sheet as a
single character. Meshy's documented multi-image route is a separate option and does not document the same
Smart Topology model configuration; do not silently replace this handoff with it.
See [Meshy Multi-image to 3D documentation](https://docs.meshy.ai/en/api/multi-image-to-3d).

**Return the unrigged models before auto-rigging.** Codex next compares anatomy and all views, inspects hidden
surfaces and fixes confirmed geometry/topology defects. After geometry is accepted, auto-rig in Meshy and
return the rig. Stock walk/run then diagnose deformation; native walking is built first, weights corrected,
and the remaining states follow their studies. Review exact anchors, intermediate arcs, loops and corpse
transitions before UV creation, Meshy texturing and final texture-return review.

All body images are empty-handed. The original equipment remains part of the animation contract and must
be built as separate props later: mage staff, peasant knives, guard halberd. No native guard sword or shield
is supported. Removing equipment from modeling images does not remove the original attacks.

## Review and corrections

Twenty selected images came from 25 imagegen returns. Four initial primaries needed wider arm separation
and clearer fingers for modeling. The guard also needed an arm-pose correction after conversion to the
three-quarter camera reduced abduction. Five superseded returns are retained, with exact prompts, inputs,
reasons and hashes in [generation_runs.json](generation_runs.json). These are reference-image corrections,
not model or weight fixes; no model has been ingested yet.

Selected views retain native clothing coverage, head/foot proportions, clear limb gaps and empty hands.
Fine face, ear interiors, finger construction, seams, weave and rear detail are reconstructed interpretations.
Do not turn illustrated mail rings or cloth grain into dense geometry. Female hidden knees/skirt interior,
mage overhead left-hand contact, exact foot plants and single-view corpse depth remain explicit fitting
uncertainties to resolve when geometry/rigs exist.

Every family has `visual_review.json`, `verification.json` and canonical `creature_3d_progress.json`.
The recorded status is **stage 1 complete; stage 2 awaits the unrigged Meshy GLB; stage 3 not started**.
Agent visual review and technical verification are separate from user artistic acceptance, which is not
recorded. There is no Meshy job receipt, model/rig deformation pass, UV or texture acceptance yet.

## Package contents and checks

Within each family:

- `submission/`: five selected modeling references, never a collage upload.
- `ANATOMY_GUIDE.md` and `anatomy_targets.json`: proportions, all regions, rigid/flexible structures and stress poses.
- `ANIMATION_STUDY.md` and `motion_spec.json`: all timed anchors, both arm chains, palm/finger orientation,
  body/head/support, prop constraints, secondary response, curve spacing and verification targets.
- `source/`: aligned native frames, complete action contacts, original palettes, descriptor rows, existing
  original 2D landmark seeds and retained generation inputs.
- `guides/`: native anatomy callouts/coordinates, landmark overlays, all-action overview and selected-view review.
- `raw/` and `generation_runs.json`: selected and superseded imagegen returns/provenance.
- `meshy_handoff.json`, `creature_3d_progress.json`, `visual_review.json`, `verification.json`: handoff and stage audit.

Images and studies are self-contained in the ZIP. Rebuilding the preserved native inventory requires this
repository's existing native BMP decoder/source archive; no service call is part of either helper:

```sh
python3 level_generation/creatures/new_sorpigal_3d_stage1_20261006/author_studies.py
python3 level_generation/creatures/new_sorpigal_3d_stage1_20261006/build_stage1.py finish
```

The final check binds every anchor to native names/time/order, verifies selected images against raw returns,
checks RGBA alpha and unclipped framing, binds progress to selected artifact hashes, and verifies ZIP CRC.
