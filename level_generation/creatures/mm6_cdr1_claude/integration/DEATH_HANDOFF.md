# MM6 Dragon death handoff

Family `mm6:cdr1`; descriptors DragonCover A/B/C; merged IDs 514–516.
The user assigned dying effects and their engine integration to another session. No burn maps or death-effect binding are authored here.

- Editable source: `../export/mm6_cdr1.blend`; runtime asset `worlds/mm6/models/mm6_cdr1.glb`.
- Materials: DragonBody_A, DragonHead_A, DragonWings_A, with shared tier ramps cdr1_a/b/c.
- Native sequence: cdr1dea0…cdr1deg0, seven held frames, 1.5 seconds; cdr1deh0 is remains. Native files under `../../mm6_cdr1/native/`; enhanced sprites already exist for comparison.
- Death: 1.5-second recoil/curl/slump cue. Dead freezes its final pose. These do not themselves reproduce burning/disintegration or charred remains.
- Mouth socket: Socket_Mouth. Rig has separate wings, head/jaw and nine tail controls.
- Keep the living mesh/UVs/weights and approved reduction; add material burn maps and the intended visibility/remains track using the shared effect support. Recheck death→dead→satchel and state reset in engine.

Current Death/Dead in the web viewer are explicitly provisional skeletal previews. Living creature delivery and tier bindings do not certify the death appearance.

**Done 2026-10-13 (burn-effects session):** burn maps, `death_effect: burn` binding and a burning Death/Dead clip
(recoil, airborne thrash, collapse to the ground) are installed; the burnt-out corpse draws nothing and the satchel
takes over. See the README section "Burning death".
