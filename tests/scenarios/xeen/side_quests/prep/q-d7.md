# Q-D7 The Gemsmiths: prep

Quest file `source/quests/q-d7.yml` (repeatable, no experience); bits 113140 started, 113141-113143 refill_a/b/c, 113144
dug, 117160/117200 the pockets' arrived_once; autonote 4470. Rocks 12357 ruby, 12358 emerald, 12359 sapphire (diamond
DD-10C, Act V); gear 12540 Ruby Broadsword, 12541 emerald leather, 12542 sapphire staff, 12543 diamond plate. Gems:
`Xeen.GemItems` (177-186, 988-998, 2056-2065); `Xeen.payGems` takes the cheapest first.

- **The smiths' row** on D1 (`briefs/d1/L4/playtest.yml:1901-1990`): each a residence of one, its talk opens on the
  door (`press_interact`), stand y 19764 z 1600 yaw π/2: Linus 4945 (house 4495) x -16275, Simon 4946 (4496) x -14739,
  Toby 4947 (4497) x -13203, Hector 4948 (4498) x -11667.
- **Topics** (`xeen_quests.lua:2567`, global events 44351-44354): with 5 rocks and the fee: the rocks and gems taken,
  the gear given ("Five ruby rocks and two gems..."); with the rocks only: "The rocks are fine. The fee is two gems,
  and you have the rocks." (Simon "Rocks, yes. Gems, no. Four gems."); else the offer line ("... you don't have enough
  Ruby rocks.") and started + autonote 4470 (every time, repeatable).
- **DD-10A** (west pocket) by D1 event 187 from (-9728, 20480, 1600) yaw π/2 (no prompt); arrival (0, 192, 0), the
  arrival window "THE GEMSTONE MINES" once. Route (`briefs/dd10a/L4/playtest.yml`, main chain 53): door 1 (event 10)
  from (0, 760) → (0, 1300) → (0, 2300) → (1400, 2432) → (2000, 2432): ruby veins events 21-25; → (3200, 2560) →
  (3900, 2560) (the queens' den) → sump door 3 (event 12) from (4288, 2200) → (4288, 1800) → (4096, 1240) → emerald door
  2 (event 11) from (3900, 1376) → (3300, 1300): emerald veins events 13-17. Back by the bone pocket (2300, 1024) →
  (1300, 1250) → (1024, 1900) → (1024, 2432) → (0, 2432) → (0, 1100) → (0, 400) → (0, 112), the adit event 19 (OK) to
  D1 (-9728, 20480).
- A rock given while the hand is empty lands on the cursor: stow after each vein.
- Gems: a new game carries none and the party block has no inventory: an honest refusal at each smith with the rocks,
  then a CONVENTION grant of exactly the fee (as q-c25).
- The emerald veins' status line is "You work an emerald rock out of the vein." (DD-10A events 13-17; A8 fixed "a
  emerald" 2026-11-21 14:26); the scenario asserts it on each vein.
