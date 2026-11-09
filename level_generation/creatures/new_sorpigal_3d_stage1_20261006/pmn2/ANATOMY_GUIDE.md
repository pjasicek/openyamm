# MM6 staff-carrying mage, pmn2; Apprentice/Journeyman/Mage descriptors 610–612: anatomy guide

Native logical pixels, body height H from crown/helmet to visible standing sole, excluding prop. Approximate projected ranges for comparison, not recovered 3D anthropometry. Keep one bottom-center pivot and comparison scale; do not independently normalize each native frame.

**Submission:** Empty-handed neutral A-pose; original handheld weapons/staff omitted. Attached clothing and accessories retained.

[Reviewed AI views](guides/selected_views_review.png) · [Native anatomy callouts](guides/anatomy_native.png) · [Native coordinates](guides/anatomy_coordinate_review.png) · [All native palette views](source/generation_inputs/native_variants.png)

## Proportions

Standing body H ≈ 257 native pixels; crown/helmet y≈15, visible sole y≈272. The prop is excluded.

| Projected measurement / H | Fitting range |
| --- | --- |
| head including beard over H | 0.17–0.2 |
| shoulder width over H | 0.34–0.4 |
| tunic hem height above floor over H | 0.36–0.42 |
| boot top height over H | 0.19–0.25 |
| profile shoe length over H | 0.13–0.18 |

## Skull Face Ears

**Native observation:** Broad adult male skull, strong brow, square nose and jaw; full dark beard/moustache and nape-length dark hair. Ears emerge through side hair. No hat or hood.

**Construction/model checks:** Retain front width and profile depth together; verify brow, eye spacing, nose projection, jaw/chin and ear location in front/left/right. Native pupils, teeth and ear interior are unresolved; choose restrained human construction. Inspect the selected render, do not treat a written prompt as evidence.

**Deformation:** Head follows neck; eyes/gaze and jaw separate if supported. Hair/beard/coif must not weld jaw to chest.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Torso Shoulders Neck

**Native observation:** Sturdy broad shoulders and compact torso; bare upper arms; short green shoulder mantle, brown sleeveless leather tunic to upper thighs, rope waist tie and two green lateral hip pouches.

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

**Native observation:** Green trousers ending at dark knee-high leather boots; knees stay separate. Rounded long toes, low heel, flat sole and ankle bend; no pointed metal sabatons.

**Construction/model checks:** Match profile toe reach, heel length, low heel height, ankle placement and sole thickness. Closed footwear hides anatomical toes; do not add toe cutouts. Both shoes need complete underside and flat support surfaces, not melted heels or razor soles.

**Deformation:** Ankle dorsiflexion/plantarflexion and toe-off must preserve shoe volume. Test heel contact, flat foot, toe contact and clear swing without sliding.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Clothing Fasteners Props

**Native observation:** Separate long wooden staff with an irregular thickened upper end; right-hand grip. Native side view shows its true length. The body submission omits the whole staff. Do not replace it with a sword or add spell effects to native attack.

**Construction/model checks:** Keep body and handheld prop geometry separate. Attach belt/knot/buckle to waist, not abdomen skin stretching; match strap/pouch count and native coverage. Make broad silhouette folds geometry, tiny weave/mail grain surface detail.

**Deformation:** Rigid prop/socket follows grip; fixed shaft/blade length. Secondary hand constrains same shaft, not an independently animated copy.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Secondary Surfaces

**Native observation:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends.

**Construction/model checks:** Preserve clothing/hair coverage while keeping joints and negative spaces readable. Never simulate away a native silhouette mismatch. Check front/side/back and both extreme and intermediate poses.

**Deformation:** Use restrained lag and damped settling; exact simulation parameters are not recovered from six sprites.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Palette Material Boundaries

**Native observation:** 802 green mantle/trousers/pouches; 801 red and 803 blue variants. Protect dark hair/beard, natural skin, brown leather tunic, ochre rope, dark blue-black bracers/boots and wood.

**Construction/model checks:** Retain clear cloth/leather/skin/metal boundaries and compare all native variants. Generated unseen detail is inference. Do not bake studio highlights, invented embossing or color spill into final geometry.

**Deformation:** Material boundaries remain stable as surfaces deform; texture and UV authoring follows accepted geometry and animations.

**Confidence:** High visible coverage; medium proportions; low hidden depth/fine anatomy.

## Family-specific ingest check

Keep two pouches at the lateral hips: apparent front/back positions are projection, not four separate pouches. Match native head size before refining face. The AI weave/grain is illustrative surface detail, not new embossed ornament.

## Rig stress poses

- right elbow 90–130 degrees with staff grip
- both hands above brow under horizontal staff
- left palm opens in attack b/e; overhead shaft contact c/d needs fitting
- left leg lift during hit
- backward fall and supine corpse

Compare each with native action contacts before approving the rig. Repair anatomical shape/topology before weight tuning; an intact low-triangle mesh can still have wrong anatomy. Stock walking/running are diagnostic only; no native running sequence exists.
