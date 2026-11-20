-- Hall of the Gods, MM9 rework (level_generation/projects/mm9r_hallofthegods/convert.py writes this file).
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

local function give(raw, source)
    local item = MM9.ItemIds[raw]
    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end
    return MM9.giveItem(raw, source)
end
local function questSound() MM9.playSound("events/quest.wav") end   -- MM9 quest.wav: the shared quest sound
-- ExitTrigger0 (Afterworld, StartPoint0): MM9's scripts trigger it (`trigger ExitTrigger0 trigger`); the volume
-- stands in the air beyond the hall's east end, out of reach. The move goes to its arrival.
local function toAfterworld()
    set("ToAfterworld", var("ToAfterworld") + 1)
    evt.MoveToMap(1731, -2225, 1168, 512, 0, 0, 0, 1, "afterworld.blv")
end

-- Krohn (NPC335.scr :OnRude :StopNjam): key 108 (Tamur spoken to) without 191: Njam's Key (576), key 191,
-- 218000 experience and the quest sound.
handlers[50124] = function()   -- Krohn0
    if MM9.hasKey(191) == 0 and MM9.hasKey(108) == 1 then
        give(576, "NPC335.scr:StopNjam")
        MM9.giveKey(191)
        MM9.giveExperience(22500) -- MM9 GiveExp 218000, mm9_quest_xp_profile.yml
        questSound()
    end
end

-- Skraelos (NPC336.scr :OnRude with ScriptParams Hall): :Teleport (key 101 without 102: key 379 and off to the
-- Afterworld), :sixfires (key 103 without 189: key 189, 52000 experience, the quest sound), :Failure (key 392:
-- keys 379-392 taken, back to the Afterworld). The six fires' scenes (:Guilt ... :Rebirth, keys 380-390) run
-- against the Afterworld's objects and are carried there (README).
handlers[50125] = function()   -- Skraelos
    local away = false
    if MM9.hasKey(102) == 0 and MM9.hasKey(101) == 1 then
        MM9.giveKey(379)
        away = true
    end
    if MM9.hasKey(189) == 0 and MM9.hasKey(103) == 1 then
        MM9.giveKey(189)
        MM9.giveExperience(22500) -- MM9 GiveExp 52000, mm9_quest_xp_profile.yml
        questSound()
    end
    if MM9.hasKey(392) == 1 then
        for key = 379, 392 do MM9.takeKey(key) end
        away = true
    end
    if away then toAfterworld() end
end

-- Fre (NPC337.scr :OnRude :GoldenHonk): key 346 without 347: 10000 gold, 80000 experience, the quest sound,
-- the Golden Honk (369) taken, key 347.
handlers[50126] = function()   -- Fre
    if MM9.hasKey(347) == 0 and MM9.hasKey(346) == 1 then
        MM9.giveGold(10000)
        MM9.giveExperience(22500) -- MM9 GiveExp 80000, mm9_quest_xp_profile.yml
        questSound()
        MM9.takeItem(369, "NPC337.scr:GoldenHonk")
        MM9.giveKey(347)
    end
end

-- The bill of sale on the bench (Prop3: BookLetter.scr "480 Letter 1": DoLetter 480).
handlers[76] = function() evt.SimpleMessage("Bill of Sale\n\nPurchased by Fre for the sum of 5,000 gold, one Emperor Goose.\nArslegard Pet Shop") end

-- The end of the game (WinMan.scr ScriptParams Part2 :Init): with key 109 (Njam beaten) and without the Writ of
-- Fate (394), :OnKrohn starts the cinema: :StartPart2 shows Hanndl, Krohn and Skraelos (WG_NPC334/335/336.scr
-- :OnStart; Hanndl's shows the three Wyrdes) and hides Krohn0 (:Loop); Hanndl walks to HanndlMarker and the
-- gods talk. :End gives the Writ of Fate; :Release hides the cinema's gods again and puts Krohn0 back.
-- The cinematic gods_epilogue (cinematics_hall.py) plays it; DoHighScore is the world's completion (key 109).
local function cinemaShown(on)
    evt.SetMonGroupBit(1, MonsterBits.Invisible, not on)
    evt.SetMonGroupBit(2, MonsterBits.Invisible, on)
end

-- Map load (WinMan.scr :Init, WG_NPC334/335/336.scr :Loop): with key 109 (Njam beaten), without the Writ of Fate
-- (394) and before the epilogue ended here, the cinematic gods_epilogue (cinematics_hall.py) plays.
handlers[1] = function()
    cinemaShown(false)
    if MM9.hasKey(109) == 1 and MM9.hasItem(394) == 0 and var("CinemaDone") == 0 then
        MM9Cinematic.start("gods_epilogue")
    end
end

-- MM9's greeting voices (dungeon/voices.py): a click on these people plays their GreetingSound or the
-- voice their script's :OnUse plays, then opens their dialogue (or runs the map's own click).
handlers[53124] = function() MM9.playSound("voices/npc/npc_335.wav"); MM9.openRude(335) end   -- Krohn0
handlers[53125] = function() MM9.playSound("voices/npc/npc_336.wav"); MM9.openRude(336) end   -- Skraelos
handlers[53126] = function() MM9.playSound("voices/npc/npc_337.wav"); MM9.openRude(337) end   -- Fre


RegisterEvent(50124, "Krohn", handlers[50124])
RegisterEvent(50125, "Skraelos", handlers[50125])
RegisterEvent(50126, "Fre", handlers[50126])
RegisterEvent(76, "Letter", handlers[76], "Letter")
RegisterEvent(1, "Map load", handlers[1])
RegisterEvent(53124, "Krohn", handlers[53124])
RegisterEvent(53125, "Skraelos", handlers[53125])
RegisterEvent(53126, "Fre", handlers[53126])


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

-- Cinematic gods_epilogue (WinMan.scr Part2 :OnKrohn..:Release, WG_Scene7Cam1.scr, WG_NPC334/335/336.scr): <stem>.cinematics.yml shows it;
-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs
-- any not yet run (mm9r_common/cutscenes.py).
MM9Cinematic.steps["gods_epilogue"] = {
    { "gather", function()
        cinemaShown(true)
    end },
    { "writ", function()
        give(394, "WinMan.scr:End")
    end },
    { "release", function()
        set("CinemaDone", 1)
        cinemaShown(false)
    end },
}
RegisterEvent(36001, "Cinema gods_epilogue: gather", function() MM9Cinematic.runStep("gods_epilogue", 1) end)
RegisterEvent(36002, "Cinema gods_epilogue: writ", function() MM9Cinematic.runStep("gods_epilogue", 2) end)
RegisterEvent(36003, "Cinema gods_epilogue: release", function() MM9Cinematic.runStep("gods_epilogue", 3) end)
RegisterEvent(36000, "Cinema gods_epilogue: done", function() MM9Cinematic.finish("gods_epilogue") end)
MM9Cinematic.play["gods_epilogue"] = function()
    if evt.GetMapVar("Cinema.gods_epilogue.started", 0) == 0 then
        evt.SetMapVar("Cinema.gods_epilogue.started", 1)
        evt.PlayCinematic("gods_epilogue", 36000)
    end
end
