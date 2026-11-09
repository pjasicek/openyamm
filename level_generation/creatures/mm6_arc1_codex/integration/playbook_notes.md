## Review round 5

Native side: forward tip +18 degrees, string ABOVE the limbs. Wrist/grip offsets 5.86%/7.94% of height. Shooting has fixed flat ankle anchors and reach-constrained pelvis. HANDOFF.md records memory tradeoff and unresolved gates.

> Review round 4 supersedes the carry/rest pose below. See [current handoff](../HANDOFF.md); shared runtime gates remain FAIL.

# Arc1 production lessons for the integrator

- Choose local clips by their visible action. The humanoid BowAttack1 is a swipe; this archer uses Mixamo draw/recoil.
  Attack, Cast and Death retain library motion. The quiet native rest/Fidget are authored to fill the rest-pose gap.
- A source-frame rig, connected finger chains and twist helpers retain anatomical elbows during reposing.
  Measure signed elbow flexion, not just its unsigned angle.
- Fit the gripping fingers first and solve the Bow attachment in the hand frame. Test palm and all five digit
  surfaces against the actual wrap at 48 Hz, including every carry and recovery frame.
- A vertical bow needs a clear plane and an outward arm path while its long lower limb passes the calf.
  Rotating only the wrist can produce a correct rest pose but failed transitions.
- Open shoulder flaps and a double-sided open quiver lip are not solid half-spaces. Confirm signed nearest-surface
  candidates with multiple ray-parity directions; report the method and keep direct visual checks.
- Use a distinct Cast action containing the bow-shot channels for a spellcasting archer. WorldFxSystem rejects
  Cast bound to the same clip name as Attack even when the desired motion is identical.
- Fireball and arrows use the same measured 0.800 s release socket. There is no remaining palm event or palm gesture.
- Paint both bracers into shared maps and exclude them from cloth recolouring. The explicit review corrected a
  right-bracer omission in the HD reference without another paid texture task.
- Retain skin mean and highlight luminance against the native ramp; measure after all rebakes.
- Reduce geometry with protected fingers, joints, soles, silhouettes and hair/quiver contact. Reproject base colour,
  region masks, material channels and tangent normal detail from the unreduced source before judging appearance.
  A silhouette/SSIM pass alone does not prove rig safety: an earlier 5% cut increased Hit quiver penetration.
- Test all three actual region-ramp tiers and all eight views. Retain the last passing result at each switch size.
  Fit each distance mesh within the installed counts; keep the chain strictly decreasing. Record supplementary action-pose losses separately from the calibrated Standing selection test.
- The active textured Body object can use a datablock named Body.001 while an orphan Body datablock still exists.
  Transfer active object geometry and its UVs, not a mesh selected only by the datablock name.
- Blender import may use 24 fps while the authoring rig uses 30. Render action landmarks by seconds.
- The batch session owns only this project. Installation, builds and game captures belong to the orchestrator.

## Review round 1

The relaxed native rest and planted soles remain the baseline. Compare normalized arm angles, foot spacing and
body width against arc1sta0; floor min-Z alone does not prove that both heels and toes are flat.

## Review round 2

Closed carry contact, matching bracers, the distinct bow-shot Cast, measured gait and rebaked reduction are the
current handoff. See ../HANDOFF.md and ../review/round2/ for exact selected files, hashes and gate results.
