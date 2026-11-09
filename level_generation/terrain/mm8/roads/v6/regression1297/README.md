# Screenshot1297: v6 visual rejection confirmed

The [assembled path and join enlargements](index.html) use the exact installed
256px textures, verified against the current export manifest. Native out01
rows51–57 / columns74–79 include the straight entry, alternating diagonal pair,
and east–west exit. Original textures are assembled in the same order for comparison.

Close inspection fails v6:

- `drsrne2 E drsrne1`: stone surfaces and outlines are visibly cut at the inner
  edge of the retained old border. The clean enlargement shows the interruption
  without diagnostic lines; marked copies locate the tile edge and adjacent8px rims.
- `drsrne1 S drsrne2`: the horizontal join neighborhood has broken stone shapes
  and a band of mismatched surface detail. Repetition makes these defects conspicuous.
- The diagonal is also narrower than the native assembled path. Controlling
  variation by shrinking interiors to old straight-donor openings was not sufficient.

`v6/compose.py` kept16 authoring pixels around the edge, registered new interior
artwork separately, and inserted it with a gradient blend. Retaining boundary RGB
does not preserve stone identity/shape across the surrounding strip. This is an
asset-level defect reproduced without the renderer; blaming filtering or stale
installation is not supported.

Both actual join pairs passed the old numerical screen. That screen compares the
exact boundary's local gradient ratio against interior ratios. It neither checks
stone continuity nor rejects displaced internal graft seams. Those passes are
not visual acceptance. V6's earlier review/completion claims are superseded here.

Next correction must author the connected diagonal pair together across both
join neighborhoods, then extract the tiles and inspect the repeated result again.
Include offset repeat joins and the native straight entry/exit; do not paste old
rims back onto independently repainted tiles or solve the problem with additional
road narrowing. Review clean enlarged join strips before any installed delivery.

This inspection creates review artifacts and records the regression. It changes
no installed textures, generated artwork, settings, or packages.
