# Native motion and selected source clips

Original family has 59 unique bitmap frames; source inventory and per-frame hashes are preserved in ../mm6_mfp/sources.json (read-only). Native standing/walking store views 0–4; other actions reuse one front view. Entries last 125 ms; action cycles have six entries (0.75 s); standing is held. Visible native standing height is 253 pixels at 0.699997 scale = 177.099 game units. Descriptors 601–603 use standing mfp/mf2/mf3, aliases for second attack, and have no spells. Palette ids 792/793/794 change only green/red/blue blouse.

Attack: right hand raises reverse-grip curved knife to cheek height, drives diagonally down across the front with free left arm balancing; knife disappears outside attacks. Braid swings behind. Death collapses via knees then prone, empty hands. Fidget is empty-handed and returns upright.

G1: local humanoid set previews rendered before Meshy (review/g1), source 30 fps, ROM work/rom.json. Standing RelaxIdle as upright reference, final authored native rest/flat feet; Fidget restrained glance/weight shift from rest (native adaptation). Walking RelaxWalkFemale3; its left hand rests on hip so replace arms with relaxed counter-swing, reduce pelvic catwalk roll. Running RelaxRunForward, reduce flight to a grounded jog. Attack DaggerAttackR3 has the diagonal reverse-grip overhand slash closest to native; R1 is a stab and R2 a straight overhead blow. Plant on rest, retain ~20% source leg motion through discrete IK steps, reduce excessive torso lean, add ~0.25 s lead-in to native 0.75 s blow. Hit UnarmedGetHitF1, blended to/from rest and <=0.75 s. Death: RelaxLaydownLayDown was previewed and rejected; final selection is Mixamo Falling Forward Death, with paired leg and floor constraints. Dead holds final pose. Cast aliases Attack because rows have no spells. No paid animation jobs.

Generated masters reviewed individually and as a contact sheet: adult identity, native costume/sash side, braid, no props, full framing and alpha. Right view revision 1 rejected as three-quarter; revision 2 is selected profile. Native five-digit hands are inferred human anatomy; final mesh digit topology must be checked. Pattern detail is generated inference, not recovered pixels.

API route verified 2026-10-12 against docs.meshy.ai/en/api/{image-to-3d,pricing,retexture,rigging}: Smart Topology meshy-t2 15000 mesh-only 5 credits, rig 5, retexture 10. Empty pose_mode preserves the supplied A-pose.


## Final selected clips

- Standing: Native upright relaxed pose; subtle breathing; authored gap fill.
- Walking: Humanoid RelaxWalkFemale3, damped upper motion and planted native gait IK.
- Running: Humanoid UnarmedRunForward2 arm swing over the planted native-size gait; stride 1.55 × walk.
- Attack: Humanoid DaggerAttackR3; stance plant and discrete leg steps; reverse-grip knife; brisk recovery to rest by 1.125 s; blow .656250 s.
- Hit: Humanoid UnarmedGetHitF1; planted native adaptation, retimed to .8125 s.
- Death: Mixamo Falling Forward Death; paired knee/hand floor constraints and garment fit.
- Dead: Exact last Death pose held.
- Fidget: Native relaxed glance and 3 mm weight shift; authored gap fill.
