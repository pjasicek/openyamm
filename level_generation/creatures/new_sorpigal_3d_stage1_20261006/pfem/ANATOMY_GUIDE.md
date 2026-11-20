# MM6 female town peasant, pfem; descriptors 595–597: anatomy guide

Native logical pixels, body height H from crown/helmet to visible standing sole, excluding prop. Approximate projected ranges for comparison, not recovered 3D anthropometry. Keep one bottom-center pivot and comparison scale; do not independently normalize each native frame.

**Submission:** Empty-handed neutral A-pose; original handheld weapons/staff omitted. Attached clothing and accessories retained.

[Reviewed AI views](guides/selected_views_review.png) · [Native anatomy callouts](guides/anatomy_native.png) · [Native coordinates](guides/anatomy_coordinate_review.png) · [All native palette views](source/generation_inputs/native_variants.png)

## Proportions

Standing body H ≈ 251 native pixels; crown/helmet y≈0, visible sole y≈251. The prop is excluded.

| Projected measurement / H | Fitting range |
| --- | --- |
| head over H | 0.13–0.17 |
| shoulder width over H | 0.24–0.29 |
| belt height above floor over H | 0.61–0.66 |
| skirt hem height over H | 0.08–0.13 |
| profile shoe length over H | 0.12–0.16 |

## Skull Face Ears

**Native observation:** Adult oval face, modest nose/chin, brown hair with low nape tie/braid; narrow forehead band. Side and rear art establish nape hair, not a tall bun or long loose mane. Ears partly exposed.

**Construction/model checks:** Retain front width and profile depth together; verify brow, eye spacing, nose projection, jaw/chin and ear location in front/left/right. Native pupils, teeth and ear interior are unresolved; choose restrained human construction. Inspect the selected render, do not treat a written prompt as evidence.

**Deformation:** Head follows neck; eyes/gaze and jaw separate if supported. Hair/beard/coif must not weld jaw to chest.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Torso Shoulders Neck

**Native observation:** Green square-neck bodice over pale short puff sleeves, modest proportions, narrow brown belt with small rectangular front buckle. Long pale pleated skirt with two green bands separated by pale stripe around hem.

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

**Native observation:** Most thighs and knees are hidden by skirt. Visible ankles and simple brown closed shoes with thin ankle fastening; rounded toes and low heel. Ordinary two legs/five toes per foot are construction inferences, not resolved sprite digits.

**Construction/model checks:** Match profile toe reach, heel length, low heel height, ankle placement and sole thickness. Closed footwear hides anatomical toes; do not add toe cutouts. Both shoes need complete underside and flat support surfaces, not melted heels or razor soles.

**Deformation:** Ankle dorsiflexion/plantarflexion and toe-off must preserve shoe volume. Test heel contact, flat foot, toe contact and clear swing without sliding.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Clothing Fasteners Props

**Native observation:** Separate small right-hand dagger appears during native attack and is absent in standing/walk/fidget. Omit it entirely from body submission. The attack grip must later be poseable without welding fingers to blade.

**Construction/model checks:** Keep body and handheld prop geometry separate. Attach belt/knot/buckle to waist, not abdomen skin stretching; match strap/pouch count and native coverage. Make broad silhouette folds geometry, tiny weave/mail grain surface detail.

**Deformation:** Rigid prop/socket follows grip; fixed shaft/blade length. Secondary hand constrains same shaft, not an independently animated copy.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Secondary Surfaces

**Native observation:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag.

**Construction/model checks:** Preserve clothing/hair coverage while keeping joints and negative spaces readable. Never simulate away a native silhouette mismatch. Check front/side/back and both extreme and intermediate poses.

**Deformation:** Use restrained lag and damped settling; exact simulation parameters are not recovered from six sprites.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Palette Material Boundaries

**Native observation:** 786 green bodice/hem bands; 787/788 native alternate ramps retained in native_variants.png. Preserve pale sleeves/skirt, brown belt/shoes, natural skin and hair. No apron, lacing, lace ornaments or jewelry.

**Construction/model checks:** Retain clear cloth/leather/skin/metal boundaries and compare all native variants. Generated unseen detail is inference. Do not bake studio highlights, invented embossing or color spill into final geometry.

**Deformation:** Material boundaries remain stable as surfaces deform; texture and UV authoring follows accepted geometry and animations.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Family-specific ingest check

Long dress is essential identity. Never shorten it, add a thigh slit, invent tight trousers, or fuse both hidden legs into a single skirt pillar for auto-rigging. Inspect model underside and hip topology before sending for a rig.

## Rig stress poses

- both hands folded in front without merging
- right-hand cross-body blade reach
- forward abdominal recoil
- deep kneeling fall and hands toward floor
- spread skirt in prone corpse

Compare each with native action contacts before approving the rig. Repair anatomical shape/topology before weight tuning; an intact low-triangle mesh can still have wrong anatomy. Stock walking/running are diagnostic only; no native running sequence exists.
