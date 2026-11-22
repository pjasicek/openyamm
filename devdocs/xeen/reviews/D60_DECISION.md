# Act IV quest experience at 1.122 (D-60)

**DECISION:** (a). Accept Act IV's counted quest experience of **179.5k of 160k per member (1.122)**. No values change: the Soul Waters stay at 1,000 (L3, bit 11348) and 2,000 (L4, bit 11349) per drinking member, as D-42 set them.
- From now on, Act IV's quest experience is **closed at 179.5k**. Any later Act IV experience must come with an equal trim in the same change, so the act never goes above 179.5k without a decider. The 1.15 gate (184.0k) stays the hard limit.
- D-53's 1.12 trigger stays for every other act. This acceptance applies to Act IV only and does not raise the trigger.

**WHY:**
1. The figure did not grow. D-42 approved the Soul Waters' 3k after D-16's ~176k ledger, and `balance.py` simply missed them until D-59. Act IV has been 179.5k since D-42, and 0.002 over the line is the cost of counting it correctly.
2. The 1.12 trigger exists to keep room for experience hooks not yet written (D-53, written for Act V). All of Act IV's amounts are now in A3's files. Their remaining `pending` markers only wire bits to maps and add no experience. So the 4.5k still left under the 1.15 gate is enough, and the closure rule protects it.
3. A 300 cut (2,000 → 1,700) gives an odd number to land exactly on a threshold, and it changes 0.005 of a level at level 40. Act IV's whole experience is (275.6k + 24.5k + 179.5k) of (287.9k + 160k) = 1.07. Acts IV and V together are 19.5k + 22.5k = 42k over, about 0.76 of a level at level 55, which is under the ~0.8 that D-53 already weighed.
4. Smaller numbers would weaken the Soul Waters, a source joke turned into a small reward on purpose (D-42 Q5). A drink is 1,000–2,000 against a level-40 level, so it is already modest.

**WHO ACTS:**
- **A2:**
  - Mark Act IV's quest row in `balance.py`'s report as "179.5k of 160k (1.12), accepted, D-60; closed: additions need an equal trim".
  - Ledger rows: the Soul Waters at 1k + 2k, now counted (D-42, D-59, D-60).
  - At each recount, flag any Act IV quest experience above 179.5k to a decider.
- **A3:** none. `m24.yml` stays as it is. Any new Act IV experience in a quest file comes with its offsetting trim in the same change.
- **Orchestrator:**
  - The DECISIONS row.
  - The STATUS log entry: "Act IV 1.12 accepted (D-60)".

**REVERSIBLE:** Yes. No data changes. Trimming later would mean changing one `AddValue(Experience, n)` in `m24.yml` and recounting, possible any time before the Act IV gate.

**SUMMARY ROW:** | D-60 | 2026-11-21 | Act IV quest XP 179.5k of 160k (1.122) once the Soul Waters are counted | Accepted, no change: D-42's 3k was always there, balance.py just missed it. Act IV is now closed at 179.5k: any later Act IV experience needs an equal trim. The 1.15 gate and D-53's 1.12 trigger for other acts stand | A2 (report note, ledger), orchestrator (row, STATUS) |
