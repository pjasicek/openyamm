# Q-F1 Alister and the Dragon Egg: prep

Quest file `source/quests/q-f1.yml`; started 114020, done 114021; FD-04 bits egg_taken 118146, alister_gone 118147;
player bits 11360 (potion), 11361 (Tome), 11362-11364 (X9 crystals). Items: Key to the Dragon Tower 12376 (FD-01's
key vault, M39: given), Dragon Egg 12375, Elder Staff 12505. Preconditions by console: m39.done 111781, xd07.linguist
116240 (Castle Burlock's Book of Languages; X9's four books need it).

- **X7 gate**: stand (-17920, 16179, 2592) yaw pi/2, event 66 (`q-f1.tower_door`, status line, key kept) -> FD-04
  (0, -1280, 0). Its status line must be read in the clicking `play_lua` (a reload drops the status history).
- **FD-04 tower** (rooms.yml; walls of an outline are 0 south, 1 east, 2 north, 3 west; openings at the middle of the
  shared span): floors z 0/1280/2560/3840; ramps in the walls: west (landing0 (-1184, -1312) -> landing1
  (-1400, 1280)), north (landing1 (-1280, 1300) -> landing2 (1280, 1300)), east (landing2 -> landing3 (1400, -1280)).
  `walk_to` plans every leg from the monsters' path map with only these points (clear radius 1000-1100, under the
  floor spacing of 1,280).
- Things (objects.yml): Alister actor 0 at (-1040, -768) (stand (-640, -768)); bone alcove notes events 12 (fraud,
  (1000, 1440)), 11 (forever, (1400, 1120)); eggs event 56 at (-416, -288); last climber: note 10 (-1300, 1150), potion
  74 (shelf (-1472, 1280)); hatchery note 9 (1450, 880); tome room door event 55 (door 10) at the crown's west wall
  y 1152, the Tome 101 at (-1312, 1440); roof stair door event 54 (door 7) at y 24, flight north to the head (z 4224)
  y 448-704, hatch event 67 ("Climb up through the hatch?") -> X9 (20352, 17280, 2048).
- **X9**: placed at (20776, 18350, 2048) as hooks_x9_dragon_clouds.yml: books 46-49, ball 44 (Mind), crystals 50-52,
  well 54/55, the Eye 53 (its window reads "Look into the eye of the Dragon and despair" / "Answer correctly or
  perish!", then the typed answer).
- Rewards: Alister 5,000 each; the Tome 4,000 to the reader; the potion +2 base Endurance to the drinker; the crystal
  3,000 to the clicker; the Eye 8,000 each and the Elder Staff. started 114020 stays set after the hand-in (`until`
  only hides the journal line).
