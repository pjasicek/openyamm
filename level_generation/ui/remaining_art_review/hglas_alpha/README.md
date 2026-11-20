# Transparent `hglas` review candidates

The 121 frame sequence is fitted from four hash-bound RGBA sheet masters. Two existing returned sheets already had
transparency. The other two returned RGB sheets (`807e40c...` and `e59cc5d...`) had a copied UI panel behind their
hourglass foreground; `raw_rgb_sheet_1_alpha.png` and `raw_rgb_sheet_2_alpha.png` are imagegen edits that remove that
panel while keeping all 54 frame positions. The final closing plate had the wrong subject in the returned sheet, so
`hglas120-imagegen-master.png` restores that one frame from its native reference and adjacent-frame style.

`extract.py` projects the frozen sheet layout, finds each real alpha subject within its slot, and fits the subject to
the native logical bounding box on the exact 2× canvas. It checks transparent alpha, minimum 2× source sampling and
aspect consistency. The [report](report.json) records every source hash, master hash, slot, crop, destination and
sampling measurement. All 121 results are technical review candidates; they are not accepted runtime assets.

The imagegen edits requested only the wooden-and-glass hourglass foreground on genuine RGBA transparency, with the
original frame order, pose and sand state, and no copied panel. The closing-frame edit requested only the small tilted
wooden closing plate with its symbol, against transparent alpha. Light and dark composites were inspected after
fitting. The 4× Real-ESRGAN closing-plate experiment is retained as provenance but is not offered as the preferred
candidate.
