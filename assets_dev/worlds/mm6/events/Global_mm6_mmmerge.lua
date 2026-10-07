-- MMMerge global supplement: MM6 quest follower behavior and topic overlays.

local function searchFlourSack()
    local food = math.random(0, 2)

    if food > 0 then
        AddValue(Food, food)
        evt.StatusText("You found " .. food .. " food!")
    else
        evt.StatusText("Empty sack")
    end

    evt.ChangeEvent(0)
end

ReplaceGlobalEvent(1741, "Flour Sack", searchFlourSack, "Flour Sack")
ReplaceGlobalEvent(1742, "Flour Sack", searchFlourSack, "Flour Sack")

local enrothGrandmasterTeacherTopics = {
    {npc = 1043, slot = 3, topic = 302}, -- GM Staff
    {npc = 837, slot = 3, topic = 305}, -- GM Sword
    {npc = 995, slot = 3, topic = 308}, -- GM Dagger
    {npc = 817, slot = 3, topic = 311, qbit = 1051}, -- GM Axe
    {npc = 991, slot = 3, topic = 314}, -- GM Spear
    {npc = 973, slot = 3, topic = 317}, -- GM Bow
    {npc = 874, slot = 3, topic = 320}, -- GM Mace
    {npc = 830, slot = 3, topic = 329}, -- GM Leather
    {npc = 811, slot = 3, topic = 332}, -- GM Chain
    {npc = 808, slot = 3, topic = 335}, -- GM Plate
    {npc = 890, slot = 4, topic = 338}, -- GM Fire
    {npc = 965, slot = 4, topic = 341}, -- GM Air
    {npc = 829, slot = 4, topic = 344}, -- GM Water
    {npc = 894, slot = 3, topic = 347}, -- GM Earth
    {npc = 923, slot = 4, topic = 350}, -- GM Spirit
    {npc = 858, slot = 3, topic = 353}, -- GM Mind
    {npc = 840, slot = 4, topic = 356}, -- GM Body
    {npc = 1057, slot = 3, topic = 359}, -- GM Light
    {npc = 1040, slot = 3, topic = 362}, -- GM Dark
    {npc = 814, slot = 3, topic = 377}, -- GM Merchant
    {npc = 996, slot = 3, topic = 380}, -- GM Repair
    {npc = 972, slot = 3, topic = 383}, -- GM Bodybuilding
    {npc = 1014, slot = 3, topic = 386}, -- GM Meditation
    {npc = 842, slot = 3, topic = 389}, -- GM Perception
    {npc = 875, slot = 3, topic = 395}, -- GM Disarm Trap
    {npc = 1114, slot = 3, topic = 405}, -- Expert Armsmaster
    {npc = 860, slot = 3, topic = 406}, -- Master Armsmaster
    {npc = 860, slot = 4, topic = 407}, -- GM Armsmaster
    {npc = 819, slot = 3, topic = 413}, -- GM Alchemy
    {npc = 809, slot = 4, topic = 416}, -- GM Learning
    {npc = 870, slot = 3, topic = 374}, -- GM Identify Item
    {npc = 915, slot = 3, topic = 973}, -- GM Blaster
    {npc = 966, slot = 4, topic = 326}, -- GM Shield
}

local function applyEnrothGrandmasterTeacherTopic(entry)
    if entry.qbit and not IsQBitSet(QBit(entry.qbit)) then
        evt.SetNPCTopic(entry.npc, entry.slot, 0)
        return
    end
    evt.SetNPCTopic(entry.npc, entry.slot, entry.topic)
end

local function applyEnrothGrandmasterTeacherTopics()
    for _, entry in ipairs(enrothGrandmasterTeacherTopics) do
        applyEnrothGrandmasterTeacherTopic(entry)
    end
end

RegisterGlobalOnLoadEvent(65300, "MMerge Enroth grandmaster teacher topics", function()
    applyEnrothGrandmasterTeacherTopics()
end)

RegisterGlobalNpcEnterHook(65301, "MMerge Enroth grandmaster teacher topics", function(context)
    for _, entry in ipairs(enrothGrandmasterTeacherTopics) do
        if context.npcId == entry.npc then
            applyEnrothGrandmasterTeacherTopic(entry)
        end
    end
end)

local SeerPilgrimageCompletedQBit = 1230
local SeerPilgrimageStateVariable = 0x7002
local SeerPilgrimageStateMonthMask = 4096
local SeerPilgrimageMinutesPerDay = 24 * 60
local SeerPilgrimageDaysPerMonth = 28
local SeerPilgrimageMonthsPerYear = 12
local SeerPilgrimageDaysPerYear = SeerPilgrimageDaysPerMonth * SeerPilgrimageMonthsPerYear

local seerPilgrimageByMonth = {
    {month = "January", stat = "Might", map = "Bootleg Bay"},
    {month = "February", stat = "Intellect", map = "Misty Islands"},
    {month = "March", stat = "Personality", map = "Silver Cove"},
    {month = "April", stat = "Endurance", map = "Frozen Highlands"},
    {month = "May", stat = "Accuracy", map = "Free Haven"},
    {month = "June", stat = "Speed", map = "Mire of the Damned"},
    {month = "July", stat = "Luck", map = "New Sorpigal"},
    {month = "August", stat = "Fire", map = "Kriegspire"},
    {month = "September", stat = "Air", map = "Castle Ironfist"},
    {month = "October", stat = "Water", map = "Kriegspire"},
    {month = "November", stat = "Earth", map = "Eel Infested Waters"},
    {month = "December", stat = "Magic", map = "Blackshire"},
}

local seerPilgrimageMonthBits = {
    1,
    2,
    4,
    8,
    16,
    32,
    64,
    128,
    256,
    512,
    1024,
    2048,
}

local function currentSeerPilgrimage()
    local dayIndex = math.floor(CurrentGameMinutes() / SeerPilgrimageMinutesPerDay)
    local yearIndex = math.floor(dayIndex / SeerPilgrimageDaysPerYear)
    local yearDay = dayIndex % SeerPilgrimageDaysPerYear
    local monthIndex = math.floor(yearDay / SeerPilgrimageDaysPerMonth) + 1
    return yearIndex, monthIndex, seerPilgrimageByMonth[monthIndex]
end

local function currentSeerPilgrimageMask(yearIndex)
    local packedState = GetPartyVariable(SeerPilgrimageStateVariable)
    local storedYear = math.floor(packedState / SeerPilgrimageStateMonthMask)
    if storedYear ~= yearIndex then
        return 0
    end
    return packedState % SeerPilgrimageStateMonthMask
end

local function setCurrentSeerPilgrimageMask(yearIndex, monthMask)
    SetPartyVariable(SeerPilgrimageStateVariable, yearIndex * SeerPilgrimageStateMonthMask + monthMask)
end

ReplaceGlobalEvent(1354, "Pilgrimage", function()
    local yearIndex, monthIndex, pilgrimage = currentSeerPilgrimage()
    local monthMask = currentSeerPilgrimageMask(yearIndex)
    local monthBit = seerPilgrimageMonthBits[monthIndex]

    if IsQBitSet(QBit(SeerPilgrimageCompletedQBit)) then
        if math.floor(monthMask / monthBit) % 2 == 1 then
            evt.SetMessage("You must wait until the new month to undergo a pilgrimage.")
            return
        end

        ClearQBit(QBit(SeerPilgrimageCompletedQBit))
        setCurrentSeerPilgrimageMask(yearIndex, monthMask + monthBit)
        AddValue(Experience, 0)
    end

    evt.SetMessage(string.format(
        "This is %s, the month of %s.\nJourney to the Shrine of %s and pray there to be rewarded.",
        pilgrimage.month,
        pilgrimage.stat,
        pilgrimage.map))
end)

RegisterGlobalEvent(1358, "I lost it", function()
    MM6.RecoverLostItem()
end)

local function showSeerHint(textId, autonoteId)
    evt.SetMessage(Game.NPCText[textId])
    if autonoteId then
        SetAutonote(autonoteId)
    end
end

ReplaceGlobalEvent(1359, "Hint", function()
    evt.ForPlayer(Players.All)

    if IsQBitSet(QBit(1105)) then
        showSeerHint(2127, 479)
        return
    end

    if IsQBitSet(QBit(1106)) then
        showSeerHint(2119, 478)
        return
    end

    if not IsAtLeast(BaseLevel, 25) then
        showSeerHint(2120, 477)
        return
    end

    if not HasAward(Award(57)) or not HasAward(Award(58)) or not HasAward(Award(59)) or
        not HasAward(Award(60)) or not HasAward(Award(61)) or not HasAward(Award(62)) then
        showSeerHint(2122, 476)
        return
    end

    if not IsQBitSet(QBit(1192)) then
        showSeerHint(2124, 475)
        return
    end

    if not HasAward(Award(75)) then
        showSeerHint(2125, 474)
        return
    end

    if HasAward(Award(78)) then
        showSeerHint(2131)
        return
    end

    if HasItem(2164) then
        showSeerHint(2130, 471)
        return
    end

    if HasItem(1666) or HasItem(1667) then
        showSeerHint(2129, 472)
        return
    end

    showSeerHint(2126, 473)
end)

AppendGlobalEvent(1344, function()
    MM6.AddQuestFollower(796)
end)

AppendGlobalEvent(1346, function()
    MM6.RemoveQuestFollowerUnless(1701, 802)
end)

AppendGlobalEvent(1347, function()
    MM6.RemoveQuestFollower(802)
end)

-- Completed Enroth quests remain available to later recruits. Promotion eligibility is exact.
local promotionFamilies = {
    {npc = 789, secondStart = 1328,
        first = {event = 1327, title = "Crusaders", from = 26, to = 27, bits = {1635, 1636},
            xp = 15000, quest = 1112, conditionBit = 1699, consumeBit = 1699, gold = 5000,
            message = 1713, refusal = 1712},
        second = {event = 1329, title = "Heroes", from = 27, to = 28, bits = {1637, 1638},
            xp = 30000, quest = 1113, item = 2075, consumeItem = true, consumeBit = 1209,
            message = 1716, refusal = 1715}},
    {npc = 790, secondStart = 1372,
        first = {event = 1371, title = "Wizards", from = 42, to = 43, bits = {1639, 1640},
            xp = 15000, quest = 1135, message = 1762},
        second = {event = 1373, title = "Master Wizards", from = 43, to = 51, bits = {1641, 1642},
            xp = 30000, quest = 1136, item = 2077, consumeItem = true, consumeBit = 1210,
            message = 1765, refusal = 1764}},
    {npc = 791, secondStart = 1383,
        first = {event = 1382, title = "Cavaliers", from = 16, to = 17, bits = {1643, 1644},
            xp = 15000, quest = 1138, message = 1776},
        second = {event = 1384, title = "Champions", from = 17, to = 19, bits = {1645, 1646},
            xp = 40000, quest = 1139, item = 2128, consumeItem = true, consumeBit = 1211,
            message = 1779, refusal = 1778}},
    {npc = 801, secondStart = 1350,
        first = {event = 1349, title = "Priests", from = 4, to = 5, bits = {1647, 1648},
            xp = 15000, quest = 1129, conditionBit = 1130, message = 1740, refusal = 1739},
        second = {event = 1351, title = "High Priests", from = 5, to = 50, bits = {1649, 1650},
            xp = 30000, quest = 1131, conditionBit = 1132, message = 1744, refusal = 1742}},
    {npc = 799, secondStart = 1397, ceremony = true,
        first = {event = 1678, title = "Great Druids", from = 12, to = 13, bits = {1651, 1652},
            xp = 15000, quest = 1142, message = 1792, ceremonyBit = 1197, ceremonyNpc = 1090},
        second = {event = 1679, title = "Arch Druids", from = 13, to = 15, bits = {1653, 1654},
            xp = 40000, quest = 1143, message = 1794, ceremonyBit = 1198, ceremonyNpc = 1091}},
    {npc = 800, secondStart = 1406,
        first = {event = 1405, title = "Warrior Mages", from = 0, to = 1, bits = {1655, 1656},
            xp = 15000, quest = 1145, item = 2106, message = 1803, refusal = 1802},
        second = {event = 1413, title = "Master Archers", from = 1, to = 2, bits = {1657, 1658},
            xp = 40000, quest = 1146, towerBits = {1180, 1181, 1182, 1183, 1184, 1185},
            message = 1807, refusal = 1805}},
}

local function promotionCompleted(stage)
    return IsQBitSet(QBit(stage.bits[1])) or IsQBitSet(QBit(stage.bits[2]))
end

local function updatePromotionTopics(family)
    if not promotionCompleted(family.first) then return end

    -- Slot 5 is unused by these six lords. Keep council quests and Anthony Stone's Ankh topic intact.
    evt.SetNPCTopic(family.npc, 5, family.first.event)
    if promotionCompleted(family.second) then
        evt.SetNPCTopic(family.npc, 1, family.second.event)
    elseif IsQBitSet(QBit(family.second.quest)) then
        evt.SetNPCTopic(family.npc, 1, family.ceremony and 1398 or family.second.event)
    else
        evt.SetNPCTopic(family.npc, 1, family.secondStart)
    end
end

local function meetsPromotionConditions(stage)
    evt.ForPlayer(Players.All)
    if stage.conditionBit ~= nil and not IsQBitSet(QBit(stage.conditionBit)) then return false end
    if stage.item ~= nil and not HasItem(stage.item) then return false end
    for _, bit in ipairs(stage.towerBits or {}) do
        if not IsQBitSet(QBit(bit)) then return false end
    end
    return true
end

for _, family in ipairs(promotionFamilies) do
    for stageIndex, stage in ipairs({family.first, family.second}) do
        ReplaceGlobalEvent(stage.event, stage.title, function()
            local firstTime = not promotionCompleted(stage)
            if firstTime and not meetsPromotionConditions(stage) then
                local message = stage.refusal
                if stage.event == 1351 and HasItem(2054) then message = 1743 end
                evt.SetMessage(Game.NPCText[message])
                return
            end

            if firstTime then
                evt.SetMessage(Game.NPCText[stage.message])
            else
                evt.SetMessage("Your party has already completed this quest. Eligible companions are promoted to "
                    .. GetClassName(stage.to) .. ".")
            end

            for _, player in ipairs(PartyMembers()) do
                evt.ForPlayer(player)
                if PlayerClassMatches(player, stage.from) then
                    SetValue(ClassId, stage.to)
                    AddValue(Experience, stage.xp)
                    SetQBit(QBit(stage.bits[1]))
                elseif firstTime then
                    AddValue(Experience, stage.xp)
                    SetQBit(QBit(stage.bits[2]))
                end
            end

            evt.ForPlayer(Players.All)
            if firstTime then
                ClearQBit(QBit(stage.quest))
                if stage.consumeItem then RemoveItem(stage.item) end
                if stage.consumeBit ~= nil then ClearQBit(QBit(stage.consumeBit)) end
                if stage.gold ~= nil then AddValue(Gold, stage.gold) end
                -- Retain the authored first-completion reputation effects.
                if stageIndex == 1 then AddValue(131307, 2) else AddValue(327915, 5) end
                if stage.ceremonyBit ~= nil then
                    SetQBit(QBit(stage.ceremonyBit))
                    evt.SetNPCTopic(stage.ceremonyNpc, 0, 0)
                end
                if stage.event == 1382 then evt.SetNPCTopic(792, 0, 1380) end
            end
            updatePromotionTopics(family)
        end)
    end
end

-- Attach follower departure after the promotion overrides replace their quest handlers.
AppendGlobalEvent(1327, function()
    MM6.RemoveQuestFollowerUnless(1699, 796)
end)

RegisterGlobalNpcEnterHook(65302, "Enroth completed promotion topics", function(context)
    for _, family in ipairs(promotionFamilies) do
        if context.npcId == family.npc then
            updatePromotionTopics(family)
            return
        end
    end
end)

ReplaceGlobalEvent(1352, "Anthony Stone High Priest done", function()
    evt.SetMessage(
        "Though your rise to high priest status was almost unseemly quick, "
        .. "I have never seen finer high priests in all my years.\n"
        .. "I am grateful for all you've done for myself and for Enroth.")
end)

ReplaceGlobalEvent(1426, nil, function()
    MM6.SellCollectorItem(
        2082,
        461,
        2000,
        0,
        "This one's a little dirty, but I suppose it will do.\nHere is the gold I promised you for it.\nThanks for your help!",
        "As part of the effort to rebuild the Temple here in Free Haven, I'm collecting temple gongs.\nIf you have any gongs, I'll pay you 2000 gold for each of them.")
end)

ReplaceGlobalEvent(1427, nil, function()
    MM6.SellCollectorItem(
        2085,
        462,
        1000,
        5,
        "Hmm...",
        "I'm looking for bones to use in my rituals.\nI prefer bones from humans or humanoids, but I suppose I can make do with whatever you find.\nI'm willing to pay up to 1000 gold for bones that I can use.")
end)

ReplaceGlobalEvent(1428, nil, function()
    MM6.SellCollectorItem(
        2090,
        463,
        5,
        0,
        "Thank you!",
        "Many people aren't able to visit the circus, so I'm collecting circus prizes to give away to those not able to visit it themselves.\nI'll buy lodestones for 5 gold each if you want to part with them.")
end)

ReplaceGlobalEvent(1429, nil, function()
    MM6.SellCollectorItem(
        2091,
        464,
        10,
        0,
        "Thanks!\nDon't tell my daughter about this, I want to surprise her.\nHere's the 10 gold.",
        "My daughter wants to go to the circus, but we never have the time when the circus is near here.\nI'd love to give her a bunch of the pretty harpy feathers for her.\nI'll take any harpy feathers you have for 10 gold each.")
end)

ReplaceGlobalEvent(1430, nil, function()
    MM6.SellCollectorItem(
        2092,
        465,
        1000,
        0,
        "Thanks!\nI can't wait to take this to Abdul's Desert Resort and see what I get!\nOh, here's the money I owe you.",
        "I've heard that you can get really nifty things from Abdul's Desert Resort if you pay with golden pyramids.\nI'm hoping to go there one day, and I want to stock up on the pyramids now.\nI'll take any golden pyramids you have for 1000 gold.")
end)

ReplaceGlobalEvent(1431, nil, function()
    MM6.SellCollectorItem(
        2093,
        466,
        300,
        0,
        "My favorite!\nThanks for the wine!\nHere's 300 gold, it's well worth the price.",
        "My favorite wine is the stuff they give you for winning at the circus.")
end)

ReplaceGlobalEvent(1432, nil, function()
    MM6.SellCollectorItem(
        2096,
        467,
        500,
        0,
        "I don't believe I have a tooth like this one yet, here's 500 gold.",
        "I have an incredible teeth collection, but I'm always looking for more.\nIf you find a tooth I don't have in my collection, I'll pay you 500 gold for it.")
end)

ReplaceGlobalEvent(1433, nil, function()
    MM6.SellCollectorItem(
        2097,
        468,
        25,
        0,
        "Hurray!",
        "I have been to the circus three times, and I can't win anything.\nAll I really want are the nifty four leaf clovers they use as prizes there.\nI'll pay 25 gold for any four leaf clover you bring me.")
end)

ReplaceGlobalEvent(1434, nil, function()
    MM6.SellCollectorItem(
        2102,
        469,
        500,
        0,
        "This will do nicely!\nThank you for the amber, here is the 500 gold I promised you.",
        "I've heard it's possible to find large chunks of amber in a series of caves north of Castle Ironfist.\nI never have the time to leave Free Haven, but I'd love to get my hands on some of that amber.\nI'll pay 500 gold for any piece of amber.")
end)

ReplaceGlobalEvent(1625, nil, function()
    MM6.SellCollectorItem(
        2094,
        0,
        300,
        0,
        "Excellent specimen!",
        "I am a collector of rare and exotic creatures, and I make a living by selling some of these creatures as pets.\nCurrently, cobras are in great demand, and I don't have many cobras left to sell.\nTherefore, I'm willing to pay handsomely for any cobra eggs you might have.\nRemember, if you find any cobra eggs, I'll give you the best prices.")
end)

AppendGlobalEvent(1631, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.RemoveQuestFollowerUnless(1702, 893)
end)

AppendGlobalEvent(1634, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.AddQuestFollower(893)
end)

AppendGlobalEvent(1638, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.RemoveQuestFollower(978)
end)

AppendGlobalEvent(1640, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.AddQuestFollower(978)
end)

AppendGlobalEvent(1642, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.RemoveQuestFollower(980)
end)

AppendGlobalEvent(1645, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.RemoveQuestFollowerUnless(1705, 940)
end)

AppendGlobalEvent(1646, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.AddQuestFollower(940)
end)

AppendGlobalEvent(1331, function()
    MM6.StartNicolaiQuest()
end)

ReplaceGlobalEvent(1333, nil, function(continueStep)
    if continueStep ~= nil then
        return
    end

    MM6.KidnapNicolai(true)
end)

AppendGlobalEvent(1334, function()
    MM6.RecoverNicolaiAtCircus()
end)
