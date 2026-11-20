"""Zones of DUNGEONOFSECRETS.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1,
z1), y up, along Chadwick's course: the hub, the entrance stair, sections 10/9 (room east of the hub), 8 (the U room),
the north corridor, the flooded pool room, section 1's plate room and corridor, section 2's corridor and stair, the
lever room (section 3), section 4's upper corridor, the octagon (section 5) and the shaft's foot, section 6's gauntlet,
the exit corridor."""
ZONES = {
    "hub": (1440, -50, -760, 2100, 200, -100),
    "entrance_stair": (2100, -50, -560, 2950, 500, -260),
    "s10_s09_room": (1300, -50, -480, 1560, 200, -100),
    "s08_room": (520, -50, -540, 1180, 200, 80),
    "north_corridor": (520, -50, 80, 680, 200, 700),
    "pool_room": (-520, -300, 220, 520, 120, 740),
    "plate_room": (-1160, -100, 740, -700, 250, 1800),
    "s02_corridor": (-1160, -100, 1800, -120, 250, 1980),
    "s02_stair": (-360, -100, 830, -120, 250, 1800),
    "lever_room": (-360, 240, 800, 1060, 600, 1720),
    "s04_corridor": (-760, 240, 420, 700, 600, 560),
    "octagon": (-1000, 240, -530, -380, 600, 80),
    "shaft_foot": (-760, -50, -530, -620, 200, -140),
    "gauntlet": (-460, -60, -800, 1030, 250, -560),
    "exit_corridor": (1030, -60, -780, 1450, 250, -600),
}
