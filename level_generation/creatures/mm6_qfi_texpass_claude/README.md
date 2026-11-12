# MM6 zDemonQueen texture pass — skipped (2026-11-11)

Stream texpass-1. Not installed; nothing changed. The audit lists the Queen for its rock alcove set (`Rock`: 51.7 %
atlas, 31.5 % fragments, stretch 3.47; a static prop with no LODs, outside the kit's LOD chain). The queen's own
2080x1024 body | head set is at 35.0 % with 1.2 % fragments and stretch 1.50.

A layout of the 12,200-triangle queen (`tp_uv.py out=uv_fine fine=250 steps=0`, head set u > 0.5 x1.8) ran 54 minutes
in the merge/SLIM stage of `uv_atlas.py` without finishing and was stopped (one heavy job at a time on the shared
machine). No Meshy job was submitted (0 credits). To resume: try `merge_below=8` or the brute-force packer on a quiet
machine; the rock would need its own pass (static mesh, no LODs, no tiers).
