-- Ruined Temple, MM9 rework (level_generation/projects/mm9r_ruinedtemple/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {AltarDoorLeft = 1, AltarDoorRight = 2, CaveInLeft = 3, CaveInLeftB = 5, CaveInLeftB_INV = 6, CaveInLeft_INV = 4, CaveInRight = 7, CaveInRightB = 9, CaveInRight_INV = 8, DestructableBrush6 = 13, DiamondButton1 = 10, DiamondButton2 = 11, DoorCryptEscape0 = 12, HiddenButton = 30, HiddenButton2 = 31, HiddenDoor = 32, HiddenDoor2 = 33, HiddenDoor3 = 34, LeftDoor = 35, MainButton = 36, MainElevator = 37, MoonButton1 = 38, MoonButton2 = 39, PrisonBars = 42, PrisonButton2 = 40, PrisonButton3 = 41, PrisonDoor = 43, PrisonEntrance = 44, PrisonEntrance2 = 45, RopeWheel = 46, SecondButton = 47, StarButton1 = 48, StarButton2 = 49, SunButton = 50, SunButton2 = 51, SunButton3 = 52, SunButton4 = 53, UpDoor = 54, WO_CounterBalance = 55, glass1_GLASS0 = 15, glass1_INV = 14, glass2_GLASS0 = 19, glass2_INV = 18, glass3_GLASS0 = 21, glass3_INV = 20, glass4_GLASS0 = 23, glass4_INV = 22, glass5_GLASS0 = 27, glass5_INV = 26, glass6 = 16, glass6_INV = 17, glass7_GLASS0 = 25, glass7_INV = 24, glass8_GLASS0 = 29, glass8_INV = 28}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- AltarDoor
handlers[102] = function() evt.SetDoorState(44, DoorAction.Trigger) end   -- PrisonEntrance
handlers[103] = function() evt.SetDoorState(45, DoorAction.Trigger) end   -- PrisonEntrance2
handlers[104] = function() evt.SetDoorState(54, DoorAction.Trigger) end   -- UpDoor

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2

-- Mover groups (each MM9 model's mechanism and its invisible collision part move together).
local GROUPS = {AltarDoor = {1, 2}, CaveInLeft = {3, 4}, CaveInLeftB = {5, 6}, CaveInRight = {7, 8}, CaveInRightB = {9}, DiamondButton1 = {10}, DiamondButton2 = {11}, DoorCryptEscape0 = {12}, EntranceFloor = {13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29}, HiddenButton = {30}, HiddenButton2 = {31}, HiddenDoor = {32}, HiddenDoor2 = {33}, HiddenDoor3 = {34}, LeftDoor = {35}, MainButton = {36}, MainElevator = {37}, MoonButton1 = {38}, MoonButton2 = {39}, PrisonButton2 = {40}, PrisonButton3 = {41}, PrisonDoor = {42, 43}, PrisonEntrance = {44}, PrisonEntrance2 = {45}, RopeWheel = {46}, SecondButton = {47}, StarButton1 = {48}, StarButton2 = {49}, SunButton = {50}, SunButton2 = {51}, SunButton3 = {52}, SunButton4 = {53}, UpDoor = {54}, WO_CounterBalance = {55}}
local function openG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Open) end end
local function closeG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Close) end end
local function toggleG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Trigger) end end
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
-- MM9 fires a trigger on any part of the party in its box: the party's 37-unit radius widens the box.
local function inBox(b, x, y, z) return x >= b[1][1] - 37 and x <= b[2][1] + 37 and y >= b[1][2] - 37 and y <= b[2][2] + 37 and z + 170 >= b[1][3] and z <= b[2][3] end
-- A PerceptionBrush switched off by MM9's wiring stays hidden; the rest show to a party with the Perception.
local function hintOff(cog) set("HintOff" .. cog, 1); evt.SetFacetBit(cog, FacetBits.Invisible, true) end
local function hintOn(cog) set("HintOff" .. cog, 0); set("PerceptionHints", 0) end
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
-- The quakes and the dust (EarthQuake, Fire): ShakeAmount 100 clamped to MM9's 12 units (intensity 1) for
-- QuakeDuration plus the decay, felt within OuterRadius of the object; the dust is a puff of smoke there.
local QUAKES = {QuakeObject0 = {1, 6, -1126, 3543, -2232, 1792}, QuakeObject2 = {1, 6, 2028, 1956, -2048, 1792}, DBQuakeObject0 = {1, 7, 256, 4946, -2744, 1024}, DBQuakeObject1 = {1, 6.7, -707, 3348, -2171, 1792}, DBQuakeObject2 = {1, 6.7, 1372, 2560, -2140, 1792}}
local function quake(name) local q = QUAKES[name]; evt.CameraShake(q[1], q[2], q[3], q[4], q[5], q[6], q[6]) end
local DUST = {DustObject0 = {215, 5212, -2760}, DustObject1 = {-563, 3338, -2166}, DustObject2 = {1352, 2591, -2048}}
local function dust(name) local p = DUST[name]; evt.SpawnWorldEffect("mm9:smoke", p[1], p[2], p[3], 1.5) end
-- DBEffectsTrigger<k>: DustObject<k> on, DBQuakeObject<k> Trigger.
local function dbEffects(k) dust("DustObject" .. k); quake("DBQuakeObject" .. k) end
-- TriggerHostile0 (one activation): DB_Crypt0's death or the party's touch relays DBEffectsTrigger0.
local function hostile0()
    if var("Hostile0Fired") == 1 then return end
    dbEffects(0)
    set("Hostile0Fired", 1)
end

-- The entrance (Trigger0, Trigger1, each triggering the other): the plank floor and the glass under it give way
-- (MM9 destroys DestructableBrush6 and glass1-8); they drop out of sight and the party falls into the hall.
local function collapse()
    if var("FloorFallen") == 1 then return end
    set("FloorFallen", 1)
    openG("EntranceFloor")
    evt.PlaySoundName("sounds/weapons/eqhammerimpact.wav", 0, 0, 0)
end

-- The hidden doors (door object wiring): SunButton opens HiddenDoor and SunButton4 opens HiddenDoor2, each with
-- both sun buttons riding it (MM9 AttachTo). SunButton2 and SunButton3, on the doors' far sides, are MM9's
-- DoubleDoorName pairs of SunButton and SunButton4: a press moves both buttons, so it opens the door from that
-- side too (as decoys the party that rode the lift down or climbed the spiral could not get out).
-- A door shuts after 10 s (CloseWaitTime) and its buttons unlock. HiddenDoor2 opening unlocks LeftDoor.
local function hiddenOpen(door, a, b, timer, cog)
    if var("Open" .. door) == 1 then return end
    set("Open" .. door, 1)
    openG(door); openG(a); openG(b)
    if cog then hintOff(cog) end
    arm(timer, 10 + 88 / 100)
end
local function hiddenClose(door, a, b, cog)
    closeG(door); closeG(a); closeG(b)
    set("Open" .. door, 0)
    if cog then hintOn(cog) end
end
handlers[201] = function() hiddenOpen("HiddenDoor", "SunButton", "SunButton2", 401, 300) end
handlers[204] = function()
    hiddenOpen("HiddenDoor2", "SunButton3", "SunButton4", 402, 310)
    set("LeftDoorUnlocked", 1)
end
handlers[202] = handlers[201]   -- SunButton's DoubleDoorName pair
handlers[203] = handlers[204]   -- SunButton4's DoubleDoorName pair
handlers[401] = function() if fired(401) then hiddenClose("HiddenDoor", "SunButton", "SunButton2", 300) end end
handlers[402] = function() if fired(402) then hiddenClose("HiddenDoor2", "SunButton3", "SunButton4", 310) end end
local function hiddenButton(button)
    openG(button)
    if var("OpenHiddenDoor3") == 1 then return end
    set("OpenHiddenDoor3", 1)
    openG("HiddenDoor3")
    arm(403, 10 + 88 / 100)
end
handlers[205] = function() hiddenButton("HiddenButton") end
handlers[206] = function() hiddenButton("HiddenButton2") end
handlers[403] = function()
    if not fired(403) then return end
    closeG("HiddenDoor3"); closeG("HiddenButton"); closeG("HiddenButton2")
    set("OpenHiddenDoor3", 0)
end
handlers[207] = function()   -- Locked until HiddenDoor2 opens
    if var("LeftDoorUnlocked") ~= 1 then evt.StatusText("The door is locked.") return end
    toggleG("LeftDoor")
end

-- The elevator (SunTempleButtons.scr): each symbol button toggles in and out and toggles its symbol; the main
-- button on the lift sends it when Star1 and Diamond2 are set and Star2, Diamond1, Moon1, Moon2 are not
-- (MM9 wires MoonButton1 to Star1, so Moon1 stays unset). SecondButton at the foot calls the lift; MM9's lift
-- stays where it went (Sticky): the main button and SecondButton send it to the other end here.
local function symbol(button, flag, cog)
    toggleG(button)
    local on = 1 - var("Sym" .. flag)
    set("Sym" .. flag, on)
    set("Pressed" .. button, 1 - var("Pressed" .. button))
    if cog then if var("Pressed" .. button) == 1 then hintOff(cog) else hintOn(cog) end end
end
handlers[210] = function() symbol("StarButton1", "Star1", 302) end
handlers[211] = function() symbol("StarButton2", "Star2", nil) end
handlers[212] = function() symbol("DiamondButton1", "Diamond1", nil) end
handlers[213] = function() symbol("DiamondButton2", "Diamond2", 301) end
handlers[214] = function() symbol("MoonButton1", "Star1", nil) end
handlers[215] = function() symbol("MoonButton2", "Moon2", nil) end
local function sendLift()
    local down = 1 - var("LiftDown")
    set("LiftDown", down)
    set("LiftTrips", var("LiftTrips") + 1)
    if down == 1 then openG("MainElevator"); openG("MainButton") else closeG("MainElevator"); closeG("MainButton") end
end
handlers[216] = function()
    if var("SymStar1") == 1 and var("SymStar2") == 0 and var("SymDiamond1") == 0 and var("SymDiamond2") == 1
            and var("SymMoon1") == 0 and var("SymMoon2") == 0 then
        sendLift()
    else
        evt.StatusText("Nothing happens.")
    end
end
handlers[217] = function()
    openG("SecondButton")
    sendLift()
    arm(412, 1)
end
handlers[412] = function() if fired(412) then closeG("SecondButton") end end

-- The crypt (RT_CounterBalance.scr): PrisonButton2 drops the counterbalance (252 LT at 300 LT/s) onto the crypt
-- lid, which breaks (DB_Crypt0 destroyed); the shaft under it is plugged with packed dirt (DestructableBrush0-5,
-- 20 hit points each, scene destructibles): weapons or a click break a plug. PrisonButton3 in the tunnel below unlocks and opens
-- DoorCryptEscape0, which opens the Tree of Life's cell (PrisonDoor, PrisonBars).
handlers[220] = function()
    if var("CounterBalanceFallen") == 1 then return end
    set("CounterBalanceFallen", 1)
    openG("PrisonButton2"); openG("WO_CounterBalance")
    arm(404, 0.9)
end
handlers[404] = function()
    if not fired(404) then return end
    evt.PlaySoundName("sounds/door/doorslammetal01.wav", 0, 0, 0)
    evt.DestroyDestructible(345)
end
handlers[244] = function()   -- DB_Crypt0 broken (the counterbalance, or weapons)
    hostile0()   -- DB_Crypt0's death triggers TriggerHostile0
    set("CryptOpen", 1)
end
handlers[230] = function()   -- DestructableBrush0 broken: PerceptionBrush4 goes off with it
    set("BrokenDestructableBrush0", 1)
    hintOff(304)
    evt.StatusText("The packed dirt gives way.")
end
handlers[231] = function()   -- DestructableBrush1 broken: PerceptionBrush5 goes off with it
    set("BrokenDestructableBrush1", 1)
    hintOff(305)
    evt.StatusText("The packed dirt gives way.")
end
handlers[232] = function()   -- DestructableBrush2 broken: PerceptionBrush6 goes off with it
    set("BrokenDestructableBrush2", 1)
    hintOff(306)
    evt.StatusText("The packed dirt gives way.")
end
handlers[233] = function()   -- DestructableBrush3 broken: PerceptionBrush7 goes off with it
    set("BrokenDestructableBrush3", 1)
    hintOff(307)
    evt.StatusText("The packed dirt gives way.")
end
handlers[234] = function()   -- DestructableBrush4 broken: PerceptionBrush8 goes off with it
    set("BrokenDestructableBrush4", 1)
    hintOff(308)
    evt.StatusText("The packed dirt gives way.")
end
handlers[235] = function()   -- DestructableBrush5 broken: PerceptionBrush9 goes off with it
    set("BrokenDestructableBrush5", 1)
    hintOff(309)
    evt.StatusText("The packed dirt gives way.")
end
handlers[221] = function()
    if var("EscapeOpen") == 1 then return end
    set("EscapeOpen", 1)
    openG("PrisonButton3"); openG("DoorCryptEscape0")
    arm(411, 0.5 + 120 / 25)
end
handlers[411] = function()   -- DoorCryptEscape0 is open: PrisonDoor Unlock, Open
    if not fired(411) then return end
    openG("PrisonDoor")   -- the bars and the door
    -- SunTemplePrison.scr :HandlePrisonGateOpen: RopeWheel reverse, on (the winch turns from then on)
    evt.SpinMover(DOORS.RopeWheel, "reverse"); evt.SpinMover(DOORS.RopeWheel, "on")
end

-- The Tree of Life (TreeofLife.scr): a world item (241, dungeon/pickups.py); its pickup gives key 256 and arms TriggerCaveIn1.
handlers[240] = function()
    if MM9.hasKey(256) == 1 then return end
    MM9.giveKey(256)
    set("CaveIn1Armed", 1)
end

-- The cave-ins (RT_CaveIn.scr): the rails (A) or the ceiling (B) break and the rocks drop onto their markers
-- (220 LT/s) half a second (left) and a second (right) after the trigger; MM9's floor slabs under them
-- shatter into the same floor (not built: overrides.yml). The trigger shakes its QuakeObject; each broken
-- rail or ceiling brush (a scene destructible: weapons break it too) sends its DBEffectsTrigger (dust and a
-- quake) from its destroyed event.
local function caveIn(left, right, timerLeft, timerRight, quakeName)
    evt.PlaySoundName("sounds/weapons/eqhammerimpact.wav", 0, 0, 0)
    quake(quakeName)
    arm(timerLeft, 0.5); arm(timerRight, 1)
end
handlers[405] = function() if fired(405) then evt.DestroyDestructible(363); openG("CaveInLeft") end end
handlers[406] = function() if fired(406) then evt.DestroyDestructible(362); openG("CaveInRight"); set("CaveIn0Done", 1) end end
handlers[407] = function() if fired(407) then evt.DestroyDestructible(380); openG("CaveInLeftB") end end
handlers[408] = function() if fired(408) then evt.DestroyDestructible(379); openG("CaveInRightB"); set("CaveIn1Done", 1) end end
handlers[245] = function() dbEffects(1) end   -- DB_RailLeft broken
handlers[246] = function() dbEffects(1) end   -- DB_RailRight broken
handlers[247] = function() dbEffects(2) end   -- DB_CeilingLeft broken
handlers[248] = function() dbEffects(2) end   -- DB_CeilingRight broken

-- MM9's Trigger volumes, polled four times a second; each fires once (MM9 turns each off after it fires).
local VOLUMES = {
    {name = "Trigger0", box = {{-164, -2007, -1638}, {164, -1475, -1475}}, armed = function() return true end, run = function() collapse() end},
    {name = "Trigger1", box = {{-182, -1534, -1638}, {182, -1170, -1475}}, armed = function() return true end, run = function() collapse() end},
    {name = "TriggerCaveIn0", box = {{-2340, 4050, -2360}, {-2084, 4306, -2104}}, armed = function() return true end, run = function() caveIn("Left", "Right", 405, 406, "QuakeObject0") end},
    {name = "TriggerCaveIn1", box = {{1746, 1818, -2278}, {2002, 2074, -2022}}, armed = function() return var("CaveIn1Armed") == 1 end, run = function() caveIn("LeftB", "RightB", 407, 408, "QuakeObject2") end},
    {name = "TriggerHostile0", box = {{365, 5511, -4679}, {621, 5767, -4423}}, armed = function() return true end, run = function() set("ShaftBottomReached", 1); hostile0() end}
}
handlers[400] = function()
    evt.StartTimer(400, seconds(0.25))
    local x, y, z = evt.GetPartyPosition()
    for _, v in ipairs(VOLUMES) do
        if var("Done" .. v.name) == 0 and v.armed() and inBox(v.box, x, y, z) then
            set("Done" .. v.name, 1)
            v.run()
        end
    end
end

-- The genie (GenieCrystal.scr, ColloidalGenie.scr): the lamp calls it once; two seconds later it stands in
-- the smoke over the lamp. MM9 opens its dialogue (435) by itself; here the party clicks it. The wish
-- (keys 5022-5025 from the dialogue): 5000 gold, 5000 experience, a random item 234-238, or Might +10 for the
-- active member (GiveAttribute 0, 10). Three seconds after the talk the genie vanishes.
local GENIE = 13
-- ColloidalGenie.scr's DoClientFX at its Smoke marker (hAppear): black smoke on the call, mist as it
-- appears, mist and black smoke as it goes
local GENIE_SMOKE = {0, 655, -2353}
local function genieFx(effect) evt.SpawnWorldEffect(effect, GENIE_SMOKE[1], GENIE_SMOKE[2], GENIE_SMOKE[3], 1) end
handlers[241] = function()
    if var("GenieCalled") == 1 then return end
    set("GenieCalled", 1)
    genieFx("mm9:blacksmoke")
    evt.PlaySoundName("sounds/animsounds/dragon/fidget1.wav", 0, 0, 0)
    arm(409, 2)
end
handlers[409] = function()
    if not fired(409) then return end
    set("GenieShown", 1)
    genieFx("mm9:mist")
    evt.SetMonsterBit(GENIE, ActorAttribute.Invisible, 0)
    evt.PlaySoundName("sounds/animsounds/zombie/ressurect2.wav", 0, 0, 0)
    evt.StatusText("A genie rises out of the lamp's smoke.")
end
handlers[50336] = function()   -- ColloidalGenie.scr :GrantWish
    if var("WishGranted") == 1 then return end
    set("WishGranted", 1)
    if MM9.hasKey(5022) == 1 then MM9.giveGold(5000); set("Wish", 1)
    elseif MM9.hasKey(5023) == 1 then MM9.giveExperience(5000); set("Wish", 2)
    elseif MM9.hasKey(5024) == 1 then give(MM9.random(234, 238, 1), "ruinedtemple:Genie"); set("Wish", 3)
    elseif MM9.hasKey(5025) == 1 then AddValue(BaseMight, 10); set("Wish", 4)
    end
    arm(410, 3)
end
handlers[410] = function()
    if not fired(410) then return end
    genieFx("mm9:mist"); genieFx("mm9:blacksmoke")
    MM9.removeActor(GENIE)
    set("GenieGone", 1)
end

-- The scrolls (BookLetter.scr DoLetter): MM9's book and scroll texts.
handlers[242] = function() evt.SimpleMessage("Excerpt from Book\n\n..And Igdrasa said, \"Let light travel through the world\", and it was so.  Her worshippers praised her as being just and good.  All creatures mourned when she traveled on to the next world.  She bade them not to.  She asked that they remember her, and wait patiently for their time to join her.") end   -- Prop7
handlers[243] = function() evt.SimpleMessage("Diary Entry\n\n..Today was the day I was supposed to be shown the Ritual of Consecration.  I don't understand why the Elders still have not shown me!  Perhaps I have not been pious enough.  I shall speak to..perhaps he will see the light, so to speak..") end   -- Prop8

-- The PerceptionBrushes: the red glow shows to a party with Perception 8 or better (MM9's PerceptionValue)
-- unless MM9's wiring has switched the brush off; on load and every 3 s.
local HINTS = {300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310}
local function updateHints()
    local want = evt.CheckSkill(29, 0, 8) and 2 or 1
    if var("PerceptionHints") == want then return end
    set("PerceptionHints", want)
    for _, cog in ipairs(HINTS) do
        evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or var("HintOff" .. cog) == 1)
    end
end
handlers[420] = updateHints
handlers[1] = function()   -- map load: what MM9 saves stays as it was left
    if var("GenieShown") == 1 and var("GenieGone") == 0 then evt.SetMonsterBit(GENIE, ActorAttribute.Invisible, 0) end
    set("PerceptionHints", 0)
    updateHints()
    evt.StartTimer(400, seconds(0.25))
end

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30391] = function() evt.SearchLootProp("mm9:ruinedtemple:object:391") end   -- BonePile0
handlers[30392] = function() evt.SearchLootProp("mm9:ruinedtemple:object:392") end   -- BonePile1
handlers[30393] = function() evt.SearchLootProp("mm9:ruinedtemple:object:393") end   -- BonePile2
handlers[30394] = function() evt.SearchLootProp("mm9:ruinedtemple:object:394") end   -- BonePile3
handlers[30395] = function() evt.SearchLootProp("mm9:ruinedtemple:object:395") end   -- BonePile4

-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38339] = function() evt.DamageDestructible(339, 1000000) end   -- DestructableBrush0
handlers[38340] = function() evt.DamageDestructible(340, 1000000) end   -- DestructableBrush1
handlers[38341] = function() evt.DamageDestructible(341, 1000000) end   -- DestructableBrush2
handlers[38342] = function() evt.DamageDestructible(342, 1000000) end   -- DestructableBrush3
handlers[38343] = function() evt.DamageDestructible(343, 1000000) end   -- DestructableBrush4
handlers[38344] = function() evt.DamageDestructible(344, 1000000) end   -- DestructableBrush5


RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(201, "SunButton", handlers[201], "Button")
RegisterEvent(202, "SunButton2", handlers[202], "Button")
RegisterEvent(203, "SunButton3", handlers[203], "Button")
RegisterEvent(204, "SunButton4", handlers[204], "Button")
RegisterEvent(205, "HiddenButton", handlers[205], "Button")
RegisterEvent(206, "HiddenButton2", handlers[206], "Button")
RegisterEvent(210, "StarButton1", handlers[210], "Button")
RegisterEvent(211, "StarButton2", handlers[211], "Button")
RegisterEvent(212, "DiamondButton1", handlers[212], "Button")
RegisterEvent(213, "DiamondButton2", handlers[213], "Button")
RegisterEvent(214, "MoonButton1", handlers[214], "Button")
RegisterEvent(215, "MoonButton2", handlers[215], "Button")
RegisterEvent(216, "MainButton", handlers[216], "Button")
RegisterEvent(217, "SecondButton", handlers[217], "Button")
RegisterEvent(220, "PrisonButton2", handlers[220], "Button")
RegisterEvent(221, "PrisonButton3", handlers[221], "Button")
RegisterEvent(207, "Door", handlers[207], "Door")
RegisterEvent(230, "Packed dirt", handlers[230])
RegisterEvent(231, "Packed dirt", handlers[231])
RegisterEvent(232, "Packed dirt", handlers[232])
RegisterEvent(233, "Packed dirt", handlers[233])
RegisterEvent(234, "Packed dirt", handlers[234])
RegisterEvent(235, "Packed dirt", handlers[235])
RegisterEvent(244, "DB_Crypt0", handlers[244])
RegisterEvent(245, "DB_RailLeft", handlers[245])
RegisterEvent(246, "DB_RailRight", handlers[246])
RegisterEvent(247, "DB_CeilingLeft", handlers[247])
RegisterEvent(248, "DB_CeilingRight", handlers[248])
RegisterEvent(240, "Tree of Life", handlers[240])
RegisterEvent(241, "Lamp", handlers[241], "Lamp")
RegisterEvent(242, "Scroll", handlers[242], "Scroll")
RegisterEvent(243, "Scroll", handlers[243], "Scroll")
RegisterEvent(50336, "Genie", handlers[50336])
RegisterMapTimerEvent(400, seconds(3), handlers[400], "Trigger volumes", "", seconds(3))
RegisterMapTimerEvent(420, seconds(3), handlers[420], "Perception hints", "", seconds(3))
RegisterMapTimerEvent(401, seconds(3), handlers[401], "Timer", "", seconds(3))
RegisterMapTimerEvent(402, seconds(3), handlers[402], "Timer", "", seconds(3))
RegisterMapTimerEvent(403, seconds(3), handlers[403], "Timer", "", seconds(3))
RegisterMapTimerEvent(404, seconds(3), handlers[404], "Timer", "", seconds(3))
RegisterMapTimerEvent(405, seconds(3), handlers[405], "Timer", "", seconds(3))
RegisterMapTimerEvent(406, seconds(3), handlers[406], "Timer", "", seconds(3))
RegisterMapTimerEvent(407, seconds(3), handlers[407], "Timer", "", seconds(3))
RegisterMapTimerEvent(408, seconds(3), handlers[408], "Timer", "", seconds(3))
RegisterMapTimerEvent(409, seconds(3), handlers[409], "Timer", "", seconds(3))
RegisterMapTimerEvent(410, seconds(3), handlers[410], "Timer", "", seconds(3))
RegisterMapTimerEvent(411, seconds(3), handlers[411], "Timer", "", seconds(3))
RegisterMapTimerEvent(412, seconds(3), handlers[412], "Timer", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30391, "Bone Pile", handlers[30391], "Bone Pile")
RegisterEvent(30392, "Bone Pile", handlers[30392], "Bone Pile")
RegisterEvent(30393, "Bone Pile", handlers[30393], "Bone Pile")
RegisterEvent(30394, "Bone Pile", handlers[30394], "Bone Pile")
RegisterEvent(30395, "Bone Pile", handlers[30395], "Bone Pile")
RegisterEvent(38339, "DestructableBrush0", handlers[38339], "Rocks")
RegisterEvent(38340, "DestructableBrush1", handlers[38340], "Rocks")
RegisterEvent(38341, "DestructableBrush2", handlers[38341], "Rocks")
RegisterEvent(38342, "DestructableBrush3", handlers[38342], "Rocks")
RegisterEvent(38343, "DestructableBrush4", handlers[38343], "Rocks")
RegisterEvent(38344, "DestructableBrush5", handlers[38344], "Rocks")
