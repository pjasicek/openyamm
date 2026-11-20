# Creature calibration: m242 ghost

The driver judged the restored-reference body revision materially much better on 2026-09-07. The
[reusable sprite-to-3D workflow](../SPRITE_TO_3D_WORKFLOW.md) consolidates the working procedure for future creatures.
This file retains the correction history; later findings supersede earlier recommendations where they differ.

## Feedback from test_img/1250.png

The first model matched the semantic inventory (hood, skull, ribs, skeletal hands, brown robe), but missed the
reference's character. A successful rig/export did not make its appearance successful.
The front comparison exposed an oval hood, large circular eye sockets, an even smiling tooth line,
stick-like exposed ribs, a narrow continuous robe and weak hands. These read as a friendly costume/simplified toy.

Before accepting a creature model, compare equal-height front, three-quarter, profile and back images to the
actual sprite family. Also compare a matching expressive pose. A neutral pose versus an attack pose is insufficient
for judging the silhouette. Check these in diffuse material light as well as rendered light; dramatic lighting must
not conceal an unsuitable model.

For this ghost, prioritize:

- A gaunt, elongated skull with angular recessed orbits, narrow irregular teeth, hollow cheeks and a restrained jaw.
  Avoid circular black patches, a broad grin, or exaggerated angry eyebrows as substitutes for skull anatomy.
- A pointed close-fitting hood and a continuous cloth connection to the hunched shoulders.
- Broad, irregular, overlapping cloth masses with diagonal tears and long points. The mid-body silhouette matters
  as much as the bottom hem; a regular fringe on a smooth cylinder is insufficient.
- Dense thin curved ribs, partial occlusion by the cloak, and dark negative space inside the body.
- Articulated hooked fingers and bent wrists. Fingers should read as grasping claws rather than flat paddles.
- Weathered dark brown cloth and muted aged bones. Color changes alone do not solve a silhouette mismatch.

Revision 2 adds these features and retains the first `.blend` and comparison image in `revisions/v1/`.
The model remains an authored approximation, not a recovered original mesh.

## Animation calibration

Legacy sprite frames specify recognizable key poses and event ordering. Their low frame count is not a good default
for a freely viewed 3D animation. Raising a playback FPS alone merely makes the same clip faster.

Revision 2 uses 69 authored geometry/rig anchor poses, sampled into seven clips at 24 fps (218 timeline samples).
It adds a moving idle, a closed floating loop, attack anticipation, a fast reaching stroke, recovery, finger curling,
and cloth motion offset along the body. Death starts with recoil and proceeds to collapse; the corpse is a hold.
The dense animation contains interpolated bone motion and cloth corrections, not duplicated rendered frames.

Check motion at real playback speed, including intermediate poses and the loop seam. Verify that added samples
preserve the intended duration. Check hands against the robe, ground clearance during collapse, and framing at
maximum arm extension. Keep bone and cloth actions synchronized. Prevent parent body compression from stretching the arm chains;
validate actual posed bone matrices at extreme scales as well as the intended joint targets. A renderer/export that requires morph targets
must retain them; dropping them changes this character's cloth animation.

Check between source anchors as well as on them. A global Z-up bone tracking frame flipped its roll near a vertical
raised arm: the exact poses were correct, but interpolated sleeves flared into wings. Use continuous rest-relative
bone swing and linear source sampling; compare evaluated intermediate surfaces to the intended geometry. Save named
clips before the long render pass so a Blender interruption can resume from an explicit checkpoint.

The portable atlas, rig weights and seven clip names receive quick structural checks. Visual comparison and motion
review are the acceptance gates; adding map scenario runners does not improve this isolated asset review.


## Revision 3: restore references before modeling

The user identified that the original skull appears largely intact, whereas the revision 2 face looked assembled from
separate bones. A pointed silhouette and angular sockets did not fix missing anatomical surfaces.

Use the imagegen skill/built-in tool to restore original multi-view and representative pose references before another
shape redesign. Keep original colors during restoration so material identity is easy to compare. Treat new detail as
interpretation and correct pose drift against the original sprite; the restored hit and dying-hand sheets both needed
such corrections. See `reference_restoration/README.md` and its prompt files.

Model continuous cranial, forehead, cheek and maxillary surfaces around carved cavities. Preserve the mandible and
normal small teeth. The revision 3 sculpt has one connected skull/jaw shell plus 18 separate teeth; its connectivity
report is in `sculpt/connectivity.json`. Facial outlines made of rods are no substitute for those bone surfaces.

Surface color can be projected from the restoration onto the real mesh for a prerendered-game appearance. Retain
original projection UVs under animation and bake an export atlas afterward. Do not paint a profile socket next to an
actual geometric socket: that produces two eyes in a three-quarter view. The final shader uses restored frontal color
and fades to neutral bone on the sides/rear; the profile reference guides geometry. The restored image includes baked
shading, so this texture treatment should not be presented as a physically neutral scan.

## Body calibration from the restored poses

The driver accepted the connected skull, then requested the same reference-driven process for the entire body.
This later calibration replaces the revision 2 preference for bulky overlapping cloth panels and uniformly hooked
resting fingers. Follow the restored pose being modeled, rather than carrying those earlier corrections forward.
Use `reference_restoration/standing_views_v1.png` and `action_poses_v2.png` to judge exposure and silhouette:

- The resting silhouette is long and comparatively narrow. Cloth falls from shoulders to torn hems in continuous
  folds; stacked triangular panels made the previous mesh look armored and bulky.
- The standing ribcage is visible through a narrow V, with much of the thorax hidden by the robe. Ribs curve around
  the chest and meet a flattened sternum; straight diagonal rods exaggerate the chest opening.
- The robe covers the upper arms. The visible forearms contain two thin bowed shafts with broader joint ends.
- Hands rest across the robe with long descending articulated fingers. Upward zigzags produced pointed tent-like
  shapes rather than skeletal anatomy. Attack fingers open into a fan above the head.
- Match bone color across head, ribs, limbs and hands, retaining cavity shadows and darker joint patina. Spatial
  mouth-shadow classification must exclude tooth components; it had incorrectly blackened the lower enamel.
- Material wear is woven fiber and irregular fraying, not broad cloud noise. The brown cloth swatch was generated
  with the built-in image tool from the restored purple robe. Large folds and torn silhouettes remain geometry.

Review front, profile, rear and action poses after these changes. Keep the approved skull geometry fixed while
iterating on clothing and limbs. Use visual and structural asset checks, not unrelated map scenarios.

## Material consistency and hood clearance: test_img/1252.png

The next close-up identified teeth, hands and ribs as visibly different from the skull, and an oversized hood opening.
A broadly similar ivory palette was insufficient: the face had restored surface detail and contrast, while the
procedural bones had strong coarse bump and a pale, chalky response. Teeth also read as a separate uniform insert.

The exposed skeleton and teeth now sample bone pigment from a forehead surface region in `skull_detail_v1.png`.
The head retains its feature-specific projection; both material paths share the finer relief and satin response.
Sample surface-only regions so eyes, teeth or other recognizable features are not painted onto unrelated anatomy.
Preserve the separate cavity classification to avoid reintroducing blackened enamel.

The hood opening's base half-width was reduced from .225 to .175 Blender units and its vertical radius from .325 to
.270; crown volume and rear depth were reduced as well. The skull geometry and proportions remain unchanged.
Check the fit in front and profile: allow cloth thickness and a small shadowed clearance without a large empty halo
around the head. Preserve the hood's folds rather than treating it as a rigid skin-tight shell.

The previous body/material state is preserved in `revisions/v3_body_accepted/`. Review the delivered baked material,
including `review/material_fit_final.png`, because a source material match can be softened or altered during baking.
