# MM6 Merchant (mer1)

**Review round 3 staged — QA HOLD.** Face/hands restored with protected geometry and separate fresh skin sets.
Shoulder stretch and sleeve-cuff containment pass on every clip/LOD. Full shared checks still have
110 FAIL rows; technical completion is false. [HANDOFF.md](HANDOFF.md) records exact
hashes, remaining faults and the cloth-cap diagnostic without waiving failures.

[Face before/after](review/round3/face_before_after.jpg), [hand before/after](review/round3/hand_before_after.jpg),
[shoulders](review/round3/shoulder_closeups.jpg), [clip sheets](review/round3/),
[reduction evidence](review/round3/reduction/README.md).

Unattended decisions: preserve 4,946 head and 3,010 hand triangles at LOD0; reduce only clothing to 6,998.
Use separate 1K head / 512px hand / 2K clothing maps, shared across LODs. Reuse adequate round-2 HD references;
spend 10 credits on each new skin retexture. Retain exact head/hand UVs outside the clothing bake, and replace
mottling-producing rank grading with gentle linear skin exposure. Correct false garment flaps caused by excessive
tangent normals, fit shoulder weights to retained library poses, preserve every closed trouser face, and keep
Jogging, the accepted club and its attachment scheme. No threshold was raised to clear these new failures.
The optional old total LOD0 count cap is superseded by the user's explicit protected head/hands instruction.

Body counts: 14954 / 2399 / 1727 / 682; club: 1122 / 290 / 252 / 200, unchanged binary.
Authoritative sources: work/round3/master.blend, work/round3/body_lod0..3.blend,
work/round3/shared_textures and review/reduction/selection.json. Editable/portable/runtime outputs are in export/.

Bindings: no BAD line. Viewer: 24/24 switches, no errors. actors.yml changed its comment only; scale/stride/socket
semantics are unchanged. These checks do not clear the contact and numerical visual findings.

Budget: 20 this round, 80/100 total, 20 remaining; no pending paid jobs. No installation, game/build or commit.
The orchestrator owns integration after reviewing or resolving the open findings.

## Installed (2026-10-15)

The club's texture-size pass (2026-10-13, HANDOFF.md) had never reached `assets_source`;
`tools/install_model.py export/mm6_mer1_club.glb --world mm6`. Previous source: `work/pre_install_20261015/`.
