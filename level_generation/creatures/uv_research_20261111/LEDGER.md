# Meshy ledger (UV study, hard cap 100 credits)

Jobs run only through `tools/creature_meshy.py` (the primary account had 2 credits, so every job went to the backup
account). Receipts are in the lease state files named per job (`--state`); downloads in `meshy/<job>/`. Prices from
docs.meshy.ai/en/api/pricing (2026-11-11): retexture 10 credits at 2K/4K, 15 at 8K.

Balance before the study (backup): 580; after: 505. Spent 75 of the 100-credit cap.

| # | Job | Task id | Backup balance before -> after | Credits | Running total | Purpose | Result |
|---|---|---|---|---|---|---|---|
| 1 | j1_m620_body_baseline_4k | 01a1ccd9-f823-7154-a4bf-6eec6bc3ecaa | 580 -> 570 | 10 | 10 | m620 body, fresh `uv_atlas.py` default layout (`combo/m620_body/base_default`, 56.5 %), 4K: honest baseline | SUCCEEDED; layout kept (56.5 %); seam step x visible length 110; pebbled vest, crackle skin (drift vs installed) |
| 2 | j2_m620_body_winner_4k | 01a1cd19-26af-7457-ae57-8cdc4bf9d359 | 570 -> 560 | 10 | 20 | m620 body, winning layout (PartUV skin t1.25 + seam pass + sparrow, 69.8 %), 4K | SUCCEEDED; layout kept (69.8 %); seam step total 59.8; vs job 1 12.6 levels at identical cameras |
| 3 | j3_m620_body_winner_4k_repeat | 01a1cd19-505e-767c-9ea0-0ba2139a978c | 560 -> 550 | 10 | 30 | same upload and request as job 2: Meshy noise floor | SUCCEEDED; vs job 2 12.0 levels (noise floor = layout difference); seam step total 59.6 |
| 4 | j4_m620_body_winner_8k | 01a1cd19-804e-756b-b313-47d59e9442b8 | 550 -> 535 | 15 | 45 | same upload as job 2 at 8K (exact charge 15, as the pricing page says) | SUCCEEDED; base colour 8192, other maps 4096; after 2K: fine band +6 %, blotch -10 % vs the 4K draws |
| 6 | j6_m620_head_winner_4k | 01a1cd19-cf50-714c-a52c-9f7c46414a39 | 535 -> 525 | 10 | 55 | m620 head set (welded), winning layout (69.7 %), 4K, production head masters `references_head/00-03` (submitted before job 5 under the same m620 lease; the budget for job 5 was confirmed first: 55 + 20 = 75) | SUCCEEDED; layout kept (69.7 %); hair better, face a different person, neck stump olive |
| 5a | j5_hyd_body_winner_4k | 01a1cd1f-b7fb-7656-8808-0621d9769d9f | 525 -> 515 | 10 | 65 | Hydra body set (Hydra_A + HydraB_A), winning layout (74.7 %), 4K, `mm6_hyd_claude/references_hd` 01/03/02/04 | SUCCEEDED; layout kept (74.7 %); design kept and sharper, diamonds yellower, neck stubs recoloured |
| 5b | j5_hyd_heads_winner_4k | 01a1cd1f-d080-74f7-b646-e6554c0fd059 | 515 -> 505 | 10 | 75 | Hydra heads set (five heads in one 2K square, body position), winning layout (71.1 %), 4K, the whole-creature masters `references_hd` (production painted each head alone with `references_heads/h<k>/`: 50 credits) | SUCCEEDED; layout kept (71.1 %); heads 1-4 keep identity, blue head painted olive-green, red head dull |
