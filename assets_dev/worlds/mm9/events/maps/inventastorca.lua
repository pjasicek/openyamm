-- Inventa Storca, MM9 rework (level_generation/projects/mm9r_inventastorca/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {DeskDrawer = 1, DeskDrawer0 = 2, DoubleDoorL1 = 3, DoubleDoorL10 = 5, DoubleDoorL11 = 7, DoubleDoorL12 = 9, DoubleDoorL13 = 11, DoubleDoorL14 = 13, DoubleDoorL2 = 15, DoubleDoorL3 = 17, DoubleDoorL4 = 19, DoubleDoorL5 = 21, DoubleDoorL6 = 23, DoubleDoorL7 = 25, DoubleDoorL8 = 27, DoubleDoorL9 = 29, DoubleDoorR1 = 4, DoubleDoorR10 = 6, DoubleDoorR11 = 8, DoubleDoorR12 = 10, DoubleDoorR13 = 12, DoubleDoorR14 = 14, DoubleDoorR2 = 16, DoubleDoorR3 = 18, DoubleDoorR4 = 20, DoubleDoorR5 = 22, DoubleDoorR6 = 24, DoubleDoorR7 = 26, DoubleDoorR8 = 28, DoubleDoorR9 = 30, Drawer1 = 31, Drawer10 = 32, Drawer11 = 33, Drawer12 = 34, Drawer13 = 35, Drawer14 = 36, Drawer15 = 37, Drawer16 = 38, Drawer2 = 39, Drawer3 = 40, Drawer4 = 41, Drawer5 = 42, Drawer6 = 43, Drawer7 = 44, Drawer8 = 45, Drawer9 = 46, DresserDoorL1 = 48, DresserDoorL2 = 50, DresserDoorL3 = 52, DresserDoorL4 = 54, DresserDoorL5 = 56, DresserDoorL6 = 58, DresserDoorL7 = 60, DresserDoorL8 = 62, DresserDoorR1 = 47, DresserDoorR2 = 49, DresserDoorR3 = 51, DresserDoorR4 = 53, DresserDoorR5 = 55, DresserDoorR6 = 57, DresserDoorR7 = 59, DresserDoorR8 = 61, FallingBookcase1 = 63, FallingBookcase2 = 64, FallingBookcase3 = 65, FallingBookcase4 = 66, FallingBookcase5 = 67, FallingBookcase6 = 68, FallingBookcaseSwitch = 69, FalseSwitch1 = 70, FalseSwitch2 = 71, FalseSwitch3 = 72, FalseSwitch4 = 73, FalseSwitch5 = 74, FalseSwitch6 = 75, LadderDoor = 76, SecretPanel = 77, SecretPanel0 = 78, SecretPanel1 = 79, SecretSwitch = 80, SecretSwitch0 = 81, SecretSwitch1 = 82}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}}})

local GROUPS = {DeskDrawer = {1}, DeskDrawer0 = {2}, DoubleDoor1 = {3, 4}, DoubleDoor10 = {5, 6}, DoubleDoor11 = {7, 8}, DoubleDoor12 = {9, 10}, DoubleDoor13 = {11, 12}, DoubleDoor14 = {13, 14}, DoubleDoor2 = {15, 16}, DoubleDoor3 = {17, 18}, DoubleDoor4 = {19, 20}, DoubleDoor5 = {21, 22}, DoubleDoor6 = {23, 24}, DoubleDoor7 = {25, 26}, DoubleDoor8 = {27, 28}, DoubleDoor9 = {29, 30}, Drawer1 = {31}, Drawer10 = {32}, Drawer11 = {33}, Drawer12 = {34}, Drawer13 = {35}, Drawer14 = {36}, Drawer15 = {37}, Drawer16 = {38}, Drawer2 = {39}, Drawer3 = {40}, Drawer4 = {41}, Drawer5 = {42}, Drawer6 = {43}, Drawer7 = {44}, Drawer8 = {45}, Drawer9 = {46}, Dresser1 = {47, 48}, Dresser2 = {49, 50}, Dresser3 = {51, 52}, Dresser4 = {53, 54}, Dresser5 = {55, 56}, Dresser6 = {57, 58}, Dresser7 = {59, 60}, Dresser8 = {61, 62}, FallingBookcase1 = {63}, FallingBookcase2 = {64}, FallingBookcase3 = {65}, FallingBookcase4 = {66}, FallingBookcase5 = {67}, FallingBookcase6 = {68}, FallingBookcaseSwitch = {69}, FalseSwitch1 = {70}, FalseSwitch2 = {71}, FalseSwitch3 = {72}, FalseSwitch4 = {73}, FalseSwitch5 = {74}, FalseSwitch6 = {75}, LadderDoor = {76}, SecretPanel = {77}, SecretPanel0 = {78}, SecretPanel1 = {79}, SecretSwitch = {80}, SecretSwitch0 = {81}, SecretSwitch1 = {82}}
local function trigger(group) for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Trigger) end end
local function openGroup(group) for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Open) end end
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- DoubleDoor1
handlers[102] = function() evt.SetDoorState(5, DoorAction.Trigger) evt.SetDoorState(6, DoorAction.Trigger) end   -- DoubleDoor10
handlers[103] = function() evt.SetDoorState(7, DoorAction.Trigger) evt.SetDoorState(8, DoorAction.Trigger) end   -- DoubleDoor11
handlers[104] = function() evt.SetDoorState(9, DoorAction.Trigger) evt.SetDoorState(10, DoorAction.Trigger) end   -- DoubleDoor12
handlers[105] = function() evt.SetDoorState(11, DoorAction.Trigger) evt.SetDoorState(12, DoorAction.Trigger) end   -- DoubleDoor13
handlers[106] = function() evt.SetDoorState(13, DoorAction.Trigger) evt.SetDoorState(14, DoorAction.Trigger) end   -- DoubleDoor14
handlers[107] = function() evt.SetDoorState(15, DoorAction.Trigger) evt.SetDoorState(16, DoorAction.Trigger) end   -- DoubleDoor2
handlers[108] = function() evt.SetDoorState(17, DoorAction.Trigger) evt.SetDoorState(18, DoorAction.Trigger) end   -- DoubleDoor3
handlers[109] = function() evt.SetDoorState(19, DoorAction.Trigger) evt.SetDoorState(20, DoorAction.Trigger) end   -- DoubleDoor4
handlers[110] = function() evt.SetDoorState(21, DoorAction.Trigger) evt.SetDoorState(22, DoorAction.Trigger) end   -- DoubleDoor5
handlers[111] = function() evt.SetDoorState(23, DoorAction.Trigger) evt.SetDoorState(24, DoorAction.Trigger) end   -- DoubleDoor6
handlers[112] = function() evt.SetDoorState(25, DoorAction.Trigger) evt.SetDoorState(26, DoorAction.Trigger) end   -- DoubleDoor7
handlers[113] = function() evt.SetDoorState(27, DoorAction.Trigger) evt.SetDoorState(28, DoorAction.Trigger) end   -- DoubleDoor8

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- Chest0
handlers[42] = function() evt.OpenChest(1) end   -- Chest1
handlers[43] = function() evt.OpenChest(2) end   -- Chest2
handlers[44] = function() evt.OpenChest(3) end   -- TreasureBag1
handlers[45] = function() evt.OpenChest(4) end   -- TreasureBag0

-- The PerceptionBrushes (MM9's red outlines of secrets): shown to a party whose Perception reaches the
-- brush's PerceptionValue, until the secret is found (each brush's Off trigger: a broken wall, an open
-- drawer or panel; the drawers and the trapdoor show theirs again when shut). On load and every 3 s.
local HINTS = {PerceptionBrush0 = {cog = 320, value = 8}, PerceptionBrush1 = {cog = 321, value = 8}, PerceptionBrush10 = {cog = 322, value = 8}, PerceptionBrush2 = {cog = 323, value = 8}, PerceptionBrush3 = {cog = 324, value = 8}, PerceptionBrush4 = {cog = 325, value = 8}, PerceptionBrush5 = {cog = 326, value = 8}, PerceptionBrush5Level10 = {cog = 327, value = 10}, PerceptionBrush7 = {cog = 328, value = 8}, PerceptionBrush8 = {cog = 329, value = 8}, PerceptionBrush9 = {cog = 330, value = 8}}
local function hintOff(name, off) set("HintOff" .. name, off and 1 or 0); set("HintsShown", -1) end
local function updateHints()
    local skill = 0
    for value = 1, 60 do if evt.CheckSkill(29, 0, value) then skill = value else break end end
    set("HintSkill", skill)
    local key = skill
    for name, _ in pairs(HINTS) do key = key * 2 + var("HintOff" .. name) end
    if var("HintsShown") == key then return end
    set("HintsShown", key)
    for name, hint in pairs(HINTS) do
        evt.SetFacetBit(hint.cog, FacetBits.Invisible, skill < hint.value or var("HintOff" .. name) == 1)
    end
end
handlers[252] = updateHints

-- Furniture (dressers, drawers, desk drawers, the trapdoor over Ladder5, the book on the wall): a click opens
-- or shuts it; the desk drawers and the trapdoor carry a perception hint (their Open/CloseTriggers).
handlers[130] = function() trigger("Dresser1") end   -- Dresser1
handlers[131] = function() trigger("Dresser2") end   -- Dresser2
handlers[132] = function() trigger("Dresser3") end   -- Dresser3
handlers[133] = function() trigger("Dresser4") end   -- Dresser4
handlers[134] = function() trigger("Dresser5") end   -- Dresser5
handlers[135] = function() trigger("Dresser6") end   -- Dresser6
handlers[136] = function() trigger("Dresser7") end   -- Dresser7
handlers[137] = function() trigger("Dresser8") end   -- Dresser8
handlers[138] = function() trigger("Drawer1") end   -- Drawer1
handlers[139] = function() trigger("Drawer2") end   -- Drawer2
handlers[140] = function() trigger("Drawer3") end   -- Drawer3
handlers[141] = function() trigger("Drawer4") end   -- Drawer4
handlers[142] = function() trigger("Drawer5") end   -- Drawer5
handlers[143] = function() trigger("Drawer6") end   -- Drawer6
handlers[144] = function() trigger("Drawer7") end   -- Drawer7
handlers[145] = function() trigger("Drawer8") end   -- Drawer8
handlers[146] = function() trigger("Drawer9") end   -- Drawer9
handlers[147] = function() trigger("Drawer10") end   -- Drawer10
handlers[148] = function() trigger("Drawer11") end   -- Drawer11
handlers[149] = function() trigger("Drawer12") end   -- Drawer12
handlers[150] = function() trigger("Drawer13") end   -- Drawer13
handlers[151] = function() trigger("Drawer14") end   -- Drawer14
handlers[152] = function() trigger("Drawer15") end   -- Drawer15
handlers[153] = function() trigger("Drawer16") end   -- Drawer16
handlers[154] = function() trigger("DeskDrawer"); hintOff("PerceptionBrush8", var("OpenDeskDrawer") == 0); set("OpenDeskDrawer", 1 - var("OpenDeskDrawer")); updateHints() end   -- DeskDrawer
handlers[155] = function() trigger("DeskDrawer0"); hintOff("PerceptionBrush7", var("OpenDeskDrawer0") == 0); set("OpenDeskDrawer0", 1 - var("OpenDeskDrawer0")); updateHints() end   -- DeskDrawer0
handlers[156] = function() trigger("LadderDoor"); hintOff("PerceptionBrush9", var("OpenLadderDoor") == 0); set("OpenLadderDoor", 1 - var("OpenLadderDoor")); updateHints() end   -- LadderDoor
handlers[157] = function() trigger("FalseSwitch4") end   -- FalseSwitch4

-- The falling bookcases (FallingBookcaseSwitch's OpenTriggers: FBR1 toggle, itself locked, PerceptionBrush5Level10
-- off; FBR k's OpenTriggers: FallingBookcase k and FBR k+1): one bookcase a second topples into the next, its
-- book switches with it; the last falls flat across the aisle (FallingBookcase6, its OpenTrigger: AITrk100 off).
local DOMINO = {{"FallingBookcase1", "FalseSwitch1", "FallingBookcaseSwitch"}, {"FallingBookcase2", "FalseSwitch2"}, {"FallingBookcase3", "FalseSwitch3"}, {"FallingBookcase4", "SecretSwitch1"}, {"FallingBookcase5", "FalseSwitch5"}, {"FallingBookcase6", "FalseSwitch6"}}
local function topple(k)
    for _, name in ipairs(DOMINO[k]) do evt.SetDoorState(DOORS[name], DoorAction.Open) end
    evt.PlaySoundName("events/woodcreak1.wav", 0, 0, 0)
end
handlers[170] = function()   -- FallingBookcaseSwitch
    if var("Domino") ~= 0 then return end
    set("Domino", 1)
    hintOff("PerceptionBrush5Level10", true); updateHints()
    topple(1)
    arm(250, 1)
end
handlers[250] = function()
    if not fired(250) then return end
    local k = var("Domino") + 1
    if k > 6 then return end
    set("Domino", k)
    topple(k)
    if k == 6 then evt.PlaySoundName("events/metalbreak01.wav", 0, 0, 0) else arm(250, 1) end
end
handlers[174] = function() end   -- FalseSwitch1-3, 5, 6: a book that does nothing

-- The secret switches (their OpenTriggers: the panel opens, the switch locks, the hint goes).
handlers[171] = function()   -- SecretSwitch1 on FallingBookcase4 -> SecretPanel1 over Chest1/Chest2
    if var("Secret1") == 1 then return end
    set("Secret1", 1)
    open("SecretPanel1"); hintOff("PerceptionBrush5Level10", true); hintOff("PerceptionBrush10", true)
    updateHints()
end
handlers[172] = function()   -- SecretSwitch -> SecretPanel (TreasureBag1's niche)
    if var("Secret") == 1 then return end
    set("Secret", 1)
    open("SecretSwitch"); open("SecretPanel"); hintOff("PerceptionBrush4", true); updateHints()
end
handlers[173] = function()   -- SecretSwitch0 -> SecretPanel0 (TreasureBag0's niche)
    if var("Secret0") == 1 then return end
    set("Secret0", 1)
    open("SecretSwitch0"); open("SecretPanel0"); hintOff("PerceptionBrush5", true); updateHints()
end

-- The breakable walls (DestructableBrush0-3, scene destructibles: MM9's party smashes them, a click still does;
-- DeathTrigger: the hint off, DestructableBrush2's through 'Tom Needed A Trigger1'): each one's destroyed event.
handlers[180] = function()   -- DestructableBrush0 broken
    set("Broken0", 1)
    hintOff("PerceptionBrush0", true); updateHints()
end
handlers[181] = function()   -- DestructableBrush1 broken
    set("Broken1", 1)
    hintOff("PerceptionBrush1", true); updateHints()
end
handlers[182] = function()   -- DestructableBrush2 broken
    set("Broken2", 1)
    hintOff("PerceptionBrush3", true); updateHints()
end
handlers[183] = function()   -- DestructableBrush3 broken
    set("Broken3", 1)
    hintOff("PerceptionBrush2", true); updateHints()
end

-- KingKong.scr: BustOutTrigger0 sends BustOutLich0 through its cage wall (ForceBreak: DestructableBrush4,
-- rock_crush.wav) and the caged pair attack; BustOutTrigger1 drops BustOutLichKing0 and its two skeletons
-- through the ceiling (ForceFall: DestructableBrush5 destroyed). Native: both are scene destructibles broken
-- here; the three appear on the floor under the hole, and each wakes and hunts the party.
handlers[190] = function()
    if var("BustOut0") == 1 then return end
    set("BustOut0", 1)
    -- BustOutLich0 breaks its own cage (ForceBreak): killed in it, it takes none and the wall stands.
    -- :RushCage roars where it stands (dragonredrattack3.wav), :BreakCage swings hattack1 (LICH.abc's
    -- Hattack1 is the model's attack_melee2).
    if MM9.receives("inventastorca", "BustOutLich0", "ForceBreak", 17) then
        local x, y, z = evt.GetMapActorPosition(17)
        if x ~= nil then
            evt.PlaySoundName("animsounds/dragonredrattack3.wav", math.floor(x), math.floor(y), math.floor(z))
        end
        evt.DestroyDestructible(671)
        evt.PlaySoundName("events/rock_crush.wav", 0, 0, 0)
        evt.PlayActorClip(17, "attack_melee2")   -- PlayAnim hattack1
    end
    evt.WakeGroup(12)
end
handlers[191] = function()
    if var("BustOut1") == 1 then return end
    set("BustOut1", 1)
    evt.DestroyDestructible(670)
    evt.PlaySoundName("events/rock_crush.wav", 0, 0, 0)
    evt.SetMapActorPosition(21, -4268, -7086, -860)
    evt.SetMonsterBit(21, ActorAttribute.Invisible, 0)
    evt.SetMapActorPosition(19, -4178, -7086, -860)
    evt.SetMonsterBit(19, ActorAttribute.Invisible, 0)
    evt.SetMapActorPosition(20, -4088, -7086, -860)
    evt.SetMonsterBit(20, ActorAttribute.Invisible, 0)
    evt.WakeGroup(13)
end

-- ScurryCreature.scr: the small basilisks run to HideMarker0 at six times their speed and vanish (Hide:
-- :GoHide's RunTo, then RemoveObject). Here they run at their own run speed; a load sends the ones still
-- running again.
local HIDE = {-9953, -3891, -860}
local function scurry(actorIndex)
    if not evt.MoveActorTo(actorIndex, HIDE[1], HIDE[2], HIDE[3], 203 + actorIndex - 22, true) then MM9.removeActor(actorIndex) end
end
handlers[203] = function() MM9.removeActor(22) end   -- ScurryBasilisk0 hidden
handlers[204] = function() MM9.removeActor(23) end   -- ScurryBasilisk1 hidden
handlers[205] = function() MM9.removeActor(24) end   -- ScurryBasilisk2 hidden
handlers[206] = function() MM9.removeActor(25) end   -- ScurryBasilisk3 hidden
handlers[207] = function() MM9.removeActor(26) end   -- ScurryBasilisk4 hidden
handlers[208] = function() MM9.removeActor(27) end   -- ScurryBasilisk5 hidden
handlers[192] = function()   -- ScurryTrigger0
    if var("ScurryTrigger0") == 1 then return end
    set("ScurryTrigger0", 1)
    evt.PlaySoundName("animsounds/dragonredhop.wav", 0, 0, 0)
    if MM9.receives("inventastorca", "ScurryBasilisk0", "Hide", 22) then scurry(22) end
    if MM9.receives("inventastorca", "ScurryBasilisk1", "Hide", 23) then scurry(23) end
    if MM9.receives("inventastorca", "ScurryBasilisk2", "Hide", 24) then scurry(24) end
end
handlers[193] = function()   -- ScurryTrigger1
    if var("ScurryTrigger1") == 1 then return end
    set("ScurryTrigger1", 1)
    evt.PlaySoundName("animsounds/dragonredhop.wav", 0, 0, 0)
    if MM9.receives("inventastorca", "ScurryBasilisk3", "Hide", 25) then scurry(25) end
    if MM9.receives("inventastorca", "ScurryBasilisk4", "Hide", 26) then scurry(26) end
    if MM9.receives("inventastorca", "ScurryBasilisk5", "Hide", 27) then scurry(27) end
end
-- IS_ficky.scr / IS_fickyflock.scr: either BirdTrigg scatters the five ickies resting in the cave shaft;
-- they fly up to the FlockM markers and vanish (Die). Here they are gone with their flapping. The scatter
-- goes to BirdIntheSky0, which sends each of the five its go: a dead one takes none (MM9.receives).
local function scatter()
    if var("Scattered") == 1 then return end
    set("Scattered", 1)
    if not MM9.receives("inventastorca", "BirdIntheSky0", "scatter", 11) then return end
    evt.PlaySoundName("events/woodcreak1.wav", 0, 0, 0)
    if MM9.receives("inventastorca", "BrettBird0", "go", 12) then MM9.removeActor(12) end
    if MM9.receives("inventastorca", "BrettBird1", "go", 13) then MM9.removeActor(13) end
    if MM9.receives("inventastorca", "BrettBird2", "go", 14) then MM9.removeActor(14) end
    if MM9.receives("inventastorca", "BrettBird3", "go", 15) then MM9.removeActor(15) end
    if MM9.receives("inventastorca", "BrettBird4", "go", 16) then MM9.removeActor(16) end
end
handlers[194] = scatter   -- BirdTrigg0
handlers[195] = scatter   -- BirdTrigg1

-- IS_KillingLich.scr / IS_DyingNpc.scr: SpookTrigger5 or opening DoubleDoor9 sends the Kill trigger; the Lich
-- King deals the dying adventurer (GreenPartyDude0) the killing blow, then attacks the party. Native: the two
-- become enemies, and the Lich King turns hostile and moves; the adventurer is on his last hit point (the
-- scene's 1, which the load-time bolster fills up), so the first blow kills him.
-- A dead Lich King takes no Kill (MM9.receives): the adventurer lives on.
local function lastHitPoint() if MM9.actorAlive(35) then evt.SetMapActorHp(35, 1) end end
local function lichKills()
    if var("LichKills") == 1 then return end
    if not MM9.receives("inventastorca", "LKToKillGreenParty0", "Kill", 38) then return end
    set("LichKills", 1)
    lastHitPoint()
    evt.SetMonsterRelation(9207, 9111, 2)
    evt.SetMonsterRelation(9111, 9207, 2)
    evt.SetMonGroupBit(10, MonsterBits.Hostile, true)
    evt.WakeGroup(10)
end
handlers[120] = function() trigger("DoubleDoor9"); lichKills() end   -- DoubleDoor9

-- Spook.scr (SpookObject): SpookTrigger0-4 play one of its sounds once each; it also plays one every 2-8
-- minutes (StartPlayLoop). SpookTrigger5 sends the Lich King's Kill trigger instead.
local SPOOK = {"door/doorcreak02.wav", "ambient/birds/owl02.wav", "ambient/thunder/thunder distant02.wav", "events/rockscrumblingloop.wav", "events/woodcreak1.wav", "ambient/insects/cricket.wav", "pickupitems/shield/metal01.wav", "events/shatterpotterybig02.wav"}
local function spook() evt.PlaySoundName(SPOOK[evt.RandomBetween(1, #SPOOK, 1)], 0, 0, 0) end
handlers[196] = function() if var("SpookTrigger0") == 0 then set("SpookTrigger0", 1); spook() end end   -- SpookTrigger0
handlers[197] = function() if var("SpookTrigger1") == 0 then set("SpookTrigger1", 1); spook() end end   -- SpookTrigger1
handlers[198] = function() if var("SpookTrigger2") == 0 then set("SpookTrigger2", 1); spook() end end   -- SpookTrigger2
handlers[199] = function() if var("SpookTrigger3") == 0 then set("SpookTrigger3", 1); spook() end end   -- SpookTrigger3
handlers[200] = function() if var("SpookTrigger4") == 0 then set("SpookTrigger4", 1); spook() end end   -- SpookTrigger4
handlers[201] = function() if var("SpookTrigger5") == 0 then set("SpookTrigger5", 1); lichKills() end end   -- SpookTrigger5
handlers[251] = function()
    if not fired(251) then return end
    spook()
    arm(251, evt.RandomBetween(120, 480, 1))
end

-- Orb.scr: an Orb of Linking taken (a world item) plays the quest sound.
handlers[210] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop0
handlers[211] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop1
handlers[212] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop2
handlers[213] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop3
handlers[214] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop4
handlers[215] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop5
handlers[216] = function() MM9.playSound("sounds/events/quest.wav") end   -- Prop6
-- BookLetter.scr (Prop7, Prop8: ScriptParams '<row> Letter'): DoLetter shows MM9's text, bookopen.wav.
handlers[220] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("Letter to Thieves\n\nI can assure you, Gavin you will be greatly rewarded if you bring me any of the valuables from the Inventa Storca.  I have great interest in these from a historical standpoint, and I'm certain that others do as well.  It is in your best interest to stop these other parties if you come across them.\n\nL.K.") end   -- Prop7
handlers[221] = function() evt.PlaySoundName("events/bookopen.wav", 0, 0, 0); evt.SimpleMessage("On Visitors from Space\n\nhave read from many credible sources that we have been visited in the past by monsters from the stars who arrived in a flying boat made of metal.  In many of the cases they handed strange devices to people who would eventually lead armies and become rulers of nations.  I wouldn't presume to imply that strange creatures have even visited anyone in the grand history of the Ursanian Empire, but I've heard that rulers of other nations have come to power in such a way.\nOne credible observer explained that he saw the strange creatures arrive at a place he said was several hundred leagues south of Verhoffin's supposed sovereign tower.  While they were there, they constructed an enormous building with a giant stick that pointed to the sky.  He overheard them tell the person in charge of that province, that when the time came to look to the sky, he would know what to do with it.\nWhether any of these claims are true has not been independently verified.  I however am one who takes their claims to heart.  While at a historical site in the Beldonian Province, I saw cave paintings of men fighting demons in the sky.  Why they were, or why they were fighting has been lost to time, but I doubt the primitives who created those paintings could hardly be sophisticated enough to have come up with those ideas on their own.") end   -- Prop8

handlers[1] = function()   -- map load
    if var("LichKills") == 1 then
        evt.SetMonsterRelation(9207, 9111, 2)
        evt.SetMonsterRelation(9111, 9207, 2)
        lastHitPoint()
    end
    if var("ScurryTrigger0") == 1 and MM9.actorAlive(22) then scurry(22) end
    if var("ScurryTrigger0") == 1 and MM9.actorAlive(23) then scurry(23) end
    if var("ScurryTrigger0") == 1 and MM9.actorAlive(24) then scurry(24) end
    if var("ScurryTrigger1") == 1 and MM9.actorAlive(25) then scurry(25) end
    if var("ScurryTrigger1") == 1 and MM9.actorAlive(26) then scurry(26) end
    if var("ScurryTrigger1") == 1 and MM9.actorAlive(27) then scurry(27) end
    if var("Armed251") == 0 then arm(251, evt.RandomBetween(120, 480, 1)) end
    set("HintsShown", -1)
    updateHints()
end
-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[30725] = function() evt.SearchLootProp("mm9:inventastorca:object:725") end   -- BonePile0
handlers[30726] = function() evt.SearchLootProp("mm9:inventastorca:object:726") end   -- BonePile1
handlers[30727] = function() evt.SearchLootProp("mm9:inventastorca:object:727") end   -- BonePile2

-- MM9's breakable brushes once built as click movers (destructibles.build_breakables): weapons break
-- them; a click still does, as a killing blow (refused while MM9's CanDamage is off).
handlers[38420] = function() evt.DamageDestructible(420, 1000000) end   -- DestructableBrush2
handlers[38421] = function() evt.DamageDestructible(421, 1000000) end   -- DestructableBrush1
handlers[38422] = function() evt.DamageDestructible(422, 1000000) end   -- DestructableBrush0
handlers[38423] = function() evt.DamageDestructible(423, 1000000) end   -- DestructableBrush3


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
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterMapTimerEvent(252, seconds(3), handlers[252], "Perception hints", "", seconds(3))
RegisterEvent(130, "Door", handlers[130], "Open")
RegisterEvent(131, "Door", handlers[131], "Open")
RegisterEvent(132, "Door", handlers[132], "Open")
RegisterEvent(133, "Door", handlers[133], "Open")
RegisterEvent(134, "Door", handlers[134], "Open")
RegisterEvent(135, "Door", handlers[135], "Open")
RegisterEvent(136, "Door", handlers[136], "Open")
RegisterEvent(137, "Door", handlers[137], "Open")
RegisterEvent(138, "Drawer", handlers[138], "Open")
RegisterEvent(139, "Drawer", handlers[139], "Open")
RegisterEvent(140, "Drawer", handlers[140], "Open")
RegisterEvent(141, "Drawer", handlers[141], "Open")
RegisterEvent(142, "Drawer", handlers[142], "Open")
RegisterEvent(143, "Drawer", handlers[143], "Open")
RegisterEvent(144, "Drawer", handlers[144], "Open")
RegisterEvent(145, "Drawer", handlers[145], "Open")
RegisterEvent(146, "Drawer", handlers[146], "Open")
RegisterEvent(147, "Drawer", handlers[147], "Open")
RegisterEvent(148, "Drawer", handlers[148], "Open")
RegisterEvent(149, "Drawer", handlers[149], "Open")
RegisterEvent(150, "Drawer", handlers[150], "Open")
RegisterEvent(151, "Drawer", handlers[151], "Open")
RegisterEvent(152, "Drawer", handlers[152], "Open")
RegisterEvent(153, "Drawer", handlers[153], "Open")
RegisterEvent(154, "Drawer", handlers[154], "Open")
RegisterEvent(155, "Drawer", handlers[155], "Open")
RegisterEvent(156, "Door", handlers[156], "Open")
RegisterEvent(157, "Door", handlers[157], "Open")
RegisterEvent(170, "Book", handlers[170], "Book")
RegisterMapTimerEvent(250, seconds(3), handlers[250], "Bookcases", "", seconds(3))
RegisterEvent(174, "Book", handlers[174], "Book")
RegisterEvent(171, "Book", handlers[171], "Book")
RegisterEvent(172, "Book", handlers[172], "Book")
RegisterEvent(173, "Book", handlers[173], "Book")
RegisterEvent(180, "Cracked wall", handlers[180])
RegisterEvent(181, "Cracked wall", handlers[181])
RegisterEvent(182, "Cracked wall", handlers[182])
RegisterEvent(183, "Cracked wall", handlers[183])
RegisterEvent(190, "BustOutTrigger0", handlers[190])
RegisterEvent(191, "BustOutTrigger1", handlers[191])
RegisterEvent(203, "ScurryBasilisk0 hidden", handlers[203])
RegisterEvent(204, "ScurryBasilisk1 hidden", handlers[204])
RegisterEvent(205, "ScurryBasilisk2 hidden", handlers[205])
RegisterEvent(206, "ScurryBasilisk3 hidden", handlers[206])
RegisterEvent(207, "ScurryBasilisk4 hidden", handlers[207])
RegisterEvent(208, "ScurryBasilisk5 hidden", handlers[208])
RegisterEvent(192, "ScurryTrigger0", handlers[192])
RegisterEvent(193, "ScurryTrigger1", handlers[193])
RegisterEvent(194, "BirdTrigg0", handlers[194])
RegisterEvent(195, "BirdTrigg1", handlers[195])
RegisterEvent(120, "Door", handlers[120], "Door")
RegisterEvent(196, "SpookTrigger0", handlers[196])
RegisterEvent(197, "SpookTrigger1", handlers[197])
RegisterEvent(198, "SpookTrigger2", handlers[198])
RegisterEvent(199, "SpookTrigger3", handlers[199])
RegisterEvent(200, "SpookTrigger4", handlers[200])
RegisterEvent(201, "SpookTrigger5", handlers[201])
RegisterMapTimerEvent(251, seconds(3), handlers[251], "Spook", "", seconds(3))
RegisterEvent(210, "Orb of Linking", handlers[210])
RegisterEvent(211, "Orb of Linking", handlers[211])
RegisterEvent(212, "Orb of Linking", handlers[212])
RegisterEvent(213, "Orb of Linking", handlers[213])
RegisterEvent(214, "Orb of Linking", handlers[214])
RegisterEvent(215, "Orb of Linking", handlers[215])
RegisterEvent(216, "Orb of Linking", handlers[216])
RegisterEvent(220, "Scroll", handlers[220], "Read")
RegisterEvent(221, "Scroll", handlers[221], "Read")
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(30725, "Bone Pile", handlers[30725], "Bone Pile")
RegisterEvent(30726, "Bone Pile", handlers[30726], "Bone Pile")
RegisterEvent(30727, "Bone Pile", handlers[30727], "Bone Pile")
RegisterEvent(38420, "DestructableBrush2", handlers[38420], "Rocks")
RegisterEvent(38421, "DestructableBrush1", handlers[38421], "Rocks")
RegisterEvent(38422, "DestructableBrush0", handlers[38422], "Rocks")
RegisterEvent(38423, "DestructableBrush3", handlers[38423], "Rocks")
