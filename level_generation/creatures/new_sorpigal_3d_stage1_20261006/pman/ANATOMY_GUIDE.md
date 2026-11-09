# MM6 male town peasant, pman; descriptors 607–609: anatomy guide

Native logical pixels, body height H from crown/helmet to visible standing sole, excluding prop. Approximate projected ranges for comparison, not recovered 3D anthropometry. Keep one bottom-center pivot and comparison scale; do not independently normalize each native frame.

**Submission:** Empty-handed neutral A-pose; original handheld weapons/staff omitted. Attached clothing and accessories retained.

[Reviewed AI views](guides/selected_views_review.png) · [Native anatomy callouts](guides/anatomy_native.png) · [Native coordinates](guides/anatomy_coordinate_review.png) · [All native palette views](source/generation_inputs/native_variants.png)

## Proportions

Standing body H ≈ 253 native pixels; crown/helmet y≈1, visible sole y≈254. The prop is excluded.

| Projected measurement / H | Fitting range |
| --- | --- |
| head over H | 0.13–0.17 |
| shoulder width over H | 0.27–0.33 |
| belt height above floor over H | 0.57–0.64 |
| tunic hem height over H | 0.4–0.45 |
| profile shoe length over H | 0.12–0.16 |

## Skull Face Ears

**Native observation:** Adult clean-shaven angular face, ordinary rounded skull, short reddish-brown hair; exposed ears, plain brow, modest projecting nose, defined chin. No headgear.

**Construction/model checks:** Retain front width and profile depth together; verify brow, eye spacing, nose projection, jaw/chin and ear location in front/left/right. Native pupils, teeth and ear interior are unresolved; choose restrained human construction. Inspect the selected render, do not treat a written prompt as evidence.

**Deformation:** Head follows neck; eyes/gaze and jaw separate if supported. Hair/beard/coif must not weld jaw to chest.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Torso Shoulders Neck

**Native observation:** Slim ordinary shoulders, green short V-neck tunic with short sleeves and brown elbow cuffs, wide brown waist belt with round front buckle; tunic notch/splits to upper thighs. Bare forearms.

**Construction/model checks:** Keep distinct clavicle, shoulder ball, elbow and wrist chain. Avoid arm-to-torso bridges, neck spikes, inverted armpits or flattened rear volume. Match torso depth in both side views and shoulder width in native standing.

**Deformation:** Shoulder rotation must preserve torso volume; garment flex around armpit, neck remains clear.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Hands Fingers Thumb

**Native observation:** Visible human palms/knuckles; held/fisted native poses obscure digit count.

**Construction/model checks:** Ordinary human hand construction selected: four fingers plus opposed thumb, four knuckle chains, broad palm tapering at wrist. Preserve individual tips/web gaps, thumb base, palm thickness and enough edge flow for grip/open fan. Native pixels cannot prove exact phalanx shapes. No extra/missing/fused digits.

**Deformation:** Separate forearm roll from wrist flex; fingers curl around prop or touch other hand, never pass through palm. Test closed grip, open palm, pronation/supination and thumb opposition.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Pelvis Hips Knees

**Native observation:** Visible leg/foot silhouettes; hip/knee depth and covered joints partly or fully hidden.

**Construction/model checks:** Keep an actual pelvis and two separate fixed-length leg chains under clothing. Native visible groin/foot seeds can guide fitting; hidden femurs, knee centers and hip depth remain inferred. Inspect underside, crossings and disconnected inside shells.

**Deformation:** Hip flex, knee flex and foot plant must work together. Cloth has its own weights; trousers follow legs, skirt never locks both legs as one limb.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Feet Ankles Soles

**Native observation:** Long relatively slim beige trouser legs, cloth folds at knees/ankles, brown low closed shoes with rounded toes and low heels. No boots, leg armor or bare toes.

**Construction/model checks:** Match profile toe reach, heel length, low heel height, ankle placement and sole thickness. Closed footwear hides anatomical toes; do not add toe cutouts. Both shoes need complete underside and flat support surfaces, not melted heels or razor soles.

**Deformation:** Ankle dorsiflexion/plantarflexion and toe-off must preserve shoe volume. Test heel contact, flat foot, toe contact and clear swing without sliding.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Clothing Fasteners Props

**Native observation:** Separate small straight dagger/knife used by the right hand only during native attack. Standing/walk/hit/fidget are empty-handed. Whole blade and grip omitted from body submission; do not model an always-present sword or knife fused to fingers.

**Construction/model checks:** Keep body and handheld prop geometry separate. Attach belt/knot/buckle to waist, not abdomen skin stretching; match strap/pouch count and native coverage. Make broad silhouette folds geometry, tiny weave/mail grain surface detail.

**Deformation:** Rigid prop/socket follows grip; fixed shaft/blade length. Secondary hand constrains same shaft, not an independently animated copy.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Secondary Surfaces

**Native observation:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length.

**Construction/model checks:** Preserve clothing/hair coverage while keeping joints and negative spaces readable. Never simulate away a native silhouette mismatch. Check front/side/back and both extreme and intermediate poses.

**Deformation:** Use restrained lag and damped settling; exact simulation parameters are not recovered from six sprites.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Palette Material Boundaries

**Native observation:** 798 green tunic, 799/800 native alternate garments/palette ramps retained in native_variants.png. Preserve brown belt/cuffs/shoes, beige trousers, skin and reddish hair.

**Construction/model checks:** Retain clear cloth/leather/skin/metal boundaries and compare all native variants. Generated unseen detail is inference. Do not bake studio highlights, invented embossing or color spill into final geometry.

**Deformation:** Material boundaries remain stable as surfaces deform; texture and UV authoring follows accepted geometry and animations.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Family-specific ingest check

Keep this a plain peasant: no leather breastplate, cape, pouch, beard or heroic shoulder expansion. AI seam stitching and grain clarify manufacture; they do not authorize new clothing coverage.

## Rig stress poses

- right shoulder cross-body thrust
- right forearm across eyes, left palm out
- deep asymmetrical protective crouch
- side fall with one straight leg
- wide prone corpse

Compare each with native action contacts before approving the rig. Repair anatomical shape/topology before weight tuning; an intact low-triangle mesh can still have wrong anatomy. Stock walking/running are diagnostic only; no native running sequence exists.
