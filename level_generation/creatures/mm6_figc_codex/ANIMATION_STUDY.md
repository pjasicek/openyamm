# FighterChain motion study

Native descriptors: FighterChain A/B/C (535–537), palettes 212/211/210. Preserved full frame inventory in source/native_inventory.json. Standing/walk have five stored directions with mirrors for 5–7; action frames reuse front view. Right hand holds double axe, left arm kite shield; sheathed sword at left hip. Attack raises axe over right shoulder, then chops diagonally across the front; shield protects torso. Death falls backwards.

Local source selection and preview: review/g1_front.png, g1_left.png, g1_three_quarter.png; work/rom.json provides humanoid-set extremes. Standing = Standard Idle; walk = ArmedWalk; run = RelaxRunForward; hit = UnarmedGetHitF1; attack = Sword And Shield Slash; fidget = Standing Taunt Battlecry; death = Standing React Death Backward. ArmedDeath1 was rejected (falls forwards). Preserve 30 fps, use world-rest-delta Mixamo retarget with forearm roll moved to hand; attack/fidget plant plus 20% leg motion as discrete steps. Source slash leans too far; reduce to upright baseline. Fit left arm/shield clearance and both grips locally. Measure actual axe edge motion at a forward-directed cut for impact. No paid animation action needed.

Native times from inventory (raw ticks /16):
- standing: 0.125 s, 1 frames.
- walk: 0.75 s, 6 frames.
- attack: 0.75 s, 6 frames.
- attack2: 0.75 s, 6 frames.
- hit: 0.75 s, 6 frames.
- death: 0.625 s, 5 frames.
- corpse: 0.125 s, 1 frames.
- fidget: 0.75 s, 6 frames.
