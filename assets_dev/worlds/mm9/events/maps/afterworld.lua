-- Afterworld, MM9 rework (level_generation/projects/mm9r_afterworld/convert.py writes this file).
-- MM9's doors, chests and scripted objects as native events; every door, pad and decoration is named by
-- its DAT object (see work/content.json and the project README).
local handlers = {}
local DOORS = {}
local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end
local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end
local function var(name) return evt.GetMapVar(name, 0) end
local function set(name, value) evt.SetMapVar(name, value) end
local function seconds(n) return n * 30 end

SetMapMetadata({onLoad = {1}, onLeave = {}, timers = {}, openedChestIds = {}})

-- Doors: each MM9 door group opens and closes on a click.

-- Chests (MM9 TreasureChest objects; loot records in the scene).

local function has(k) return MM9.hasKey(k) == 1 end
local function quest() MM9.playSound("sounds/events/quest.wav") end
local function reward(key, xp, gold) MM9.giveKey(key); if xp > 0 then MM9.giveExperience(xp) end; if gold > 0 then MM9.giveGold(gold) end; quest() end

SKRAELOS_ACTOR = 1   -- Skraelos0: the speaker of the talks his scenes open (greeting_lua)
local function show(a, on) evt.SetMonsterBit(a, ActorAttribute.Invisible, on and 0 or 1) end
local HEROES = {6, 3, 4, 7, 5, 2}   -- BjarniThorvaldssen0, KiratheCold0, MarkeltheGreat0, SigmundtheStressed0, SvenSvenssen0, TryggvaRavenlocks0
local function showHeroes(on)
    set("HeroesShown", on and 1 or 0)
    for _, a in ipairs(HEROES) do show(a, on) end
end
local function allKeys(first, last) for k = first, last do if not has(k) then return false end end return true end
local function sixFires()   -- the Six Fires, by their stages' keys (SixFires.inc, NPC336.scr "On")
    evt.SetSprite(420, has(381) and 1 or 0, "0")   -- GuiltFire
    evt.SetSprite(421, has(383) and 1 or 0, "0")   -- ConfessionFire
    evt.SetSprite(422, has(491) and 1 or 0, "0")   -- SufferingFire
    evt.SetSprite(423, has(387) and 1 or 0, "0")   -- RetributionFire
    evt.SetSprite(424, has(389) and 1 or 0, "0")   -- AbsolutionFire
    evt.SetSprite(425, has(391) and 1 or 0, "0")   -- RebirthFire
end

-- On load: the Six Fires; the heroes as SixFires.inc :Confession left them, Forad Darre while Retribution waits for his death,
handlers.regionLoad = function()
    sixFires()
    showHeroes(var("HeroesShown") == 1)
    set("Mm9ExitDisabled105", has(390) and 0 or 1)   -- ExitTrigger1 (StartOn 0) until :Rebirth
    show(0, has(5021) and not has(387))   -- ForadDarre0
end


-- NPC336.scr :OnUse (a click on Skraelos, then his dialogue): Confession's six confessions (keys 501-506) give
-- key 383; Absolution's five swords (items 563-567) are taken for key 389. 52 000 experience each.
handlers[53094] = function()   -- Skraelos0
    if has(382) and not has(383) and allKeys(501, 506) then
        reward(383, 22500, 0)   -- ConfessionFire On -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
    end
    if has(388) and not has(389) then
        local swords = 0
        for item = 563, 567 do swords = swords + MM9.hasItem(item, "afterworld:NPC336") end
        if swords == 5 then
            for item = 563, 567 do MM9.takeItem(item, "afterworld:NPC336") end
            reward(389, 22500, 0)   -- AbsolutionFire On -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
        end
    end
    sixFires()
    MM9.openRude(336)
end
-- NPC336.scr :Init ("Afterworld") -> OnFoundPlayer :DoRude: key 379, his dialogue and voice (each visit).
handlers[56094] = function()   -- Skraelos0
    MM9.giveKey(379)
    MM9.openRude(336)
    MM9.playSound("voices/npc/npc_336.wav")
end

-- NPC336.scr :OnRude with SixFires.inc: the fire whose key the dialogue just gave (then the fires shown).
local function skraelosExit()
    if has(392) then   -- :Failure
        for k = 379, 392 do MM9.takeKey(k) end
        evt.MoveToMap(-7281, 2952, 1, 0, 0, 0, 0, 0, "hallofthegods.blv")   -- ExitTrigger0's row
        return
    end
    if has(380) and not has(381) then   -- :Guilt: the cinematic afterworld_guilt (key 381, then his greeting)
        MM9Cinematic.start("afterworld_guilt")
        return
    end
    if has(382) then showHeroes(not has(383)) end   -- :Confession
    if has(384) and not has(491) then   -- :Suffering
        if has(385) then
            MM9.giveKey(491); MM9.giveExperience(22500) -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
            evt.ForPlayer(Players.All); MM9.clearCondition(13)   -- SufferingFire On
            quest()
            set("Questioned", 0)
        elseif var("Questioned") == 1 then
            set("Questioned", 0)   -- the Questioner's own exit: asked again on the next talk
        else
            set("Questioned", 1)   -- :Questioner: SetCondition 13 (poisoned and diseased), DoRude 432
            evt.ForPlayer(Players.All); SetValue(VarTag.PoisonedGreen, 0); SetValue(VarTag.DiseasedGreen, 0)
            MM9.openRude(432)
            return
        end
    end
    if has(386) and not has(387) and not has(5021) then   -- :Retribution
        MM9.giveKey(5021)
        show(0, true)   -- ForadDarre0 setflag visible
        evt.SummonMonstersById({monster = 9131, x = 7466, y = 5148, z = 1051, radius = 128, count = 3})   -- BadGuys0
        evt.SummonMonstersById({monster = 9130, x = 7466, y = 5148, z = 1051, radius = 128, count = 2})   -- BadGuys0
        evt.SummonMonstersById({monster = 9131, x = 10087, y = 561, z = 1051, radius = 128, count = 5})   -- BadGuys1
        evt.SummonMonstersById({monster = 9130, x = 10087, y = 561, z = 1051, radius = 128, count = 2})   -- BadGuys1
    end
    if has(388) and not has(492) then   -- :Absolution (RetributionFire On)
        reward(492, 22500, 0) -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
        evt.SummonMonstersById({monster = 9182, x = 7466, y = 5148, z = 1051, radius = 128, count = 1})   -- BadGuys0
        evt.SummonMonstersById({monster = 9174, x = 10087, y = 561, z = 1051, radius = 128, count = 1})   -- BadGuys1
        evt.SummonMonstersById({monster = 9162, x = 7466, y = 4493, z = 1079, radius = 128, count = 5})   -- GoodGuys0
    end
    if has(390) then   -- :Rebirth: ExitTrigger1 on; its undead come again at every exit, as MM9's
        set("Mm9ExitDisabled105", 0)
        evt.SummonMonstersById({monster = 9182, x = 7466, y = 5148, z = 1051, radius = 128, count = 1})   -- BadGuys0
        evt.SummonMonstersById({monster = 9174, x = 10087, y = 561, z = 1051, radius = 128, count = 1})   -- BadGuys1
        evt.SummonMonstersById({monster = 9162, x = 7466, y = 4493, z = 1079, radius = 128, count = 5})   -- GoodGuys0
    end
end
handlers[50094] = function() skraelosExit(); sixFires() end   -- Skraelos0

-- PropTrigger.scr on ExitTrigger1 ("Skraelos0 Reborn", on touch) -> NPC336.scr :OnReborn: after :Rebirth (key
-- 390) leaving by ExitTrigger1 (nearer it than ExitTrigger0) gives keys 391 and 102 and 52 000 experience.
-- A slain Skraelos takes no Reborn (MM9.receives, scr_audit README "Implicit engine semantics").
handlers[600] = function()
    if not has(390) or has(391) then return end
    local x, y = evt.GetPartyPosition()
    local d0 = (x - 16969) ^ 2 + (y - -1405) ^ 2
    local d1 = (x - -2941) ^ 2 + (y - 5160) ^ 2
    if d1 > d0 then return end
    if not MM9.receives("afterworld", "Skraelos0", "Reborn", 1) then return end
    MM9.giveKey(391); MM9.giveKey(102); MM9.giveExperience(22500); quest()   -- RebirthFire On -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
end
-- TM_Hardrock.scr "1 387" (RetributionCounter, Forad Darre's DeathTriggerTarget "OneDown"): one death
-- completes it: key 387 and the quest sound.
handlers[601] = function(context)
    if context.actorIndex == 0 and not has(387) then MM9.giveKey(387); quest(); sixFires() end
end



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

-- Cinematic afterworld_guilt (SixFires.inc :Guilt..:FadeIn2, AfterWorldCam1.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["afterworld_guilt"] = {
    { "done", function()
        if not has(381) then MM9.giveKey(381) end
    end },
    { "greeting", function()
        MM9.giveKey(379); MM9.openRude(336, SKRAELOS_ACTOR); MM9.playSound("voices/npc/npc_336.wav")
    end },
}
RegisterEvent(36001, "Cinema afterworld_guilt: done", function() MM9Cinematic.runStep("afterworld_guilt", 1) end)
RegisterEvent(36002, "Cinema afterworld_guilt: greeting", function() MM9Cinematic.runStep("afterworld_guilt", 2) end)
RegisterEvent(36000, "Cinema afterworld_guilt: done", function() MM9Cinematic.finish("afterworld_guilt") end)
MM9Cinematic.play["afterworld_guilt"] = function()
    if evt.GetMapVar("Cinema.afterworld_guilt.started", 0) == 0 then
        evt.SetMapVar("Cinema.afterworld_guilt.started", 1)
        evt.PlayCinematic("afterworld_guilt", 36000)
    end
end

handlers[1] = function()
    if handlers.regionLoad then handlers.regionLoad() end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53096] = function() MM9.playSound("voices/npc/npc_180.wav"); MM9.openRude(180) end   -- TryggvaRavenlocks0
handlers[53097] = function() MM9.playSound("voices/npc/npc_239.wav"); MM9.openRude(239) end   -- KiratheCold0
handlers[53098] = function() MM9.playSound("voices/npc/npc_127.wav"); MM9.openRude(127) end   -- MarkeltheGreat0
handlers[53099] = function() MM9.playSound("voices/npc/npc_003.wav"); MM9.openRude(3) end   -- SvenSvenssen0
handlers[53100] = function() MM9.playSound("voices/npc/npc_045.wav"); MM9.openRude(45) end   -- BjarniThorvaldssen0
handlers[53101] = function() MM9.playSound("voices/npc/npc_087.wav"); MM9.openRude(87) end   -- SigmundtheStressed0


RegisterEvent(53094, "Skraelos", handlers[53094])
RegisterEvent(56094, "Skraelos", handlers[56094])
RegisterEvent(50094, "Skraelos", handlers[50094])
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53096, "Tryygva Ravenlocks", handlers[53096])
RegisterEvent(53097, "Kira the Cold", handlers[53097])
RegisterEvent(53098, "Markel the Great", handlers[53098])
RegisterEvent(53099, "Sven Forkbeard", handlers[53099])
RegisterEvent(53100, "Bjarni Thorvaldssen", handlers[53100])
RegisterEvent(53101, "Sigmund the Stressed", handlers[53101])
RegisterMonsterKilledHook(601, "Forad Darre killed", handlers[601])
RegisterMapOnLeaveEvent(600, "Reborn", handlers[600])
