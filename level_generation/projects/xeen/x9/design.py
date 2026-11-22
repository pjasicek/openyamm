"""X9 Clouds of Xeen: the L1 design as data (A5, 2026-11-20). gen_l1.py writes the brief from it; render_x9.py draws
and measures it. Units are map units (512 to a cell), x east, y north, the room's middle at (0, 0); floors are heights
in map units (the stair head 320, the castle's base 768). Nothing here is read by the game or the studio.

Source: the Clouds of Xeen (MM4 maze 27 with x106-x108, a 32 x 32 sky; xeen/aaze0027). Its layout is kept: a long
southern cloud with the stair head in the middle, four rhyming statues and two roc nests on it; an open gap crossed by
"Xeen--9N." (nine squares north over the sky); the northern cloud with Slick's carnival west of the way, Castle Xeen's
gate at (16,29), the "Xeen's Aviary" roc rookery to the north-east; offering statues on lone clouds down both sides.
"""

ROOM = (96, 90)                 # cells: 49,152 x 46,080 units (D-50: grown north and east to hold XD-19's measured shell)
# Castle Xeen's shell over XD-19's measured footprint (A7, 2026-11-21): 10,240 x 10,080 inside, 10,560 x 10,400
# outside: on X9 x -5280..5280, y 11136..21536, the gate wall at y 11776 (XD-19's -4320), 640 behind the south towers'
# faces (480 plus the wall). Heights above the sill: wall walks 1,408, keep 2,816, the aviary's walls 3,456 (the
# highest). Heights over the castle's base (768) here: the walls clear 3,456 with a parapet, the roof closed over all.
CASTLE_HEIGHTS = dict(walls=3584, towers=4096, keep=4608, tower_radius=768, keep_size=(3584, 2816), gate_recess=640,
                      gate_leaves=(256, 512))
# XD-19's frame to X9's: X9 = XD-19 + (0, 16096) (the gate wall y -4320 -> 11776)
XD19_OFFSET = (0, 16096)
HALF = (ROOM[0] * 256, ROOM[1] * 256)

# ------------------------------------------------------------------------------------------------ spaces
# kind: cloud (walkable island), castle (the closed shell of XD-19 on its cloud), sealed (the Dragon Clouds)
# region: south, west, north, east, sky
SPACES = [
    # ---- the stair clouds (south): the source's long southern cloud, y 1-9
    dict(id='room:stair_head', name="The cloud stair's head", kind='cloud', region='south', at=(0, -16896),
         extent=(4608, 3584), floor=320, seed=1,
         shape="a broad flat cloud ringed with old cloud-stone flags round the stair's head (the source's different floor at (13-17, 1-5))",
         purpose="Arrival from Darzog's Tower roof (XD-12's cloud stair), the head of the stair rising out of the cloud sea. Quiet."),
    dict(id='room:brink', name='The brink', kind='cloud', region='south', at=(0, -11776), extent=(3584, 2304),
         floor=448, seed=2,
         shape="the southern cloud's north lip, thinning to wisps over the gap",
         purpose="The 'Xeen--9N.' sign at the foot of the unseen way; the signature view over the gap to Castle Xeen."),
    dict(id='room:west_wing', name='The west statues', kind='cloud', region='south', at=(-7168, -17152),
         extent=(3584, 3072), floor=384, seed=3,
         purpose="Two rhyming statues (the source's (7,1) and (10,9))."),
    dict(id='room:sw_nest', name='The south-west nest', kind='cloud', region='south', at=(-13312, -15616),
         extent=(3840, 3328), floor=512, seed=4,
         shape="a heaped cloud with a roc nest of whole trees on its crown",
         purpose="A roc nest to burn (the source's (5,5)) and the hollow under it with stolen goods."),
    dict(id='room:east_wing', name='The east statues', kind='cloud', region='south', at=(7168, -17152),
         extent=(3584, 3072), floor=384, seed=5,
         purpose="Two rhyming statues (the source's (26,1) and (27,9))."),
    dict(id='room:se_nest', name='The south-east nest', kind='cloud', region='south', at=(13312, -15616),
         extent=(3840, 3328), floor=512, seed=6,
         purpose="A roc nest to burn (the source's (25,5))."),
    # ---- the west chain: the source's lone clouds down the west side, (3,11), (4-5,13-16), (1-2,20-22), (1-4,26-30)
    dict(id='room:west_pillar', name='The first offering cloud', kind='cloud', region='west', at=(-15616, -9472),
         extent=(2560, 2304), floor=384, seed=7, purpose="An offering statue on a lone cloud (the source's (3,11))."),
    dict(id='room:west_spine', name='The cloud spine', kind='cloud', region='west', at=(-16896, -2816),
         extent=(2304, 4608), floor=448, seed=8,
         shape="a long narrow cloud lying north-south", purpose="An offering statue (the source's (4,15))."),
    dict(id='room:west_shelf', name='The west shelf', kind='cloud', region='west', at=(-16896, 4352),
         extent=(3072, 2816), floor=512, seed=9, purpose="An offering statue (the source's (1,21))."),
    dict(id='room:nw_isle', name='The north-west isle', kind='cloud', region='west', at=(-15616, 11008),
         extent=(4096, 3584), floor=576, seed=10,
         purpose="An offering statue (the source's (2,27)) and an old traveller's cache."),
    # ---- the north cloud: Xeendom
    dict(id='room:landing', name="Xeendom's landing", kind='cloud', region='north', at=(0, -4424),
         extent=(3584, 3328), floor=256, seed=11,
         shape="the northern cloud's southern nose (the source's (16,18)), cloud-stone flags at its tip",
         purpose="The unseen way's head and the 'Now entering Xeendom' sign. Quiet."),
    dict(id='room:carnival', name="Slick's carnival", kind='cloud', region='north', at=(-2560, 2560),
         extent=(6144, 4608), floor=448, seed=12,
         shape="the cloud plaza: a paved square of cloud-stone west of the Xeen road, four booths under striped awnings",
         purpose="Slick the Gamemaster's four stat games (M34; the source's (15,24), (14,26), (11,25), (12,22)). Quiet."),
    dict(id='room:back_lot', name="The carnival's back lot", kind='cloud', region='north', at=(-9472, 7424),
         extent=(3328, 3072), floor=512, seed=13,
         purpose="Behind the booths: the bridge from the north-west isle lands here; three cloud golems (the source's (7,25-27))."),
    dict(id='room:gate_court', name='The gate causeway', kind='cloud', region='north', at=(0, 9472),
         extent=(4096, 2816), floor=704, seed=14,
         shape="a broad cloud-stone causeway up to the gate, the prize stand at its west side",
         purpose="The causeway up to Castle Xeen's gate (XD-19's door, m34.gate) and Slick's prize stand (the source's (12,29)). Quiet: the gate's three cloud golems (the source's (18,28-29), (15,30)) stand on the castle's east apron by the aviary stair."),
    dict(id='zone:castle', name='Castle Xeen', kind='castle', region='north', at=(0, 16336), extent=(10560, 10400),
         floor=768, seed=15,
         purpose="Lord Xeen's castle as seen from outside: a closed shell of black stone and gold on its own cloud, the gate in its south wall. Inside is XD-19 (A7). Gone on m35.done."),
    dict(id='room:aviary', name="Xeen's Aviary", kind='cloud', region='north', at=(13440, 13440),
         extent=(6144, 4608), floor=1024, seed=16,
         shape="a high cloud ringed with broken rock spurs, five great nests among them",
         purpose="The roc rookery (the source's (26,26) sign and the nests at (27-30, 27-30)): rocs and griffins, three nests to burn, the rocs' hoard."),
    # ---- the east chain: (23,10), (23,12), (28-30, 19-21)
    dict(id='room:east_pillar', name='The lone pillar', kind='cloud', region='east', at=(14720, -8704),
         extent=(2816, 3072), floor=384, seed=17, purpose="A small cloud on the way north (the source's (23,10))."),
    dict(id='room:east_ledge', name='The offering ledge', kind='cloud', region='east', at=(15232, -1792),
         extent=(3584, 3584), floor=512, seed=18, purpose="An offering statue (the source's (23,12))."),
    dict(id='room:east_horn', name='The east horn', kind='cloud', region='east', at=(14848, 5504),
         extent=(4096, 3584), floor=704, seed=19,
         purpose="An offering statue (the source's (29,20)) and a lost traveller's pack."),
    # ---- the Dragon Clouds (Q-F1): sealed
    dict(id='room:dragon_clouds', name='The Dragon Clouds', kind='sealed', region='sky', at=(20864, 18304),
         extent=(4096, 3584), floor=2048, seed=20,
         shape="a high cloud above the aviary with a rock shaped like a dragon's head",
         purpose="Q-F1 (optional, Act VI): reached only from the Dragon Tower's roof (FD-04 on X7); no link to the rest. Empty and sealed until Q-F1 is written."),
]

# ------------------------------------------------------------------------------------------------ links
# style: neck (one cloud, a waist), causeway (cloud-stone stair on a cloud tongue), road (the Xeen road, flags on x 0),
# bridge (rope bridge), unseen (the 9N way), gate (XD-19's door)
LINKS = [
    dict(id='link:brink_neck', a='room:stair_head', b='room:brink', kind='open', style='neck', width=1536,
         notes="one cloud; the 'Danger! Go back!' post stands on it"),
    dict(id='link:west_neck', a='room:stair_head', b='room:west_wing', kind='open', style='neck', width=1280),
    dict(id='link:sw_neck', a='room:west_wing', b='room:sw_nest', kind='open', style='neck', width=1280),
    dict(id='link:east_neck', a='room:stair_head', b='room:east_wing', kind='open', style='neck', width=1280),
    dict(id='link:se_neck', a='room:east_wing', b='room:se_nest', kind='open', style='neck', width=1280),
    dict(id='link:unseen_way', a='room:brink', b='room:landing', kind='path', style='unseen', width=768,
         notes="'Xeen--9N.': nine cells (4,608) due north from the sign over the open gap, falling 192; 768 wide, its "
               "wisp top faint from the brink and readable underfoot within about 1,000, a cloud-stone lip at each end (D-50 change 1)"),
    dict(id='link:west_bridge_1', a='room:sw_nest', b='room:west_pillar', kind='bridge', style='bridge', width=256),
    dict(id='link:west_bridge_2', a='room:west_pillar', b='room:west_spine', kind='bridge', style='bridge', width=256),
    dict(id='link:west_bridge_3', a='room:west_spine', b='room:west_shelf', kind='bridge', style='bridge', width=256),
    dict(id='link:west_bridge_4', a='room:west_shelf', b='room:nw_isle', kind='bridge', style='bridge', width=256),
    dict(id='link:back_lot_bridge', a='room:nw_isle', b='room:back_lot', kind='bridge', style='bridge', width=384),
    dict(id='link:back_lot_neck', a='room:back_lot', b='room:carnival', kind='open', style='neck', width=1536),
    dict(id='link:landing_road', a='room:landing', b='room:carnival', kind='road', style='road', width=768,
         notes="the Xeen road begins: cloud-stone flags laid on the cloud"),
    dict(id='link:xeen_road', a='room:carnival', b='room:gate_court', kind='road', style='road', width=768,
         notes="the Xeen road up the plaza's east side to the gate"),
    dict(id='link:gate', a='room:gate_court', b='zone:castle', kind='double_door', style='gate', width=512,
         notes="Castle Xeen's gate: two leaves, XD-19's door; condition m34.gate"),
    dict(id='link:aviary_stair', a='zone:castle', b='room:aviary', kind='ramp', style='causeway', width=512,
         notes="from the castle cloud's east apron a cloud-stone stair climbs to the rookery"),
    dict(id='link:east_bridge_1', a='room:se_nest', b='room:east_pillar', kind='bridge', style='bridge', width=256),
    dict(id='link:east_bridge_2', a='room:east_pillar', b='room:east_ledge', kind='bridge', style='bridge', width=256),
    dict(id='link:east_bridge_3', a='room:east_ledge', b='room:east_horn', kind='bridge', style='bridge', width=256),
    dict(id='link:east_bridge_4', a='room:east_horn', b='room:aviary', kind='bridge', style='bridge', width=256),
]

# ------------------------------------------------------------------------------------------------ places
# kind: arrival, return, sign, statue (rhyming), offering, nest, booth, stand, gate, chest, landmark.
# off: from the space's middle (units); 'rim_n' puts a thing 384 inside that space's north rim on its middle line.
PLACES = [
    dict(id='entrance:xd12_roof', kind='arrival', space='room:stair_head', off=(0, -1024), facing='n',
         text="Arrival from XD-12's cloud stair (Darzog's Tower roof): the stair's top step, facing north."),
    dict(id='entrance:xd19_gate', kind='return', space='zone:castle', gate_off=640 - 512, facing='s',
         text="XD-19's way out and the scepter cinematic's leave: on the causeway 512 south of the gate's leaves, facing south (A7; D-47 Q14)."),
    dict(id='poi:danger_sign', kind='sign', space='room:stair_head', off=(640, 1664),
         text="'Danger! Go back!' (aaze0027:7), on the neck to the brink."),
    dict(id='poi:nine_north', kind='sign', space='room:brink', rim='n', off=(-448, -320),
         text="'Xeen--9N.' (aaze0027:6), at the unseen way's foot."),
    dict(id='poi:xeendom_sign', kind='sign', space='room:landing', rim='s', off=(-448, 384),
         text="'Now entering Xeendom' (aaze0027:8), at the unseen way's head."),
    dict(id='poi:aviary_sign', kind='sign', space='room:aviary', off=(-2304, -1152),
         text="'Xeen's Aviary' (aaze0027:9), at the head of the aviary stair (D-47's relay)."),
    dict(id='poi:statue_1', kind='statue', space='room:west_wing', off=(1024, 768),
         text="m34.statue_1: 'Advisor will a dig permit / five coins more you must submit.' (aaze0027:2)"),
    dict(id='poi:statue_2', kind='statue', space='room:west_wing', off=(-896, -896),
         text="m34.statue_2: 'Taxman becomes a faithful vassal / Xeen's bane lies under castle.' (aaze0027:3)"),
    dict(id='poi:statue_3', kind='statue', space='room:east_wing', off=(-1024, 768),
         text="m34.statue_3: 'In clouds above island tower / waits Lord Xeen his final hour.' (aaze0027:4)"),
    dict(id='poi:statue_4', kind='statue', space='room:east_wing', off=(896, -896),
         text="m34.statue_4: 'Only the sword Xeen's life can take / All his plans of war unmake.' (aaze0027:5)"),
    dict(id='poi:nest_sw', kind='nest', space='room:sw_nest', off=(-384, 384), text="'Roc Nest. Destroy?' (aaze0027:0)"),
    dict(id='poi:nest_se', kind='nest', space='room:se_nest', off=(384, 384), text="'Roc Nest. Destroy?' (aaze0027:0)"),
    dict(id='poi:nest_a1', kind='nest', space='room:aviary', off=(-896, 768), text="'Roc Nest. Destroy?' (aaze0027:0)"),
    dict(id='poi:nest_a2', kind='nest', space='room:aviary', off=(1792, 512), text="'Roc Nest. Destroy?' (aaze0027:0)"),
    dict(id='poi:nest_a3', kind='nest', space='room:aviary', off=(768, -1408), text="'Roc Nest. Destroy?' (aaze0027:0)"),
    dict(id='poi:offering_1', kind='offering', space='room:west_pillar', off=(0, 0), text="'Offering' (aaze0027:33)"),
    dict(id='poi:offering_2', kind='offering', space='room:west_spine', off=(0, 0), text="'Offering'"),
    dict(id='poi:offering_3', kind='offering', space='room:west_shelf', off=(-384, 256), text="'Offering'"),
    dict(id='poi:offering_4', kind='offering', space='room:nw_isle', off=(-768, 768), text="'Offering'"),
    dict(id='poi:offering_5', kind='offering', space='room:east_ledge', off=(256, 0), text="'Offering'"),
    dict(id='poi:offering_6', kind='offering', space='room:east_horn', off=(768, 512), text="'Offering'"),
    dict(id='poi:might_game', kind='booth', space='room:carnival', off=(1536, -1280),
         text="m34.might_game: the bell on a pole and a hammer (aaze0027:12-14, :35)."),
    dict(id='poi:speed_game', kind='booth', space='room:carnival', off=(1024, 1408),
         text="m34.speed_game: the gremlin's track (aaze0027:16-18, :37)."),
    dict(id='poi:endurance_game', kind='booth', space='room:carnival', off=(-1792, 1280),
         text="m34.endurance_game: the treadmill (aaze0027:20-22, :38)."),
    dict(id='poi:accuracy_game', kind='booth', space='room:carnival', off=(-1152, -1024),
         text="m34.accuracy_game: the shooting line, the bullseye 1,536 west on the plaza's west rim (aaze0027:24-26, :39)."),
    dict(id='landmark:bullseye', kind='landmark', space='room:carnival', off=(-2688, -1024),
         text="The straw bullseye on the plaza's west rim, 1,536 west of the shooting line (D-50 change 2)."),
    dict(id='poi:prize_stand', kind='stand', space='room:gate_court', off=(-1024, 0),
         text="m34.prize_stand: Slick's prize stand, the Lord Xeen dolls on its shelf (aaze0027:31, :41-43)."),
    dict(id='poi:castle_gate', kind='gate', space='zone:castle', gate_off=640,
         text="m34.gate: 'Enter Castle Xeen?' / 'No one may enter Castle Xeen without a cupie doll!' (aaze0027:40, :10); after m35.done the spot reads 'The great Castle Xeen recently stood here.' (aaze0027:44)."),
    dict(id='landmark:lip_south', kind='landmark', space='room:brink', rim='n', off=(0, -128),
         text="A cloud-stone lip at the unseen way's foot, by the 'Xeen--9N.' sign (D-50 change 1)."),
    dict(id='landmark:lip_north', kind='landmark', space='room:landing', rim='s', off=(0, 128),
         text="A cloud-stone lip at the unseen way's head, under 'Now entering Xeendom' (D-50 change 1)."),
    dict(id='landmark:slick', kind='landmark', space='room:gate_court', off=(-1368, 0),
         text="Slick the Gamemaster (11914, peaceful, placed, uncounted, NoArena), behind the prize stand (D-50 Q6)."),
    dict(id='poi:chest_hollow', kind='chest', space='room:sw_nest', off=(896, -768), text="The hollow under the south-west nest (T5)."),
    dict(id='poi:chest_cache', kind='chest', space='room:nw_isle', off=(1024, -640), text="An old traveller's cache (T5)."),
    dict(id='poi:chest_pack', kind='chest', space='room:east_horn', off=(-896, -512), text="A lost traveller's pack (T5)."),
    # F3 feedback fix (2026-11-21): at (1024, 1408) the hoard stood half on aviary_spur_3's top, 1,088 over the floor:
    # now on the aviary floor, its back against the spur's south face
    dict(id='poi:chest_hoard', kind='chest', space='room:aviary', off=(1024, 1360), text="The rocs' hoard: shiny things carried up from the land (T5)."),
    dict(id='landmark:dragon_rock', kind='landmark', space='room:dragon_clouds', off=(512, 256),
         text="The Dragon Clouds' dragon-head rock, seen from the aviary and the east horn."),
]

# ------------------------------------------------------------------------------------------------ monsters
# Rocs 11561 (38, 1,824 XP), Griffins 11562 (48, 2,784), Cloud Golems 11592 (50, 3,000): MAPS X9 35-55, 50 placed
ROWS = {11561: ('Roc', 38, 1824), 11562: ('Griffin', 48, 2784), 11592: ('Cloud Golem', 50, 3000)}
GROUPS = [
    # the south: rocs over the two nests and over the statues (the first fight from the stair head)
    dict(id='pop:sw_rocs', space='room:sw_nest', actor=11561, count=3, off=(768, -512)),
    dict(id='pop:sw_rocs_b', space='room:sw_nest', actor=11561, count=3, off=(-896, 768)),
    dict(id='pop:se_rocs', space='room:se_nest', actor=11561, count=3, off=(-768, -512)),
    dict(id='pop:se_rocs_b', space='room:se_nest', actor=11561, count=3, off=(1152, 1024)),
    dict(id='pop:west_statue_rocs', space='room:west_wing', actor=11561, count=2, off=(1280, 0)),
    dict(id='pop:east_statue_rocs', space='room:east_wing', actor=11561, count=2, off=(-1280, 0)),
    # the west chain
    dict(id='pop:pillar_rocs', space='room:west_pillar', actor=11561, count=2, off=(384, 384)),
    dict(id='pop:spine_rocs', space='room:west_spine', actor=11561, count=3, off=(0, 1152)),
    dict(id='pop:shelf_rocs', space='room:west_shelf', actor=11561, count=2, off=(512, -384)),
    dict(id='pop:isle_rocs', space='room:nw_isle', actor=11561, count=2, off=(512, 768)),
    dict(id='pop:back_lot_golems', space='room:back_lot', actor=11592, count=3, off=(-512, 384)),
    # the gate: three golems on the castle's east apron, by the aviary stair (the gate itself stays quiet)
    dict(id='pop:gate_golems', space='zone:castle', actor=11592, count=3, off=(5792, -3328)),
    # the east chain
    dict(id='pop:east_pillar_rocs', space='room:east_pillar', actor=11561, count=2, off=(0, 384)),
    dict(id='pop:ledge_rocs', space='room:east_ledge', actor=11561, count=2, off=(-512, -768)),
    dict(id='pop:horn_rocs', space='room:east_horn', actor=11561, count=3, off=(-256, 640)),
    # Xeen's Aviary
    dict(id='pop:aviary_rocs', space='room:aviary', actor=11561, count=3, off=(-1536, -512)),
    dict(id='pop:aviary_rocs_b', space='room:aviary', actor=11561, count=3, off=(1024, 640)),
    dict(id='pop:aviary_griffins', space='room:aviary', actor=11562, count=3, off=(1280, -896)),
    dict(id='pop:aviary_griffins_b', space='room:aviary', actor=11562, count=3, off=(-256, 1536)),
]

# the signature camera: from the brink by the 9N sign, looking north over the gap to the castle
CAMERA = dict(id='view:xeendom', space='room:brink', rim='n', off=(256, -576), eye=176, yaw_deg=90.0,
              pitch_deg=-3.0, fov=72.0)
# X2's entrance:x9_fall as installed (lead, 2026-11-21): D-50's (-14592, 2816) failed its dragon check (3,874 from the
# lake dragon at [36.5, 66]) and moved along the island toward the tower door; the same spot as entrance:xd12_tower
FALL_LANDING_X2 = dict(cell=(34.0, 58.0), at=(-15360, 3072), ground=768, facing=0,
                       text="Darzog's island on X2 by the tower door (entrance:x9_fall)")
UNSEEN_CELLS = 9                # 'Xeen--9N.': nine cells of 512
