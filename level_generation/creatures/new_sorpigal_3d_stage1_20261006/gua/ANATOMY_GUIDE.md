# MM6 New Sorpigal Guard A, gua; descriptor 553, palette 748; lieutenant/captain 554–555 are variants: anatomy guide

Native logical pixels, body height H from crown/helmet to visible standing sole, excluding prop. Approximate projected ranges for comparison, not recovered 3D anthropometry. Keep one bottom-center pivot and comparison scale; do not independently normalize each native frame.

**Submission:** Empty-handed neutral A-pose; original handheld weapons/staff omitted. Attached clothing and accessories retained.

[Reviewed AI views](guides/selected_views_review.png) · [Native anatomy callouts](guides/anatomy_native.png) · [Native coordinates](guides/anatomy_coordinate_review.png) · [All native palette views](source/generation_inputs/native_variants.png)

## Proportions

Standing body H ≈ 253 native pixels; crown/helmet y≈43, visible sole y≈296. The prop is excluded.

| Projected measurement / H | Fitting range |
| --- | --- |
| helmet plus coif over H | 0.17–0.22 |
| shoulder width over H | 0.28–0.33 |
| belt height above floor over H | 0.56–0.62 |
| mail hem height over H | 0.38–0.44 |
| profile shoe length over H | 0.12–0.17 |

## Skull Face Ears

**Native observation:** Compact rounded dark iron helmet with narrow nasal bar; small eye/face opening, mail around jaw/chin and nape. Side view retains nose/face clearance. No horns, plume or broad visor.

**Construction/model checks:** Retain front width and profile depth together; verify brow, eye spacing, nose projection, jaw/chin and ear location in front/left/right. Native pupils, teeth and ear interior are unresolved; choose restrained human construction. Inspect the selected render, do not treat a written prompt as evidence.

**Deformation:** Head follows neck; eyes/gaze and jaw separate if supported. Hair/beard/coif must not weld jaw to chest.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Torso Shoulders Neck

**Native observation:** Average solid human frame; warm bronze/brown short-sleeve mail hauberk to upper thighs, navy cloth sleeves to elbows, bare forearms/hands, brown waist belt and round front buckle.

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

**Native observation:** Dark teal trousers, plain low brown closed shoes with rounded toes and low heels. No plate greaves, knee plates or knee-high boots.

**Construction/model checks:** Match profile toe reach, heel length, low heel height, ankle placement and sole thickness. Closed footwear hides anatomical toes; do not add toe cutouts. Both shoes need complete underside and flat support surfaces, not melted heels or razor soles.

**Deformation:** Ankle dorsiflexion/plantarflexion and toe-off must preserve shoe volume. Test heel contact, flat foot, toe contact and clear swing without sliding.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Clothing Fasteners Props

**Native observation:** Separate long halberd: wood shaft, dark broad axe blade with projecting points/spike and blue binding near head. Side view reveals full length obscured by frontal foreshortening. Right carries it; left joins the shaft during attack. Body input omits shaft/blade completely. No shield or sword in this native family.

**Construction/model checks:** Keep body and handheld prop geometry separate. Attach belt/knot/buckle to waist, not abdomen skin stretching; match strap/pouch count and native coverage. Make broad silhouette folds geometry, tiny weave/mail grain surface detail.

**Deformation:** Rigid prop/socket follows grip; fixed shaft/blade length. Secondary hand constrains same shaft, not an independently animated copy.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Secondary Surfaces

**Native observation:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate.

**Construction/model checks:** Preserve clothing/hair coverage while keeping joints and negative spaces readable. Never simulate away a native silhouette mismatch. Check front/side/back and both extreme and intermediate poses.

**Deformation:** Use restrained lag and damped settling; exact simulation parameters are not recovered from six sprites.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Palette Material Boundaries

**Native observation:** 748 navy sleeves/teal trousers/warm mail. Native 749/750 alter sleeves, trousers, mail and other material ramps: inspect retained palettes rather than recolor the whole body with one tint. Helmet dark metal; wood and blade protected as separate prop.

**Construction/model checks:** Retain clear cloth/leather/skin/metal boundaries and compare all native variants. Generated unseen detail is inference. Do not bake studio highlights, invented embossing or color spill into final geometry.

**Deformation:** Material boundaries remain stable as surfaces deform; texture and UV authoring follows accepted geometry and animations.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Family-specific ingest check

Budget the body at approximately 15000 triangles; tiny mail rings belong to normal/base-color surface detail, not thousands of disconnected physical rings. Keep nasal bar away from the nose and coif clear of shoulder/neck pivots.

## Rig stress poses

- two-hand polearm grip with fixed shaft
- right overhead lift
- left open palm above head in hit
- backward knee buckle
- curled side/back corpse with head/coif clearance

Compare each with native action contacts before approving the rig. Repair anatomical shape/topology before weight tuning; an intact low-triangle mesh can still have wrong anatomy. Stock walking/running are diagnostic only; no native running sequence exists.
