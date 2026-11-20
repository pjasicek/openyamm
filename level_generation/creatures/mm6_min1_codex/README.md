# MM6 BMinotaur — review round 3, closed hips

The hip/crotch/upper-thigh skin is now continuous at every colour and shadow LOD. Empty-bake UVs along the cut rims
now sample opaque fur from the existing atlas. All accepted animation channels, texture images, the axe and
integration/actors.yml are unchanged. **Shared gates still FAIL; this is a staged geometry repair, not full technical completion.**

[Handoff, hashes and counts](HANDOFF.md) · [hip review](review/round3/closed_hips_viewer.png) ·
[geometry receipt](review/round3/geometry_receipt.json) · [shared comparison](review/round3/GATE_COMPARISON.md) ·
[viewer](review/viewer/index.html). Viewer 27/27; bindings no BAD. Budget **30/100 credits**, zero this round.

Unattended decisions: preserve every accepted curve and original body vertex; add the smallest connected hip patch
at each LOD using the pre-trim anatomical cross section; weight new vertices to pelvis/thighs; reuse opaque fur UVs
instead of changing texture files. Retain the kilt's intentional hem/waist openings and existing two-sided material.
Required closure increases body triangles to **7995/1743/1660/781** (including identical shadow counts).
The previous-count caps remain unchanged in gates.json and correctly flag this increase; no further reduction was requested.

Canonical master: work/production_master.blend. Lower masters: work/round1_lod1.blend through round1_lod3.blend.
With a reclaimed lease, export using the four-thread Blender wrapper on scripts/round3_export.py, then run
scripts/round1_pack_maps.py, scripts/round1_assemble_lods.py and scripts/finish_export.py through the workspace wrapper.
Use the shared gate runner with gates.json, scripts/validate_exports.py, check_bindings.py and shared check_viewer.mjs.
The round3 repair script starts from immutable round-2 backups and is separate from ordinary re-export.
Do not rerun the old round2 motion/export producers: they replace the repaired masters. The old hidden-skin deletion
script is retired and rejects use because it violates the closed-body rule.

No install, game launch, build or commit. The orchestrator owns integration; ../mm6_min1/ is read-only source material.
