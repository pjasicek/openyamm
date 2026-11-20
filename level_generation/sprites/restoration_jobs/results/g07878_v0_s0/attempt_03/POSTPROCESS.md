# Reproduce final export

After queue process, run clean_edges.py, then calibrate_orb_gamma.py, then queue check. Both scripts retain immutable intermediate backups and JSON provenance. The first removes magenta mixture only in the outer three pixels. The second grades only the orb above physical row 62 to each native state, preserving alpha and brass. Raw RGB and companion mask remain unchanged.
