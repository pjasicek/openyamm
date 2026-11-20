# KnightPlate lessons for orchestrator review

- Keep the source animation bone frames and fit joint locations to the Meshy body. Wrist/elbow placement, finger
  connectivity and source grip axes mattered more than adding correction rotations. The fitted rig has 52 source
  bones, four twist helpers and Sword/SwordTip; Meshy rigging supplied the anatomical starting point and weights.
- Rigid skull pauldrons follow clavicles. Bracers follow forearm twist. The decorative neck curls follow Neck;
  mistaking elbows or curls for head geometry caused false ownership and avoidable collisions.
- A plate fauld cannot use soft trouser weights. Split the existing shell into an overlapping pelvic band and two
  thigh-mounted tassets; keep the upper trousers inside those panels. Preserve the lower exposed trousers.
- Open/disconnected armour makes a nearest-face-normal test unreliable. Confirm candidate interior points using
  multiple ray exits. A genuine blade/helmet collision survived that confirmation and required a roll correction.
  A covered-thigh test must use its intended tasset, excluding the exposed leg below the hem and unrelated panels.
  These are scoped contact checks, not a proof against every possible triangle intersection or runtime head offset.
- Choose the blade roll from its actual swept mesh and cutting-edge velocity. The selected +48° correction clears
  the helmet; the fastest target-facing blow at 0.71875 s has positive edge lead 0.654 and edge share 0.662.
  There is no claim that its edge share exceeds 0.75. Weapon carry/turn samples are retained for every other clip.
- Standing Taunt Battlecry conflicted with this armour. Standing Idle 02 Looking gives a quieter, upright Fidget.
  Attack/Fidget keep a planted stance with about 20% discrete leg motion. Ground Hit using the actual boot soles;
  preserve Running's authored flight phase. Relax the free-hand fingers independently from the weapon grip.
- A sealed helmet does not justify a separate head-only texture job. One 2K body colour atlas plus 1K detail maps
  covers this character. Meshy deduplicated overlapping tasset faces: 74 faces required bounded barycentric UV
  transfer, localized to the three known fauld pieces. The fitted geometry and animation were never replaced.
- PNG colours recover native palette colours, but do not always recover the original palette index. Native A
  RGB 8/8/8 and 12/12/12 each correspond to two indices with slightly different B/C near-black values. Record this
  uncertainty; never describe RGB matching as exact indexed-source recovery. Other visible palette colours match.
- Review anchors must separate animation phases from camera directions: native attack/hit/death/fidget have only
  frontal images. Walking has five stored directions per phase. Label approximate normalized timing explicitly.

No shared playbook was edited during the batch.

## Review round 1 — weapon fidelity

- The user accepted the body but rejected a low-detail weapon. Make the prop a separate design task: native-frame
  imagegen side/three-quarter reference, then bevel/fullers/guard/wrap/pommel geometry and detailed texture.
- The 2,292-triangle hand model preserves the accepted Sword attachment and exact tip. Do not alter an accepted
  rig or clip set merely to replace its prop. Check blade-only contact separately from the intentional fist/grip.
- Meshy original-UV retexture preserved UVs exactly per triangle corner. Retain our mesh, use only returned maps,
  and grade shared steel to dull grey across all tiers. MR red must survive glTF export for specular masking.
- A 1.717 mm hidden grip/cuff contact during Death remains below the existing 2 mm allowance; blade and hand
  furniture contacts are zero. Report those separately instead of claiming the entire sword has zero contact.
- Final LOD3 has 180 glTF triangles rather than Blender's 182: export drops two degenerate triangles. Count exports.


## Review round 2: measured triangle reduction

See `../review/round2/README.md` and HANDOFF's Triangle reduction section. Combined LOD0 drops 15,107 → 13,085
triangles, with eight-view IoU/SSIM gates and independent switch-size fitting of the accepted LODs. Preserve glTF
seams during decimation: welding damaged normals/UV interpolation. Do not classify nearest points on exposed
armour or panel boundaries as penetration without a closed-volume/interior-panel test.

New strict audits expose accepted baseline findings: Attack's elbow-plane deviation (13.735° left / 26.146° right)
and coarse LOD3 G4 p99 2.89×. Clip/skeleton/palm data are bit-exact; repairing the accepted animation is outside
this geometry-only round. These findings are recorded, not reported as all-pass. Bindings remain unchanged.
