"""Zones of TRAININGHALL.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. The roof room (floor 640), the lobby (0) and the pole room (water 200), the corridors and the hall level (0), the
joust level (-272) and the caves below (-280 to -720)."""
ZONES = {
    "roof": (-480, 600, -500, 480, 900, 580),
    "lobby": (-480, -60, -600, 480, 590, 590),
    "pole_room": (-300, 90, 650, 340, 1500, 1350),
    "corridor_east": (460, -20, -650, 1160, 200, 100),
    "crate_room": (-1520, -20, -1420, -1000, 200, -640),
    "training_room": (-330, -20, -1420, 330, 300, -640),
    "archery": (640, -20, -2090, 1510, 330, -650),
    "joust": (-840, -290, -2060, 840, -30, -1020),
    "lower_cross": (-840, -290, -1020, 840, -30, -60),
    "caves": (0, -760, -3450, 2200, -250, -2000),
}
