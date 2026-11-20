-- Wizard's Lab, MM9 rework (level_generation/projects/mm9r_wizardslab/citylua.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {Cell15 = 1, Cell16 = 2, Cell17 = 3, Cell18 = 4, Cell19 = 5, Cell20 = 6, Cell21 = 7, Cell22 = 8, Cell23 = 9, Cell24 = 10, Cell25 = 11, Cell26 = 12, Cell27 = 13, Cell28 = 14, Closet1Door1 = 15, Closet1Door2 = 16, Closet2Door1 = 17, Closet2Door2 = 18, DoubleDoorL10 = 19, DoubleDoorL11 = 21, DoubleDoorL12 = 23, DoubleDoorL17 = 25, DoubleDoorL18 = 27, DoubleDoorL21 = 29, DoubleDoorL25 = 31, DoubleDoorL27 = 33, DoubleDoorL8 = 35, DoubleDoorL9 = 37, DoubleDoorR10 = 20, DoubleDoorR11 = 22, DoubleDoorR12 = 24, DoubleDoorR17 = 26, DoubleDoorR18 = 28, DoubleDoorR21 = 30, DoubleDoorR25 = 32, DoubleDoorR27 = 34, DoubleDoorR8 = 36, DoubleDoorR9 = 38, Drawer1 = 39, Drawer2 = 40, Drawer3 = 41, Drawer4 = 42, DresserDoorL2 = 44, DresserDoorR2 = 43, Switch15 = 45, Switch16 = 46, Switch17 = 47, Switch18 = 48, Switch19 = 49, Switch20 = 50, Switch21 = 51, Switch22 = 52, Switch23 = 53, Switch24 = 54, Switch25 = 55, Switch26 = 56, Switch27 = 57, Switch28 = 58, blue1 = 59, blue2 = 60, blue3 = 61, blue4 = 62, blue5 = 63, green0 = 64, green2 = 65, green3 = 66, green4 = 67, green5 = 68, purple0 = 69, purple1 = 70, purple3 = 71, purple4 = 72, purple5 = 73, red0 = 74, red1 = 75, red2 = 76, red4 = 77, red5 = 78, ["super eye door_GLASS0"] = 80, ["super eye door_INV"] = 79, white0 = 81, white1 = 82, white2 = 83, white3 = 84, white5 = 85, yellow0 = 86, yellow1 = 87, yellow2 = 88, yellow3 = 89, yellow4 = 90}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end
local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end
SetMapMetadata({onLoad = {1, 902}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}}})


-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- Closet1Door
handlers[102] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- Closet2Door
handlers[103] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- DoubleDoor11
handlers[104] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- DoubleDoor12
handlers[105] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- DoubleDoor17
handlers[106] = function() evt.SetDoorState(29, DoorAction.Trigger) evt.SetDoorState(30, DoorAction.Trigger) end   -- DoubleDoor21
handlers[107] = function() evt.SetDoorState(33, DoorAction.Trigger) evt.SetDoorState(34, DoorAction.Trigger) end   -- DoubleDoor27
handlers[108] = function() evt.SetDoorState(35, DoorAction.Trigger) evt.SetDoorState(36, DoorAction.Trigger) end   -- DoubleDoor8
handlers[109] = function() evt.SetDoorState(37, DoorAction.Trigger) evt.SetDoorState(38, DoorAction.Trigger) end   -- DoubleDoor9
handlers[110] = function() evt.SetDoorState(39, DoorAction.Trigger) end   -- Drawer1
handlers[111] = function() evt.SetDoorState(40, DoorAction.Trigger) end   -- Drawer2
handlers[112] = function() evt.SetDoorState(41, DoorAction.Trigger) end   -- Drawer3
handlers[113] = function() evt.SetDoorState(42, DoorAction.Trigger) end   -- Drawer4
handlers[114] = function() evt.SetDoorState(43, DoorAction.Trigger) evt.SetDoorState(44, DoorAction.Trigger) end   -- DresserDoor2

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- TreasureChest0
handlers[42] = function() evt.OpenChest(1) end   -- TreasureChest1
handlers[43] = function() evt.OpenChest(2) end   -- TreasureChest2

local GROUPS = {Cell15 = {1}, Cell16 = {2}, Cell17 = {3}, Cell18 = {4}, Cell19 = {5}, Cell20 = {6}, Cell21 = {7}, Cell22 = {8}, Cell23 = {9}, Cell24 = {10}, Cell25 = {11}, Cell26 = {12}, Cell27 = {13}, Cell28 = {14}, Closet1Door = {15, 16}, Closet2Door = {17, 18}, DoubleDoor10 = {19, 20}, DoubleDoor11 = {21, 22}, DoubleDoor12 = {23, 24}, DoubleDoor17 = {25, 26}, DoubleDoor18 = {27, 28}, DoubleDoor21 = {29, 30}, DoubleDoor25 = {31, 32}, DoubleDoor27 = {33, 34}, DoubleDoor8 = {35, 36}, DoubleDoor9 = {37, 38}, Drawer1 = {39}, Drawer2 = {40}, Drawer3 = {41}, Drawer4 = {42}, DresserDoor2 = {43, 44}, Switch15 = {45}, Switch16 = {46}, Switch17 = {47}, Switch18 = {48}, Switch19 = {49}, Switch20 = {50}, Switch21 = {51}, Switch22 = {52}, Switch23 = {53}, Switch24 = {54}, Switch25 = {55}, Switch26 = {56}, Switch27 = {57}, Switch28 = {58}, blue1 = {59}, blue2 = {60}, blue3 = {61}, blue4 = {62}, blue5 = {63}, green0 = {64}, green2 = {65}, green3 = {66}, green4 = {67}, green5 = {68}, purple0 = {69}, purple1 = {70}, purple3 = {71}, purple4 = {72}, purple5 = {73}, red0 = {74}, red1 = {75}, red2 = {76}, red4 = {77}, red5 = {78}, ["super eye door"] = {79, 80}, white0 = {81}, white1 = {82}, white2 = {83}, white3 = {84}, white5 = {85}, yellow0 = {86}, yellow1 = {87}, yellow2 = {88}, yellow3 = {89}, yellow4 = {90}}
local function trigger(group) for _, d in ipairs(GROUPS[group]) do evt.SetDoorState(d, DoorAction.Trigger) end end
local function openGroup(group) for _, d in ipairs(GROUPS[group]) do evt.SetDoorState(d, DoorAction.Open) end end
local function closeGroup(group) for _, d in ipairs(GROUPS[group]) do evt.SetDoorState(d, DoorAction.Close) end end
local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function fx(id, p) evt.SpawnWorldEffect(id, p[1], p[2], p[3]) end
local function sprite(cog, on) if cog then evt.SetSprite(cog, on and 1 or 0, "0") end end
local function inBox(b, x, y, z)
    return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] and z >= b[1][3] and z <= b[2][3]
end
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function locked()
    evt.PlaySoundName("door/doorlock01.wav", 0, 0, 0)
    evt.StatusText("The door is locked.")
end
local COG = {}

-- MM9's locked pair (DoubleDoorL10/R10: Locked 1, no key, nothing unlocks it).
handlers[200] = function() locked() end

-- The super eye (DAT wiring, no .scr). EvilGrandSorcerer1's DeathTriggerTarget 'super eye trigger':
-- GlowingLight0 off, 'super eye door' (the force field) open (256 down), DoubleDoorL25 and R18 closed (MM9
-- names one leaf of each; here both pairs shut, as their CloseWaitTime 4 shuts the other leaves anyway) and
-- both pairs locked. Oculus0's DeathTriggerTarget 'super eye trigger0' unlocks them (the targets
-- 'super eye lock' and 'super eye unlock' name no object). Not in MM9: an Oculus killed first leaves the
-- pairs unlocked (MM9 would lock them for good).
local function superEye()
    if var("SuperEye") == 1 then return end
    set("SuperEye", 1)
    evt.SetLight(40338, false)
    openGroup("super eye door")
    if var("OculusDead") == 1 then return end
    closeGroup("DoubleDoor18"); closeGroup("DoubleDoor25")
    set("EyeLock", 1)
end
handlers[201] = function()   -- DoubleDoor18: a plain double door unless the super eye locked it
    if var("EyeLock") == 1 then locked() return end
    trigger("DoubleDoor18")
end
handlers[202] = function()   -- DoubleDoor25: a plain double door unless the super eye locked it
    if var("EyeLock") == 1 then locked() return end
    trigger("DoubleDoor25")
end

-- The cell levers (DAT wiring: RotatingDoor Switch<n>, OpenTriggerTarget0 Cell<n> 'open',
-- CloseTriggerTarget0 Cell<n> 'toggle'; the AITrack 'on'/'off' messages, MM9's AI rails, are not
-- carried).
handlers[210] = function()   -- Switch15 -> Cell15
    local on = var("Switch15") == 0
    set("Switch15", on and 1 or 0)
    trigger("Switch15")
    if on then openGroup("Cell15") else trigger("Cell15") end
end
handlers[211] = function()   -- Switch16 -> Cell16
    local on = var("Switch16") == 0
    set("Switch16", on and 1 or 0)
    trigger("Switch16")
    if on then openGroup("Cell16") else trigger("Cell16") end
end
handlers[212] = function()   -- Switch17 -> Cell17
    local on = var("Switch17") == 0
    set("Switch17", on and 1 or 0)
    trigger("Switch17")
    if on then openGroup("Cell17") else trigger("Cell17") end
end
handlers[213] = function()   -- Switch18 -> Cell18
    local on = var("Switch18") == 0
    set("Switch18", on and 1 or 0)
    trigger("Switch18")
    if on then openGroup("Cell18") else trigger("Cell18") end
end
handlers[214] = function()   -- Switch19 -> Cell19
    local on = var("Switch19") == 0
    set("Switch19", on and 1 or 0)
    trigger("Switch19")
    if on then openGroup("Cell19") else trigger("Cell19") end
end
handlers[215] = function()   -- Switch20 -> Cell20
    local on = var("Switch20") == 0
    set("Switch20", on and 1 or 0)
    trigger("Switch20")
    if on then openGroup("Cell20") else trigger("Cell20") end
end
handlers[216] = function()   -- Switch21 -> Cell21
    local on = var("Switch21") == 0
    set("Switch21", on and 1 or 0)
    trigger("Switch21")
    if on then openGroup("Cell21") else trigger("Cell21") end
end
handlers[217] = function()   -- Switch22 -> Cell22
    local on = var("Switch22") == 0
    set("Switch22", on and 1 or 0)
    trigger("Switch22")
    if on then openGroup("Cell22") else trigger("Cell22") end
end
handlers[218] = function()   -- Switch23 -> Cell23
    local on = var("Switch23") == 0
    set("Switch23", on and 1 or 0)
    trigger("Switch23")
    if on then openGroup("Cell23") else trigger("Cell23") end
end
handlers[219] = function()   -- Switch24 -> Cell24
    local on = var("Switch24") == 0
    set("Switch24", on and 1 or 0)
    trigger("Switch24")
    if on then openGroup("Cell24") else trigger("Cell24") end
end
handlers[220] = function()   -- Switch25 -> Cell25
    local on = var("Switch25") == 0
    set("Switch25", on and 1 or 0)
    trigger("Switch25")
    if on then openGroup("Cell25") else trigger("Cell25") end
end
handlers[221] = function()   -- Switch26 -> Cell26
    local on = var("Switch26") == 0
    set("Switch26", on and 1 or 0)
    trigger("Switch26")
    if on then openGroup("Cell26") else trigger("Cell26") end
end
handlers[222] = function()   -- Switch27 -> Cell27
    local on = var("Switch27") == 0
    set("Switch27", on and 1 or 0)
    trigger("Switch27")
    if on then openGroup("Cell27") else trigger("Cell27") end
end
handlers[223] = function()   -- Switch28 -> Cell28
    local on = var("Switch28") == 0
    set("Switch28", on and 1 or 0)
    trigger("Switch28")
    if on then openGroup("Cell28") else trigger("Cell28") end
end

-- The teleporters. TeleporterSwitch.scr (the crystals, "<teleporter> <destination> <light>"): a click sets
-- the station's destination (MM9's console TELEPORTER_DESTINATION, then 'on' + 'update' to that teleporter
-- only), plays wizardeyeloop.wav and the spell reaver at the teleporter and lights the crystal's colour for
-- 4 s, its 'use' removed meanwhile. TeleporterMulti.scr (TeleporterAt*, Dims 50): the party walking in goes
-- to the destination (UseRotation: facing it), and 0.5 s later the teleporter turns off (:ResetDestination):
-- one trip per click. With no destination set it does nothing (StartOn 1, TeleportDestination "").
local STATIONS = {
    {name = "TeleporterAtBlue", box = {{-16488, 8314, 236}, {-16158, 8644, 579}}, at = {-16323, 8479, 451}},
    {name = "TeleporterAtGreen", box = {{-17819, 12266, -778}, {-17489, 12596, -435}}, at = {-17654, 12431, -563}},
    {name = "TeleporterAtPurple", box = {{-8029, 15082, 1505}, {-7699, 15412, 1848}}, at = {-7864, 15247, 1720}},
    {name = "TeleporterAtRed", box = {{-3114, 3071, 31}, {-2784, 3401, 374}}, at = {-2949, 3236, 246}},
    {name = "TeleporterAtWhite", box = {{-206, 7003, 31}, {124, 7333, 374}}, at = {-41, 7168, 246}},
    {name = "TeleporterAtYellow", box = {{327, 10464, 31}, {657, 10794, 374}}, at = {492, 10629, 246}},
}
local DESTINATIONS = {
    {name = "DestinationBlue", at = {-16323, 8274, 204}, yaw = 1536},
    {name = "DestinationGreen", at = {-17654, 12227, -817}, yaw = 1536},
    {name = "DestinationPurple", at = {-7864, 15043, 1477}, yaw = 1536},
    {name = "DestinationRed", at = {-2949, 3441, 2}, yaw = 512},
    {name = "DestinationWhite", at = {164, 7168, 2}, yaw = 0},
    {name = "DestinationYellow", at = {492, 10834, 2}, yaw = 512},
}
local CRYSTALS = {
    [230] = {name = "yellow0", station = 1, dest = 6, light = 40757},
    [231] = {name = "white0", station = 1, dest = 5, light = 40760},
    [232] = {name = "red0", station = 1, dest = 4, light = 40756},
    [233] = {name = "purple0", station = 1, dest = 3, light = 40759},
    [234] = {name = "green0", station = 1, dest = 2, light = 40755},
    [235] = {name = "yellow1", station = 2, dest = 6, light = 40763},
    [236] = {name = "white1", station = 2, dest = 5, light = 40766},
    [237] = {name = "red1", station = 2, dest = 4, light = 40762},
    [238] = {name = "purple1", station = 2, dest = 3, light = 40765},
    [239] = {name = "blue1", station = 2, dest = 1, light = 40764},
    [240] = {name = "yellow2", station = 3, dest = 6, light = 40769},
    [241] = {name = "white2", station = 3, dest = 5, light = 40772},
    [242] = {name = "red2", station = 3, dest = 4, light = 40768},
    [243] = {name = "green2", station = 3, dest = 2, light = 40767},
    [244] = {name = "blue2", station = 3, dest = 1, light = 40770},
    [245] = {name = "yellow3", station = 4, dest = 6, light = 40775},
    [246] = {name = "white3", station = 4, dest = 5, light = 40778},
    [247] = {name = "purple3", station = 4, dest = 3, light = 40777},
    [248] = {name = "green3", station = 4, dest = 2, light = 40773},
    [249] = {name = "blue3", station = 4, dest = 1, light = 40776},
    [250] = {name = "yellow4", station = 5, dest = 6, light = 40781},
    [251] = {name = "red4", station = 5, dest = 4, light = 40780},
    [252] = {name = "purple4", station = 5, dest = 3, light = 40783},
    [253] = {name = "green4", station = 5, dest = 2, light = 40779},
    [254] = {name = "blue4", station = 5, dest = 1, light = 40782},
    [255] = {name = "white5", station = 6, dest = 5, light = 40790},
    [256] = {name = "red5", station = 6, dest = 4, light = 40786},
    [257] = {name = "purple5", station = 6, dest = 3, light = 40789},
    [258] = {name = "green5", station = 6, dest = 2, light = 40785},
    [259] = {name = "blue5", station = 6, dest = 1, light = 40788},
}
-- The closet teleporters (Teleporter1/2: no script, StartOn 1, UseRotation 0): always on, the party keeps
-- its facing.
local CLOSETS = {
    {name = "Teleporter1", box = {{5114, 11811, -41}, {5331, 11926, 287}}, at = {-1710, 13230, 2}},
    {name = "Teleporter2", box = {{-1809, 13357, -44}, {-1612, 13472, 284}}, at = {5222, 12083, 2}},
}
local function teleport(at, yaw)
    sound("magic/teleport.wav")
    evt.MoveToMap(at[1], at[2], at[3], yaw, 0, 0, 0, 0)
end
local function pressCrystal(event)
    local c = CRYSTALS[event]
    if var("CrystalBusy" .. c.station) == 1 then return end
    set("Dest" .. c.station, c.dest)
    set("CrystalBusy" .. c.station, 1); set("CrystalEvent" .. c.station, event)
    evt.SetLight(c.light, true)
    sound("magic/wizardeyeloop.wav")
    fx("mm9:spell_reaver", STATIONS[c.station].at)
    openGroup(c.name)
    arm(263 + c.station - 1, 4)
end
local function crystalOff(station)
    local event = var("CrystalEvent" .. station)
    set("CrystalBusy" .. station, 0)
    if CRYSTALS[event] == nil then return end
    evt.SetLight(CRYSTALS[event].light, false)
    closeGroup(CRYSTALS[event].name)
end
for event, _ in pairs(CRYSTALS) do handlers[event] = function() pressCrystal(event) end end
for station = 1, #STATIONS do
    handlers[263 + station - 1] = function()
        if fired(263 + station - 1) then crystalOff(station) end
    end
end

-- The summoning in the tower top. WizardLabCamera.scr (CameraSummon) runs a camera cinema when the party
-- first arrives at DestinationPurple (a touch Trigger, ActivationCount 1, 'next' to the camera): fade out 2
-- s, then shots at MarkerLocation0-3; its first shot's notify (TriggerNotify0) starts SummoningGuy0. The
-- cinema is the cinematic summoning (cinematic_scenes), whose steps run the ritual's ticks below (each once,
-- in order; a skip runs them at once). WizardSummoner.scr (six apprentices, friends of the party):
-- :ConjureSpell (thunder, its shooter's sparklies and green dots, WizardEffect.scr), 2.5 s later
-- :FinishSpell (the shooter's lightning and bugs at SummonLocation: shoot) starts the next in the chain
-- 0 -> 6 -> 1 -> 5 -> 2 -> 4 -> the master.
-- WizardMaster.scr (SummoningGuy3): :ConjureSpell (meteor, town portal, sparklies, column
-- of fire at SummonLocation), 2.5 s later :Summon spawns a Greater Demon (WizardDemon.scr: enemy of the
-- sorcerers and the party), elemental blast and paralyze. The apprentices then fight it (AddEnemy
-- GreaterDemon); one hurt by anything but the party dies at once (:OnDamage -> Die) and sends the master
-- 'finish'; at six the master banishes the demon (:BanishDemon: dark grasp, lifted 4 s, dropped 2 s,
-- :RemoveDemon). When the demon is gone (:OnTargetDead) the master passes out (dies) while the party is his
-- friend, else turns on the party (EvilSorcerer.scr). Hurting an apprentice makes it the party's enemy and
-- the party no friend (PLAYER_FRIEND FALSE); hurting the master only the latter. Here: a dying apprentice is
-- killed by a lethal hit (the damage hook); the master passing out is hidden (no script call kills an
-- actor); after the demon is up any hit on an apprentice counts as the demon's (README).
local SUMMONERS = {46, 52, 47, 51, 48, 50}
local SUMMONER_OF = {[46] = 1, [52] = 2, [47] = 3, [51] = 4, [48] = 5, [50] = 6}
local SUMMON_AT = {-7864, 14418, 1477}
local SHOOTER_AT = {{-7455, 14828, 1760}, {-8274, 14828, 1760}, {-7291, 14418, 1760}, {-8438, 14418, 1760}, {-7455, 14008, 1760}, {-8274, 14008, 1760}}   -- their lightning's start
local MASTER = 49
local function summonerAlive(k)
    return not evt.CheckMonstersKilled(ActorKillCheck.Group, 21 + k - 1, 0, false)
end
-- Apprentice k's :FinishSpell (Trigger hShooter, shoot), run by the next tick (2.5 s after its :ConjureSpell,
-- as the next caster starts): its shooter (ShooterSummon<k>, ProjectileName Lightning) fires at SummonLocation
-- (PROJECTILE.txt Lightning: launch chainlight01, explosion Sparks with chainlight03; here an arc and MM9's
-- Sparks explosion) and WizardEffect.scr :PlayShootEffect plays SPELL_BUGS at SummonLocation. A dead
-- apprentice's :FinishSpell never comes.
local function shoot(k, timed)
    if not summonerAlive(k) then return end
    local from = SHOOTER_AT[k]
    evt.Beam("SummonBeam" .. k, "openyamm:fx/arc_beam", from[1], from[2], from[3], SUMMON_AT[1], SUMMON_AT[2], SUMMON_AT[3], 1.0)
    fx("mm9:explosion_sparks", SUMMON_AT)
    fx("mm9:bugs", SUMMON_AT)
    if timed then sound("weapons/chainlight01.wav"); sound("weapons/chainlight03.wav") end
end
-- timed: timer 270 runs a summoning an old save left half-way (it plays the sounds the cinematic's cues play
-- and arms the next tick)
local function ritualStep(timed)
    local step = var("RitualStep")
    if step >= 2 and step <= 7 then shoot(step - 1, timed) end
    if step >= 1 and step <= 6 then
        if not summonerAlive(step) then return end   -- MM9: a dead apprentice never starts the next
        if timed then sound("ambient/thunder/thunderlong.wav") end
        -- WizardEffect.scr :PlayConjureEffect: DoClientFX hCaster (the apprentice), SPELL_SPARKLIES, on its
        -- body; DoClientFX hMe (the shooter above it), SPELL_GREENDOTS. Its hands' dots are its clips' own DoFX
        -- keys (fidget2 redyeldots, rattack1 greenyeldots: actors.yml events, played by the cinematic's cues).
        MM9.actorFx(SUMMONERS[step], "mm9:sparklies")
        fx("mm9:greenyeldots", SHOOTER_AT[step])
        set("RitualStep", step + 1)
        if timed then arm(270, 2.5) end
    elseif step == 7 then
        if evt.CheckMonstersKilled(ActorKillCheck.Group, 27, 0, false) then return end
        fx("mm9:meteor_shower", SUMMON_AT); fx("mm9:town_portal", SUMMON_AT)
        fx("mm9:sparklies", SUMMON_AT); fx("mm9:column_of_fire", SUMMON_AT)
        if timed then sound("magic/cast03.wav") end
        set("RitualStep", 8)
        if timed then arm(270, 2.5) end
    elseif step == 8 then
        if timed then sound("animsounds/dragon/fidget2.wav") end
        evt.SummonMonstersById({monster = 9242, x = SUMMON_AT[1], y = SUMMON_AT[2], z = SUMMON_AT[3], radius = 32, group = 28, count = 1})
        fx("mm9:elemental_blast", SUMMON_AT); fx("mm9:paralyze", SUMMON_AT)
        -- :Backup then :BeginBanish (the master steps back): DoClientFX hMe, SPELL_SPARKLIES and SPELL_BLUEFIRE
        MM9.actorFx(MASTER, "mm9:sparklies"); MM9.actorFx(MASTER, "mm9:fireblue")
        for _, row in ipairs({9156, 9158}) do
            evt.SetMonsterRelation(9242, row, 2); evt.SetMonsterRelation(row, 9242, 2)
        end
        set("RitualStep", 9); set("DemonUp", 1)
    end
end
local function ritualAdvance(step)   -- a step of the cinematic summoning: the ritual's tick `step`
    if var("RitualStep") == step then ritualStep(false) end
end
local function startRitual()   -- DestinationPurple -> CameraSummon 'next' (once): the cinematic
    if var("RitualStep") ~= 0 then return end
    set("RitualStep", 1)
    MM9Cinematic.start("summoning")
end
handlers[270] = function() if fired(270) then ritualStep(true) end end
local function demonGone()   -- WizardMaster.scr :OnTargetDead
    if var("DemonGone") == 1 then return end
    set("DemonGone", 1)
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 27, 0, false) then return end
    if var("Betrayed") == 1 then
        evt.SetMonGroupBit(27, MonsterBits.Hostile, true)   -- RunScript EvilSorcerer.scr
    else
        sound("animsounds/evilsorcerer/wince2.wav")   -- :PassOut
        MM9.removeActor(MASTER)
    end
end
local function banish()   -- :BanishDemon at the sixth 'finish'
    if var("Banishing") == 1 or var("DemonGone") == 1 then return end
    set("Banishing", 1)
    sound("magic/wizardeyeloop.wav")
    fx("mm9:dark_grasp", SUMMON_AT)
    arm(271, 6.0)
end
handlers[271] = function()   -- :RemoveDemon
    if not fired(271) then return end
    sound("magic/cast01.wav")
    fx("mm9:spell_reaver", SUMMON_AT); fx("mm9:elemental_blast", SUMMON_AT)
    -- Trigger hLocation, destroy: a demon already slain stays a corpse (DESTROY on a dead AI does nothing)
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 28, 0, false) then
        evt.SetMonGroupBit(28, MonsterBits.Invisible, true)
    end
    demonGone()
end
local function betray(index)   -- WizardSummoner.scr / WizardMaster.scr :OnDamage by the party
    set("Betrayed", 1)
    local k = SUMMONER_OF[index]
    if k ~= nil then evt.SetMonGroupBit(21 + k - 1, MonsterBits.Hostile, true) end
end
handlers[281] = function(context)
    local index = context.actorIndex
    if SUMMONER_OF[index] == nil and index ~= MASTER then return end
    if var("DemonUp") == 0 or var("DemonGone") == 1 then betray(index) return end
    if SUMMONER_OF[index] ~= nil then   -- :OnDamage, not the party: DoClientFX hShooter (itself), SPELL_BLUEDOTS; Die
        MM9.actorFx(index, "mm9:bluedots", "palm_left,palm_right")   -- its emitters on LHand1 and RHand1
        evt.SetHookDamage(100000)
    end
end
handlers[280] = function(context)
    local index = context.actorIndex
    if index == 33 then superEye() end   -- EvilGrandSorcerer1
    if index == 34 then set("OculusDead", 1); set("EyeLock", 0) end   -- Oculus0
    -- 'finish' to the master: a dead master takes none (MM9.receives), so no banishing
    if SUMMONER_OF[index] ~= nil and var("DemonUp") == 1
            and MM9.receives("wizardslab", "SummoningGuy3", "finish", MASTER) then
        set("Finished", var("Finished") + 1)
        if var("Finished") >= 6 then banish() end
    end
    if var("DemonUp") == 1 and var("DemonGone") == 0
            and evt.CheckMonstersKilled(ActorKillCheck.Group, 28, 0, false) then
        demonGone()
    end
end

-- NPC55.scr (Mad Wizard Robinssen, ReverendMonk0, RUDE 55): a click plays his voice and
-- opens the dialogue (:OnUse); its exit (:OnRude -> :BlackOrb) sells the Black Orb of Knowledge: with the
-- deal agreed (key 312, RUDE row 8.1) and no orb yet (313): 2 000 gold taken, key 313, item 250, quest.wav;
-- without the gold the deal is off (312 taken) and a party voice complains (nogold.inc :NoGold, not
-- carried).
handlers[53044] = function()
    MM9.playSound("voices/npc/npc_055.wav")
    MM9.openRude(55)
end
handlers[50044] = function()
    if has(313) or not has(312) then return end
    if MM9.hasGold(2000) == 1 then
        MM9.takeGold(2000); MM9.giveKey(313); MM9.giveItem(250, "wizardslab:Robinssen"); quest()
    else
        MM9.takeKey(312)
        evt.StatusText("You don't have enough gold.")
    end
end

-- BookLetter.scr letters (BOOK AND SCROLL TEXT.csv rows), Book.scr books (pages turn, no text),
-- Relic.scr.
handlers[330] = function() sound("events/bookopen.wav") end   -- Prop148 (Book.scr)
handlers[331] = function() sound("events/bookopen.wav") end   -- Prop149 (Book.scr)
handlers[332] = function() sound("events/bookopen.wav"); evt.SimpleMessage("To All Wizards Studying Here\n\nI have, for the last time, woken up to a pile of deformed frogs in my washbasin.  Will whoever is responsible for these foul creatures please take care of their behavior?  I would hate for my Giant Magreeb to end up in your washbasin.  He doesn't like these frogs, and who knows how he will react to a constant stream of them.\n\nHallin, Mage") end   -- Prop7 (498)
handlers[333] = function() sound("events/bookopen.wav"); evt.SimpleMessage("Formula\n\n16 toads, boiled.\n27 lbs insect eyes (doesn't matter which insect)\n4 gallons worm blood.\n\nMix this mixture well while reciting the following chant, \"Ahal Natrax\".  Continue for four hours.  When complete, pour mixture into cube mold, and chill for four hours.\n\nYour Colloidal Cube should be then enchanted with the \"Restore Life\" spell.") end   -- Prop8 (499)
-- barrel: Relic.scr, the Saint's Relic (item 368), a world item (dungeon/pickups.py). Its pickup: with
-- key 338 and no 340 key 340, else without 339 key 339; quest.wav plays.
handlers[334] = function()
    local key = has(338) and 340 or 339
    if has(key) then return end
    MM9.giveKey(key); quest()
end

-- MM9's Teleporter and Trigger volumes, polled four times a second (the party's feet in the box; one shot
-- per entry).
local PURPLE = {{-7942, 14965, 1464}, {-7786, 15121, 1720}}   -- DestinationPurple (Trigger, TouchNotify, ActivationCount 1)
local function volumes()
    local x, y, z = evt.GetPartyPosition()
    for k, s in ipairs(STATIONS) do
        local inside = inBox(s.box, x, y, z)
        local entered = inside and var("In" .. s.name) == 0
        set("In" .. s.name, inside and 1 or 0)
        if entered and var("Dest" .. k) > 0 then
            local dest = var("Dest" .. k)
            local d = DESTINATIONS[dest]
            set("Dest" .. k, 0)   -- TeleporterMulti.scr :ResetDestination
            teleport(d.at, d.yaw)
            if dest == 3 then startRitual() end
            return
        end
    end
    for _, c in ipairs(CLOSETS) do
        local inside = inBox(c.box, x, y, z)
        local entered = inside and var("In" .. c.name) == 0
        set("In" .. c.name, inside and 1 or 0)
        if entered then teleport(c.at, nil) return end
    end
    if inBox(PURPLE, x, y, z) then startRitual() end   -- destination 3
end
local function poll()
    volumes()
    evt.StartTimer(262, seconds(0.25))
end
handlers[262] = poll
handlers[1] = function()   -- map load
    for station = 1, #STATIONS do if var("CrystalBusy" .. station) == 1 then crystalOff(station) end end
    local step = var("RitualStep")   -- a summoning saved half-way goes on
    if step >= 1 and step <= 8 then arm(270, 2.5) end
    if var("Banishing") == 1 and var("DemonGone") == 0 then arm(271, 1) end
    poll()
end
-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30217] = function() evt.SearchLootProp("mm9:wizardslab:object:217") end   -- BonePile0
handlers[30218] = function() evt.SearchLootProp("mm9:wizardslab:object:218") end   -- BonePile1
handlers[30219] = function() evt.SearchLootProp("mm9:wizardslab:object:219") end   -- BonePile2
handlers[30220] = function() evt.SearchLootProp("mm9:wizardslab:object:220") end   -- BonePile3

-- MM9's bonus props (dungeon/objects.py bonus_lines; the use of each class, object.lto): wells, cauldrons,
-- cook pots and clovers.
handlers[30882] = function() MM9.useCauldron(882, 1, 5) end   -- Cauldron0 (Cauldron)
handlers[30883] = function() MM9.useWell(883, 0, 0, 5, 0, 50) end   -- Cauldron1 (WellMMIX)
handlers[30884] = function() MM9.useWell(884, 1, 0, 5, 0, 50) end   -- Cauldron2 (WellMMIX)

-- MM9's PerceptionBrushes (dungeon/perception.py): the red glow shows to a party whose Perception reaches the
-- brush's PerceptionValue, checked on load and every 3 s; map Lua turns one off for good with
-- set("HintOff<cog>", 1) (MM9's Off message to the brush).
local HINTS = {[23682] = 8}
handlers[901] = function()
    for cog, value in pairs(HINTS) do
        local want = (var("HintOff" .. cog) == 0 and evt.CheckSkill(29, 0, value)) and 2 or 1
        if var("Hint" .. cog) ~= want then
            set("Hint" .. cog, want)
            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1)
        end
    end
end
handlers[902] = function()   -- map load: the shared objects
    for cog, _ in pairs(HINTS) do set("Hint" .. cog, 0) end
    handlers[901]()
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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(200, "Locked door", handlers[200], "Door")
RegisterEvent(201, "Door", handlers[201], "Door")
RegisterEvent(202, "Door", handlers[202], "Door")
RegisterEvent(210, "Lever", handlers[210], "Lever")
RegisterEvent(211, "Lever", handlers[211], "Lever")
RegisterEvent(212, "Lever", handlers[212], "Lever")
RegisterEvent(213, "Lever", handlers[213], "Lever")
RegisterEvent(214, "Lever", handlers[214], "Lever")
RegisterEvent(215, "Lever", handlers[215], "Lever")
RegisterEvent(216, "Lever", handlers[216], "Lever")
RegisterEvent(217, "Lever", handlers[217], "Lever")
RegisterEvent(218, "Lever", handlers[218], "Lever")
RegisterEvent(219, "Lever", handlers[219], "Lever")
RegisterEvent(220, "Lever", handlers[220], "Lever")
RegisterEvent(221, "Lever", handlers[221], "Lever")
RegisterEvent(222, "Lever", handlers[222], "Lever")
RegisterEvent(223, "Lever", handlers[223], "Lever")
RegisterEvent(230, "Crystal", handlers[230], "Crystal")
RegisterEvent(231, "Crystal", handlers[231], "Crystal")
RegisterEvent(232, "Crystal", handlers[232], "Crystal")
RegisterEvent(233, "Crystal", handlers[233], "Crystal")
RegisterEvent(234, "Crystal", handlers[234], "Crystal")
RegisterEvent(235, "Crystal", handlers[235], "Crystal")
RegisterEvent(236, "Crystal", handlers[236], "Crystal")
RegisterEvent(237, "Crystal", handlers[237], "Crystal")
RegisterEvent(238, "Crystal", handlers[238], "Crystal")
RegisterEvent(239, "Crystal", handlers[239], "Crystal")
RegisterEvent(240, "Crystal", handlers[240], "Crystal")
RegisterEvent(241, "Crystal", handlers[241], "Crystal")
RegisterEvent(242, "Crystal", handlers[242], "Crystal")
RegisterEvent(243, "Crystal", handlers[243], "Crystal")
RegisterEvent(244, "Crystal", handlers[244], "Crystal")
RegisterEvent(245, "Crystal", handlers[245], "Crystal")
RegisterEvent(246, "Crystal", handlers[246], "Crystal")
RegisterEvent(247, "Crystal", handlers[247], "Crystal")
RegisterEvent(248, "Crystal", handlers[248], "Crystal")
RegisterEvent(249, "Crystal", handlers[249], "Crystal")
RegisterEvent(250, "Crystal", handlers[250], "Crystal")
RegisterEvent(251, "Crystal", handlers[251], "Crystal")
RegisterEvent(252, "Crystal", handlers[252], "Crystal")
RegisterEvent(253, "Crystal", handlers[253], "Crystal")
RegisterEvent(254, "Crystal", handlers[254], "Crystal")
RegisterEvent(255, "Crystal", handlers[255], "Crystal")
RegisterEvent(256, "Crystal", handlers[256], "Crystal")
RegisterEvent(257, "Crystal", handlers[257], "Crystal")
RegisterEvent(258, "Crystal", handlers[258], "Crystal")
RegisterEvent(259, "Crystal", handlers[259], "Crystal")
RegisterMapTimerEvent(263, seconds(3), handlers[263], "Crystal light", "", seconds(3))
RegisterMapTimerEvent(264, seconds(3), handlers[264], "Crystal light", "", seconds(3))
RegisterMapTimerEvent(265, seconds(3), handlers[265], "Crystal light", "", seconds(3))
RegisterMapTimerEvent(266, seconds(3), handlers[266], "Crystal light", "", seconds(3))
RegisterMapTimerEvent(267, seconds(3), handlers[267], "Crystal light", "", seconds(3))
RegisterMapTimerEvent(268, seconds(3), handlers[268], "Crystal light", "", seconds(3))
RegisterMapTimerEvent(270, seconds(3), handlers[270], "Summoning", "", seconds(3))
RegisterMapTimerEvent(271, seconds(3), handlers[271], "Banishing", "", seconds(3))
RegisterEvent(53044, "Robinssen", handlers[53044])
RegisterEvent(50044, "Robinssen", handlers[50044])
RegisterEvent(330, "Prop148", handlers[330], "Book")
RegisterEvent(331, "Prop149", handlers[331], "Book")
RegisterEvent(332, "Prop7", handlers[332], "Read")
RegisterEvent(333, "Prop8", handlers[333], "Read")
RegisterEvent(334, "barrel", handlers[334])
RegisterMapTimerEvent(262, seconds(3), handlers[262], "Teleporters", "", seconds(3))
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30217, "Bone Pile", handlers[30217], "Bone Pile")
RegisterEvent(30218, "Bone Pile", handlers[30218], "Bone Pile")
RegisterEvent(30219, "Bone Pile", handlers[30219], "Bone Pile")
RegisterEvent(30220, "Bone Pile", handlers[30220], "Bone Pile")
RegisterEvent(30882, "Cauldron", handlers[30882], "Drink")
RegisterEvent(30883, "Well", handlers[30883], "Drink")
RegisterEvent(30884, "Well", handlers[30884], "Drink")
RegisterMapTimerEvent(901, seconds(3), handlers[901], "Perception hints", "", seconds(3))
RegisterEvent(902, "Shared objects", handlers[902])
RegisterMonsterKilledHook(280, "Wizard's Lab deaths", handlers[280])
RegisterMonsterDamageHook(281, "The summoners", handlers[281])


-- MM9 cutscenes as in-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md; mm9r_common/cutscenes.py).
MM9Cinematic = MM9Cinematic or { steps = {}, play = {} }

function MM9Cinematic.runStep(id, index)
    local step = MM9Cinematic.steps[id][index]
    local name = "Cinema." .. id .. ".step." .. step[1]
    if evt.GetMapVar(name, 0) == 0 then
        evt.SetMapVar(name, 1)
        step[2]()
    end
end

function MM9Cinematic.finish(id)
    for index = 1, #MM9Cinematic.steps[id] do
        MM9Cinematic.runStep(id, index)
    end
end

-- Starts a cinematic once per map state (its started map var); a second start while or after it played does nothing.
function MM9Cinematic.start(id)
    local play = MM9Cinematic.play[id]
    if play ~= nil then
        play()
    end
end

-- Cinematic summoning (WizardLabCamera.scr, CutScene.inc (CameraSummon); WizardSummoner.scr, WizardMaster.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["summoning"] = {
    { "apprentice1", function()
        ritualAdvance(1)
    end },
    { "apprentice2", function()
        ritualAdvance(2)
    end },
    { "apprentice3", function()
        ritualAdvance(3)
    end },
    { "apprentice4", function()
        ritualAdvance(4)
    end },
    { "apprentice5", function()
        ritualAdvance(5)
    end },
    { "apprentice6", function()
        ritualAdvance(6)
    end },
    { "master", function()
        ritualAdvance(7)
    end },
    { "demon", function()
        ritualAdvance(8)
    end },
}
RegisterEvent(36001, "Cinema summoning: apprentice1", function() MM9Cinematic.runStep("summoning", 1) end)
RegisterEvent(36002, "Cinema summoning: apprentice2", function() MM9Cinematic.runStep("summoning", 2) end)
RegisterEvent(36003, "Cinema summoning: apprentice3", function() MM9Cinematic.runStep("summoning", 3) end)
RegisterEvent(36004, "Cinema summoning: apprentice4", function() MM9Cinematic.runStep("summoning", 4) end)
RegisterEvent(36005, "Cinema summoning: apprentice5", function() MM9Cinematic.runStep("summoning", 5) end)
RegisterEvent(36006, "Cinema summoning: apprentice6", function() MM9Cinematic.runStep("summoning", 6) end)
RegisterEvent(36007, "Cinema summoning: master", function() MM9Cinematic.runStep("summoning", 7) end)
RegisterEvent(36008, "Cinema summoning: demon", function() MM9Cinematic.runStep("summoning", 8) end)
RegisterEvent(36000, "Cinema summoning: done", function() MM9Cinematic.finish("summoning") end)
MM9Cinematic.play["summoning"] = function()
    if evt.GetMapVar("Cinema.summoning.started", 0) == 0 then
        evt.SetMapVar("Cinema.summoning.started", 1)
        evt.PlayCinematic("summoning", 36000)
    end
end
