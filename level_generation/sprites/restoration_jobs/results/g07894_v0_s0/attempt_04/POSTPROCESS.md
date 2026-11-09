# Final export

Run queue process, calibrate_orb_gamma.py, then queue check. Script reads immutable before_orb_grade backups and maps common orb luminance through bounded native-channel curves; only physical rows 0:62 change. This supersedes the initial independent RGB curves that introduced cool green shadows. Native per-state mean color, alpha and brass are preserved; orb_gamma.json stores targets and curves. Raw masters remain unchanged.
