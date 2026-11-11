-- Lindisfarne Monastery, MM9 rework (level_generation/projects/mm9r_lindisfarnemonastery/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {OrganA1 = 5, OrganA2 = 6, OrganAs1 = 7, OrganAs2 = 8, OrganB1 = 9, OrganB2 = 10, OrganC1 = 11, OrganC2 = 12, OrganCs1 = 13, OrganCs2 = 14, OrganD1 = 15, OrganD2 = 16, OrganDs1 = 17, OrganDs2 = 18, OrganE1 = 19, OrganE2 = 20, OrganE3 = 21, OrganF1 = 22, OrganF2 = 23, OrganFs1 = 24, OrganFs2 = 25, OrganG1 = 26, OrganG2 = 27, OrganGs1 = 28, OrganGs2 = 29, Rope1 = 30, Rope2 = 31, Rope3 = 32, Rope4 = 33, Rope5 = 34, RotatingDoor0 = 35, RotatingDoor1 = 36, RotatingDoor2 = 37, RotatingDoor3 = 38, RotatingDoor4 = 39, RotatingDoor5 = 40, anavedoor1 = 2, anavedoor2 = 4, bnavedoor1 = 1, bnavedoor2 = 3}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.
handlers[101] = function() evt.SetDoorState(1, DoorAction.Trigger) evt.SetDoorState(2, DoorAction.Trigger) end   -- NaveDoor1
handlers[102] = function() evt.SetDoorState(3, DoorAction.Trigger) evt.SetDoorState(4, DoorAction.Trigger) end   -- NaveDoor2
handlers[103] = function() evt.SetDoorState(35, DoorAction.Trigger) end   -- RotatingDoor0
handlers[104] = function() evt.SetDoorState(36, DoorAction.Trigger) end   -- RotatingDoor1
handlers[105] = function() evt.SetDoorState(37, DoorAction.Trigger) end   -- RotatingDoor2
handlers[106] = function() evt.SetDoorState(38, DoorAction.Trigger) end   -- RotatingDoor3
handlers[107] = function() evt.SetDoorState(39, DoorAction.Trigger) end   -- RotatingDoor4
handlers[108] = function() evt.SetDoorState(40, DoorAction.Trigger) end   -- RotatingDoor5

-- Chests (MM9 TreasureChest objects; loot records in the scene).

-- Pressed movers (the organ keys, the ropes) rise again a second (a rope two: 32 LT at 25 LT/s) after the last
-- press (MM9's Door closes after its wait).
local PRESSED = {}
local function press(door, hold)
    evt.SetDoorState(door, DoorAction.Open)
    PRESSED[door] = true
    set("ReleaseArmed", 1)
    evt.StartTimer(260, seconds(hold or 1))
end
handlers[260] = function()
    if var("ReleaseArmed") ~= 1 then return end
    set("ReleaseArmed", 0)
    for door in pairs(PRESSED) do evt.SetDoorState(door, DoorAction.Close) end
    PRESSED = {}
end

local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
local function questSound() MM9.playSound("events/quest.wav") end   -- MM9 quest.wav: the shared quest sound

-- The monks' hostility (MonkHostility.inc, MONK_HOSTILITY): every monk is the party's friend (AddFriend Player)
-- until the party hurts or kills one (_OnDamage, _OnDeath: TurnHostilityOn). Then alarmbell.wav rings, the link
-- object is removed and every monk becomes hostile (BecomeHostile: AddEnemy Player, no more talk: BlockRude);
-- Thjorad turns on (Thjorad.scr OnObjectLinkBroken). Robert Aefgil (NPC284.scr) has no MonkHostility.
local MONKS = {[0] = true, [1] = true, [3] = true, [4] = true, [5] = true, [6] = true, [7] = true, [8] = true, [9] = true, [10] = true, [11] = true, [12] = true, [13] = true, [14] = true, [15] = true, [16] = true, [17] = true, [18] = true, [19] = true, [20] = true, [21] = true, [22] = true, [23] = true, [24] = true, [25] = true, [26] = true}
local function hostile() return var("MonksHostile") == 1 end
local function applyHostility()
    local on = hostile()
    evt.SetMonGroupBit(1, MonsterBits.Hostile, on)
    evt.SetMonGroupBit(2, MonsterBits.Hostile, on)
    -- BecomeHostile's AddEnemy Player: MM9's monster AI walks the monks at the party, the ones placed still at
    -- their chores and prayers too; the Thjorad monks' prayer after the bells ends (ThjoradMonk.scr OnDamage:
    -- Playanim stand)
    if on then for i in pairs(MONKS) do evt.SetActorImmobile(i, false) evt.ClearActorPresentation(i) end end
end
local function alarm()
    if hostile() then return end
    set("MonksHostile", 1)
    evt.PlaySoundName("events/alarmbell.wav", 0, 0, 0)
    applyHostility()
end
handlers[96] = function(context) if context.actorIndex ~= nil and MONKS[context.actorIndex] then alarm() end end
handlers[97] = function(context) if context.actorIndex ~= nil and MONKS[context.actorIndex] then alarm() end end

-- A click on a monk opens its dialogue (MonkGuardBasic.scr ScriptParams p1, ThjoradMonk.scr p2) unless the monks
-- are hostile (BlockRude); the Thjorad monks talk only while they guard Thjorad (OnUse: AtPrayer 0), the organ
-- player not while he plays (NPC420.scr OnUse: bIsPlaying).
handlers[53408] = function() if hostile() then return end MM9.openRude(283) end   -- Abbot Leffery
handlers[53409] = function() if hostile() then return end MM9.openRude(282) end   -- Grehgknak
handlers[53411] = function() if hostile() or var("OrganPlaying") == 1 then return end MM9.openRude(420) end   -- CommonerElfMaleA0
handlers[53572] = function() if hostile() then return end MM9.openRude(296) end   -- Initiate1
handlers[53573] = function() if hostile() then return end MM9.openRude(298) end   -- Initiate3
handlers[53574] = function() if hostile() then return end MM9.openRude(306) end   -- Initiate9
handlers[53575] = function() if hostile() then return end MM9.openRude(303) end   -- Initiate8
handlers[53576] = function() if hostile() then return end MM9.openRude(299) end   -- CommonerHuman2MaleB0
handlers[53577] = function() if hostile() then return end MM9.openRude(300) end   -- CommonerHuman2MaleB1
handlers[53578] = function() if hostile() then return end MM9.openRude(424) end   -- CommonerHuman2MaleB2
handlers[53579] = function() if hostile() then return end MM9.openRude(424) end   -- CommonerHuman2MaleB3
handlers[53580] = function() if hostile() then return end MM9.openRude(424) end   -- CommonerHuman2MaleB4
handlers[53581] = function() if hostile() then return end MM9.openRude(424) end   -- CommonerHuman2MaleB5
handlers[53582] = function() if hostile() then return end MM9.openRude(424) end   -- CommonerHuman2MaleB6
handlers[53583] = function() if hostile() then return end MM9.openRude(424) end   -- CommonerHuman2MaleB7
handlers[53584] = function() if hostile() then return end MM9.openRude(296) end   -- Initiate0
handlers[53585] = function() if hostile() then return end MM9.openRude(304) end   -- Initiate4
handlers[53586] = function() if hostile() then return end MM9.openRude(297) end   -- Initiate5
handlers[53587] = function() if hostile() then return end MM9.openRude(307) end   -- Initiate10
handlers[53588] = function() if hostile() then return end MM9.openRude(302) end   -- Initiate2
handlers[53589] = function() if hostile() then return end MM9.openRude(424) end   -- Initiate6
handlers[53590] = function() if hostile() then return end MM9.openRude(301) end   -- Initiate7
handlers[53591] = function() if hostile() or var("AtPrayer") == 1 then return end MM9.openRude(434) end   -- ThjoradMonk1
handlers[53592] = function() if hostile() or var("AtPrayer") == 1 then return end MM9.openRude(423) end   -- ThjoradMonk2
handlers[53593] = function() if hostile() or var("AtPrayer") == 1 then return end MM9.openRude(422) end   -- ThjoradMonk3
handlers[53594] = function() if hostile() or var("AtPrayer") == 1 then return end MM9.openRude(421) end   -- ThjoradMonk4

-- Thjorad (Thjorad.scr :OnUse): only once it is on (the bells rung, key 9507, or the monks hostile). With key 2
-- (the quest) and no key 31: key 31; else, without key 162: key 162; either way item 197 and 1000 experience, and the hammer is gone.
local function thjoradOn() return hostile() or MM9.hasKey(9507) == 1 end
local function thjoradTaken() return MM9.hasKey(31) == 1 or MM9.hasKey(162) == 1 end
handlers[75] = function()
    if not thjoradOn() or var("ThjoradTaken") == 1 then return end
    if MM9.hasKey(2) == 1 and MM9.hasKey(31) == 0 then
        MM9.giveKey(31)
        questSound()
    elseif MM9.hasKey(162) == 0 then
        MM9.giveKey(162)
    else
        return
    end
    give(197, "Thjorad.scr:Onuse")
    MM9.giveExperience(1000)
    set("ThjoradTaken", 1)
    evt.SetSprite(300, false)
end

-- The bells (LindisfarneBell.scr; ScriptParams p2 picks the note): a pull on a rope (the rope Door's OpenTrigger0
-- 'use') or a click on the bell uses it. :OnUse (only while Counter is 0: BellBusy<n>) plays Ring; its model keys
-- BellBing and BellBong play the note; at its end (RingDone) Stop plays, whose keys play the note again, and
-- Wait 1,3,StopDone: Counter 0 and, until key 9507, Trigger BellControl Bell<n>. Each step below is
-- (seconds from the use, what), the key times read from BELL.abc. The bell part and its clapper swing with the clips.
-- LindisfarneBellController.scr: :OnBell1 sets FirstBell; :OnBell<n> sets the next flag if the one before is set,
-- else :Reset clears all five; Bell5 after Bell4 runs :Finish.
local BELL_SOUND = {[1] = "events/churchbellring.wav", [2] = "events/churchbellring2.wav", [3] = "events/churchbellring3.wav", [4] = "events/churchbellring4.wav", [5] = "events/churchbellring5.wav"}
local BELL_STEPS = {{0.400, "note"}, {1.200, "note"}, {2.000, "stop"}, {2.366, "note"}, {3.233, "note"}, {5.000, "done"}}
local BELL_ORDER = {"FirstBell", "SecondBell", "ThirdBell", "FourthBell", "FifthBell"}
-- the Finish's peal: its waits before Bell2..Bell5 (wait 1 .5, 1 .5, 1 .25, 1 .25)
local FINALE_WAITS = {[2] = 0.5, [3] = 0.5, [4] = 0.25, [5] = 0.25}
local useBell, peal
local function praying(atLoad)   -- ThjoradMonk.scr :OnGoToPray (MM9 walks them; here they stand at the markers)
    if atLoad and MM9.actorAlive(23) or not atLoad and MM9.receives("lindisfarnemonastery", "ThjoradMonk1", "GoToPray", 23) then evt.SetMapActorPosition(23, 61, 10394, 1) end
    if atLoad and MM9.actorAlive(24) or not atLoad and MM9.receives("lindisfarnemonastery", "ThjoradMonk2", "GoToPray", 24) then evt.SetMapActorPosition(24, -108, 10399, 1) end
    if atLoad and MM9.actorAlive(25) or not atLoad and MM9.receives("lindisfarnemonastery", "ThjoradMonk3", "GoToPray", 25) then evt.SetMapActorPosition(25, -328, 10399, 4) end
    if atLoad and MM9.actorAlive(26) or not atLoad and MM9.receives("lindisfarnemonastery", "ThjoradMonk4", "GoToPray", 26) then evt.SetMapActorPosition(26, -553, 10404, 1) end
    if MM9.actorAlive(23) and not hostile() then evt.PlayActorClip(23, "pray", true) end
end
local function finish()
    if MM9.hasKey(9507) == 0 then MM9.giveExperience(2000) end
    MM9.giveKey(9507)
    set("AtPrayer", 1)
    praying()
    set("FinaleStep", 1)
    peal()
end
local function control(n)   -- BellControl :OnBell<n>
    if n == 1 then set(BELL_ORDER[1], 1) return end
    if var(BELL_ORDER[n - 1]) ~= 1 then
        for k = 1, 5 do set(BELL_ORDER[k], 0) end   -- :Reset
        return
    end
    set(BELL_ORDER[n], 1)
    if n == 5 then finish() end
end
useBell = function(n)   -- :OnUse
    if var("BellBusy" .. n) ~= 0 then return end
    set("BellBusy" .. n, 1)
    evt.PlayDecorationClip(310 + n, "ring")
    evt.StartTimer(270 + n, seconds(BELL_STEPS[1][1]))
end
local function swing(n)   -- the bell's timer: step BellBusy<n> of BELL_STEPS
    local step = var("BellBusy" .. n)
    local at = BELL_STEPS[step]
    if at == nil then
        evt.StopTimer(270 + n)
        return
    end
    if at[2] == "note" then
        evt.PlaySoundName(BELL_SOUND[n], 0, 0, 0)
    elseif at[2] == "stop" then
        evt.PlayDecorationClip(310 + n, "stop")
    else   -- :StopDone (Stop has ended: back to rest)
        set("BellBusy" .. n, 0)
        evt.StopTimer(270 + n)
        evt.PlayDecorationClip(310 + n, "")
        if MM9.hasKey(9507) == 0 then control(n) end
        return
    end
    set("BellBusy" .. n, step + 1)
    evt.StartTimer(270 + n, seconds(BELL_STEPS[step + 1][1] - at[1]))
end
-- :Finish uses Bell1 to Bell5 again (Trigger use: a bell still swinging ignores it), FINALE_WAITS apart.
peal = function()
    local step = var("FinaleStep")
    if step < 1 or step > 5 then
        evt.StopTimer(261)
        return
    end
    useBell(step)
    set("FinaleStep", step + 1)
    if step < 5 then evt.StartTimer(261, seconds(FINALE_WAITS[step + 1])) else evt.StopTimer(261) end
end
handlers[261] = function() peal() end
handlers[81] = function() useBell(1) end   -- Bell1
handlers[271] = function() swing(1) end   -- Bell1 swings
handlers[82] = function() useBell(2) end   -- Bell2
handlers[272] = function() swing(2) end   -- Bell2 swings
handlers[83] = function() useBell(3) end   -- Bell3
handlers[273] = function() swing(3) end   -- Bell3 swings
handlers[84] = function() useBell(4) end   -- Bell4
handlers[274] = function() swing(4) end   -- Bell4 swings
handlers[85] = function() useBell(5) end   -- Bell5
handlers[275] = function() swing(5) end   -- Bell5 swings
-- The ropes: each pull lowers the rope (Door, 32 LT down; it rises again) and rings its bell.
handlers[91] = function() press(DOORS.Rope1, 2) useBell(1) end   -- Rope1
handlers[92] = function() press(DOORS.Rope2, 2) useBell(3) end   -- Rope2
handlers[93] = function() press(DOORS.Rope3, 2) useBell(5) end   -- Rope3
handlers[94] = function() press(DOORS.Rope4, 2) useBell(4) end   -- Rope4
handlers[95] = function() press(DOORS.Rope5, 2) useBell(2) end   -- Rope5

-- The organ's 25 keys (Door, MoveDir down, MoveDist 2 LT, OpenStartSound Sounds\Music\<note>.wav).
handlers[130] = function() press(DOORS.OrganC1) evt.PlaySoundName("music/c1.wav", 0, 0, 0) end   -- C1
handlers[131] = function() press(DOORS.OrganCs1) evt.PlaySoundName("music/c#1.wav", 0, 0, 0) end   -- C#1
handlers[132] = function() press(DOORS.OrganD1) evt.PlaySoundName("music/d1.wav", 0, 0, 0) end   -- D1
handlers[133] = function() press(DOORS.OrganDs1) evt.PlaySoundName("music/d#2.wav", 0, 0, 0) end   -- D#1
handlers[134] = function() press(DOORS.OrganE1) evt.PlaySoundName("music/e1.wav", 0, 0, 0) end   -- E1
handlers[135] = function() press(DOORS.OrganF1) evt.PlaySoundName("music/f1.wav", 0, 0, 0) end   -- F1
handlers[136] = function() press(DOORS.OrganFs1) evt.PlaySoundName("music/f#1.wav", 0, 0, 0) end   -- F#1
handlers[137] = function() press(DOORS.OrganG1) evt.PlaySoundName("music/g1.wav", 0, 0, 0) end   -- G1
handlers[138] = function() press(DOORS.OrganGs1) evt.PlaySoundName("music/g#1.wav", 0, 0, 0) end   -- G#1
handlers[139] = function() press(DOORS.OrganA1) evt.PlaySoundName("music/a1.wav", 0, 0, 0) end   -- A1
handlers[140] = function() press(DOORS.OrganAs1) evt.PlaySoundName("music/a#1.wav", 0, 0, 0) end   -- A#1
handlers[141] = function() press(DOORS.OrganB1) evt.PlaySoundName("music/b1.wav", 0, 0, 0) end   -- B1
handlers[142] = function() press(DOORS.OrganC2) evt.PlaySoundName("music/c2.wav", 0, 0, 0) end   -- C2
handlers[143] = function() press(DOORS.OrganCs2) evt.PlaySoundName("music/c#2.wav", 0, 0, 0) end   -- C#2
handlers[144] = function() press(DOORS.OrganD2) evt.PlaySoundName("music/d2.wav", 0, 0, 0) end   -- D2
handlers[145] = function() press(DOORS.OrganDs2) evt.PlaySoundName("music/d#1.wav", 0, 0, 0) end   -- D#2
handlers[146] = function() press(DOORS.OrganE2) evt.PlaySoundName("music/e2.wav", 0, 0, 0) end   -- E2
handlers[147] = function() press(DOORS.OrganF2) evt.PlaySoundName("music/f2.wav", 0, 0, 0) end   -- F2
handlers[148] = function() press(DOORS.OrganFs2) evt.PlaySoundName("music/f#2.wav", 0, 0, 0) end   -- F#2
handlers[149] = function() press(DOORS.OrganG2) evt.PlaySoundName("music/g2.wav", 0, 0, 0) end   -- G2
handlers[150] = function() press(DOORS.OrganGs2) evt.PlaySoundName("music/g#2.wav", 0, 0, 0) end   -- G#2
handlers[151] = function() press(DOORS.OrganA2) evt.PlaySoundName("music/a2.wav", 0, 0, 0) end   -- A2
handlers[152] = function() press(DOORS.OrganAs2) evt.PlaySoundName("music/a#2.wav", 0, 0, 0) end   -- A#2
handlers[153] = function() press(DOORS.OrganB2) evt.PlaySoundName("music/b2.wav", 0, 0, 0) end   -- B2
handlers[154] = function() press(DOORS.OrganE3) evt.PlaySoundName("music/e3.wav", 0, 0, 0) end   -- E3

-- The organ player (NPC420.scr :OnRude, :PlaySong, :Play): with key 9506 from his dialogue he turns to the
-- organ (FaceObject E2, 180 degrees a second) and plays the hymn (LoopAnim play, HeroesPipe441.wav, 24 s), the key taken;
-- while he plays he does not talk (OnUse: bIsPlaying).
handlers[50411] = function()
    if MM9.hasKey(9506) == 0 then return end
    MM9.takeKey(9506)
    evt.PlaySoundName("events/heroespipe441.wav", 0, 0, 0)
    evt.FaceActorTo(3, -328, 10383, 1)
    evt.PlayActorClip(3, "play", true)
    set("OrganPlaying", 1)
    evt.StartTimer(263, seconds(24))
end
handlers[263] = function()   -- :OnExit
    evt.StopTimer(263)
    if var("OrganPlaying") ~= 1 then return end
    evt.ClearActorPresentation(3)
    set("OrganPlaying", 0)
end

-- Grehgknak the Right (NPC282.scr :OnRude): :giveletter (key 228 without 229: key 229, item 419); :paladins
-- (key 236 without 237: 63000 experience, :PromotePaladin for each character holding key 421-424, 5000 gold, key 237).
handlers[50409] = function()
    if MM9.hasKey(229) == 0 and MM9.hasKey(228) == 1 then
        MM9.giveKey(229)
        give(419, "NPC282.scr:giveletter")
        return
    end
    if MM9.hasKey(237) == 0 and MM9.hasKey(236) == 1 then
        MM9.giveExperience(37500) -- MM9 GiveExp 63000, mm9_quest_xp_profile.yml
        questSound()
        MM9.promoteParty("Paladin")
        MM9.giveGold(5000)
        MM9.giveKey(237)
    end
end

-- Abbot Leffery (NPC283.scr :OnRude :MissingRelic): key 341 without 342: item 368 taken, 3000 gold, 80000 experience, key 342.
handlers[50408] = function()
    if MM9.hasKey(342) == 0 and MM9.hasKey(341) == 1 then
        MM9.takeItem(368, "NPC283.scr:MissingRelic")
        MM9.giveGold(3000)
        MM9.giveExperience(12500) -- MM9 GiveExp 80000, mm9_quest_xp_profile.yml
        questSound()
        MM9.giveKey(342)
    end
    if MM9.hasKey(253) == 1 and var("PriestAskedAt") == 0 then
        set("PriestAskedAt", evt.CurrentGameMinutes() + 1)
    end
end

-- Robert Aefgil (NPC284.scr): hidden and not solid without key 254, gone with 255 (he left with
-- the party). NPC283.scr's '@M 5 : 00 Givekey': the first 5:00 after the abbot agreed (key 253) gives key 254
-- and Robert appears (NPC284.scr :Appear, also '@M 6 : 00').
local function robert()
    local shown = MM9.hasKey(254) == 1 and MM9.hasKey(255) == 0
    evt.SetMonGroupBit(3, MonsterBits.Invisible, not shown)
end
handlers[262] = function()
    if MM9.hasKey(253) == 1 and MM9.hasKey(254) == 0 and MM9.hasKey(255) == 0 then
        local asked = var("PriestAskedAt")
        if asked == 0 then asked = evt.CurrentGameMinutes() set("PriestAskedAt", asked) end
        local five = math.floor((asked - 1) / 1440) * 1440 + 300
        if five < asked - 1 then five = five + 1440 end
        if evt.CurrentGameMinutes() >= five then MM9.giveKey(254) end
    end
    robert()
end

handlers[76] = function() evt.SimpleMessage("Prayer to Igdra\n\nOh, Igdra\nYou bring us life eternal\nAnd warm our hearts.\nI shall give you your demands.\nAll my soul\nMy humility\nmy chastity\nmy very life itself\nThat you might walk beside me hereafter") end   -- Prop5: BookLetter.scr "470 Letter"
handlers[77] = function() evt.SimpleMessage("Letter to mother\n\nDearest mother,\nI know you bid me to work my hardest ever, and I try.  Life here is difficult.  I spend my days hard at work in the fields, and all night in prayer at the temple.  I am forbidden from speaking to another soul, not even to acknowledge their presence  \nI have not felt this lonely ever.  I long to be warm by the fire, eating the stew you prepared.  The emptiness in my heart would be unbearable, save for the warmth given to it at the beauty of this place.  Perhaps one day, you will find the strength to make a pilgrimage here.  I eagerly await that visit.\n\nHenrolm") end   -- Prop6: BookLetter.scr "471 Letter"
handlers[78] = function() evt.SimpleMessage("Letter to Abbot Leffery\n\nAbbot Leffery,\nMust we support that musician in our rafters?  I know that he plays the organ during your services, and the music he provides is a wonderful gift from Igdra, but he is intolerable!  I haven't had a nights rest in weeks.  In my dreams I hear the songs he plays.  I can hardly tolerate it.  Please, make it stop!") end   -- Prop7: BookLetter.scr "472 Letter"
handlers[79] = function() evt.SimpleMessage("Thjorad\n\nI've instructed a few of our monks to guard Thjorad while a case is being made to properly display it.  All monks are instructed to not bother any of those who are guarding Thjorad.  They are not to leave Thjorad except to obey the call to prayer.  Please do not make their job any more difficult than it already is.\n\nAbbot Leffery") end   -- Prop8: BookLetter.scr "473 Letter"

-- Map load (Thjorad.scr :Init, ThjoradMonk.scr :Init, NPC284.scr :Init, MonkHostility.inc).
handlers[1] = function()
    applyHostility()
    if thjoradTaken() then set("ThjoradTaken", 1) end
    if var("ThjoradTaken") == 1 then evt.SetSprite(300, false) end
    if MM9.hasKey(9507) == 1 then set("AtPrayer", 1) praying(true) end
    robert()
    set("OrganPlaying", 0)   -- a hymn a save cut short is over
    for n = 1, 5 do set("BellBusy" .. n, 0) end   -- so is a bell's swing (its report to BellControl too)
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
do local own = handlers[53408]; handlers[53408] = function() MM9.playSound("voices/npc/npc_283.wav"); own() end end   -- Abbot Leffery
do local own = handlers[53409]; handlers[53409] = function() MM9.playSound("voices/npc/npc_282.wav"); own() end end   -- Grehgknak
handlers[53410] = function() MM9.playSound("voices/npc/npc_284.wav"); MM9.openRude(284) end   -- CommonerHuman2MaleA1
do local own = handlers[53411]; handlers[53411] = function() MM9.playSound("voices/npc/npc_177.wav"); own() end end   -- CommonerElfMaleA0


RegisterEvent(101, "Door", handlers[101], "Door")
RegisterEvent(102, "Door", handlers[102], "Door")
RegisterEvent(103, "Door", handlers[103], "Door")
RegisterEvent(104, "Door", handlers[104], "Door")
RegisterEvent(105, "Door", handlers[105], "Door")
RegisterEvent(106, "Door", handlers[106], "Door")
RegisterEvent(107, "Door", handlers[107], "Door")
RegisterEvent(108, "Door", handlers[108], "Door")
RegisterEvent(53408, "Abbot Leffery", handlers[53408])
RegisterEvent(53409, "Grehgknak", handlers[53409])
RegisterEvent(53411, "CommonerElfMaleA0", handlers[53411])
RegisterEvent(53572, "Initiate1", handlers[53572])
RegisterEvent(53573, "Initiate3", handlers[53573])
RegisterEvent(53574, "Initiate9", handlers[53574])
RegisterEvent(53575, "Initiate8", handlers[53575])
RegisterEvent(53576, "CommonerHuman2MaleB0", handlers[53576])
RegisterEvent(53577, "CommonerHuman2MaleB1", handlers[53577])
RegisterEvent(53578, "CommonerHuman2MaleB2", handlers[53578])
RegisterEvent(53579, "CommonerHuman2MaleB3", handlers[53579])
RegisterEvent(53580, "CommonerHuman2MaleB4", handlers[53580])
RegisterEvent(53581, "CommonerHuman2MaleB5", handlers[53581])
RegisterEvent(53582, "CommonerHuman2MaleB6", handlers[53582])
RegisterEvent(53583, "CommonerHuman2MaleB7", handlers[53583])
RegisterEvent(53584, "Initiate0", handlers[53584])
RegisterEvent(53585, "Initiate4", handlers[53585])
RegisterEvent(53586, "Initiate5", handlers[53586])
RegisterEvent(53587, "Initiate10", handlers[53587])
RegisterEvent(53588, "Initiate2", handlers[53588])
RegisterEvent(53589, "Initiate6", handlers[53589])
RegisterEvent(53590, "Initiate7", handlers[53590])
RegisterEvent(53591, "ThjoradMonk1", handlers[53591])
RegisterEvent(53592, "ThjoradMonk2", handlers[53592])
RegisterEvent(53593, "ThjoradMonk3", handlers[53593])
RegisterEvent(53594, "ThjoradMonk4", handlers[53594])
RegisterEvent(81, "Bell", handlers[81], "Bell")
RegisterMapTimerEvent(271, seconds(3), handlers[271], "Bell1 swing", "", seconds(3))
RegisterEvent(82, "Bell", handlers[82], "Bell")
RegisterMapTimerEvent(272, seconds(3), handlers[272], "Bell2 swing", "", seconds(3))
RegisterEvent(83, "Bell", handlers[83], "Bell")
RegisterMapTimerEvent(273, seconds(3), handlers[273], "Bell3 swing", "", seconds(3))
RegisterEvent(84, "Bell", handlers[84], "Bell")
RegisterMapTimerEvent(274, seconds(3), handlers[274], "Bell4 swing", "", seconds(3))
RegisterEvent(85, "Bell", handlers[85], "Bell")
RegisterMapTimerEvent(275, seconds(3), handlers[275], "Bell5 swing", "", seconds(3))
RegisterEvent(91, "Rope", handlers[91], "Rope")
RegisterEvent(92, "Rope", handlers[92], "Rope")
RegisterEvent(93, "Rope", handlers[93], "Rope")
RegisterEvent(94, "Rope", handlers[94], "Rope")
RegisterEvent(95, "Rope", handlers[95], "Rope")
RegisterEvent(130, "Organ key", handlers[130], "Organ")
RegisterEvent(131, "Organ key", handlers[131], "Organ")
RegisterEvent(132, "Organ key", handlers[132], "Organ")
RegisterEvent(133, "Organ key", handlers[133], "Organ")
RegisterEvent(134, "Organ key", handlers[134], "Organ")
RegisterEvent(135, "Organ key", handlers[135], "Organ")
RegisterEvent(136, "Organ key", handlers[136], "Organ")
RegisterEvent(137, "Organ key", handlers[137], "Organ")
RegisterEvent(138, "Organ key", handlers[138], "Organ")
RegisterEvent(139, "Organ key", handlers[139], "Organ")
RegisterEvent(140, "Organ key", handlers[140], "Organ")
RegisterEvent(141, "Organ key", handlers[141], "Organ")
RegisterEvent(142, "Organ key", handlers[142], "Organ")
RegisterEvent(143, "Organ key", handlers[143], "Organ")
RegisterEvent(144, "Organ key", handlers[144], "Organ")
RegisterEvent(145, "Organ key", handlers[145], "Organ")
RegisterEvent(146, "Organ key", handlers[146], "Organ")
RegisterEvent(147, "Organ key", handlers[147], "Organ")
RegisterEvent(148, "Organ key", handlers[148], "Organ")
RegisterEvent(149, "Organ key", handlers[149], "Organ")
RegisterEvent(150, "Organ key", handlers[150], "Organ")
RegisterEvent(151, "Organ key", handlers[151], "Organ")
RegisterEvent(152, "Organ key", handlers[152], "Organ")
RegisterEvent(153, "Organ key", handlers[153], "Organ")
RegisterEvent(154, "Organ key", handlers[154], "Organ")
RegisterEvent(50411, "Organ player", handlers[50411])
RegisterEvent(50409, "Grehgknak", handlers[50409])
RegisterEvent(50408, "Abbot Leffery", handlers[50408])
RegisterEvent(75, "Thjorad", handlers[75], "Thjorad")
RegisterMapTimerEvent(261, seconds(3), handlers[261], "Bell peal", "", seconds(3))
RegisterMapTimerEvent(260, seconds(3), handlers[260], "Release", "", seconds(3))
RegisterMapTimerEvent(262, seconds(3), handlers[262], "Robert", "", seconds(3))
RegisterMapTimerEvent(263, seconds(3), handlers[263], "Hymn", "", seconds(3))
RegisterEvent(76, "Letter", handlers[76], "Letter")
RegisterEvent(77, "Letter", handlers[77], "Letter")
RegisterEvent(78, "Letter", handlers[78], "Letter")
RegisterEvent(79, "Letter", handlers[79], "Letter")
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53410, "Robert Aefgil", handlers[53410])
RegisterMonsterDamageHook(96, "Monks hurt", handlers[96])
RegisterMonsterKilledHook(97, "Monks killed", handlers[97])
