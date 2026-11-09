# Crystal cleanup correction

Preserved original cyan master. Fixed finish.clean_soft to apply fringe color checks in the recorded matte channel order; its previous hardcoded magenta check deleted real purple edge pixels. No companion mask was present. Reprocessed with common `--adjust 0.94 0 6`, then reproducible shared native tone grade (alpha unchanged). All six corrected light/dark proofs and native-order contact inspected. Earlier review_findings.json describes the now-corrected fringe.
