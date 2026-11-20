-- Verhoffin Ruins, MM9 rework (level_generation/projects/mm9r_verhoffinruins/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {CellBars10 = 1, CellBars11 = 3, CellBars12 = 5, CellBars13 = 7, CellBars14 = 9, CellBars15 = 11, CellBars16 = 13, CellBars17 = 15, CellBars4 = 17, CellBars5 = 19, CellBars6 = 21, CellBars7 = 23, CellBars8 = 25, CellDoor10 = 2, CellDoor11 = 4, CellDoor12 = 6, CellDoor13 = 8, CellDoor14 = 10, CellDoor15 = 12, CellDoor16 = 14, CellDoor17 = 16, CellDoor4 = 18, CellDoor5 = 20, CellDoor6 = 22, CellDoor7 = 24, CellDoor8 = 26, DDoorL11 = 31, DDoorL12 = 33, DDoorL13 = 35, DDoorL14 = 37, DDoorR11 = 32, DDoorR12 = 34, DDoorR13 = 36, DDoorR14 = 38, Door5 = 55, DoubleDoorL1 = 27, DoubleDoorL10 = 29, DoubleDoorL2 = 39, DoubleDoorL3 = 41, DoubleDoorL4 = 43, DoubleDoorL5 = 45, DoubleDoorL6 = 47, DoubleDoorL7 = 49, DoubleDoorL8 = 51, DoubleDoorL9 = 53, DoubleDoorR1 = 28, DoubleDoorR10 = 30, DoubleDoorR2 = 40, DoubleDoorR3 = 42, DoubleDoorR4 = 44, DoubleDoorR5 = 46, DoubleDoorR6 = 48, DoubleDoorR7 = 50, DoubleDoorR8 = 52, DoubleDoorR9 = 54, FallingDoor = 56, Paddle = 57, PaddlePlate = 58, PrisonDoor1 = 59, PrisonDoor2 = 61, PrisonDoor3 = 62, PrisonDoor4 = 60, SawBlade1 = 63, SawBladeArm1 = 64, TortureChamberDoor0 = 66, TortureChamberDoor1 = 65, TortureChamberDoor6 = 67, TortureChamberDoor7 = 68, WaterNozzle0 = 69, WaterNozzle1 = 70, WaterNozzle2 = 71, WaterNozzle3 = 72, WaterRoomButton1 = 73, WaterRoomButton2 = 74, WaterTrap = 75}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}}})

local GROUPS = {Cell10 = {1, 2}, Cell11 = {3, 4}, Cell12 = {5, 6}, Cell13 = {7, 8}, Cell14 = {9, 10}, Cell15 = {11, 12}, Cell16 = {13, 14}, Cell17 = {15, 16}, Cell4 = {17, 18}, Cell5 = {19, 20}, Cell6 = {21, 22}, Cell7 = {23, 24}, Cell8 = {25, 26}, DD1 = {27, 28}, DD10 = {29, 30}, DD11 = {31, 32}, DD12 = {33, 34}, DD13 = {35, 36}, DD14 = {37, 38}, DD2 = {39, 40}, DD3 = {41, 42}, DD4 = {43, 44}, DD5 = {45, 46}, DD6 = {47, 48}, DD7 = {49, 50}, DD8 = {51, 52}, DD9 = {53, 54}, Door5 = {55}, FallingDoor = {56}, Paddle = {57}, PaddlePlate = {58}, PrisonDoor14 = {59, 60}, PrisonDoor2 = {61}, PrisonDoor3 = {62}, Saw = {63, 64}, TortureDoor = {65, 66}, TortureSide6 = {67}, TortureSide7 = {68}, WaterNozzle0 = {69}, WaterNozzle1 = {70}, WaterNozzle2 = {71}, WaterNozzle3 = {72}, WaterRoomButton1 = {73}, WaterRoomButton2 = {74}, WaterTrap = {75}}
local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end
local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end
local function toggleGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end end
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z + 170 >= b[1][3] and z <= b[2][3] end
local function hurt(amount, kind) evt.DamagePlayer(Players.All, kind or const.Damage.Physical, amount) end
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
local function locked() evt.StatusText("The door is locked.") end
local BOX = {BustTrigger0 = {{-2725, -5684, -471}, {-2006, -5129, 20}}, BustTrigger1 = {{-3575, -5684, -471}, {-2856, -5129, 20}}, PaddleTrigger = {{-5971, -4005, -338}, {-5661, -3450, -297}}, PentaCenter = {{-4440, -3785, -332}, {-4325, -3670, -280}}, PitDamage = {{-6472, -3973, -737}, {-5980, -3482, -410}}, SawBladeTrigger1 = {{-4701, -2326, -317}, {-4392, -1770, -154}}, SawDamage = {{-4669, -2212, -307}, {-4403, -1884, -82}}, TortureChamber = {{-7424, -4403, -328}, {-4736, -3046, 164}}, TrapRoom = {{-82, -2703, -983}, {819, -778, 0}}, Trigger0 = {{-257, -1553, -476}, {-152, -833, 15}}, TriggerPentagram1 = {{-4182, -3936, -319}, {-4092, -3846, -293}}, TriggerPentagram2 = {{-4468, -3526, -319}, {-4379, -3437, -293}}, TriggerPentagram3 = {{-4468, -4018, -319}, {-4379, -3928, -293}}, TriggerPentagram4 = {{-4182, -3608, -319}, {-4092, -3519, -293}}, TriggerPentagram5 = {{-4673, -3772, -319}, {-4584, -3683, -293}}}

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- Cell10
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- Cell11
handlers[103] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- Cell12
handlers[104] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- Cell13
handlers[105] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- Cell14
handlers[106] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- Cell15
handlers[107] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- Cell16
handlers[108] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- Cell17
handlers[109] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- Cell4
handlers[110] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- Cell5
handlers[111] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- Cell6
handlers[112] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- Cell7
handlers[113] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- DD1
handlers[114] = function() evt.SetDoorState(31, DoorAction.Trigger) evt.SetDoorState(32, DoorAction.Trigger) end   -- DD11
handlers[115] = function() evt.SetDoorState(33, DoorAction.Trigger) evt.SetDoorState(34, DoorAction.Trigger) end   -- DD12
handlers[116] = function() evt.SetDoorState(35, DoorAction.Trigger) evt.SetDoorState(36, DoorAction.Trigger) end   -- DD13
handlers[117] = function() evt.SetDoorState(37, DoorAction.Trigger) evt.SetDoorState(38, DoorAction.Trigger) end   -- DD14
handlers[118] = function() evt.SetDoorState(39, DoorAction.Trigger) evt.SetDoorState(40, DoorAction.Trigger) end   -- DD2
handlers[119] = function() evt.SetDoorState(41, DoorAction.Trigger) evt.SetDoorState(42, DoorAction.Trigger) end   -- DD3
handlers[120] = function() evt.SetDoorState(43, DoorAction.Trigger) evt.SetDoorState(44, DoorAction.Trigger) end   -- DD4
handlers[121] = function() evt.SetDoorState(45, DoorAction.Trigger) evt.SetDoorState(46, DoorAction.Trigger) end   -- DD5
handlers[122] = function() evt.SetDoorState(47, DoorAction.Trigger) evt.SetDoorState(48, DoorAction.Trigger) end   -- DD6
handlers[123] = function() evt.SetDoorState(49, DoorAction.Trigger) evt.SetDoorState(50, DoorAction.Trigger) end   -- DD7
handlers[124] = function() evt.SetDoorState(51, DoorAction.Trigger) evt.SetDoorState(52, DoorAction.Trigger) end   -- DD8
handlers[125] = function() evt.SetDoorState(62, DoorAction.Trigger) end   -- PrisonDoor3

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2
handlers[44] = function() evt.OpenChest(3) end   -- TreasureChest3
handlers[45] = function() evt.OpenChest(4) end   -- TreasureChest4
handlers[46] = function() evt.OpenChest(5) end   -- BlackBox

-- Doors MM9 locks with nothing to open them (DoubleDoorL/R10, TortureChamberDoor6/7) and the trap room's dummy
-- button (WaterRoomButton1: Locked, no trigger unlocks it).
handlers[200] = locked
handlers[215] = function() evt.StatusText("The button does not move.") end
-- Doors in broken walls (no doorway portal: the ruin joins both sides): a click swings the leaves.
handlers[201] = function() toggleGroup("DD9") end
handlers[202] = function() toggleGroup("PrisonDoor14") end
handlers[203] = function() toggleGroup("Cell8") end

-- The bolt on PrisonDoor2 (DestructableBrush12: HitPoints 50; its DamageTrigger turns PerceptionBrush0 off, its
-- DeathTrigger unlocks PrisonDoor2): a scene destructible; weapons break it as in MM9, a click still does
-- (the shared click's killing blow).
handlers[209] = function()   -- damaged
    set("BoltHintOff", 1)
    evt.SetFacetBit(320, FacetBits.Invisible, true)
end
handlers[206] = function()   -- broken
    set("BoltBroken", 1); set("BoltHintOff", 1)
    evt.PlaySoundName("events/doorbreak.wav", 0, 0, 0)
    evt.SetFacetBit(320, FacetBits.Invisible, true)
end
handlers[205] = function()
    if var("BoltBroken") == 0 then evt.StatusText("The door is bolted shut.") return end
    toggleGroup("PrisonDoor2")
end

-- Door5 (DoorLock.scr "559 1"): the key (item 559, givetake.scr on the table in the south-east room) unlocks it and is taken.
handlers[207] = function()
    if var("Door5Unlocked") == 0 then
        if MM9.hasItem(559, "verhoffinruins:Door5") == 0 then locked() return end
        MM9.takeItem(559, "verhoffinruins:Door5")
        set("Door5Unlocked", 1)
    end
    toggleGroup("Door5")
end

-- FallingDoor: it falls flat once (its OpenTrigger2 locks it; FallingFrame and DroppingFrame are not in the map).
handlers[208] = function()
    if var("DoorFallen") == 1 then return end
    set("DoorFallen", 1)
    open("FallingDoor")
end


-- The PerceptionBrushes (Perception 9): the bolt, the saw's slot and the paddle's plate show to a
-- party with the Perception for them; the drain button's only while the room is full (the nozzles'
-- OpenTrigger turns it on, Trigger0 and the drain turn it off). Checked on load and every 3 s.
local function perceptive() return evt.CheckSkill(29, 0, 9) end
local HINTS = {320, 321, 322}
local function updateHints()
    local want = perceptive() and 2 or 1
    if var("PerceptionHints") == want then return end
    set("PerceptionHints", want)
    for _, cog in ipairs(HINTS) do
        if not (cog == 320 and var("BoltHintOff") == 1) then
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
    if var("WaterState") ~= 1 then evt.SetFacetBit(323, FacetBits.Invisible, true) end
end
handlers[157] = updateHints

-- The headsman's block (HeadsmanBlock1, placeCapstone.scr :Use1): on the capstone quest (key 98) with the Capstone of Order (item 396)
-- the capstone is placed (Capstone.scr :OnPlace): key 99, 154000 experience, the capstone shows,
-- the writ (a world item shown with key 99) appears (Writ.scr :OnInit), the item is taken.
handlers[223] = function()
    if MM9.hasKey(98) == 0 or MM9.hasKey(99) == 1 then return end
    if MM9.hasItem(396, "verhoffinruins:HeadsmanBlock1") == 0 then return end
    MM9.giveKey(99)
    MM9.giveExperience(18500) -- MM9 GiveExp 154000, mm9_quest_xp_profile.yml
    MM9.playSound("sounds/events/quest.wav")
    evt.SetSprite(303, true)
    MM9.takeItem(396, "verhoffinruins:HeadsmanBlock1")
end
handlers[222] = function()   -- writ picked up, Writ.scr :Onuse: the Writ of Fate (item 392), key 100
    if MM9.hasKey(100) == 1 or MM9.hasKey(99) == 0 then return end
    MM9.giveExperience(18500) -- MM9 GiveExp 162000, mm9_quest_xp_profile.yml
    MM9.giveKey(100)
    MM9.playSound("sounds/events/quest.wav")
end
handlers[220] = function()   -- Book, fakebook.scr :haskey: the fake Verhoffin book (item 242), keys 281 and 290
    if MM9.hasKey(281) == 1 then return end
    MM9.giveKey(281)
    MM9.giveKey(290)
    give(242, "verhoffinruins:Book")
    evt.SetSprite(300, false)
end
handlers[224] = function() evt.SimpleMessage("Scrap of Diary\n\n..That Emperor Trandis is up to something, I'm certain of it!  He had some soldiers out here from their encampment scoping out the terrain.  He'll be in for a shock, that's for certain!  I am the only one who knows where all the traps are.  Should his troops gain entry into my tower they'll certainly not find a way out..\n..from the letter I got today.  It was from someone claiming to be my sister!  I will be the first to admit I do not recall anything from my childhood, but I'm certain I didn't have a sister..did I?..\n..he claimed to be one of the creatures who created me.  As if I was not born from a womb at all!  He claimed that I was the victim of some bizarre experiments.  I laughed at him..\n..I won't back down.  I am sovereign from the Ursanian Empire, and I mean it!  Those soldiers will be sorry on this day!..\n..He paid me to give him the thing.  He called it the \"Capstone of Order\".  I no longer had any use of it.  It was a lot of money, so why not?..\n..Perhaps?  I have locked my diary in the study.  It should be safe from prying eyes there!") end   -- Prop2, BookLetter.scr "484 Letter"
handlers[225] = function() evt.SimpleMessage("Scrap of Diary\n\n..I Fear that the RED skeletons have escaped from my control.  I should have known those YELLOW bellied cowards I hired from the Ursanian Army would not be suitable for transformation..\n..I don't understand what is wrong with my soldiers.  As the days go on, their attitude worsens.  The other day, one of the division captains told his superior he was feeling BLUE.  Perhaps the power I infused in them has been corrupting their souls..\n..and then they fought each other, both because of GREEN envy.  Had I not enjoyed watching them fight, I might have put a stop to it.  It gave the men a laugh though, and I saw more than a few of them bet on it..\n..found it in the barbarian region called Cheh'dian.  It was an ORANGE metal, somewhat akin to gold.  During my experiments I found it takes readily to enchantment.  I think I will need to aquire more of this substance.") end   -- Prop3, BookLetter.scr "485 Letter"

-- The pentagram (PentagramPuzzle.scr "TortureChamberDoor0 TortureChamberDoor1"): the torture chamber's door is
-- shut and locked; the centre starts the puzzle and lights the five flames (PentaCenter); the points in the order
-- of the flames' colours (red, yellow, blue, green, orange; letter 485) each latch with a click, a wrong one
-- re-arms them all (OnFailure); the fifth unlocks both leaves and opens TortureChamberDoor1 only (UnlockDoor's
-- "Trigger NULL, open" leaves TortureChamberDoor0 shut).
local POINTS = {"TriggerPentagram1", "TriggerPentagram2", "TriggerPentagram3", "TriggerPentagram4", "TriggerPentagram5"}
local function pointsOn() for k = 1, 5 do set("Point" .. k .. "Off", 0) end end
local function puzzleStart()
    if var("PuzzleStarted") == 1 then return end
    set("PuzzleStarted", 1)
    for k = 0, 4 do evt.SetSprite(310 + k, true) end
    pointsOn()
end
local function puzzleStep(k)
    if var("PuzzleStarted") == 0 or var("PuzzleSolved") == 1 or var("Point" .. k .. "Off") == 1 then return end
    set("Point" .. k .. "Off", 1)
    if var("PuzzleProgress") ~= k - 1 then        -- OnFailure
        set("PuzzleProgress", 0); pointsOn()
        set("PuzzleFailures", var("PuzzleFailures") + 1)
        return
    end
    set("PuzzleProgress", k)
    evt.PlaySoundName("door/doorlatch01.wav", 0, 0, 0)
    if k == 5 then                                   -- UnlockDoor
        set("PuzzleSolved", 1)
        open("TortureChamberDoor1"); set("Leaf1Open", 1)
    end
end
-- The leaves' OpenTriggers: TortureChamberDoor0 turns DoorShooter0/1 on, TortureChamberDoor1 turns them off.
handlers[204] = function()
    if var("PuzzleSolved") == 0 then locked() return end
    local opening0 = var("Leaf0Open") == 0
    local opening1 = var("Leaf1Open") == 0
    toggleGroup("TortureDoor")
    set("Leaf0Open", opening0 and 1 or 0); set("Leaf1Open", opening1 and 1 or 0)
    if opening0 then set("ShootersOn", 1) end
    if opening1 then set("ShootersOn", 0) end
end

-- The water trap (DrainWater.scr on WaterTrap): opening any of the four nozzles fills the room (its fill: the
-- TriggerWaterLock relay shuts and locks DoubleDoor5, locks the nozzles and unlocks the drain button; the
-- nozzles' OpenTriggers light the drain button's PerceptionBrush and put out the nozzles' PerceptionLights).
-- The water rises to the ceiling at MM9's 10 LT a second; under it the party drowns. The drain button
-- (WaterRoomButton2) lowers it again and unlocks the door and the nozzles (TriggerWaterUnlock).
local function trapFill()
    if var("WaterState") ~= 0 then return end
    set("WaterState", 1)
    set("WaterFills", var("WaterFills") + 1)
    closeGroup("DD5")
    closeGroup("WaterTrap")
    -- a nozzle's OpenTrigger2: PerceptionLightOff, which puts out the four nozzles' PerceptionLights
    set("LightOff40550", 1); set("Light40550", 1); evt.SetLight(40550, false)
    set("LightOff40551", 1); set("Light40551", 1); evt.SetLight(40551, false)
    set("LightOff40552", 1); set("Light40552", 1); evt.SetLight(40552, false)
    set("LightOff40553", 1); set("Light40553", 1); evt.SetLight(40553, false)
    evt.PlaySoundName("ambient/fountain_20.wav", 0, 0, 0)
    evt.SetFacetBit(323, FacetBits.Invisible, not perceptive())
    set("WaterSeconds", 0); evt.StartTimer(155, seconds(1))
end
local function trapDrain()
    if var("WaterState") ~= 1 then return end
    set("WaterState", 0)
    set("WaterDrains", var("WaterDrains") + 1)
    openGroup("WaterTrap")
    open("WaterRoomButton2")
    set("AmbientSound556", 2)   -- its OpenTrigger2: waterfill off
    for k = 0, 3 do close("WaterNozzle" .. k) end
    -- the nozzles' CloseTriggers: PerceptionLight0-3 on again
    set("LightOff40550", 0); set("Light40550", 0); handlers[904]()
    set("LightOff40551", 0); set("Light40551", 0); handlers[904]()
    set("LightOff40552", 0); set("Light40552", 0); handlers[904]()
    set("LightOff40553", 0); set("Light40553", 0); handlers[904]()
    evt.PlaySoundName("ambient/fountain_20.wav", 0, 0, 0)
    evt.SetFacetBit(323, FacetBits.Invisible, true)
end
local function nozzle(k)
    if var("WaterState") ~= 0 then evt.StatusText("The valve will not turn.") return end
    open("WaterNozzle" .. k)
    set("AmbientSound556", 1)   -- its OpenTrigger3: waterfill on
    trapFill()
end
handlers[210] = function() nozzle(0) end   -- WaterNozzle0
handlers[211] = function() nozzle(1) end   -- WaterNozzle1
handlers[212] = function() nozzle(2) end   -- WaterNozzle2
handlers[213] = function() nozzle(3) end   -- WaterNozzle3
handlers[214] = function()   -- WaterRoomButton2: locked unless the room is full
    if var("WaterState") ~= 1 then evt.StatusText("The button does not move.") return end
    close("WaterRoomButton2")
    trapDrain()
end
handlers[155] = function()   -- the rising water: the engine drowns a party under it (breath)
    if var("WaterState") ~= 1 then return end
    evt.StartTimer(155, seconds(1))
    set("WaterSeconds", var("WaterSeconds") + 1)
end

-- The saw blade (SawBladeTrigger1: SawBlade1 on, SawBladeArm1 use, its damage brush on 0.5 s later and off at
-- 5 s): blade and arm slide out across the corridor and back; 40 to a party in the blade's path.
-- The blade (RotatingBrush AttachTo SawBladeArm1: mover spin) spins up as it comes out (SawBladeTrigger1: on)
-- and down once the arm is back (SawBladeArm1's CloseTrigger: off).
local function saw()
    openGroup("Saw")
    evt.SpinMover(DOORS.SawBlade1, "on")
    evt.PlaySoundName("events/gears01.wav", 0, 0, 0)
    set("SawRuns", var("SawRuns") + 1)
    arm(151, 2)
end
handlers[151] = function()
    if not fired(151) then return end
    closeGroup("Saw")
    arm(152, 3)
end
handlers[152] = function() if fired(152) then set("DoneSawBladeTrigger1", 0); evt.SpinMover(DOORS.SawBlade1, "off") end end

-- The paddle over the electrified pit (PaddleTrigger: Paddle toggle; its OpenTrigger swings SwingPaddle, whose
-- CloseTrigger swings the paddle back; the paddle's CloseTrigger re-arms PaddleTrigger): it sweeps across the
-- plate toward the pit and back, pushing what stands in its way.
local function paddle()
    openGroup("Paddle"); openGroup("PaddlePlate")
    set("PaddleRuns", var("PaddleRuns") + 1)
    arm(153, 2)
end
handlers[153] = function()
    if not fired(153) then return end
    closeGroup("Paddle"); closeGroup("PaddlePlate")
    arm(154, 4)
end
handlers[154] = function() if fired(154) then set("DonePaddleTrigger", 0) end end

-- The busts (KingKong.scr "BreakOut<k>" :FallThrough on BustTrigger0/1's ForceFall): the trigger sends
-- ForceFall to the pocket's KingKong monster (its first), which destroys the ceiling slab it stands on (a
-- scene destructible: stone debris and MM9's crumble sound). Only alive does it take ForceFall (MM9.receives).
-- A slab broken, by the bust or by the party's weapons (CanDamage, 100 HP), drops its pocket's monsters into
-- the corridor, hostile, and its dust rises (its DeathTrigger: BreakOutDust<k> On).
local BUSTS = {BustTrigger0 = 10, BustTrigger1 = 11}
local KINGKONG = {BustTrigger0 = {"BustZombie0", 19}, BustTrigger1 = {"BustWraith0", 18}}
local SLABS = {BustTrigger0 = 597, BustTrigger1 = 598}   -- DAT index: the destructible
local function bust(name)
    local k = KINGKONG[name]
    if k ~= nil and not MM9.receives("verhoffinruins", k[1], "ForceFall", k[2]) then return end
    set("Busted" .. name, 1)
    evt.DestroyDestructible(SLABS[name])
end
handlers[226] = function()   -- BreakOut1 broken: the BustTrigger0 pocket's monsters fall
    evt.SetMonGroupBit(10, MonsterBits.Invisible, false)
    evt.SetMonGroupBit(10, MonsterBits.Hostile, true)
    evt.SpawnWorldEffect("mm9:smoke", -2365, -5407, -225, 1)   -- BreakOutDust1
end
handlers[227] = function()   -- BreakOut0 broken: the BustTrigger1 pocket's monsters fall
    evt.SetMonGroupBit(11, MonsterBits.Invisible, false)
    evt.SetMonGroupBit(11, MonsterBits.Hostile, true)
    evt.SpawnWorldEffect("mm9:smoke", -3215, -5366, -225, 1)   -- BreakOutDust0
end

-- The door's shooters (DoorShooter0/1: FireBolt, DamageAmt 20, every 4 s while on) at the far wall of the
-- torture chamber, aimed at a party inside it; a bolt strikes the party in its path (strikesParty).
local function shoot(sx, sy, sz, damage)
    local x, y, z = evt.GetPartyPosition()
    z = z + 100
    local dx, dy, dz = x - sx, y - sy, z - sz
    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))
    local k = math.max(64 / length, 0.1)
    local shot = evt.FireMissile("Fire", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, "Fire", 0, 0, true)
    if shot then MM9.launchSound("FireBolt", sx, sy, sz) end
    set("ShotsFired", var("ShotsFired") + (shot and 1 or 0)); if shot then set("Shot", 1) end
end
handlers[156] = function()
    if var("ShootersOn") ~= 1 then return end
    local x, y, z = evt.GetPartyPosition()
    if not inBox(BOX.TortureChamber, x, y, z) then return end
    shoot(-6861, -3666, -256, 20); shoot(-6861, -3809, -256, 20)
end

-- MM9's Trigger volumes, polled four times a second: each fires once on entry (Trigger0, the saw's and the
-- paddle's re-arm themselves, the busts' turn themselves off).
local VOLUMES = {
    {name = "Trigger0", run = function()   -- PerceptionLightWaterTrap off (the trap room's door)
        evt.SetFacetBit(323, FacetBits.Invisible, true) end, rearm = true},
    {name = "SawBladeTrigger1", run = saw},
    {name = "PaddleTrigger", run = paddle},
    {name = "PentaCenter", run = puzzleStart},
    {name = "TriggerPentagram1", run = function() puzzleStep(1) end, rearm = true},
    {name = "TriggerPentagram2", run = function() puzzleStep(2) end, rearm = true},
    {name = "TriggerPentagram3", run = function() puzzleStep(3) end, rearm = true},
    {name = "TriggerPentagram4", run = function() puzzleStep(4) end, rearm = true},
    {name = "TriggerPentagram5", run = function() puzzleStep(5) end, rearm = true},
    {name = "BustTrigger0", run = function() bust("BustTrigger0") end},
    {name = "BustTrigger1", run = function() bust("BustTrigger1") end},
}
local inside, polls = {}, 0
handlers[150] = function()
    evt.StartTimer(150, seconds(0.25))
    local x, y, z = evt.GetPartyPosition()
    polls = polls + 1
    for _, v in ipairs(VOLUMES) do
        local now = inBox(BOX[v.name], x, y, z)
        if now and not inside[v.name] and var("Done" .. v.name) == 0 then
            if not v.rearm then set("Done" .. v.name, 1) end
            v.run()
        end
        inside[v.name] = now
    end
    if polls % 4 == 0 then
        if var("Armed151") == 1 and inBox(BOX.SawDamage, x, y, z) then
            hurt(40); set("SawHits", var("SawHits") + 1); set("SawHit", 1)
        end
        if inBox(BOX.PitDamage, x, y, z) then hurt(5, const.Damage.Electric); set("PitHits", var("PitHits") + 1); set("PitHit", 1) end
        if polls % 16 == 0 then handlers[156]() end
    end
end

handlers[1] = function()   -- map load: the scripts' Init (Capstone.scr :placed, Writ.scr :Init, fakebook.scr
                           -- :deletecheck, givetake.scr :Init, PentagramPuzzle.scr :InitPentagramPuzzle)
    if MM9.hasKey(281) == 1 or MM9.hasKey(282) == 1 then evt.SetSprite(300, false) end
    evt.SetSprite(303, MM9.hasKey(99) == 1)
    for k = 0, 4 do evt.SetSprite(310 + k, var("PuzzleStarted") == 1) end
    if var("BoltHintOff") == 1 then evt.SetFacetBit(320, FacetBits.Invisible, true) end
    updateHints()
    evt.StartTimer(150, seconds(0.25))
end
-- DamageTriggerTarget "On" (BustWraith0-3 -> the Fire BreakOutDust0): a hit raises its dust once.
local DUST_ON_HIT = {[14] = {-3215, -5366, -225}, [15] = {-3215, -5366, -225}, [16] = {-3215, -5366, -225}, [18] = {-3215, -5366, -225}}
handlers[97] = function(context)
    local p = DUST_ON_HIT[context.actorIndex]
    if p == nil or var("BustDust" .. context.actorIndex) == 1 then return end
    set("BustDust" .. context.actorIndex, 1)
    evt.SpawnWorldEffect("mm9:smoke", p[1], p[2], p[3], 1)
end
-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38648] = function() evt.DamageDestructible(648, 1000000) end   -- DestructableBrush12

-- MM9's PerceptionLights (dungeon/lights.py perception_lights): the red hint lights shine for a party whose
-- Perception reaches their PerceptionValue (scene pulsing lights, evt.SetLight), checked on load and every
-- 3 s. MM9's Off message: set("LightOff<key>", 1) and evt.SetLight(key, false); On: set("LightOff<key>", 0).
local PERCEPTION_LIGHTS = {[40550] = 9, [40551] = 9, [40552] = 9, [40553] = 9}
handlers[904] = function()
    for key, value in pairs(PERCEPTION_LIGHTS) do
        local want = (var("LightOff" .. key) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Light" .. key) ~= want then
            set("Light" .. key, want)
            evt.SetLight(key, want == 2)
        end
    end
end
-- MM9's touch Triggers switching AmbientSounds (dungeon/objects.py): entering one sends its On / Off / Toggle
-- (the scene sound's map variable AmbientSound<key>: 1 on, 2 off); ActivationCount limits the uses.
local SOUND_TRIGGERS = {
    {name = "PentaCenter", box = {{-4445, -3790, -502}, {-4320, -3665, -280}}, uses = 1, switches = {{582, "on", false}, {584, "on", false}, {587, "on", false}, {588, "on", false}, {590, "on", false}}},
}
local soundInside = {}
handlers[903] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(SOUND_TRIGGERS) do
        local b = t.box
        local now = x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]
        if now and not soundInside[t.name] and (t.uses == 0 or var("SoundUses" .. t.name) < t.uses) then
            set("SoundUses" .. t.name, var("SoundUses" .. t.name) + 1)
            for _, s in ipairs(t.switches) do
                local name = "AmbientSound" .. s[1]
                local on = var(name) == 1 or (var(name) == 0 and s[3])
                local want = (s[2] == "on" or (s[2] == "toggle" and not on)) and 1 or 2
                set(name, want)
            end
        end
        soundInside[t.name] = now
    end
    evt.StartTimer(903, seconds(0.25))
end
handlers[902] = function()   -- map load: the shared objects
    for key, _ in pairs(PERCEPTION_LIGHTS) do set("Light" .. key, 0) end
    handlers[904]()
    handlers[903]()
end

RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(108, "Door", handlers[108], "Door")
RegisterEvent(109, "Door", handlers[109], "Door")
RegisterEvent(110, "Door", handlers[110], "Door")
RegisterEvent(111, "Door", handlers[111], "Door")
RegisterEvent(112, "Door", handlers[112], "Door")
RegisterEvent(113, "Door", handlers[113], "Door")
RegisterEvent(114, "Door", handlers[114], "Door")
RegisterEvent(115, "Door", handlers[115], "Door")
RegisterEvent(116, "Door", handlers[116], "Door")
RegisterEvent(117, "Door", handlers[117], "Door")
RegisterEvent(118, "Door", handlers[118], "Door")
RegisterEvent(119, "Door", handlers[119], "Door")
RegisterEvent(120, "Door", handlers[120], "Door")
RegisterEvent(121, "Door", handlers[121], "Door")
RegisterEvent(122, "Door", handlers[122], "Door")
RegisterEvent(123, "Door", handlers[123], "Door")
RegisterEvent(124, "Door", handlers[124], "Door")
RegisterEvent(125, "Door", handlers[125], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(200, "Door", handlers[200], "Door")
RegisterEvent(215, "Button", handlers[215], "Button")
RegisterEvent(201, "Door", handlers[201], "Door")
RegisterEvent(202, "Door", handlers[202], "Door")
RegisterEvent(203, "Cell door", handlers[203], "Door")
RegisterEvent(206, "Bolt", handlers[206])
RegisterEvent(209, "Bolt", handlers[209])
RegisterEvent(205, "Door", handlers[205], "Door")
RegisterEvent(207, "Door", handlers[207], "Door")
RegisterEvent(208, "Door", handlers[208], "Door")
RegisterEvent(223, "Headsman's block", handlers[223], "Block")
RegisterEvent(222, "Writ", handlers[222], "Writ")
RegisterEvent(220, "Book", handlers[220], "Book")
RegisterEvent(224, "Scrap of Diary", handlers[224], "Scroll")
RegisterEvent(225, "Scrap of Diary", handlers[225], "Scroll")
RegisterEvent(226, "BreakOut1 broken", handlers[226])
RegisterEvent(227, "BreakOut0 broken", handlers[227])
RegisterEvent(204, "Door", handlers[204], "Door")
RegisterEvent(210, "Valve", handlers[210], "Valve")
RegisterEvent(211, "Valve", handlers[211], "Valve")
RegisterEvent(212, "Valve", handlers[212], "Valve")
RegisterEvent(213, "Valve", handlers[213], "Valve")
RegisterEvent(214, "Button", handlers[214], "Button")
RegisterMapTimerEvent(150, seconds(3), handlers[150], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(151, seconds(3), handlers[151], "Saw back", "", seconds(3))
RegisterMapTimerEvent(152, seconds(3), handlers[152], "Saw re-armed", "", seconds(3))
RegisterMapTimerEvent(153, seconds(3), handlers[153], "Paddle back", "", seconds(3))
RegisterMapTimerEvent(154, seconds(3), handlers[154], "Paddle re-armed", "", seconds(3))
RegisterMapTimerEvent(155, seconds(3), handlers[155], "Water", "", seconds(3))
RegisterMapTimerEvent(157, seconds(3), handlers[157], "Perception hints", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(38648, "DestructableBrush12", handlers[38648], "Boards")
RegisterMapTimerEvent(904, seconds(3), handlers[904], "Perception lights", "", seconds(3))
RegisterMapTimerEvent(903, seconds(3), handlers[903], "Ambient triggers", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterDamageHook(97, "Bust dust", handlers[97])
