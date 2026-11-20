# MM6 Goblin interactive animation review

Open <http://127.0.0.1:8901/level_generation/creatures/mm6_goblin/review_20261006/>.
If the server is stopped, run from the repository root:

```sh
python3 -m http.server 8901 --bind 127.0.0.1 --directory /home/pjasicek/github/OpenYAMM
```

Select an animation, pause, and step or scrub to the relevant pose. Frames start at **0**. The page displays both
the exact time and the chosen 48 or 192 fps frame index, including the final endpoint. Changing the frame-step
rate preserves the pose. Orbit/zoom/pan or choose a front/profile/rear camera and a detail focus.

Choose **Highlight area**, drag a rectangle, and enter a note. **Copy feedback** includes the exact clip/time,
model hash, camera and highlights in a link that restores the pose. **Screenshot** downloads a marked PNG with
the frame/time caption. **Save note** keeps multiple poses in this browser; **Copy all notes** or **Download notes**
provides the feedback to send back. Saving a note does not write to the repository or send it to Codex.

The seven previous clips remain: Standing, Walk, Attack, Hit, Death, Corpse and Fidget. The native source images
and pose buttons are available beside those clips. Walk is explicitly labelled the previous reconstruction.
**Meshy Walk** and **Meshy Run** are new comparison candidates using the already downloaded Meshy clips on the
same corrected, textured rig, with closed sword fingers/thumb. They retain stock provenance and preset timing;
they are not a reconstruction of native goblin walking or a native running animation.

The retained **Face / neck · R4** corrects the head/neck geometry and demonstrated chin weight leakage.
Switch to **Previous model** for a comparison at the same animation time and camera. The expanded comparison
includes original sprite crops and identically rendered before/after views. See the [anatomy revision](../anatomy_20261006_r1/README.md)
for the diagnosis, selected files and checks. Skirt and attack defects remain so exact feedback can identify them. This
workspace is a review handoff, not an accepted final model. The six open findings and eight original annotated
screenshots are retained in [user_feedback.json](feedback/user_feedback.json). Head/neck likeness is pending review of the revised candidate; skirt fit, wrist
and sword-path continuity, hand/cloth contact and the adapted gait still require revision. Existing
floor/rotation/export checks do not establish artistic acceptance or coherent motion.

The original delivery and its package remain unchanged. [goblin_review.blend](goblin_review.blend) is an editable
comparison master; [goblin_review.glb](goblin_review.glb) is the previous model. The default is now [the R5 export](../anatomy_20261006_r5/goblin_anatomy_r5.glb); all three versions remain available through the model selector. The canonical progress record remains
[the existing production record](../stage1_20261006/creature_3d_progress.json), with stages 2 and 3 marked
`needs_revision`. No new Meshy job was submitted; the original FULL run remains at **20 / 100 credits**.

Validation: [browser_validation.json](browser_validation.json) records 43 browser checks, including all nine
clips, exact endpoints, rate changes, annotations, restored camera/frame links and mobile layout, with no
uncaught exceptions or failed HTTP requests. [preservation_check.json](preservation_check.json) checks unchanged
mesh/topology/UV/weights/bind buffers, all four PNG images, material factors and every channel/sample of the
seven original animations. The comparison export also carries an existing pommel-correction metadata note.
The original preservation report concerns `goblin_review.glb`; [the anatomy preservation report](../anatomy_20261006_r1/review/preservation_checks.json)
checks R4. These checks verify the page and preserved assets; they do not clear the reported defects.

Recheck the controls with:

```sh
node level_generation/creatures/mm6_goblin/review_20261006/scripts/check_viewer.mjs
```

This uses headless Chrome and Node's standard library, writes screenshots/report under
`/tmp/openyamm-goblin-viewer-check`, and requires the local server. The page uses a pinned local copy of
[Three.js 0.186.1](https://github.com/mrdoob/three.js/releases/tag/r186) with its retained
[MIT license](vendor/LICENSE); no CDN or build step is needed. GLB playback uses the standard
[GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html) and
[AnimationMixer](https://threejs.org/docs/pages/AnimationMixer.html).

Latest refinement: [Brow / jaw · R5](../anatomy_20261006_r5/README.md) reduces the projecting brow and refines the lower-face contour. Neutral hand/foot views document the outstanding side anatomy differences. Select R4 versus R5 for the current comparison; the original is retained for older feedback links.
