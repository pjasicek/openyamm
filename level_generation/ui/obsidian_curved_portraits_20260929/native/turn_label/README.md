# Turn phase label size correction

2026-09-29: the reported “Attack” label used Lucida at scale 0.40784314 (6.93 logical pixels high).
The phase row now uses scale 0.7 (11.9 logical pixels), inside its existing 12.8-high row. The same change covers
Attack, Movement and Waiting; the panel and the SMALLNUM detail line are unchanged.

This first native run checks the label before the subsequent arc antialiasing fix. See
[arc smoothing](../arc_smoothing/README.md) for the final combined executable and native checks.
