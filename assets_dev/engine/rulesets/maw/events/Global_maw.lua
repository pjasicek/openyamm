-- MAW's skill reset (devdocs/maw/TRAINERS_SKILLS.md §4.5): the Oracle, Judge Grey and the Seer explain it, and reset
-- the active character's skills for 1000 gold per level. Masteries come back on their own as the skills grow again.

RegisterGlobalEvent(10010, "Skill reset", function()
    local cost = evt.SkillResetCost()
    evt.SetMessage(tr("I can make the selected hero forget every skill lesson and learn anew. The weapons, schools of"
        .. " magic and racial abilities go back to 1 and return the points they cost, every other skill but Alchemy"
        .. " the same way. The masteries are not lost: each returns once the skill reaches its requirement again."
        .. "\n\nFor this hero it costs {cost} gold.", {cost = cost}))
end)

RegisterGlobalEvent(10011, "Reset skills", function()
    local _, status = evt.ResetSkills()
    evt.SetMessage(status)
end)

-- MAW's quest changes (devdocs/maw/MAPS_CONTENT.md §4.1, GLOBAL.lua).

-- Black potion quests take the reagents of every world: red, blue and yellow of MM8, MM7 and MM6.
local MawReagents = {
    red = {{200, 204}, {1002, 1006}, {1764, 1764}},
    blue = {{205, 209}, {1007, 1011}, {1763, 1763}},
    yellow = {{210, 214}, {1012, 1016}, {1762, 1762}},
}

local function mawReagentCount(color)
    local count = 0
    for _, range in ipairs(MawReagents[color]) do
        count = count + evt.CountItems(range[1], range[2])
    end
    return count
end

local function mawTakeReagents(color, count)
    for _, range in ipairs(MawReagents[color]) do
        local take = math.min(count, evt.CountItems(range[1], range[2]))
        if take > 0 then
            evt.RemoveItems(range[1], range[2], take)
            count = count - take
        end
    end
end

-- Hands the potion over when the party has red, blue and yellow reagents as asked.
local function mawBrewQuest(eventId, title, red, blue, yellow, thanks, oldQBit, newQBit, potion, experience, npc)
    ReplaceGlobalEvent(eventId, title, function()
        if mawReagentCount("red") < red or mawReagentCount("blue") < blue or mawReagentCount("yellow") < yellow then
            evt.SetMessage("You are missing all or some of the needed ingredients.\nReturn when you have them all.")
            return
        end
        evt.SetMessage(thanks)
        mawTakeReagents("red", red)
        mawTakeReagents("blue", blue)
        mawTakeReagents("yellow", yellow)
        ClearQBit(QBit(oldQBit))
        SetQBit(QBit(newQBit))
        AddValue(InventoryItem(potion), potion)
        evt.ForPlayer(Players.All)
        AddValue(Experience, experience)
        evt.SetNPCTopic(npc, 2, 0)
    end)
end


mawBrewQuest(181, "Do you have the Ingredients?", 4, 2, 1,
    "The ingredients!\n" .. "Thank you!\n" .. "Take this as a reward!",
    113, 114, 254, 1000, 68)

mawBrewQuest(203, "Do you have the Ingredients?", 2, 3, 3,
    "Excellent!\n" .. "With this I can brew another Potion of Pure Luck.\n" .. "Take this potion as your reward!",
    115, 116, 254, 5000, 74)

mawBrewQuest(212, "Do you have the Ingredients?", 2, 4, 1,
    "Excellent!\n" .. "With this I can brew another Potion of Pure Luck.\n" .. "Take this potion as your reward!",
    121, 122, 254, 5000, 78)

mawBrewQuest(234, "Do you have the Ingredients?", 1, 2, 4,
    "You have returned with the ingredients, holding up you end of the bargain.\n" .. "Here is your Potion of Pure Intellect.",
    123, 124, 253, 5000, 83)

mawBrewQuest(246, "Do you have the Ingredients?", 2, 1, 4,
    "Ah, the right ingredients always do the trick! Here is your potion.",
    132, 133, 252, 5000, 77)


-- Galvinus (Ravage Roaming): the quest runs on QBit 132, its journal entry, and ends with 133 (MM8 used 133 and then
-- 134, which belongs to Isthric's topic). A save that took it the old way has 133 and can still hand it in.
ReplaceGlobalEvent(244, "Potion of Pure Accuracy", function()
    evt.SetMessage("Accuracy can determine who lives and who dies in battle.\nIf you cannot hit your opponent you will"
        .. " surely perish!\nIf you bring me the ingredients of a Potion of Pure Accuracy, I will brew that potion for you.")
    SetQBit(QBit(132)) -- Bring Galvinus in Ravage Roaming the basic ingredients for a potion of Pure Accuracy.
    evt.SetNPCTopic(77, 0, 0)
end)
RegisterCanShowTopic(244, function()
    return not IsQBitSet(QBit(132)) and not IsQBitSet(QBit(133))
end)
RegisterCanShowTopic(246, function()
    return IsQBitSet(QBit(132)) or IsQBitSet(QBit(133))
end)


-- Rust asks for MAW's Elemental Resistance potions (item 249) where MM8 used Fire Resistance (256).
ReplaceGlobalEvent(207, "Quest", function()
    evt.SetMessage("The survivors in this region need Potions of Fire Resistance!\nWith them we can survive until a place is found for us to move to!\nTake these potions!\nUnfortunately they are all I have!\nDeliver them to the six southernmost houses that remain standing in the village of Rust!")
    SetQBit(QBit(142)) -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
    AddValue(InventoryItem(249), 249) -- Elemental Resistance
    AddValue(InventoryItem(249), 249) -- Elemental Resistance
    AddValue(InventoryItem(249), 249) -- Elemental Resistance
    evt.SetNPCTopic(84, 1, 208) -- Pole topic 1: Not enough potions?
end)

ReplaceGlobalEvent(208, "Not enough potions?", function()
    if not IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have not delivered Potions of Fire Resistance to all of the houses!\nIf the lake of fire grows in size everyone will perish!")
        return
    end
    evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
    evt.ForPlayer(Players.Member0)
    AddValue(Gold, 1500)
    evt.ForPlayer(Players.All)
    SetAutonote(499) -- Brought Potions of Fire Resistance to the southern houses of Rust.
    ClearQBit(QBit(142)) -- Deliver Fire Resistance Potions to the six southernmost houses of Rust. Return to Hobert in Rust.
    evt.SetNPCTopic(84, 1, 209) -- Pole topic 1: The village can hold its own.
end)

ReplaceGlobalEvent(571, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!\nThank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        evt.SetMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(249) then -- Elemental Resistance
            evt.SetMessage("I an defenseless against the onslaught of the sea of fire!\nI need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(249) -- Elemental Resistance
        SetQBit(QBit(143)) -- Delivered potion to house 1
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
        if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
            if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 7500)
                        evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SetMessage("Thanks for the potion, but others in the area are without protection!\nBe sure to deliver a potion to them as well!")
end)

ReplaceGlobalEvent(572, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!\nThank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(144)) then -- Delivered potion to house 2
        evt.SetMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(249) then -- Elemental Resistance
            evt.SetMessage("I an defenseless against the onslaught of the sea of fire!\nI need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(249) -- Elemental Resistance
        SetQBit(QBit(144)) -- Delivered potion to house 2
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
            if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SetMessage("Thanks for the potion, but others in the area are without protection!\nBe sure to deliver a potion to them as well!")
end)

ReplaceGlobalEvent(573, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!\nThank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(145)) then -- Delivered potion to house 3
        evt.SetMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(249) then -- Elemental Resistance
            evt.SetMessage("I an defenseless against the onslaught of the sea of fire!\nI need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(249) -- Elemental Resistance
        SetQBit(QBit(145)) -- Delivered potion to house 3
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SetMessage("Thanks for the potion, but others in the area are without protection!\nBe sure to deliver a potion to them as well!")
end)

ReplaceGlobalEvent(574, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!\nThank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(146)) then -- Delivered potion to house 4
        evt.SetMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(249) then -- Elemental Resistance
            evt.SetMessage("I an defenseless against the onslaught of the sea of fire!\nI need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(249) -- Elemental Resistance
        SetQBit(QBit(146)) -- Delivered potion to house 4
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
                if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SetMessage("Thanks for the potion, but others in the area are without protection!\nBe sure to deliver a potion to them as well!")
end)

ReplaceGlobalEvent(575, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!\nThank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(147)) then -- Delivered potion to house 5
        evt.SetMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(249) then -- Elemental Resistance
            evt.SetMessage("I an defenseless against the onslaught of the sea of fire!\nI need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(249) -- Elemental Resistance
        SetQBit(QBit(147)) -- Delivered potion to house 5
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
                if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                    if IsQBitSet(QBit(148)) then -- Delivered potion to house 6
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SetMessage("Thanks for the potion, but others in the area are without protection!\nBe sure to deliver a potion to them as well!")
end)

ReplaceGlobalEvent(576, "Fire Resistance Potion", function()
    if IsQBitSet(QBit(149)) then -- Southern houses of Rust all have Potions of Fire Resistance.
        evt.SetMessage("You have at least pushed our demise away for a time, but a new home needs to be found for us!\nThank you for delivering the Potions of Fire Resistance!")
        return
    elseif IsQBitSet(QBit(148)) then -- Delivered potion to house 6
        evt.SetMessage("Thanks for the potion!")
    else
        evt.ForPlayer(Players.All)
        if not HasItem(249) then -- Elemental Resistance
            evt.SetMessage("I an defenseless against the onslaught of the sea of fire!\nI need a Potion of Fire Resistance!")
            return
        end
        RemoveItem(249) -- Elemental Resistance
        SetQBit(QBit(148)) -- Delivered potion to house 6
        evt.ForPlayer(Players.All)
        AddValue(Experience, 1000)
    end
    if IsQBitSet(QBit(143)) then -- Delivered potion to house 1
        if IsQBitSet(QBit(144)) then -- Delivered potion to house 2
            if IsQBitSet(QBit(145)) then -- Delivered potion to house 3
                if IsQBitSet(QBit(146)) then -- Delivered potion to house 4
                    if IsQBitSet(QBit(147)) then -- Delivered potion to house 5
                        evt.ForPlayer(Players.All)
                        AddValue(Experience, 1500)
                        evt.SetMessage("Thanks for providing Potions of Fire Resistance to the southernmost houses here in Rust.\nPerhaps we can survive until a new home can be found for us!")
                        SetQBit(QBit(149)) -- Southern houses of Rust all have Potions of Fire Resistance.
                        return
                    end
                end
            end
        end
    end
    evt.SetMessage("Thanks for the potion, but others in the area are without protection!\nBe sure to deliver a potion to them as well!")
end)

-- The circus traders give at most ten trades of each kind per circus visit: "We have no more items to trade".
local function mawCircusTrade(eventId, item, strength, kind, done, missing, counter)
    ReplaceGlobalEvent(eventId, nil, function()
        if evt.GetMapVar(counter, 0) >= 10 then
            evt.SetMessage("We have no more items to trade, come back another time.")
            return
        end
        for _, player in ipairs(PartyMembers()) do
            evt.ForPlayer(player)
            if HasItem(item) then
                RemoveItem(item)
                evt.GiveItem(strength, kind)
                evt.SetMapVar(counter, evt.GetMapVar(counter, 0) + 1)
                evt.SetMessage(done)
                return
            end
        end
        evt.SetMessage(missing)
    end)
end

local NoPyramid = "I'm afraid you don't have a golden pyramid, so I can't make a deal with you."
local NoKeg = "You don't have a keg of wine to trade!"
mawCircusTrade(1442, 2092, 6, ItemType.Armor_, "Great to do business with you, here's your armor!", NoPyramid,
    "MawCircusPyramid")
mawCircusTrade(1443, 2092, 6, ItemType.Weapon_, "Great to do business with you, here's your weapon!", NoPyramid,
    "MawCircusPyramid")
mawCircusTrade(1444, 2092, 6, ItemType.Misc, "Great to do business with you, here's your accessory!", NoPyramid,
    "MawCircusPyramid")
mawCircusTrade(1445, 2093, 4, ItemType.Armor_, "Great to do business with you, here's your armor!", NoKeg,
    "MawCircusKeg")
mawCircusTrade(1446, 2093, 4, ItemType.Weapon_, "Great to do business with you, here's your weapon!", NoKeg,
    "MawCircusKeg")
mawCircusTrade(1447, 2093, 4, ItemType.Misc, "Great to do business with you, here's your accessory!", NoKeg,
    "MawCircusKeg")

-- The Druid Circlet (zzMAW_DruidCircletQuest.lua): Dantillion in Murmurwoods asks for the circlet in the Druid Circle
-- (item 638) and pays 3000 gold, 10000 experience and an amulet. Journal QBit 10001.
RegisterGlobalEvent(10020, "Druid Circlet", function()
    if evt.GetGlobalVar("MawDruidCircletDone", 0) ~= 0 then
        evt.SetMessage("The circlet is in safe hands. The Temple of the Sun will not forget your help.")
        return
    end
    if not IsQBitSet(QBit(10001)) then
        evt.SetMessage("The pilgrims bound for the Druid Circle were seeking more than old stones. It is said the druids"
            .. " of the Ancients left a relic there, the Druid Circlet of Power. The Temple of the Sun wishes to keep it"
            .. " safe before it falls into the wrong hands. The Circle lies to the northeast of here. If you find the"
            .. " circlet, bring it to me, and the Temple will reward you.")
        SetQBit(QBit(10001))
        return
    end
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if HasItem(638) then -- Druid Circlet of Power
            RemoveItem(638)
            ClearQBit(QBit(10001))
            evt.SetGlobalVar("MawDruidCircletDone", 1)
            evt.SetMessage("The Druid Circlet of Power! How many pilgrims gave their lives just to set eyes on it... The"
                .. " Temple of the Sun will keep it safe. Accept the Temple's gratitude, and this amulet.")
            AddValue(Gold, 3000)
            evt.ForPlayer(Players.All)
            AddValue(Experience, 10000)
            -- MAW identifies the Temple's amulet (zzMAW_DruidCircletQuest.lua:7-11).
            evt.GiveItem(5, ItemType.Amulet, {identified = true})
            return
        end
    end
    evt.SetMessage("You do not have the circlet. The Druid Circle lies to the northeast of here; look for it there.")
end)

-- The Dragon Hatchling (Quest_DragonHatchling.lua): feeding says how much the hatchling has eaten and how many days it
-- still needs, and the party can release the dragon for good. A dismissed dragon joins again, except in Beyond Madness
-- (Quest_DragonHatchling.lua:74).
ReplaceGlobalEvent(789, "MMMerge Dragon Hatchling", function()
    -- A released dragon is gone for good (Quest_DragonHatchling.lua:28-30).
    if MM7.GetCrossVar("DragonReleased", 0) ~= 0 then
        evt.SimpleMessage("The dragon has flown away for good.")
        return
    end
    if MM7.GetCrossVar("DragonJoined", 0) ~= 0 then
        if HasFollowerNpc(396) then
            evt.SimpleMessage("The dragon is already traveling with you.")
        elseif evt.RulesetInfo().challengeMode == "beyond_madness" then
            evt.SimpleMessage("The dragon will not travel with you again.")
        else
            AddFollowerNpc(396)
            evt.SimpleMessage("The dragon joins your company again.")
        end
        return
    end
    if MM7.GetCrossVar("DragonGrown", 0) ~= 0 then
        AddFollowerNpc(396)
        MM7.SetCrossVar("DragonJoined", 1)
        evt.SetNPCName(396, "Dragon")
        evt.SimpleMessage("The grown dragon joins your company.")
        return
    end
    local foodEaten = MM7.GetCrossVar("DragonFood", 0)
    if foodEaten >= 100 then
        local grownAt = MM7.GetCrossVar("DragonFirstFeedMinutes", CurrentGameMinutes()) + 28 * 24 * 60
        if CurrentGameMinutes() >= grownAt then
            MM7.SetCrossVar("DragonGrown", 1)
            evt.SimpleMessage("The hatchling has grown enough to travel with you.")
        else
            evt.SimpleMessage("The hatchling has eaten enough and only needs time to grow.\nDays left: "
                .. math.max(1, math.ceil((grownAt - CurrentGameMinutes()) / (24 * 60))) .. ".")
        end
        return
    end
    if not IsAtLeast(Food, 5) then
        evt.SimpleMessage("Grrr! The dragon needs 5 food, the party has less.")
        return
    end
    SubtractValue(Food, 5)
    if MM7.GetCrossVar("DragonFirstFeedMinutes", 0) == 0 then
        MM7.SetCrossVar("DragonFirstFeedMinutes", CurrentGameMinutes())
    end
    MM7.SetCrossVar("DragonFood", foodEaten + 5)
    evt.SimpleMessage(tr("Yum! The dragon ate 5 food. Eaten so far: {eaten} of 100.", {eaten = foodEaten + 5}))
end)

-- Releasing is offered only while he travels with the party (Quest_DragonHatchling.lua:191-210).
RegisterGlobalNpcEnterHook(65400, "MAW Dragon Hatchling release", function(context)
    if context ~= nil and context.npcId == 396 then
        evt.SetNPCTopic(396, 1, HasFollowerNpc(396) and 10021 or 0)
    end
end)

RegisterGlobalEvent(10021, "Release the dragon", function()
    evt.SetMessage("The dragon will fly away for good. Release him?")
    evt.SetNPCTopic(396, 1, 10022)
end)

RegisterGlobalEvent(10022, "Yes, release him", function()
    -- A hatchling flies away too.
    if HasFollowerNpc(396) then
        RemoveFollowerNpc(396)
    end
    MM7.SetCrossVar("DragonReleased", 1)
    evt.MoveNPC(396, 0)
    evt.SetMessage("The dragon spread his wings and flew away.")
end)

-- The Endless Arena (zzMaw_Arena.lua): the Arena Master starts the level after the best one cleared; its waves come in
-- the Arena (engine/rulesets/maw/events/maps/d42_maw.lua). Global vars: MawArenaBest, the best level cleared, and
-- MawArenaLevel, the level being fought (0 for none).
RegisterGlobalEvent(10030, "Endless Arena", function()
    evt.SetMessage(tr("It looks like you've never tried the Endless Waves mode before. In this mode, waves of enemies"
        .. " will keep appearing, growing stronger over time. Every time you clear a level, your progress is saved, and"
        .. " you can start from the latest checkpoint. Prepare yourself for a relentless challenge!\n\nNext: level"
        .. " {level}.", {level = evt.GetGlobalVar("MawArenaBest", 0) + 1}))
    evt.SetNPCTopic(313, 1, 10031)
end)

RegisterGlobalEvent(10031, "Start the next level", function()
    local level = evt.GetGlobalVar("MawArenaBest", 0) + 1
    evt.SetGlobalVar("MawArenaLevel", level)
    evt.SetGlobalVar("MawArenaWave", level * 3 - 2)
    evt.SetGlobalVar("MawArenaWavesLeft", 3)
    evt.SetGlobalVar("MawArenaStep", 1)
    evt.SetGlobalVar("MawArenaWait", 0)
    evt.SetGlobalVar("MawArenaProgress", 0)
    evt.SetNPCTopic(313, 1, 0)
    evt.SetMessage(tr("Let's get started! Level {level}.", {level = level}))
    evt.MoveToMap(3850, 5776, 1, 512, 0, 0, 0, 0, "d42.blv")
end)

-- Dimensional Maps (Global/zzMaw_DimensionalMapsQuest.lua): the Oracle, Judge Grey and the Seer give a dimension map
-- for each tier of party level and reward it once cleared; from the level 500 tier on, monsters drop maps. The rules
-- keep the quest (evt.RulesTopic).
RegisterGlobalEvent(10040, "Dimensional Maps", function()
    evt.SetMessage(evt.RulesTopic("dimensional_maps") or "")
end)

-- Doom and the modes after it: the circus traders of the keg and pyramid trades are gone (GLOBAL.lua:799-803).
RegisterGlobalOnLoadEvent(65401, "MAW Doom circus traders", function()
    local mode = evt.RulesetInfo().challengeMode
    if mode == "doom" or mode == "road_to_insanity" or mode == "beyond_madness" then
        evt.MoveNPC(1109, 0)
        evt.MoveNPC(1165, 0)
        evt.MoveNPC(1166, 0)
    end
end)

-- Road to Insanity and Beyond Madness: a trader sells his trade good once; buying it takes the topic away
-- (GLOBAL.lua:38-50, which clears the selling NPC's first topic). Each trade good is its seller's first topic.
local TradeGoods = {
    {event = 250, npc = 97, item = 643, title = "Buy Tobersk Fruit for 200 gold"},
    {event = 252, npc = 98, item = 644, title = "Buy Tobersk Pulp for 300 gold"},
    {event = 254, npc = 99, item = 645, title = "Buy Tobersk Brandy 500 gold"},
    {event = 256, npc = 100, item = 646, title = "Buy Heartwood of Jadame for 1000 gold"},
    {event = 258, npc = 101, item = 647, title = "Buy Pirate Amulets for 1500 gold"},
    {event = 260, npc = 103, item = 648, title = "Buy Dried Sunfish for 2000 gold"},
    {event = 262, npc = 104, item = 649, title = "Buy Silver Dust of the Sea for 5000 gold"},
    {event = 264, npc = 105, item = 650, title = "Buy Forged Credit Vouchers for 6500 gold"},
    {event = 266, npc = 106, item = 651, title = "Buy Ground Wyvern Horn for 7500 gold"},
    {event = 515, npc = 719, item = 1494},
    {event = 1258, npc = 722, item = 1495},
    -- MAW lists 1946 here, a typo for the Tularean Wood (DEVIATIONS, audit CNT-10).
    {event = 1260, npc = 723, item = 1496},
    {event = 1262, npc = 761, item = 1497},
    {event = 1264, npc = 762, item = 1498},
    {event = 1266, npc = 724, item = 1499},
}

for _, trade in ipairs(TradeGoods) do
    local buy = evt.global[trade.event]
    if buy ~= nil then
        ReplaceGlobalEvent(trade.event, trade.title, function(...)
            local before = evt.CountItems(trade.item, trade.item)
            buy(...)
            local mode = evt.RulesetInfo().challengeMode
            if (mode == "road_to_insanity" or mode == "beyond_madness")
                and evt.CountItems(trade.item, trade.item) > before then
                evt.SetNPCTopic(trade.npc, 0, 0)
            end
        end)
    end
end
