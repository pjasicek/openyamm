"""Zones of RUINEDTEMPLE.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up, from the plans (work/rooms_*.png): the entrance hall (upper floor -672, hall -944), the south ruins, the main
temple, the east rooms (room 3, the spiral room, the chest room), the pew hall and elevator room, the crypt level
(-1120) and the shaft bottom with its spiral ramps (-1808..-1144)."""
ZONES = {
    "entrance_hall": (-400, -1000, -1000, 400, -300, -250),
    "south_ruins": (-1100, -1000, -1600, 1100, -300, -1000),
    "main_temple": (-400, -1000, -250, 400, -500, 650),
    "east_rooms": (380, -1000, 200, 950, -500, 1700),
    "north_corridor": (-400, -1000, 650, 380, -500, 1500),
    "pew_hall": (-1150, -1000, 1000, -400, -500, 1750),
    "elevator_room": (-1100, -1000, 1720, -800, -500, 2100),
    "crypt_level": (-1000, -1200, 1700, 500, -1000, 2400),
    "shaft_and_ramps": (-100, -1900, 2000, 450, -1130, 2700),
}
