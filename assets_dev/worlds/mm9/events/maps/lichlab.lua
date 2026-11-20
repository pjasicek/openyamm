-- Lich Lab, MM9 rework (level_generation/projects/mm9r_lichlab/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {DB1 = 1, DB2 = 5, DestructableBrush16 = 92, DestructableBrush19 = 93, DestructableBrush6 = 94, EngineLever = 9, Enginedoor1 = 10, Engineglass1_GLASS5 = 12, Engineglass1_INV = 11, PeasantDoor = 13, PeasantDoor0 = 14, RotatingDoor0 = 15, RotatingDoor128 = 16, RotatingDoor129 = 17, RotatingDoor130 = 18, RotatingDoor131 = 19, RotatingDoor134 = 20, RotatingDoor135 = 21, RotatingDoor136 = 22, RotatingDoor137 = 23, RotatingDoor138 = 24, RotatingDoor139 = 25, RotatingDoor146 = 26, RotatingDoor147 = 27, RotatingDoor148 = 28, RotatingDoor149 = 29, RotatingDoor150 = 30, RotatingDoor151 = 31, RotatingDoor152 = 32, RotatingDoor153 = 33, RotatingDoor154 = 34, RotatingDoor155 = 35, RotatingDoor156 = 36, RotatingDoor157 = 37, RotatingDoor158 = 38, RotatingDoor159 = 39, RotatingDoor160 = 40, RotatingDoor161 = 41, RotatingDoor162 = 42, RotatingDoor163 = 43, RotatingDoor164 = 44, RotatingDoor165 = 45, RotatingDoor166 = 46, RotatingDoor167 = 8, RotatingDoor168 = 4, RotatingDoor169 = 47, RotatingDoor170 = 48, RotatingDoor171 = 49, RotatingDoor172 = 50, RotatingDoor173 = 51, RotatingDoor174 = 52, RotatingDoor175 = 53, RotatingDoor176 = 54, RotatingDoor177 = 55, RotatingDoor178 = 56, RotatingDoor179 = 57, RotatingDoor180 = 58, RotatingDoor181 = 59, RotatingDoor182 = 60, RotatingDoor183 = 61, RotatingDoor184 = 62, RotatingDoor185 = 63, RotatingDoor186 = 64, RotatingDoor187 = 65, RotatingDoor188 = 66, RotatingDoor189 = 67, RotatingDoor190 = 68, RotatingDoor191 = 69, RotatingDoor192 = 70, RotatingDoor193 = 71, RotatingDoor194 = 72, RotatingDoor195 = 73, RotatingDoor196 = 74, RotatingDoor197 = 75, RotatingDoor198 = 76, RotatingDoor199 = 77, RotatingDoor200 = 78, RotatingDoor201 = 79, RotatingDoor202 = 80, RotatingDoor203 = 81, TransformSwitch0 = 95, TransformSwitch1 = 96, TransformSwitch2 = 97, TransformSwitch3 = 98, breakwindow1_GLASS4 = 3, breakwindow1_INV = 2, breakwindow2_GLASS4 = 7, breakwindow2_INV = 6, skeletondoora = 82, skeletondoora0 = 87, skeletondoora0_GLASS1 = 89, skeletondoora0_GLASS6 = 90, skeletondoora0_GLASS7 = 91, skeletondoora0_INV = 88, skeletondoora_GLASS1 = 84, skeletondoora_GLASS6 = 85, skeletondoora_GLASS7 = 86, skeletondoora_INV = 83}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1, 900}, onLeave = {}, timers = {}, openedChestIds = {[41] = {0}, [42] = {1}, [43] = {2}, [44] = {3}, [45] = {4}, [46] = {5}, [47] = {6}, [48] = {7}}})

local GROUPS = {CageGhast = {1, 2, 3}, CageRevenant = {4}, CageSpectre = {5, 6, 7}, CageVenomous = {8}, EngineLever = {9}, EnginePod1 = {10, 11, 12}, PeasantDoor = {13}, PeasantDoor0 = {14}, RotatingDoor0 = {15}, RotatingDoor128 = {16}, RotatingDoor129 = {17}, RotatingDoor130 = {18}, RotatingDoor131 = {19}, RotatingDoor134 = {20}, RotatingDoor135 = {21}, RotatingDoor136 = {22}, RotatingDoor137 = {23}, RotatingDoor138 = {24}, RotatingDoor139 = {25}, RotatingDoor146 = {26}, RotatingDoor147 = {27}, RotatingDoor148 = {28}, RotatingDoor149 = {29}, RotatingDoor150 = {30}, RotatingDoor151 = {31}, RotatingDoor152 = {32}, RotatingDoor153 = {33}, RotatingDoor154 = {34}, RotatingDoor155 = {35}, RotatingDoor156 = {36}, RotatingDoor157 = {37}, RotatingDoor158 = {38}, RotatingDoor159 = {39}, RotatingDoor160 = {40}, RotatingDoor161 = {41}, RotatingDoor162 = {42}, RotatingDoor163 = {43}, RotatingDoor164 = {44}, RotatingDoor165 = {45}, RotatingDoor166 = {46}, RotatingDoor169 = {47}, RotatingDoor170 = {48}, RotatingDoor171 = {49}, RotatingDoor172 = {50}, RotatingDoor173 = {51}, RotatingDoor174 = {52}, RotatingDoor175 = {53}, RotatingDoor176 = {54}, RotatingDoor177 = {55}, RotatingDoor178 = {56}, RotatingDoor179 = {57}, RotatingDoor180 = {58}, RotatingDoor181 = {59}, RotatingDoor182 = {60}, RotatingDoor183 = {61}, RotatingDoor184 = {62}, RotatingDoor185 = {63}, RotatingDoor186 = {64}, RotatingDoor187 = {65}, RotatingDoor188 = {66}, RotatingDoor189 = {67}, RotatingDoor190 = {68}, RotatingDoor191 = {69}, RotatingDoor192 = {70}, RotatingDoor193 = {71}, RotatingDoor194 = {72}, RotatingDoor195 = {73}, RotatingDoor196 = {74}, RotatingDoor197 = {75}, RotatingDoor198 = {76}, RotatingDoor199 = {77}, RotatingDoor200 = {78}, RotatingDoor201 = {79}, RotatingDoor202 = {80}, RotatingDoor203 = {81}, SkeletonDoorA = {82, 83, 84, 85, 86}, SkeletonDoorA0 = {87, 88, 89, 90, 91}, Target16 = {92}, Target19 = {93}, Target6 = {94}, TransformSwitch0 = {95}, TransformSwitch1 = {96}, TransformSwitch2 = {97}, TransformSwitch3 = {98}}
local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end
local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end
-- One-shot timers: the map's timers run from load (RegisterMapTimerEvent repeats), so each is armed by a
-- named variable when started and acts only when armed.
local function arm(timer, delay) set("Armed" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end
local function fired(timer)
    evt.StopTimer(timer)
    if var("Armed" .. timer) ~= 1 then return false end
    set("Armed" .. timer, 0)
    return true
end
local function inside(box, x, y, z) return x >= box[1][1] and x <= box[2][1] and y >= box[1][2] and y <= box[2][2] and z >= box[1][3] - 40 and z <= box[2][3] end

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(13, DoorAction.Trigger) end   -- PeasantDoor
handlers[102] = function() evt.SetDoorState(14, DoorAction.Trigger) end   -- PeasantDoor0
handlers[103] = function() evt.SetDoorState(15, DoorAction.Trigger) end   -- RotatingDoor0
handlers[104] = function() evt.SetDoorState(16, DoorAction.Trigger) end   -- RotatingDoor128
handlers[105] = function() evt.SetDoorState(17, DoorAction.Trigger) end   -- RotatingDoor129
handlers[106] = function() evt.SetDoorState(18, DoorAction.Trigger) end   -- RotatingDoor130
handlers[107] = function() evt.SetDoorState(19, DoorAction.Trigger) end   -- RotatingDoor131
handlers[108] = function() evt.SetDoorState(20, DoorAction.Trigger) end   -- RotatingDoor134
handlers[109] = function() evt.SetDoorState(21, DoorAction.Trigger) end   -- RotatingDoor135
handlers[110] = function() evt.SetDoorState(22, DoorAction.Trigger) end   -- RotatingDoor136
handlers[111] = function() evt.SetDoorState(23, DoorAction.Trigger) end   -- RotatingDoor137
handlers[112] = function() evt.SetDoorState(24, DoorAction.Trigger) end   -- RotatingDoor138
handlers[113] = function() evt.SetDoorState(25, DoorAction.Trigger) end   -- RotatingDoor139
handlers[114] = function() evt.SetDoorState(26, DoorAction.Trigger) end   -- RotatingDoor146
handlers[115] = function() evt.SetDoorState(27, DoorAction.Trigger) end   -- RotatingDoor147
handlers[116] = function() evt.SetDoorState(28, DoorAction.Trigger) end   -- RotatingDoor148
handlers[117] = function() evt.SetDoorState(29, DoorAction.Trigger) end   -- RotatingDoor149
handlers[118] = function() evt.SetDoorState(30, DoorAction.Trigger) end   -- RotatingDoor150
handlers[119] = function() evt.SetDoorState(31, DoorAction.Trigger) end   -- RotatingDoor151
handlers[120] = function() evt.SetDoorState(32, DoorAction.Trigger) end   -- RotatingDoor152
handlers[121] = function() evt.SetDoorState(33, DoorAction.Trigger) end   -- RotatingDoor153
handlers[122] = function() evt.SetDoorState(34, DoorAction.Trigger) end   -- RotatingDoor154
handlers[123] = function() evt.SetDoorState(35, DoorAction.Trigger) end   -- RotatingDoor155
handlers[124] = function() evt.SetDoorState(36, DoorAction.Trigger) end   -- RotatingDoor156
handlers[125] = function() evt.SetDoorState(37, DoorAction.Trigger) end   -- RotatingDoor157
handlers[126] = function() evt.SetDoorState(38, DoorAction.Trigger) end   -- RotatingDoor158
handlers[127] = function() evt.SetDoorState(39, DoorAction.Trigger) end   -- RotatingDoor159
handlers[128] = function() evt.SetDoorState(40, DoorAction.Trigger) end   -- RotatingDoor160
handlers[129] = function() evt.SetDoorState(41, DoorAction.Trigger) end   -- RotatingDoor161
handlers[130] = function() evt.SetDoorState(42, DoorAction.Trigger) end   -- RotatingDoor162
handlers[131] = function() evt.SetDoorState(43, DoorAction.Trigger) end   -- RotatingDoor163
handlers[132] = function() evt.SetDoorState(44, DoorAction.Trigger) end   -- RotatingDoor164
handlers[133] = function() evt.SetDoorState(45, DoorAction.Trigger) end   -- RotatingDoor165
handlers[134] = function() evt.SetDoorState(46, DoorAction.Trigger) end   -- RotatingDoor166
handlers[135] = function() evt.SetDoorState(47, DoorAction.Trigger) end   -- RotatingDoor169
handlers[136] = function() evt.SetDoorState(48, DoorAction.Trigger) end   -- RotatingDoor170
handlers[137] = function() evt.SetDoorState(49, DoorAction.Trigger) end   -- RotatingDoor171
handlers[138] = function() evt.SetDoorState(50, DoorAction.Trigger) end   -- RotatingDoor172
handlers[139] = function() evt.SetDoorState(51, DoorAction.Trigger) end   -- RotatingDoor173
handlers[140] = function() evt.SetDoorState(52, DoorAction.Trigger) end   -- RotatingDoor174
handlers[141] = function() evt.SetDoorState(53, DoorAction.Trigger) end   -- RotatingDoor175
handlers[142] = function() evt.SetDoorState(54, DoorAction.Trigger) end   -- RotatingDoor176
handlers[143] = function() evt.SetDoorState(55, DoorAction.Trigger) end   -- RotatingDoor177
handlers[144] = function() evt.SetDoorState(56, DoorAction.Trigger) end   -- RotatingDoor178
handlers[145] = function() evt.SetDoorState(57, DoorAction.Trigger) end   -- RotatingDoor179
handlers[146] = function() evt.SetDoorState(58, DoorAction.Trigger) end   -- RotatingDoor180
handlers[147] = function() evt.SetDoorState(59, DoorAction.Trigger) end   -- RotatingDoor181
handlers[148] = function() evt.SetDoorState(60, DoorAction.Trigger) end   -- RotatingDoor182
handlers[149] = function() evt.SetDoorState(61, DoorAction.Trigger) end   -- RotatingDoor183
handlers[150] = function() evt.SetDoorState(62, DoorAction.Trigger) end   -- RotatingDoor184
handlers[151] = function() evt.SetDoorState(63, DoorAction.Trigger) end   -- RotatingDoor185
handlers[152] = function() evt.SetDoorState(64, DoorAction.Trigger) end   -- RotatingDoor186
handlers[153] = function() evt.SetDoorState(65, DoorAction.Trigger) end   -- RotatingDoor187
handlers[154] = function() evt.SetDoorState(66, DoorAction.Trigger) end   -- RotatingDoor188
handlers[155] = function() evt.SetDoorState(67, DoorAction.Trigger) end   -- RotatingDoor189
handlers[156] = function() evt.SetDoorState(68, DoorAction.Trigger) end   -- RotatingDoor190
handlers[157] = function() evt.SetDoorState(69, DoorAction.Trigger) end   -- RotatingDoor191
handlers[158] = function() evt.SetDoorState(70, DoorAction.Trigger) end   -- RotatingDoor192
handlers[159] = function() evt.SetDoorState(71, DoorAction.Trigger) end   -- RotatingDoor193
handlers[160] = function() evt.SetDoorState(72, DoorAction.Trigger) end   -- RotatingDoor194
handlers[161] = function() evt.SetDoorState(73, DoorAction.Trigger) end   -- RotatingDoor195
handlers[162] = function() evt.SetDoorState(74, DoorAction.Trigger) end   -- RotatingDoor196
handlers[163] = function() evt.SetDoorState(75, DoorAction.Trigger) end   -- RotatingDoor197
handlers[164] = function() evt.SetDoorState(76, DoorAction.Trigger) end   -- RotatingDoor198
handlers[165] = function() evt.SetDoorState(77, DoorAction.Trigger) end   -- RotatingDoor199
handlers[166] = function() evt.SetDoorState(78, DoorAction.Trigger) end   -- RotatingDoor200
handlers[167] = function() evt.SetDoorState(79, DoorAction.Trigger) end   -- RotatingDoor201
handlers[168] = function() evt.SetDoorState(80, DoorAction.Trigger) end   -- RotatingDoor202
handlers[169] = function() evt.SetDoorState(81, DoorAction.Trigger) end   -- RotatingDoor203

-- Chests (MM9 TreasureChest objects; loot records in the scene).
handlers[41] = function() evt.OpenChest(0) end   -- Treasurechest0
handlers[42] = function() evt.OpenChest(1) end   -- Treasurechest1
handlers[43] = function() evt.OpenChest(2) end   -- Treasurechest2
handlers[44] = function() evt.OpenChest(3) end   -- Treasurechest3
handlers[45] = function() evt.OpenChest(4) end   -- Treasurechest4
handlers[46] = function() evt.OpenChest(5) end   -- Blackbox
handlers[47] = function() evt.OpenChest(6) end   -- Treasurechest6
handlers[48] = function() evt.OpenChest(7) end   -- Treasurechest7

-- The Transmutation Engine (ILSHealerRoom.scr on PromoTrigger, Switch.scr on lichswitch, LichEngineProp.scr).
-- The lich switch lowers pod 1's lid and glass (MM9 Doors Enginedoor1/Engineglass1: down 96) round
-- whoever stands in it; 3 s later the engine strikes (lightning down the shaft onto it) and, with the
-- party inside PromoVol1, transmutes: MM9 runs this only once the engine is 'fixed', which nothing in
-- MM9 does; here the Lich Instructions (key 296) are what make it work. Each member who carries an
-- Elixir of Defedation (MM9: 'subjects must drink from their own vial'; here any pack's vial, its own first:
-- the burner puts the elixir in the active member's pack) and is a Wizard (MM9's
-- Scholar) becomes a Lich; the first working strike gives MM9's 63000 experience and key 299 (journal
-- 'Become a Lich' done) whoever it changes (every promotion quest pays its rewards to any party, the user
-- 2026-11-08); the engine works again at any time for those ready later. 2 s after the strike the pod rises.
local POD_BOX = {{-1393, 5632, -655}, {-1126, 5898, -410}}
local LICH_CLASSES = {Wizard = true, Necromancer = true}  -- one step from Lich (MM7 dark path, MM8)
local function transmute()
    local x, y, z = evt.GetPartyPosition()
    if not inside(POD_BOX, x, y, z) then return 0 end
    if MM9.hasKey(296) == 0 then
        evt.StatusText("The engine shudders, but nothing happens.")
        return 0
    end
    local elixir = MM9.ItemIds[246]
    local count = evt.GetPartyMemberCount()
    local function takeElixir(i)   -- the subject's own vial, else one from another pack
        for _, j in ipairs({i, 0, 1, 2, 3, 4}) do
            if j < count and evt.PartyMemberHasItem(j, elixir) then
                evt.RemovePartyMemberItem(j, elixir)
                return true
            end
        end
        return false
    end
    local changed, ready = 0, 0
    for i = 0, count - 1 do
        if LICH_CLASSES[evt.GetPlayerClassName(i)] then
            ready = ready + 1
            if elixir ~= nil and takeElixir(i) and evt.ApplyLichTransformation(i) then changed = changed + 1 end
        end
    end
    if MM9.hasKey(299) == 0 then
        MM9.giveExperience(55500) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
        MM9.playSound("sounds/events/quest.wav")
        MM9.giveKey(299)
    end
    if changed == 0 then
        evt.StatusText(ready > 0 and "The engine roars, but there is no Elixir of Defedation to drink."
            or "The engine roars, but no one is ready for the change.")
        return 0
    end
    set("Transmuted", var("Transmuted") + changed)
    return changed
end
-- Switch.scr Onuse: each use plays the lever's Down, the next its Up (bUp), and triggers Engineglass1.
handlers[200] = function()   -- lichswitch
    local down = var("LichSwitchDown") == 0
    set("LichSwitchDown", down and 1 or 0)
    evt.PlayDecorationClip(3, down and "down" or "up")
    if var("PodClosed") == 1 then return end
    set("PodClosed", 1)
    openGroup("EnginePod1")
    evt.SetLight(41369, true)   -- Engineglass1's OpenTrigger: Glow1 on (the pod glows while shut)
    arm(250, 3)
end
handlers[250] = function()   -- the engine strikes
    if not fired(250) or var("PodClosed") ~= 1 then return end
    evt.Beam("EngineLightning", "openyamm:fx/arc_beam", -1720, 6226, 1659, -1720, 6226, 1147, 1.5)
    evt.PlaySoundName("sounds/magic/projectile14.wav", 0, 0, 0)
    set("EngineStrikes", var("EngineStrikes") + 1)
    transmute()
    arm(251, 2)
end
handlers[251] = function()   -- the pod rises
    if not fired(251) or var("PodClosed") ~= 1 then return end
    closeGroup("EnginePod1")
    evt.SetLight(41369, false)   -- Engineglass1's CloseTrigger: Glow1 off
    set("PodClosed", 0)
end

-- The Lich engine (LichEngineProp.scr on Lichengine): RotatingDoor1, the lever before it, sends it
-- "start" once open and "finish" once shut again (3.6 s of travel). "start" at rest plays
-- startup, then loops spincycle; "finish" while it spins plays shutdown, then it stands at rest
-- (LoopAnim static_model).
-- Each message is heard only in its own state (the script removes the other's trigger): EngineSpin 0 rest,
-- 1 starting, 2 spinning, 3 stopping. EngineLeverOpen is where the lever was last sent (a click while it
-- swings turns it back).
handlers[201] = function()   -- RotatingDoor1
    local open = var("EngineLeverOpen") == 0
    set("EngineLeverOpen", open and 1 or 0)
    for _, id in ipairs(GROUPS.EngineLever) do evt.SetDoorState(id, open and DoorAction.Open or DoorAction.Close) end
    arm(266, 3.6)
end
handlers[266] = function()   -- the lever is there: OpenTrigger start / CloseTrigger finish
    if not fired(266) then return end
    local spin = var("EngineSpin")
    if var("EngineLeverOpen") == 1 and spin == 0 then
        set("EngineSpin", 1)
        evt.PlayDecorationClip(129, "startup")   -- PowerUp: PlayAnim startup, Spin
        arm(267, 3.5)
    elseif var("EngineLeverOpen") == 0 and spin == 2 then
        set("EngineSpin", 3)
        evt.PlayDecorationClip(129, "shutdown")   -- PowerDown: PlayAnim shutdown, Stop
        arm(267, 3.5)
    end
end
handlers[267] = function()   -- startup or shutdown played out
    if not fired(267) then return end
    if var("EngineSpin") == 1 then
        set("EngineSpin", 2)
        evt.PlayDecorationClip(129, "spincycle", "loop")   -- Spin: LoopAnim spincycle
    elseif var("EngineSpin") == 3 then
        set("EngineSpin", 0)
        evt.PlayDecorationClip(129, "")   -- Stop: LoopAnim static_model
    end
end

-- The elixir (Givetake.scr, ElixirCook.scr, GiveElixir.scr): the storeroom's herb bags (Elixir Ingredients,
-- 378) and jars (a Jar, 358) are world items; the kitchen's cook pot turns ingredients into Elixir Fluid
-- (561); the burner by the kitchen turns fluid and a jar into the Elixir of Defedation (246).
-- MM9's giveitem puts the item in the party's packs: the active member's first, then the others' (the
-- cursor only when every pack is full).
local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
handlers[222] = function()   -- Prop18, the cook pot
    if MM9.hasItem(378, "lichlab:Prop18") == 1 then
        MM9.takeItem(378, "lichlab:Prop18")
        give(561, "lichlab:Prop18")
        MM9.playSound("sounds/events/quest.wav")
    end
end
handlers[223] = function()   -- Prop17, the burner
    if MM9.hasItem(358, "lichlab:Prop17") == 1 and MM9.hasItem(561, "lichlab:Prop17") == 1 then
        MM9.takeItem(358, "lichlab:Prop17")
        MM9.takeItem(561, "lichlab:Prop17")
        give(246, "lichlab:Prop17")
        MM9.playSound("sounds/events/quest.wav")
    end
end

-- The letters (BookLetter.scr DoLetter): MM9's book and scroll texts.
handlers[224] = function() evt.SimpleMessage("The Skeleton Transformer\n\nAs I have told you all numerous times before, do not use the skeleton transformer to deposit your experimental waste!  On three occasions now, I've created skeletons who have extra arms growing out of where their eyesockets are, and one had a tentacle growing from its finger.  I am sure this is all amusing to the rest of you, but I will not tolerate it if I catch you!") end   -- Prop16
handlers[225] = function() evt.SimpleMessage("Scrap of Diary\n\n..I've secured the way to my domination!  I will create a giant army of skeletons.  The machine is here and in working order.  All I need is a constant supply of conscripts, and soon all will bow down to me!  I can nearly taste victory already.  The only one who might stand in my way is that lich who calls himself Pinky.  I am certain he has plans to conquer the world as well..dispatch him..everything would be easy.") end   -- Prop19
handlers[226] = function() evt.SimpleMessage("Elixir Instructions\n\nIf you're planning to make a new batch of Elixir of Defidation, follow these instructions.  If you don't, you could have unpredictable results.\nStep One:  Retrieve the Elixir Ingredients and a jar from the storeroom.  There should be plenty in Storeroom B next to the Observation Deck.\nStep Two:  Place the ingredients in the cookpot in the center of the kitchen.  From this you will get a few vials of Elixir Fluid.\nStep Three:  Take the Elixir Fluid to the burners, to refine it into the Elixir of Defidation.\nStep Four:  Drink the elixir when you are ready to be transformed.\n\nMaster-of-Liches") end   -- Prop20

local TRANSFORMERS = {SkeletonDoorA = {switches = {"TransformSwitch0", "TransformSwitch1"}, strike = 252, spawn = 260, panel = 1655}, SkeletonDoorA0 = {switches = {"TransformSwitch2", "TransformSwitch3"}, strike = 254, spawn = 263, panel = 1690}}
local function transform(door)
    if var(door) ~= 0 then evt.StatusText("The switch is locked.") return end
    set(door, 1)
    for _, s in ipairs(TRANSFORMERS[door].switches) do evt.SetDoorState(DOORS[s], DoorAction.Open) end
    closeGroup(door)
    set("AmbientSound" .. TRANSFORMERS[door].panel, 1)   -- the switches' OpenTrigger2: PanelOn on
    arm(TRANSFORMERS[door].spawn, 4.3)
end
-- The skeleton transformers (Converter.scr): a switch locks both switches and lowers the chamber's glass
-- door (4.3 s at MM9's speed); the door's OpenTrigger "create" spawns the conscript (a Commoner) at the
-- closet's marker, and 2 s later PeasantTransformee.scr walks him to the chamber's centre, where he cowers
-- (the Cower clip once, wizardeyeloop.wav) and winces: "convert", the shooters over the chamber strike and
-- a Skeleton stands where he stood; 1 s later the door rises and the switches unlock. (Converter.scr's
-- TransformCreature removes him only `if (hDummy != 0)`, a name it never sets, and spawns the Skeleton at
-- the marker: the evident intent, the peasant turned where he stands, is carried.)
handlers[202] = function() transform("SkeletonDoorA") end   -- TransformSwitch0
handlers[203] = function() transform("SkeletonDoorA") end   -- TransformSwitch1
handlers[260] = function()   -- SkeletonDoorA: the door is down, OpenTrigger create (SpawnCreature)
    if not fired(260) or var("SkeletonDoorA") ~= 1 then return end
    local _, made = evt.SummonMonstersById({monster = 9050, x = 2826, y = 5386, z = 1311, radius = 0, group = 75, hostile = false, loot = false, count = 1, mm9 = {wander = "aimless", wander_wait = {30, 30}}})   -- a wanderer thinks out of the party's room (MM9 wakes the actors near the player), so the walk below runs; the wait keeps him still till then
    set("SkeletonDoorAPeasant", made ~= nil and made[1] ~= nil and made[1] + 1 or 0)
    openGroup("PeasantDoor")   -- the closet's door (AITriggerable: MM9's conscript opens it)
    arm(261, 2)
end
handlers[261] = function()   -- SkeletonDoorA: SignalCreature walk (WalkToSpawner)
    if not fired(261) or var("SkeletonDoorA") ~= 1 then return end
    local i = var("SkeletonDoorAPeasant") - 1
    if i < 0 or not evt.MoveActorTo(i, 2867, 4588, 1319, 262) then arm(252, 0.1) return end
    arm(252, 20)
end
handlers[262] = function()   -- SkeletonDoorA: at the chamber's centre (PlayMagicSound)
    if var("SkeletonDoorA") ~= 1 then return end
    local i = var("SkeletonDoorAPeasant") - 1
    if i >= 0 then evt.PlayActorClip(i, "cower") end
    closeGroup("PeasantDoor")   -- its CloseWaitTime
    set("SkeletonDoorACowered", var("SkeletonDoorACowered") + 1)
    evt.PlaySoundName("sounds/magic/wizardeyeloop.wav", 0, 0, 0)
    arm(252, 1.2)
end
handlers[252] = function()   -- SkeletonDoorA: the strike (TriggerSpawner convert, TransformCreature)
    if not fired(252) or var("SkeletonDoorA") ~= 1 then return end
    local x, y, z = 2867, 4588, 1319
    local peasant = var("SkeletonDoorAPeasant") - 1
    -- "convert" comes from the conscript himself (TriggerSpawner): a dead one sends none, and the chamber
    -- stays down with its switches locked (MM9.actorAlive; the walk timeout stands in for a live one's OnStuck)
    if peasant >= 0 and not MM9.actorAlive(peasant) then return end
    if peasant >= 0 then
        local px, py, pz = evt.GetMapActorPosition(peasant)
        if px ~= nil then x, y, z = px, py, pz end
        evt.StopActorMove(peasant); evt.ClearActorPresentation(peasant)
        evt.SetMonsterBit(peasant, ActorAttribute.Invisible, 1)   -- RemoveObject
        set("SkeletonDoorAPeasant", 0)
    end
    evt.PlaySoundName("sounds/animsounds/pig/wince1.wav", 0, 0, 0)
    evt.Beam("ShooterTransform0", "openyamm:fx/arc_beam", 2867, 4588, 1751, 2867, 4588, 1379, 1.2)
    evt.Beam("ShooterTransform1", "openyamm:fx/arc_beam", 2867, 4751, 1751, 2867, 4588, 1379, 1.2)
    evt.Beam("ShooterTransform2", "openyamm:fx/arc_beam", 2867, 4424, 1751, 2867, 4588, 1379, 1.2)
    evt.PlaySoundName("sounds/magic/projectile14.wav", 0, 0, 0)
    local made = evt.SummonMonstersById({monster = 9135, x = x, y = y, z = z, radius = 16, group = 73, count = 1})
    set("SkeletonsMade", var("SkeletonsMade") + made)
    set("SkeletonDoorA", 2)
    arm(253, 1)
end
handlers[253] = function()   -- SkeletonDoorA: the release
    if not fired(253) or var("SkeletonDoorA") ~= 2 then return end
    openGroup("SkeletonDoorA")
    evt.SetDoorState(DOORS.TransformSwitch0, DoorAction.Close)
    evt.SetDoorState(DOORS.TransformSwitch1, DoorAction.Close)
    set("SkeletonDoorA", 0)
    set("AmbientSound" .. TRANSFORMERS.SkeletonDoorA.panel, 2)   -- the switches' CloseTrigger1: PanelOn off
end
handlers[204] = function() transform("SkeletonDoorA0") end   -- TransformSwitch2
handlers[205] = function() transform("SkeletonDoorA0") end   -- TransformSwitch3
handlers[263] = function()   -- SkeletonDoorA0: the door is down, OpenTrigger create (SpawnCreature)
    if not fired(263) or var("SkeletonDoorA0") ~= 1 then return end
    local _, made = evt.SummonMonstersById({monster = 9050, x = 2458, y = 2749, z = 2376, radius = 0, group = 75, hostile = false, loot = false, count = 1, mm9 = {wander = "aimless", wander_wait = {30, 30}}})   -- a wanderer thinks out of the party's room (MM9 wakes the actors near the player), so the walk below runs; the wait keeps him still till then
    set("SkeletonDoorA0Peasant", made ~= nil and made[1] ~= nil and made[1] + 1 or 0)
    openGroup("PeasantDoor0")   -- the closet's door (AITriggerable: MM9's conscript opens it)
    arm(264, 2)
end
handlers[264] = function()   -- SkeletonDoorA0: SignalCreature walk (WalkToSpawner)
    if not fired(264) or var("SkeletonDoorA0") ~= 1 then return end
    local i = var("SkeletonDoorA0Peasant") - 1
    if i < 0 or not evt.MoveActorTo(i, 2458, 1966, 2384, 265) then arm(254, 0.1) return end
    arm(254, 20)
end
handlers[265] = function()   -- SkeletonDoorA0: at the chamber's centre (PlayMagicSound)
    if var("SkeletonDoorA0") ~= 1 then return end
    local i = var("SkeletonDoorA0Peasant") - 1
    if i >= 0 then evt.PlayActorClip(i, "cower") end
    closeGroup("PeasantDoor0")   -- its CloseWaitTime
    set("SkeletonDoorA0Cowered", var("SkeletonDoorA0Cowered") + 1)
    evt.PlaySoundName("sounds/magic/wizardeyeloop.wav", 0, 0, 0)
    arm(254, 1.2)
end
handlers[254] = function()   -- SkeletonDoorA0: the strike (TriggerSpawner convert, TransformCreature)
    if not fired(254) or var("SkeletonDoorA0") ~= 1 then return end
    local x, y, z = 2458, 1966, 2384
    local peasant = var("SkeletonDoorA0Peasant") - 1
    -- "convert" comes from the conscript himself (TriggerSpawner): a dead one sends none, and the chamber
    -- stays down with its switches locked (MM9.actorAlive; the walk timeout stands in for a live one's OnStuck)
    if peasant >= 0 and not MM9.actorAlive(peasant) then return end
    if peasant >= 0 then
        local px, py, pz = evt.GetMapActorPosition(peasant)
        if px ~= nil then x, y, z = px, py, pz end
        evt.StopActorMove(peasant); evt.ClearActorPresentation(peasant)
        evt.SetMonsterBit(peasant, ActorAttribute.Invisible, 1)   -- RemoveObject
        set("SkeletonDoorA0Peasant", 0)
    end
    evt.PlaySoundName("sounds/animsounds/pig/wince1.wav", 0, 0, 0)
    evt.Beam("ShooterTransform3", "openyamm:fx/arc_beam", 2458, 1966, 2744, 2458, 1966, 2444, 1.2)
    evt.Beam("ShooterTransform4", "openyamm:fx/arc_beam", 2458, 2130, 2744, 2458, 1966, 2444, 1.2)
    evt.Beam("ShooterTransform5", "openyamm:fx/arc_beam", 2458, 1802, 2744, 2458, 1966, 2444, 1.2)
    evt.PlaySoundName("sounds/magic/projectile14.wav", 0, 0, 0)
    local made = evt.SummonMonstersById({monster = 9135, x = x, y = y, z = z, radius = 16, group = 73, count = 1})
    set("SkeletonsMade", var("SkeletonsMade") + made)
    set("SkeletonDoorA0", 2)
    arm(255, 1)
end
handlers[255] = function()   -- SkeletonDoorA0: the release
    if not fired(255) or var("SkeletonDoorA0") ~= 2 then return end
    openGroup("SkeletonDoorA0")
    evt.SetDoorState(DOORS.TransformSwitch2, DoorAction.Close)
    evt.SetDoorState(DOORS.TransformSwitch3, DoorAction.Close)
    set("SkeletonDoorA0", 0)
    set("AmbientSound" .. TRANSFORMERS.SkeletonDoorA0.panel, 2)   -- the switches' CloseTrigger1: PanelOn off
end

-- The shooting range (ILSshootingbook.scr): a book's first use plays its OpenBook and starts its shooter,
-- which fires a bolt at the straw target in front of it every 1.5 s; ten bolts (50 HP, FireBolt 5) break
-- the target (it sinks into the floor), whose DeathTrigger sends the book Done. A use before that stops and
-- restarts the shooter (MM9's Off/On); the first use after it plays CloseBook and stops it for good.
-- Book var: 0 shut, 1 open and shooting, 2 done (target broken), 3 closed for good.
handlers[206] = function()   -- firebook2 -> shootfire1 -> Target19
    local state = var("firebook2")
    if state == 3 then return end   -- Stopped
    if state == 2 then
        evt.PlayDecorationClip(2, "closebook")   -- Done: PlayAnim CloseBook, Stopped
        set("firebook2", 3)
        return
    end
    if state == 0 then evt.PlayDecorationClip(2, "openbook") end   -- PlayAnim OpenBook
    set("firebook2", 1)
    evt.StartTimer(256, seconds(1.5))
end
handlers[256] = function()
    if var("firebook2") ~= 1 then evt.StopTimer(256) return end
    evt.FireMissile("Fire", 1762, 10214, 1454, 197, 10220, 1467, 0, "Fire", 0)
    MM9.launchSound("FireBolt", 1792, 10214, 1454)
    set("Target19Hits", var("Target19Hits") + 1)
    if var("Target19Hits") >= 10 then
        evt.StopTimer(256)
        set("firebook2", 2)
        openGroup("Target19")
    else
        evt.StartTimer(256, seconds(1.5))
    end
end
handlers[207] = function()   -- firebook3 -> fireball1 -> Target16
    local state = var("firebook3")
    if state == 3 then return end   -- Stopped
    if state == 2 then
        evt.PlayDecorationClip(0, "closebook")   -- Done: PlayAnim CloseBook, Stopped
        set("firebook3", 3)
        return
    end
    if state == 0 then evt.PlayDecorationClip(0, "openbook") end   -- PlayAnim OpenBook
    set("firebook3", 1)
    evt.StartTimer(257, seconds(1.5))
end
handlers[257] = function()
    if var("firebook3") ~= 1 then evt.StopTimer(257) return end
    evt.FireMissile("Fire", 1762, 10583, 1454, 197, 10578, 1467, 0, "Fire", 0)
    MM9.launchSound("FireBolt", 1792, 10583, 1454)
    set("Target16Hits", var("Target16Hits") + 1)
    if var("Target16Hits") >= 10 then
        evt.StopTimer(257)
        set("firebook3", 2)
        openGroup("Target16")
    else
        evt.StartTimer(257, seconds(1.5))
    end
end
handlers[208] = function()   -- firebook4 -> fireball2 -> Target6
    local state = var("firebook4")
    if state == 3 then return end   -- Stopped
    if state == 2 then
        evt.PlayDecorationClip(1, "closebook")   -- Done: PlayAnim CloseBook, Stopped
        set("firebook4", 3)
        return
    end
    if state == 0 then evt.PlayDecorationClip(1, "openbook") end   -- PlayAnim OpenBook
    set("firebook4", 1)
    evt.StartTimer(258, seconds(1.5))
end
handlers[258] = function()
    if var("firebook4") ~= 1 then evt.StopTimer(258) return end
    evt.FireMissile("Fire", 1757, 10908, 1454, 197, 10885, 1467, 0, "Fire", 0)
    MM9.launchSound("FireBolt", 1787, 10908, 1454)
    set("Target6Hits", var("Target6Hits") + 1)
    if var("Target6Hits") >= 10 then
        evt.StopTimer(258)
        set("firebook4", 2)
        openGroup("Target6")
    else
        evt.StartTimer(258, seconds(1.5))
    end
end

-- The summoner (Summoner.scr on LichSummoner, SpawnMgr.scr, SpawnLoc.scr on GhostPool0-3): the touch trigger
-- at the stair foot wakes it; a Specter rises from each ghost pool, and each time one dies another rises
-- from a random pool, while the summoner lives and until 10 are dead.
local POOLS = {{1475, -2621, -1159}, {-655, -492, -1159}, {-2785, -2621, -1159}, {-655, -4751, -1159}}
local function raiseGhost(k)
    local p = POOLS[k]
    local made = evt.SummonMonstersById({monster = 9140, x = p[1], y = p[2], z = p[3], radius = 32, group = 71, count = 1})
    set("GhostsRaised", var("GhostsRaised") + made)
end
handlers[230] = function()   -- TriggerLich -> LichSummoner startup
    if var("Summoner") ~= 0 then return end
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 70, 0, false) then return end
    set("Summoner", 1)
    for k = 1, 4 do raiseGhost(k) end
end

-- The explosion lab (KingKong.scr on ExplodeGhast, ExplodeRevenant, ExplodeDagrell0/1): either touch
-- trigger (they switch each other off: ForceBreak goes out once) makes each critter smash its own cage
-- front (it sinks away) with a swing (BreakCage: PlayAnim hattack1, the attack_melee clip) and the fire
-- behind that broken glass flares up (ExplodeSmoke0-3). A dead critter takes no ForceBreak (MM9.receives):
-- its cage stays standing and its fire unlit. None has an ANIM_NAME (p1): nothing loops while caged.
local KINGKONG = {{"ExplodeGhast", 139, "CageGhast", 323}, {"ExplodeRevenant", 138, "CageRevenant", 322}, {"ExplodeDagrell0", 141, "CageSpectre", 320}, {"ExplodeDagrell1", 140, "CageVenomous", 321}}   -- critter, its actor, its cage, its fire
local function bustCages()
    if var("CagesBroken") == 1 then return end
    set("CagesBroken", 1)
    for _, k in ipairs(KINGKONG) do
        if MM9.receives("lichlab", k[1], "ForceBreak", k[2]) then
            set("Broken" .. k[3], 1)
            openGroup(k[3])
            evt.PlayActorClip(k[2], "attack_melee")
            evt.SetSprite(k[4], true)
        end
    end
end
handlers[231] = function() bustCages() end   -- TriggerExplodeL
handlers[232] = function() bustCages() end   -- TriggerExplodeR

-- The hanging ickies (LL_FlyingCreature.scr): each wing's touch triggers send its eight ickies off; here
-- they hang peaceful until then and turn hostile.
handlers[233] = function() if var("BatsLobby") == 0 then set("BatsLobby", 1); evt.SetMonGroupBit(60, MonsterBits.Hostile, true) end end   -- LobbyBatTrigger0
handlers[234] = function() if var("BatsLobby") == 0 then set("BatsLobby", 1); evt.SetMonGroupBit(60, MonsterBits.Hostile, true) end end   -- LobbyBatTrigger1
handlers[235] = function() if var("BatsRightWing") == 0 then set("BatsRightWing", 1); evt.SetMonGroupBit(61, MonsterBits.Hostile, true) end end   -- RightWingBatTrigger0
handlers[236] = function() if var("BatsRightWing") == 0 then set("BatsRightWing", 1); evt.SetMonGroupBit(61, MonsterBits.Hostile, true) end end   -- RightWingBatTrigger1
handlers[237] = function() if var("BatsLeftWing") == 0 then set("BatsLeftWing", 1); evt.SetMonGroupBit(62, MonsterBits.Hostile, true) end end   -- LeftWingBatTrigger0
handlers[238] = function() if var("BatsLeftWing") == 0 then set("BatsLeftWing", 1); evt.SetMonGroupBit(62, MonsterBits.Hostile, true) end end   -- LeftWingBatTrigger1

handlers[95] = function()   -- any monster killed: the summoner's ghosts
    if var("Summoner") ~= 1 then return end
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 70, 0, false) then set("Summoner", 2) return end
    local killed = var("GhostKills")
    while killed < 10 and evt.CheckMonstersKilled(ActorKillCheck.Group, 71, killed + 1, false) do
        killed = killed + 1
        set("GhostKills", killed)
        if killed < 10 then raiseGhost(evt.RandomBetween(1, 4, 1)) end
    end
end
handlers[1] = function()   -- map load: the cage fires burn only once broken; the switch and the engine as left
    for _, k in ipairs(KINGKONG) do if var("Broken" .. k[3]) == 0 then evt.SetSprite(k[4], false) end end
    if var("LichSwitchDown") == 1 then evt.PlayDecorationClip(3, "down", "end") end
    for _, b in ipairs({{"firebook2", 2}, {"firebook3", 0}, {"firebook4", 1}}) do
        local state = var(b[1])
        if state == 1 or state == 2 then evt.PlayDecorationClip(b[2], "openbook", "end")
        elseif state == 3 then evt.PlayDecorationClip(b[2], "closebook", "end") end
    end
    if var("EngineSpin") == 1 or var("EngineSpin") == 2 then evt.PlayDecorationClip(129, "spincycle", "loop") end
end
-- DamageTriggerTarget (AutoResurrect.scr :OnResurrect): SkeletonMaster1 -> SkeletonMaster52.
local RAISED_BY_HIT = {[53] = 36}
handlers[96] = function(context)
    local risen = RAISED_BY_HIT[context.actorIndex]
    if risen == nil or var("Risen" .. risen) == 1 then return end
    set("Risen" .. risen, 1)
    evt.SetMonsterBit(risen, MonsterBits.Invisible, false)
    evt.SetMonsterBit(risen, MonsterBits.Hostile, true)
    evt.WakeActor(risen)
end
-- MM9's TouchToOpen doors: walking into one opens it (a 4 Hz poll of the party's position).
local TOUCH_DOORS = {
    {door = 13, box = {{2748, 5216, 1274}, {2986, 5311, 1638}}},   -- PeasantDoor
    {door = 14, box = {{2339, 2595, 2339}, {2577, 2689, 2662}}},   -- PeasantDoor0
}
handlers[900] = function()
    local x, y, z = evt.GetPartyPosition()
    for _, t in ipairs(TOUCH_DOORS) do
        local b = t.box
        if x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2]
                and z >= b[1][3] and z <= b[2][3] then
            evt.SetDoorState(t.door, DoorAction.Open)   -- an open door ignores it; a closing one reopens
        end
    end
    evt.StartTimer(900, seconds(0.25))
end

-- MM9's BonePile objects (dungeon/objects.py): a click searches the pile (evt.SearchLootProp: its
-- TreasureLevel loot once, DiseaseChance; the pile stays).
handlers[31551] = function() evt.SearchLootProp("mm9:lichlab:object:1551") end   -- BonePile2
handlers[31552] = function() evt.SearchLootProp("mm9:lichlab:object:1552") end   -- BonePile1
handlers[31553] = function() evt.SearchLootProp("mm9:lichlab:object:1553") end   -- BonePile0


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
RegisterEvent(126, "Door", handlers[126], "Door")
RegisterEvent(127, "Door", handlers[127], "Door")
RegisterEvent(128, "Door", handlers[128], "Door")
RegisterEvent(129, "Door", handlers[129], "Door")
RegisterEvent(130, "Door", handlers[130], "Door")
RegisterEvent(131, "Door", handlers[131], "Door")
RegisterEvent(132, "Door", handlers[132], "Door")
RegisterEvent(133, "Door", handlers[133], "Door")
RegisterEvent(134, "Door", handlers[134], "Door")
RegisterEvent(135, "Door", handlers[135], "Door")
RegisterEvent(136, "Door", handlers[136], "Door")
RegisterEvent(137, "Door", handlers[137], "Door")
RegisterEvent(138, "Door", handlers[138], "Door")
RegisterEvent(139, "Door", handlers[139], "Door")
RegisterEvent(140, "Door", handlers[140], "Door")
RegisterEvent(141, "Door", handlers[141], "Door")
RegisterEvent(142, "Door", handlers[142], "Door")
RegisterEvent(143, "Door", handlers[143], "Door")
RegisterEvent(144, "Door", handlers[144], "Door")
RegisterEvent(145, "Door", handlers[145], "Door")
RegisterEvent(146, "Door", handlers[146], "Door")
RegisterEvent(147, "Door", handlers[147], "Door")
RegisterEvent(148, "Door", handlers[148], "Door")
RegisterEvent(149, "Door", handlers[149], "Door")
RegisterEvent(150, "Door", handlers[150], "Door")
RegisterEvent(151, "Door", handlers[151], "Door")
RegisterEvent(152, "Door", handlers[152], "Door")
RegisterEvent(153, "Door", handlers[153], "Door")
RegisterEvent(154, "Door", handlers[154], "Door")
RegisterEvent(155, "Door", handlers[155], "Door")
RegisterEvent(156, "Door", handlers[156], "Door")
RegisterEvent(157, "Door", handlers[157], "Door")
RegisterEvent(158, "Door", handlers[158], "Door")
RegisterEvent(159, "Door", handlers[159], "Door")
RegisterEvent(160, "Door", handlers[160], "Door")
RegisterEvent(161, "Door", handlers[161], "Door")
RegisterEvent(162, "Door", handlers[162], "Door")
RegisterEvent(163, "Door", handlers[163], "Door")
RegisterEvent(164, "Door", handlers[164], "Door")
RegisterEvent(165, "Door", handlers[165], "Door")
RegisterEvent(166, "Door", handlers[166], "Door")
RegisterEvent(167, "Door", handlers[167], "Door")
RegisterEvent(168, "Door", handlers[168], "Door")
RegisterEvent(169, "Door", handlers[169], "Door")
RegisterEvent(41, "Chest", handlers[41], "Chest")
RegisterEvent(42, "Chest", handlers[42], "Chest")
RegisterEvent(43, "Chest", handlers[43], "Chest")
RegisterEvent(44, "Chest", handlers[44], "Chest")
RegisterEvent(45, "Chest", handlers[45], "Chest")
RegisterEvent(46, "Chest", handlers[46], "Chest")
RegisterEvent(47, "Chest", handlers[47], "Chest")
RegisterEvent(48, "Chest", handlers[48], "Chest")
RegisterEvent(200, "Lich switch", handlers[200], "Switch")
RegisterMapTimerEvent(250, seconds(3), handlers[250], "Engine strike", "", seconds(3))
RegisterMapTimerEvent(251, seconds(3), handlers[251], "Pod rises", "", seconds(3))
RegisterEvent(201, "Lever", handlers[201], "Lever")
RegisterMapTimerEvent(266, seconds(3), handlers[266], "Engine lever", "", seconds(3))
RegisterMapTimerEvent(267, seconds(3), handlers[267], "Engine clip", "", seconds(3))
RegisterEvent(222, "Cook pot", handlers[222], "Cook pot")
RegisterEvent(223, "Burner", handlers[223], "Burner")
RegisterEvent(224, "Scroll", handlers[224], "Scroll")
RegisterEvent(225, "Scroll", handlers[225], "Scroll")
RegisterEvent(226, "Scroll", handlers[226], "Scroll")
RegisterEvent(202, "Switch", handlers[202], "Switch")
RegisterEvent(203, "Switch", handlers[203], "Switch")
RegisterMapTimerEvent(252, seconds(3), handlers[252], "SkeletonDoorA strike", "", seconds(3))
RegisterMapTimerEvent(253, seconds(3), handlers[253], "SkeletonDoorA release", "", seconds(3))
RegisterMapTimerEvent(260, seconds(3), handlers[260], "SkeletonDoorA conscript", "", seconds(3))
RegisterMapTimerEvent(261, seconds(3), handlers[261], "SkeletonDoorA conscript walks", "", seconds(3))
RegisterEvent(262, "SkeletonDoorA conscript arrives", handlers[262])
RegisterEvent(204, "Switch", handlers[204], "Switch")
RegisterEvent(205, "Switch", handlers[205], "Switch")
RegisterMapTimerEvent(254, seconds(3), handlers[254], "SkeletonDoorA0 strike", "", seconds(3))
RegisterMapTimerEvent(255, seconds(3), handlers[255], "SkeletonDoorA0 release", "", seconds(3))
RegisterMapTimerEvent(263, seconds(3), handlers[263], "SkeletonDoorA0 conscript", "", seconds(3))
RegisterMapTimerEvent(264, seconds(3), handlers[264], "SkeletonDoorA0 conscript walks", "", seconds(3))
RegisterEvent(265, "SkeletonDoorA0 conscript arrives", handlers[265])
RegisterEvent(206, "Book", handlers[206], "Book")
RegisterMapTimerEvent(256, seconds(3), handlers[256], "shootfire1", "", seconds(3))
RegisterEvent(207, "Book", handlers[207], "Book")
RegisterMapTimerEvent(257, seconds(3), handlers[257], "fireball1", "", seconds(3))
RegisterEvent(208, "Book", handlers[208], "Book")
RegisterMapTimerEvent(258, seconds(3), handlers[258], "fireball2", "", seconds(3))
RegisterEvent(230, "TriggerLich", handlers[230])
RegisterEvent(231, "TriggerExplodeL", handlers[231])
RegisterEvent(232, "TriggerExplodeR", handlers[232])
RegisterEvent(233, "LobbyBatTrigger0", handlers[233])
RegisterEvent(234, "LobbyBatTrigger1", handlers[234])
RegisterEvent(235, "RightWingBatTrigger0", handlers[235])
RegisterEvent(236, "RightWingBatTrigger1", handlers[236])
RegisterEvent(237, "LeftWingBatTrigger0", handlers[237])
RegisterEvent(238, "LeftWingBatTrigger1", handlers[238])
RegisterEvent(1, "Map load", handlers[1])
RegisterMapTimerEvent(900, seconds(3), handlers[900], "Touch doors", "", seconds(3))
RegisterEvent(31551, "Bone Pile", handlers[31551], "Bone Pile")
RegisterEvent(31552, "Bone Pile", handlers[31552], "Bone Pile")
RegisterEvent(31553, "Bone Pile", handlers[31553], "Bone Pile")
RegisterMonsterKilledHook(95, "Lich Lab summoner", handlers[95])
RegisterMonsterDamageHook(96, "Lich Lab resurrect on hit", handlers[96])
