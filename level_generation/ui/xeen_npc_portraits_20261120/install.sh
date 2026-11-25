#!/bin/sh
# Cuts the accepted sheets into assets_dev/worlds/xeen/icons_x2/npc<10000+id>.png (126x146, opaque RGBA, 0644).
# Later lines overwrite earlier ones: batch 2 (sheet10, sheet11) replaces 4048, 4151 and 4201.
set -e
cd "$(dirname "$0")"
OUT=../../../assets_dev/worlds/xeen/icons_x2
ids() { python3 -c "import yaml;print(*yaml.safe_load(open('sheets.yml'))['$1']['ids'])"; }
python3 extract.py raw/sheet01_v2.png $OUT $(ids sheet01)
python3 extract.py raw/sheet02_v2.png $OUT $(ids sheet02)
for s in 03 04 05 06 07 08; do python3 extract.py raw/sheet${s}_v1.png $OUT $(ids sheet$s); done
# sheet09: cells 10-12 are second takes of 4153-4155, not used
python3 extract.py raw/sheet09_v1.png $OUT 4147 4148 4149 4150 4151 4152 4153 4154 4155
# batch 2: sheet10 (4151 with human ears, 4048 older, ten Act II people; its 4201 had elven ears: sheet11 has him)
python3 extract.py raw/sheet10_v1.png $OUT $(ids sheet10)
for s in 11 12 13 14 15 16 17; do python3 extract.py raw/sheet${s}_v1.png $OUT $(ids sheet$s); done
# sheet18: 4283, 4284 and the second take of 4332 (the other second takes are not used): cut into a scratch
# folder, three copied
TMP=$(mktemp -d)
python3 extract.py raw/sheet18_v1.png $TMP $(ids sheet18)
cp $TMP/npc14283.png $TMP/npc14284.png $TMP/npc14332.png $OUT/
# sheet19 v2: the first two cells (4601, 4602; the rest are further takes)
python3 extract.py raw/sheet19_v2.png $OUT 4601 4602
# batch 3, the Darkside towns: sheets 20-29, then from sheet30 5246, 5247 and the second take of 5106 (Nibbler)
for s in 20 21 22 23 24 25 26 27 28 29; do python3 extract.py raw/sheet${s}_v1.png $OUT $(ids sheet$s); done
python3 extract.py raw/sheet30_v1.png $TMP $(ids sheet30)
cp $TMP/npc15246.png $TMP/npc15247.png $TMP/npc15106.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 4 (third session): Rivercity's sorceresses and the phase 4-6 towns, sheets 31-36; sheet36's last cell is a
# second take of 5309 (Sir Malvern), not used
for s in 31 32 33 34 35; do python3 extract.py raw/sheet${s}_v1.png $OUT $(ids sheet$s); done
python3 extract.py raw/sheet36_v1.png $TMP $(ids sheet36)
for n in 4709 4710 4711 4712 4713 4714 4715 4716 4717 4718 4719; do cp $TMP/npc1$n.png $OUT/; done
# batch 5 (fourth session): X6's Sphinx Wells and the Warzone coachman, and Sablewing (4720, moved to X7 by D-5.2)
# again on a volcanic slope (overwrites sheet35's desert take); cells 7-12 are second takes, not used
python3 extract.py raw/sheet37_v1.png $TMP 4603 4604 4605 4606 4607 4720 9001 9002 9003 9004 9005 9006
for n in 4603 4604 4605 4606 4607 4720; do cp $TMP/npc1$n.png $OUT/; done
# batch 6 (fourth session): A3's quest and story people, sheet38; cell 12 (a second take of 5453) not used
python3 extract.py raw/sheet38_v1.png $TMP 4955 4956 4957 5109 5110 5317 5512 5453 4608 5318 5513 9001
for n in 4955 4956 4957 5109 5110 5317 5512 5453 4608 5318 5513; do cp $TMP/npc1$n.png $OUT/; done
chmod 0644 $OUT/npc1*.png
# batch 7 (fifth session): A3's Shinobu (4530), Leafpoint (5319), Ector (5320), sheet39 row 1; rows 2-4 are second
# takes, not used
python3 extract.py raw/sheet39_v1.png $TMP 4530 5319 5320 9001 9002 9003 9004 9005 9006 9007 9008 9009
for n in 4530 5319 5320; do cp $TMP/npc1$n.png $OUT/; done
chmod 0644 $OUT/npc1*.png
# batch 8 (sixth session): D-26's Felix (4958) and Carl (5014), D-27's DD-09 prisoners (5111-5114), sheet40 rows 1-2;
# rows 3-4 are second takes, not used
python3 extract.py raw/sheet40_v1.png $TMP 4958 5014 5111 5112 5113 5114 9001 9002 9003 9004 9005 9006
for n in 4958 5014 5111 5112 5113 5114; do cp $TMP/npc1$n.png $OUT/; done
chmod 0644 $OUT/npc1*.png
# batch 9 (seventh session): Picard the Aged (5704, FD-02), sheet41_v2 cell 1; the other cells are takes and variants
python3 extract.py raw/sheet41_v2.png $TMP 5704 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011
cp $TMP/npc15704.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 10 (ninth session): Tern (5321, D4's Isle ferry back, D-36 (6)), sheet42_v1 cell 1; the other cells are takes
# and variants
python3 extract.py raw/sheet42_v1.png $TMP 5321 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011
cp $TMP/npc15321.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 11 (tenth session): Varro (4609, XD-20's Arena Master, D-39), sheet43_v1 cell 1; the worker drew a 4x4 grid
# (four rows of the same takes), so --grid 4x4; the other cells are takes and variants
python3 extract.py raw/sheet43_v1.png $TMP 4609 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011 9012 9013 9014 9015 --grid 4x4
cp $TMP/npc14609.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 12 (eleventh session): Blastem (5248, DD-19's talking wizard, D-42 Q5), sheet44_v1 cell 1; the other cells are
# takes and variants
python3 extract.py raw/sheet44_v1.png $TMP 5248 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011
cp $TMP/npc15248.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 13 (thirteenth session): Alister (5705, FD-04's fraud druid in the gate hall, D-57 Q27), sheet45_v1 cell 1;
# the other cells are takes and variants
python3 extract.py raw/sheet45_v1.png $TMP 5705 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011
cp $TMP/npc15705.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 14 (fourteenth session): Cyrano Jones (5614, DD-26's Salesman of Pets Unlimited, D-65 Q57), sheet46_v1 cell 1;
# the other cells are takes and variants
python3 extract.py raw/sheet46_v1.png $TMP 5614 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011
cp $TMP/npc15614.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 15 (sixteenth session): Sparrow (4158, Rivercity's Pit Fighter in Martial Training, D-73), sheet47_v1 cell 1;
# the other cells are takes and variants
python3 extract.py raw/sheet47_v1.png $TMP 4158 9001 9002 9003 9004 9005 9006 9007 9008 9009 9010 9011
cp $TMP/npc14158.png $OUT/
chmod 0644 $OUT/npc1*.png
# batch 16 (2026-11-25, agent xeen-fb4-town): the goblin-eared boy (4053, XD-04's cage 1, D-155), Rudd (4054) and
# Marla (4346), the mates of Nystor's return boats (D-150): sheet48_v1 row 1; rows 2-4 are unrelated faces (the worker
# drew no second takes), not used
python3 extract.py raw/sheet48_v1.png $TMP 4053 4054 4346 9001 9002 9003 9004 9005 9006 9007 9008 9009
cp $TMP/npc14053.png $TMP/npc14054.png $TMP/npc14346.png $OUT/
chmod 0644 $OUT/npc1*.png
