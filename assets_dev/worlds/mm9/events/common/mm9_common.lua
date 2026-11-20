MM9 = MM9 or {}
MM9.ItemIds = MM9.ItemIds or {}

-- MM9's promotion quests on our MMerge class lines (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And Classes",
-- the user's decision 2026-11-05): each quest promotes the lines of its theme, a first-tier quest a base class to its
-- first promotion, a second-tier one a first promotion to its second; MM9 is a wildcard world (every line, Jadame's
-- racial classes too). Keys: canonical class names (ClassSkillTable, compared case- and space-blind).
MM9.Promotions = {
    -- tier 1: the base classes' first promotion
    mercenary = {Knight = "Cavalier", Thief = "Rogue", Archer = "WarriorMage"},
    crusader = {Paladin = "Crusader", Ranger = "Hunter", Monk = "Initiate"},
    scholar = {Sorcerer = "Wizard"},
    healer = {Cleric = "Priest", Druid = "GreatDruid"},
    -- tier 2: the final promotion; Jadame's racial classes start at the first tier, so theirs comes here
    -- (Minotaur, Troll, Dragon with the champion's quest, Vampire with the assassin's, Dark Elf with the druid's)
    gladiator = {Cavalier = "Champion", Initiate = "Master", Minotaur = "MinotaurLord", Troll = "WarTroll",
        Dragon = "GreatWyrm"},
    assassin = {Rogue = "Assassin", Vampire = "Nosferatu"},
    paladin = {Crusader = "Hero"},
    ranger = {Hunter = "RangerLord", WarriorMage = "MasterArcher"},
    mage = {Wizard = "ArchMage"},
    lich = {Wizard = "Lich"},
    priest = {Priest = "PriestLight"},
    druid = {GreatDruid = "ArchDruid", DarkElf = "Patriarch"},
}

local function classKey(name)
    return (string.gsub(string.lower(tostring(name or "")), "[%s_%-]", ""))
end

-- The class an MM9 promotion quest gives a member, or nil (not of the quest's lines, or past that tier).
function MM9.promotionTarget(rawPromotion, playerIndex)
    local lines = MM9.Promotions[string.lower(tostring(rawPromotion))]
    if lines == nil then
        return nil
    end
    local current = classKey(GetPlayerClassName(playerIndex))
    for from, to in pairs(lines) do
        if classKey(from) == current then
            return to
        end
    end
    return nil
end

-- Whether some member would be promoted by the quest.
function MM9.canPromote(rawPromotion)
    for _, playerIndex in ipairs(PartyMembers()) do
        if MM9.promotionTarget(rawPromotion, playerIndex) ~= nil then
            return true
        end
    end
    return false
end

local function rawQBit(rawKey)
    if rawKey == nil or rawKey < 1 or rawKey > 9999 then
        evt.StatusText("Invalid MM9 quest key: " .. tostring(rawKey))
        return nil
    end

    return 90000 + rawKey
end

function MM9.hasKey(rawKey)
    local qbit = rawQBit(rawKey)
    return qbit ~= nil and evt.HasQuestBit(qbit) and 1 or 0
end

function MM9.giveKey(rawKey)
    local qbit = rawQBit(rawKey)
    if qbit ~= nil then
        evt.SetQuestBit(qbit)
    end
end

function MM9.takeKey(rawKey)
    local qbit = rawQBit(rawKey)
    if qbit ~= nil then
        evt.ClearQuestBit(qbit)
    end
end

local function reportUnavailableItem(operation, rawItemId, provenance)
    local source = provenance ~= nil and tostring(provenance) or "unknown source"
    local status = "MM9 item " .. tostring(rawItemId) .. " is not imported yet."
    evt.Debug(
        "[MM9RuntimeError] kind=item operation=" .. tostring(operation)
        .. " raw_item_id=" .. tostring(rawItemId) .. " source=\"" .. source .. "\"")
    evt.StatusText(status)
end

local function itemId(rawItemId, operation, provenance)
    local item = MM9.ItemIds[rawItemId]
    if item == nil then
        reportUnavailableItem(operation, rawItemId, provenance)
    end

    return item
end

function MM9.hasItem(rawItemId, provenance)
    local item = itemId(rawItemId, "has", provenance)
    return item ~= nil and HasItemAnywhere(item) and 1 or 0
end

function MM9.giveItem(rawItemId, provenance)
    local item = itemId(rawItemId, "give", provenance)
    if item == nil then
        return false
    end

    GiveItem(item)
    return true
end

-- A script's take is the item handed in: Hjordisa the Hag does not give it back as lost (dialogue/lost_items.yml,
-- game/mm9/Mm9RudeDialogue.cpp).
function MM9.takeItem(rawItemId, provenance)
    local item = itemId(rawItemId, "take", provenance)
    if item == nil then
        return false
    end

    RemoveItem(item)
    evt.SetGlobalVar("MM9.HandedIn." .. tostring(rawItemId), 1)
    return true
end

function MM9.hasGold(amount)
    return evt.Cmp(Gold, amount) and 1 or 0
end

-- actorIndex (optional): the speaker, for a talk a map script opens outside his click (an approach talk), so that
-- the dialogue's close runs his OnRudeExit event.
function MM9.openRude(rudeId, actorIndex)
    evt.OpenMm9Rude(rudeId, actorIndex)
end

-- MM9's AddNPC / RemoveNPC: the party's MM9 hireling of that RUDE id (Tamur Leng joins, NPC309.scr; Forad leaves at
-- the council, ARGUMENT.scr). Keys stay as the script sets them.
function MM9.addHireling(rudeId)
    return evt.AddMm9Hireling(rudeId)
end

function MM9.removeHireling(rudeId)
    return evt.RemoveMm9Hireling(rudeId)
end

function MM9.playSound(soundName)
    local normalizedName = string.lower(string.gsub(tostring(soundName or ""), "\\", "/"))
    if normalizedName == "sounds/events/quest.wav" or normalizedName == "events/quest.wav" then
        evt.PlaySoundOnce(20001, 0, 0)
        return
    end

    evt.PlaySoundName(soundName, 0, 0, 0)
end

-- The launch sounds of MM9's projectiles that Shooters and map scripts fire (PROJECTILE.txt "Launch Sound"; the
-- client's projectile effect plays it where the projectile starts, cshell.dll 0x10076d15). DragonBreath2 has none.
-- Keyed by the projectile's name in lower case.
MM9.ProjectileLaunchSounds = {
    firebolt = "weapons/dragonfireboltlaunch.wav",
    kbyellowline = "weapons/kbyellowlinelaunch.wav",
    lightning = "weapons/chainlight01.wav",
    purplethingy = "weapons/purplethingylaunch.wav",
    screamingskull = "weapons/fear.wav",
    yellowline = "weapons/yellowlinelaunch.wav",
}

-- A shot's launch sound at the shooter (x, y, z); `projectile` is its PROJECTILE.txt name.
function MM9.launchSound(projectile, x, y, z)
    local soundName = MM9.ProjectileLaunchSounds[string.lower(projectile)]
    if soundName ~= nil then
        evt.PlaySoundName(soundName, math.floor(x + 0.5), math.floor(y + 0.5), math.floor(z + 0.5))
    end
end

local function scrVariableName(sourceObjectIndex, variableName)
    return "MM9.SCR." .. tostring(sourceObjectIndex) .. "." .. tostring(variableName)
end

function MM9.scrValue(sourceObjectIndex, variableName, defaultValue)
    return evt.GetMapVar(scrVariableName(sourceObjectIndex, variableName), defaultValue or 0)
end

function MM9.setScrValue(sourceObjectIndex, variableName, value)
    evt.SetMapVar(scrVariableName(sourceObjectIndex, variableName), value or 0)
end

function MM9.foundPlayerEnabled(sourceObjectIndex)
    return MM9.scrValue(sourceObjectIndex, "FoundPlayerDisabled", 0) == 0
end

function MM9.disableFoundPlayer(sourceObjectIndex)
    MM9.setScrValue(sourceObjectIndex, "FoundPlayerDisabled", 1)
end

function MM9.giveGold(amount)
    AddValue(Gold, amount)
end

function MM9.takeGold(amount)
    SubtractValue(Gold, amount)
end

-- MM9's GiveExp gives the full amount to every member (MM6-MM8 quests do the same through ForPlayer(All)). MM9 scripts
-- never select a member, so the selection goes back to the current member for the commands that follow.
function MM9.giveExperience(amount)
    evt.ForPlayer(Players.All)
    AddValue(Experience, amount)
    evt.ForPlayer(Players.Current)
end

function MM9.random(minimum, maximum, step)
    return evt.RandomBetween(minimum, maximum, step)
end

function MM9.excludedActorOperation(operation)
    return operation ~= nil
end

local function removedVar(actorIndex)
    return "MM9.Removed." .. tostring(actorIndex)
end

-- MM9's RemoveObject on a map actor: it is gone (hidden here) and takes no further message (MM9.receives).
function MM9.removeActor(actorIndex)
    evt.SetMonsterBit(actorIndex, ActorAttribute.Invisible, 1)
    evt.SetMapVar(removedVar(actorIndex), 1)
end

-- Whether a map actor is still an MM9 object that runs its script's handlers: not dead or dying, not removed. A
-- hidden actor is alive (MM9 hides spawners and buried monsters). For hand-ported OnXxx callbacks of an actor (a dead
-- AI fires only OnDeath and OnDeathDone); its pending Wait timers still fire.
function MM9.actorAlive(actorIndex)
    return actorIndex ~= nil and evt.GetMapVar(removedVar(actorIndex), 0) == 0 and not evt.IsMapActorDead(actorIndex)
end

-- MM9's object lifecycle for script messages (Trigger <object>, <message>; a DAT object's TargetName/MessageName, its
-- death and damage triggers), devdocs/mm9_rework/scr_audit/README.md "Implicit engine semantics": a dead or dying AI
-- drops every message (object.lto 0x10019e90; only RESURRECT reaches one waiting for resurrection, which the rework
-- does not have), and so does a removed object; a destroyed destructible keeps its script and takes every message.
-- `actorIndex` is the receiver's map actor (nil for a receiver that is no actor: the message is delivered). A dropped
-- message is traced for review, not an error. Every converter's message dispatcher asks this before a handler runs.
function MM9.receives(map, target, message, actorIndex)
    if actorIndex == nil or MM9.actorAlive(actorIndex) then
        return true
    end
    evt.Debug("[MM9RuntimeTrace] kind=dropped_message map=" .. tostring(map) .. " target=" .. tostring(target)
        .. " message=" .. tostring(message) .. " actor=" .. tostring(actorIndex)
        .. " reason=" .. (evt.GetMapVar(removedVar(actorIndex), 0) ~= 0 and "removed" or "dead"))
    return false
end

-- MM9's SetPropNumber CanDamage, TRUE/FALSE on a map actor: while off no hit hurts it (saved with the map).
function MM9.setCanDamage(actorIndex, canDamage)
    return evt.SetMm9ActorCanReceiveDamage(actorIndex, canDamage)
end

function MM9.setActorPosition(actorIndex, sourceX, sourceY, sourceZ)
    local scale = 2.56
    evt.SetMapActorPosition(actorIndex, sourceX * scale, sourceZ * scale, sourceY * scale)
end

-- MM9's DoClientFX <actor>, <effect> (devdocs/mm9_rework/scr_audit/client_fx.md): the MM9 effect (an mm9:* world
-- effect) where the map actor stands, `up` units above its feet (the dots' hands at the chest). A spawned creature
-- takes its effect through evt.SummonMonstersById's `effect`.
function MM9.clientFx(actorIndex, effect, scale, up)
    local x, y, z = evt.GetMapActorPosition(actorIndex)
    if x ~= nil then evt.SpawnWorldEffect(effect, x, y, z + (up or 0), scale or 1) end
end

-- An MM9 effect carried on a map actor: on a socket of its 3D model (an actors.yml animation.sockets name such as
-- palm_left, or a node of the model such as LHand1; nil for the middle of its body; "palm_left,palm_right" for one on
-- each, the hands sharing a dots effect's two emitters as MM9 puts them on LHand1 and RHand1), following it while it
-- plays, for `seconds` (nil or 0: until the effect ends by itself or the actor is gone). MM9.stopActorFx ends the
-- actor's carried effects (or those of one effect).
function MM9.actorFx(actorIndex, effect, socket, seconds, scale)
    evt.SpawnActorEffect(actorIndex, effect, socket or "", seconds or 0, scale or 1)
end

function MM9.stopActorFx(actorIndex, effect)
    evt.StopActorEffect(actorIndex, effect)
end

function MM9.clearCondition(rawCondition)
    if rawCondition ~= 13 then
        evt.StatusText("MM9 condition is unavailable: " .. tostring(rawCondition))
        return false
    end

    SubtractValue(VarTag.PoisonedGreen, 0)
    SubtractValue(VarTag.PoisonedYellow, 0)
    SubtractValue(VarTag.PoisonedRed, 0)
    SubtractValue(VarTag.DiseasedGreen, 0)
    SubtractValue(VarTag.DiseasedYellow, 0)
    SubtractValue(VarTag.DiseasedRed, 0)
    return true
end

-- Completing an MM9 promotion quest promotes every eligible member at once (MMerge's way); MM9's per-character keys
-- 401-448 are not used. Returns how many were promoted.
function MM9.promoteParty(rawPromotion)
    local promoted = 0
    for _, playerIndex in ipairs(PartyMembers()) do
        local target = MM9.promotionTarget(rawPromotion, playerIndex)
        if target ~= nil and SetPlayerClass(playerIndex, target) then
            promoted = promoted + 1
        end
    end
    if MM9.Promotions[string.lower(tostring(rawPromotion))] == nil then
        evt.StatusText("MM9 promotion is unavailable: " .. tostring(rawPromotion))
    end
    return promoted
end

-- Every promotion quest is offered to any party and pays its rewards whoever it promotes (the user, 2026-11-08). Once
-- it is done, its promoter's first page keeps "Promote our eligible characters." (dialogue/promotions.yml), which runs
-- this event (the engine's Mm9PromotionServiceEventId) with the promotion in the hook context: the members eligible
-- now are promoted, with no experience or gold; the engine lists them in the dialogue.
RegisterEvent(49990, "MM9 promotion service", function()
    if MM9.promoteParty(evt.GetHookContext().promotion) > 0 then MM9.playSound("sounds/events/quest.wav") end
end)

-- Fridleif's first Gladiatorial Labor (Sturmford City, RUDE 61) needs a Basilisk Skin (raw item 380, or a King
-- Basilisk's 591), and MM9's basilisks carry none here. Until Fridleif has seen one (keys 215, 218), a basilisk killed
-- while nobody carries a skin has one in its corpse (the user, 2026-11-08). On every MM9 map: this file comes before
-- each map's script.
local BASILISK_SKINS = {[9150] = 380, [9151] = 380, [9152] = 591}   -- Basilisk, Fibrase Basilisk, King Basilisk
RegisterMonsterKilledHook(49991, "MM9 basilisk skin", function()
    local context = evt.GetHookContext()
    local skin = BASILISK_SKINS[context.monsterId]
    if skin == nil or MM9.hasKey(215) == 1 or MM9.hasKey(218) == 1 then return end
    if MM9.hasItem(380, "basilisk skin") == 1 or MM9.hasItem(591, "basilisk skin") == 1 then return end
    local item = MM9.ItemIds[skin]
    if item ~= nil then evt.SetMonsterItem(context.actorIndex, item) end
end)

-- The older generated scripts' per-character promotion (GivePromo <promotion> CharN): that member, when eligible.
function MM9.givePromotion(rawPromotion, rawCharacter)
    local characterNumber = string.match(string.lower(tostring(rawCharacter)), "^char(%d+)$")
    local playerIndex = characterNumber ~= nil and tonumber(characterNumber) - 1 or nil
    local target = playerIndex ~= nil and MM9.promotionTarget(rawPromotion, playerIndex) or nil
    return target ~= nil and SetPlayerClass(playerIndex, target) or false
end

-- MM9's bonus props: the use handlers of object.lto's WellMMIX, Cauldron, Cookpot and Clover classes (Rizin,
-- devdocs/mm9_rework/MM9_BONUS_PROPS_RE.md), placed by the converter's shared rule (dungeon/objects.py bonus_lines).
-- `index` is the prop's DAT index: its uses are kept in map variables. MM9 gives the selected character what is not
-- the party's; here the current member. MM9's timed bonuses (BonusSeconds) become the MM6-MM8 temporary event bonuses,
-- which last until the party rests.
local BONUS_STATS = {[0] = {"Might"}, {"Intellect", "Personality"}, {"Endurance"}, {"Accuracy"}, {"Speed"}, {"Luck"}}
local BONUS_STAT_NAMES = {[0] = "Might", "Magic", "Endurance", "Accuracy", "Speed", "Luck"}
-- MM9's five resistances on the MM6-MM8 schools (as the monster import, generate_mm9_monster_tables.py)
local BONUS_SCHOOLS = {[0] = {"Fire", "Air", "Water", "Earth"}, {"Dark"}, {"Light"}, {"Spirit", "Mind", "Body"},
    {"Physical"}}
local BONUS_SCHOOL_NAMES = {[0] = "Elemental", "Dark", "Light", "Spirit", "Physical"}
local MINUTES_PER_DAY = 24 * 60

local function bonusVar(index, name)
    return "MM9.Bonus." .. tostring(index) .. "." .. name
end

local function bonusFailed()
    MM9.playSound("events/error.wav")
end

local function bonusDone(text)
    evt.StatusText(text)
    MM9.playSound("sounds/events/quest.wav")
end

-- A dose of a prop with DosesPerDay: the count starts again a day after the last use (MM9 compares with the last use,
-- 86 400 s, and stamps every attempt); false once the day's doses are gone.
local function takeDose(index, perDay)
    local now = math.floor(evt.CurrentGameMinutes())
    if now > evt.GetMapVar(bonusVar(index, "Last"), 0) + MINUTES_PER_DAY then
        evt.SetMapVar(bonusVar(index, "Doses"), 0)
    end
    local doses = evt.GetMapVar(bonusVar(index, "Doses"), 0) + 1
    evt.SetMapVar(bonusVar(index, "Last"), now)
    evt.SetMapVar(bonusVar(index, "Doses"), doses)
    return doses <= perDay and evt.GetMapVar(bonusVar(index, "Spent"), 0) == 0
end

-- The current member's temporary bonus of `prefix` .. "Bonus" / "ResistanceBonus": raised to `amount`, not stacked.
local function temporaryBonus(names, suffix, amount)
    evt.ForPlayer(Players.Current)
    for _, name in ipairs(names) do
        local variable = VarTag[name .. suffix]
        if not IsAtLeast(variable, amount) then SetValue(variable, amount) end
    end
end

-- WellMMIX (Stat 0 hit points, 1 spell points, 2 an attribute StatType, 3 a resistance StatType; BonusAmt,
-- BonusSeconds 0 for good; DosesPerDay). An attribute for good is the party's, once: MM9 then empties the well.
function MM9.useWell(index, stat, statType, amount, seconds, perDay)
    if not takeDose(index, perDay) then bonusFailed() return end
    if stat == 0 then
        evt.ForPlayer(Players.Current); AddValue(CurrentHealth, amount)
        bonusDone("+" .. amount .. " Hit Points!")
    elseif stat == 1 then
        evt.ForPlayer(Players.Current); AddValue(CurrentSpellPoints, amount)
        bonusDone("+" .. amount .. " Spell Points!")
    elseif stat == 2 and BONUS_STATS[statType] ~= nil then
        if seconds == 0 then
            evt.ForPlayer(Players.All)
            for _, name in ipairs(BONUS_STATS[statType]) do AddValue(VarTag["Base" .. name], amount) end
            evt.ForPlayer(Players.Current)
            evt.SetMapVar(bonusVar(index, "Spent"), 1)
            bonusDone("The party gains +" .. amount .. " " .. BONUS_STAT_NAMES[statType] .. "!")
        else
            temporaryBonus(BONUS_STATS[statType], "Bonus", amount)
            bonusDone("+" .. amount .. " " .. BONUS_STAT_NAMES[statType] .. " temporarily")
        end
    elseif stat == 3 and BONUS_SCHOOLS[statType] ~= nil then
        if seconds == 0 then
            evt.ForPlayer(Players.Current)
            for _, name in ipairs(BONUS_SCHOOLS[statType]) do AddValue(VarTag[name .. "Resistance"], amount) end
            bonusDone("+" .. amount .. " " .. BONUS_SCHOOL_NAMES[statType] .. " Resistance!")
        else
            temporaryBonus(BONUS_SCHOOLS[statType], "ResistanceBonus", amount)
            bonusDone("+" .. amount .. " " .. BONUS_SCHOOL_NAMES[statType] .. " Resistance temporarily")
        end
    end
end

-- Cauldron (Resistance, BonusAmt): once, every member gains the resistance for good.
function MM9.useCauldron(index, school, amount)
    if evt.GetMapVar(bonusVar(index, "Used"), 0) ~= 0 or BONUS_SCHOOLS[school] == nil then return end
    evt.SetMapVar(bonusVar(index, "Used"), 1)
    evt.ForPlayer(Players.All)
    for _, name in ipairs(BONUS_SCHOOLS[school]) do AddValue(VarTag[name .. "Resistance"], amount) end
    evt.ForPlayer(Players.Current)
    bonusDone("The party gains +" .. amount .. " " .. BONUS_SCHOOL_NAMES[school] .. " Resistance!")
end

-- Cookpot (PoisonChance, PoisonPower, Resistance, BonusAmt, BonusSeconds, DosesPerDay): a temporary resistance for the
-- current member, who is poisoned with the PoisonChance (MM9's condition 13 for an hour; here poisoned, weak).
function MM9.useCookpot(index, poisonChance, school, amount, perDay)
    if not takeDose(index, perDay) or BONUS_SCHOOLS[school] == nil then bonusFailed() return end
    evt.ForPlayer(Players.Current)
    if evt.RandomBetween(1, 100) < poisonChance then SetValue(VarTag.PoisonedGreen, 1) end
    temporaryBonus(BONUS_SCHOOLS[school], "ResistanceBonus", amount)
    bonusDone("+" .. amount .. " " .. BONUS_SCHOOL_NAMES[school] .. " Resistance temporarily")
end

-- Clover: once, a four-leaf clover (MM9 item 590).
function MM9.useClover(index, provenance)
    if evt.GetMapVar(bonusVar(index, "Used"), 0) ~= 0 then return end
    evt.SetMapVar(bonusVar(index, "Used"), 1)
    MM9.giveItem(590, provenance)
    bonusDone("A four-leaf clover!")
end
