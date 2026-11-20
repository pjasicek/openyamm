"""Zones of LINDISFARNEMONASTERY.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units
(x0, y0, z0, x1, y1, z1), y up. Ground floor 0, galleries and library 384, attic and organ loft 896, bell floor 1264."""
ZONES = {
    "narthex": (-1024, -40, -512, 512, 450, 0),
    "tower_west": (-1024, -40, 0, -512, 900, 512),
    "tower_east": (256, -40, 0, 768, 900, 512),
    "nave": (-512, -40, 512, 256, 900, 2304),
    "transepts": (-1200, -40, 2304, 780, 380, 3070),
    "library_upper": (-1200, 380, 2304, 780, 890, 3070),
    "choir": (-560, -40, 3072, 320, 900, 4864),
    "attic_loft": (-560, 890, 2304, 320, 1250, 4300),
    "bell_tower": (-560, 1250, 2304, 320, 2100, 3072),
    "courtyard": (256, -40, 512, 2320, 1500, 2304),
    "ne_block": (780, -40, 2304, 2852, 400, 3072),
    "outside": (-1920, -700, -6400, 2852, 2048, -512),
}
