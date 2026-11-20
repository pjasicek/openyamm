# MM6 Goblin A: anatomy and model-ingest guide

H=256 native pixels from topmost standing ear/crown at y=33 to logical bottom y=289. Ranges are manually estimated projected proportions, not recovered 3D dimensions. Compare silhouettes in native standing views 0..4 before fitting a 3D volume. AI views are appearance references, not calibrated orthographic scans.

**Submission**: Unarmed neutral A pose; sword remains a separate required animation prop.

[Selected views](guides/selected_views_review.png) · [Native detail crops](guides/native_details.png) · [Native standing views](source/standing_native.png) · [Annotated native anatomy](guides/anatomy_native.png)

## Silhouette

**Priority**: critical. **Confidence**: high for front/side silhouette; medium for muscle volume.

**Observed**: Bald lean muscular biped; broad shoulders taper to narrow exposed waist; long forearms and hanging clawed hands; thighs exposed below short skirt; plantigrade elongated feet. No tail, wings, horns or full torso armor.

**Inferred or selected**: Continuous plausible muscle volumes and neutral A pose. Surface pores/veins in the AI images are descriptive texture, not required geometry.

**Model checks**:

- Match head/torso/leg ratios before small surface detail.
- Inspect front, right profile and back against gobsta0/2/4 on common ground and scale.
- Preserve separate arm/torso, fingers, thighs and skirt gaps; remove accidental bridges.

**Deformation**: Smooth skin volumes at shoulder, elbow, hip and knee; rigid equipment must not define skin joint centers.

| Projected measurement / standing H | Range |
| --- | --- |
| crown to chin | 0.19–0.23 |
| shoulder width without spikes | 0.28–0.33 |
| waist width | 0.18–0.23 |
| chin to belt | 0.24–0.3 |
| belt to sole | 0.49–0.54 |

## Head

**Priority**: critical. **Confidence**: high for skull silhouette/brow/jaw; medium for mouth interior.

**Observed**: Compact sloping bald crown, heavy inward brow, recessed small yellow eyes, short broad nose, cheek hollows, projecting lower jaw/chin, visible irregular pale teeth. Profile rear cranium tapers to a short horizontal occipital wedge. Long exposed neck below jaw.

**Inferred or selected**: Actual eyelid thickness, tongue and inner mouth are inferred. The rear wedge is skull volume rather than an added horn. Selected neutral snarl has nearly closed jaw.

**Model checks**:

- No spherical toy head, giant round eyes or long dog muzzle.
- Check crown, brow, nose tip, lower lip, chin, ear roots and rear-skull contour in all native views.
- Use a real jaw hinge if opening is needed; avoid sliding entire face or jaw through gorget.

**Deformation**: Head/neck rotations remain distinct; jaw opening modest. Eyes stay seated in sockets.

## Ears And Jewelry

**Priority**: high. **Confidence**: high for ear silhouette and right-side jewelry; medium for exact hoop count.

**Observed**: Tall pointed fleshy ears rise beside temples and sweep backward in profile. Small gold hoops appear on anatomical right ear in front/right native views.

**Inferred or selected**: Three small right-ear hoops selected for reference consistency; individual hoop count is less certain than side and presence. Left ear has no visible corresponding jewelry. Inner ear folds and shell thickness inferred.

**Model checks**:

- Keep ear roots connected to skull with thickness; no paper-thin disconnected planes.
- Right-ear hoops must not migrate to left through mirror use.
- Ear tips point up/back, not sideways like large horizontal bat wings.

**Deformation**: Ear shell mostly follows head; optional subtle lag must not move jewelry through ear.

## Hands

**Priority**: critical. **Confidence**: medium-high for three long free-hand digit silhouettes plus thumb; medium for hidden grip joints.

**Observed**: Large green bare palms with long tapered clawed fingers. Free-hand silhouettes in gobsta0 and gobwib0 support three long fingers and an opposed thumb. Sword hand closes firmly around gold-guarded hilt.

**Inferred or selected**: Three long fingers plus one opposable thumb per hand is the modeling target. Joint segmentation and palm depth are inferred; no claim of hidden fourth finger. Neutral source hands are opened and fanned for modeling rather than copied from closed combat grip.

**Model checks**:

- Count three long fingers plus thumb on both hands; inspect occluded side-view digit before declaring it absent.
- Provide real gaps, knuckles and palm thickness, no welded fingers or mitten caps.
- Claws align with distal phalanges and remain separate from adjacent digits.
- Opposed thumb and finger curl must form a stable sword grip without thumb penetrating guard.

**Deformation**: Separate digit controls or equivalent usable hand deformation are required for grip and hit guard. Forearm bracer stays rigid; wrist and palm bend below it.

| Projected measurement / standing H | Range |
| --- | --- |
| wrist to longest claw tip | 0.13–0.17 |

## Feet

**Priority**: critical. **Confidence**: high for three visible forward claws and long flat foot; medium for sole padding.

**Observed**: Three broad forward toes/claws visible in frontal standing, long toes in right profile; exposed green toes and heel below small iron ankle/instep piece. No boots, hooves, bird hock, toe-only stance or extra rear talon.

**Inferred or selected**: Three forward toes per foot, ordinary plantar sole and rounded heel. Toe hinge location and sole thickness inferred. Preserve visible heel instead of converting to digitigrade legs.

**Model checks**:

- Inspect profile length and front toe count; earlier notes proposing four toes are superseded by the native close-up.
- Both heels and toe pads can contact one plane in neutral pose.
- Ankle guard must not swallow toes or create a fused shoe-shaped foot.
- Toe pivot must follow actual modeled metatarsal/claw geometry; do not assume human foot length.

**Deformation**: Stable sole contact and heel/toe roll without stretching rigid claws. Shin guard avoids ankle and knee creases.

| Projected measurement / standing H | Range |
| --- | --- |
| heel to longest toe in profile | 0.19–0.25 |

## Torso Armor

**Priority**: high. **Confidence**: high for coverage; medium for exact riveting and straps.

**Observed**: Dark riveted V-shaped gorget over upper chest; modest spiked shoulder caps; two separate small upper-back plates. Abdomen and most back exposed.

**Inferred or selected**: Plate thickness, fastening straps, exact spike count and micro-rivets inferred from low-resolution highlights. AI references clarify dark iron with small warm gold fittings.

**Model checks**:

- No full cuirass, studded spine strap or armor covering entire abdomen/back.
- Gorget clears jaw and clavicle motion; shoulder cap follows shoulder rather than forearm.
- Preserve spikes as stable shapes, not stretched skin ridges.

**Deformation**: Gorget and rear plates primarily chest-bound; shoulder plates primarily clavicle/upper-arm-bound with clearance. Avoid heavy mixed weights across elbow.

## Bracers And Greaves

**Priority**: high. **Confidence**: high for location and exposed joints; medium for construction.

**Observed**: Dark spiked forearm and front shin armor, exposed upper arms, elbows and knees; narrow metal coverage over ankle/instep with green toes beyond it.

**Inferred or selected**: Open backs, brown retaining straps, thickness and buckle placement clarify plausible construction. AI buckle/strap count differs slightly across views and is subordinate to coverage, not exact topology authority.

**Model checks**:

- No spikes attached to wrong limb group.
- Forearm pronation rolls bracer with forearm without crushing wrist/palm.
- Elbow and knee can bend deeply for death without plates stretching or bridging creases.

**Deformation**: Plate shells near-rigid with clear skin beneath; protect local hinge clearance.

## Belt Skirt Pouch

**Priority**: high. **Confidence**: high for silhouette/side; medium for panel count and hidden folds.

**Observed**: Brown buckled belt, overlapping pointed leather strips ending at upper thigh, dark rivets at strip ends; one small pouch at anatomical right hip. Native rear view has skirt, exposed back and no large cape.

**Inferred or selected**: Independent strip thickness, attachment and folds inferred. Exact seam/rivet/panel counts in generated views are not equal to original recovered counts.

**Model checks**:

- No skirt fused to both thighs or pelvis-to-hand bridge.
- Strips allow alternating leg swing and deep squat, and follow gravity in prone death.
- Pouch remains on right through all views and clips.

**Deformation**: Belt follows pelvis; pouch follows right hip with small restrained lag; strip bases follow belt while tips permit bend/overlap.

## Sword Separate Prop

**Priority**: critical_for_animation. **Confidence**: high for one-handed curved blade/guard and right-hand ownership; medium for unseen grip detail.

**Observed**: Long curved single-edged blade with broad swept tip and gold guard, held in anatomical right hand. gobsta2 shows true blade length; frontal standing is strongly foreshortened. Attack changes apparent blade width/length through rotation.

**Inferred or selected**: Sword omitted from body submission only. Separate prop must later match native profile and grip frame; no scabbard is established. Blade depth and hidden handle construction inferred.

**Model checks**:

- Do not generate a giant blade from a foreshortened front view.
- Attach one rigid sword to right-hand grip transform; never hand-swap through mirrored sprite directions.
- Use blade plane and guard orientation as evidence for wrist roll, not texture color alone.
- Provide release/ground placement only as needed for death; native shows sword beside right hand.

**Deformation**: Rigid prop; right grip remains stable across walk/attack/hit, lowers with death. No blade bending or grip sliding.

| Projected measurement / standing H | Range |
| --- | --- |
| guard to tip in standing profile | 0.4–0.47 |

## Material families

**Skin**: Olive green/yellow-green, shaded brown-green; avoid lime/neon or Shaman/King palette. Matte to softly rough.

**Eyes**: Small yellow iris in dark recessed socket, controlled highlight; no emissive flashlight eyes.

**Iron**: Dark grey worn iron, restrained specular highlights; metalness local to metal parts, not whole body.

**Leather**: Brown belt, skirt and pouch, rough with moderate folds; not shiny plastic.

**Gold**: Small warm gold ear hoops, buckle, guard and armor fittings; avoid bright full gold armor.

**Claws_Teeth**: Pale ivory to yellow-brown; shape matters before detailed texture.

## Review order and evidence limits

- Fit large silhouette and head first, hands/feet second, equipment placement third, surface detail last.
- The new images preserve key identity but remain AI interpretations; subtle rivet, strap, skin-mark and profile hand-pose differences are not additional required anatomy.
- Front/back/source side references are not calibrated scans. Do not force inconsistent perspective details into one distorted mesh.
- Technical readiness, agent visual review and user artistic acceptance must remain separate.
