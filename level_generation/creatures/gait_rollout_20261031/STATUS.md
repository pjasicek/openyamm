# Rollout status

| package | state | notes |
|---|---|---|
| q1 | done | Spiders Sprint, Wyrm Walk2/Run2, Cockatrice Run2/Sprint; bindings applied, regressions pass |
| q2 | done | zrat Walk3+Walk2 run, zdog/zcat Trot, Dire Wolf Walk2/Run2/Sprint; bindings applied |
| q3 | done | Manticore Walk2, Hydra Run2, Gorgon and Thunder Lizard Walk2/Run2/Sprint; bindings applied, regressions pass |
| q4 | done | Unicorn Walk2, zchicken Run2, Crystal Dragon + Centaur Walk2/Run2; bindings applied, regressions pass |
| h01 | done | MM6 Thief, Barbarian, FighterChain: Jog + Sprint (Thief Walk2); FighterLeath Sprint only (Standard chase walks, user choice); bindings applied, regressions pass |
| h02 | done | Dwarf, Minotaur, Jackalman, Werewolf: walk/run fixes + Sprint; bindings applied, regressions pass |
| h03 | done | MM6 Archer, Lich, Cleric, Druidess, Sorcerer Jog; bindings applied, 11 regressions pass (Cleric tunic notch: skin weights, open) |
| h04 | done | five MM6 peasants: Jog (PeasantM3 also Walk2 + Sprint); bindings applied, 6 regressions pass |
| h05 | done | MM6 PeasantM4/F3/F4, Nobleman Walk2/Jog/Sprint (skirt/cape cloth); Merchant Jog; bindings applied, regressions pass |
| h06 | done | MM6 Demon, Guard, BGoblin, Skeleton, LizardArch, ElemEarth; bindings applied; 2 diagnostics updated to the new Walk2 name, 12 regressions pass |
| h07 | done | MM7 Fighters Chain/Leather/Plate, Swordsman: Jog + Sprint (Chain, Plate Walk2); bindings applied |
| h08 | done | Thief, Troglodyte, Vampire, Monk: Jog + Sprint (Trog Lope walk; robe/coat cloth); bindings applied |
| h09 | done | MM7 Skeleton Warrior, Wight Jog/Sprint; Lich Walk2/Jog; Ghoul Sprint; Zombie Walk2/Jog/Sprint; bindings applied |
| h10 | done | MM7 Behemoth, AMinotaur Sprint; Dwarf, Golem Walk2/Sprint; ATroll Walk2/Run; bindings applied (Behemoth Attack floor fault predates, left open) |
| h11 | done | MM7 Mage, Warlock, Necromancer Jog; Clerics Walk2/Jog (Sun A keeps walking); bindings applied |
| h12 | done | MM7 Goblin Jog/Sprint, Devil + Elf Archer Walk2/Jog, Elf Spearman Walk2/Jog/Sprint, Blaster Guy Jog; bindings applied |
| h13 | done | MM7 dwarf and elf peasants Jog (flight); bindings applied |
| h14 | done | MM7 human peasants Jog (women also Walk2, skirts re-simulated); bindings applied |
| h15 | done except Gog chase | MM7 goblin peasants Jog; Earth Elemental Walk2/Jog/Run (MM7+MM8); Gog Walk2 on MM7 AGog C only - Gog chase awaits the user (walk-as-run choice); bindings applied |
| h16 | done | lizardmen, Triton, Dragon Hunter: Run/Jog + Sprint; bindings applied, 4 regressions pass |
| h17 | done | MM8 pirates per-tier (Sprint, Jog2, WalkSlow/Walk3), Bedraggled Walk2, Mercenary Sprint; bindings applied; Bedraggled clip-count diagnostic updated |
| h18 | done | MM8 dark elf peasants Walk2, Warrior Walk2/Jog (Running as sprint), Ether Knight Walk2/Jog/Sprint, Cleric Jog; bindings applied |
| h19 | done | MM8 Ogre Warrior, Cyclops, Ogre Mage: Jog + Sprint (Mage Walk2); Ogre Peasant Walk2; bindings applied, regressions pass |
| h20 | done | MM8 Troll, Minotaur Walk2/Jog/Sprint; Troll Peasant Walk2; Minotaur Peasant Jog/Sprint (kilt/skirt solvers); bindings applied, regressions pass |
| h21 | done | Ratman Sprint; Wererat Human, Vampire Walk2/Jog/Sprint; Dark Dwarf Walk2/Sprint; Skeleton Archer Walk2/WalkFast; bindings applied, regressions pass |
| h22 | done | Crystal Walker Sprint; Plane Guardian Walk2/Jog/Sprint; bindings applied (both have skin-weight faults, open) |

Queue order (worst first, four at a time): q2, h16, h08, h02, then h04, h01, h07, h19, h15, q3, h20, h21, h05, h06, h09,
h10, h12, h17, q1, q4, h03, h11, h13, h14, h18, h22.

Coordinator steps per finished package: read its report, `apply_bindings.py <id>/bindings.yml`, rerun `ledger.py`,
set the row to done (or partial, with the reason), start the next queued package.

Footless bodies bound by the coordinator (2026-10-31, gait_rate, no clips): mm6_cob, mm6_hyd, mm6_med, mm6_ooz,
mm7_m282, mm7_m298, mm8_m408, mm8_m524, mm8_m536, mm8_m568, mm8_m600, mm8_m624 ([0.8, 1.5]); mm8_m608 Juggernaut
([0, 0], rolling).

Open questions for the user (collected, asked at the end):
- MM6 FighterLeath walks when chasing in Standard by the user's earlier choice and plays its walk at x1.63-1.95; a brisker
  walk bound as its run would fix that without making it run (h01).
- MM7/MM8 Gog: chases on its walk by the user's earlier choice (made at pursuit 1.75); at pursuit 2.0 the walk plays at
  x2.08-2.70, held at the 2x ceiling with sliding feet. Gogs are ranged, so MAW does not change them. Building a
  Jog/Run (like h15's Earth Elemental) needs the user to drop that choice (h15).
- Recurring, not judged by the gate: under MAW a hostile monster wanders at its fast speed, and the engine's walk
  preference while not hurrying keeps several on their walk at x1.5-1.8 (Dire Wolf B/C, Fighter Plate A, Wererat
  Human A, Cockatrice, MM7 Spider). Dropping the walk preference above about 1.5x would move them to the run (engine,
  actorModelGait), to be offered to the user at the end.
- The MM8 Troll Peasant's pending texture pass (mm8_m480_texpass_claude/scripts/merge_install.sh) keeps every clip of
  the installed file and can run now (h20).
- MM6 Cleric: his front tunic panel is skinned to both thighs and shows a 4-7 cm notch over the right thigh in the Jog
  (smaller in his accepted walk); a fix needs skin weights in the Cleric project (h03).
- MM8 Crystal Walker: 159 vertices weighted to both arm and leg stretch a claw-to-shin strand (Walk2 +21 cm, Run2 +30,
  Sprint +43); needs a weight fix in its project (h22). MM8 Plane Guardian: inner-thigh web visible in the Sprint (h22).

Final (2026-10-31): all 26 packages done and applied. `ledger.py` leaves 3 models, all awaiting user decisions:
MM6 FighterLeath (Standard chase walks, x1.63-1.95) and the MM7/MM8 Gog (Standard chase walks, x2.08-2.70).
Diagnostics updated for renamed walk clips/clip counts: mm6 Demon and Skeleton (Walk2), mm8 Bedraggled Human (7 clips).
