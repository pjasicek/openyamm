-- MMMerge global supplement: MM6 quest follower behavior and topic overlays.

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

RegisterGlobalEvent(1358, "I lost it", function()
    MM6.RecoverLostItem()
end)

AppendGlobalEvent(1327, function()
    MM6.RemoveQuestFollowerUnless(1699, 796)
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

local EnrothClericClassId = 4
local EnrothPriestClassId = 5
local EnrothHighPriestClassId = 50

ReplaceGlobalEvent(1349, "Anthony Stone Priest promotion", function()
    if not IsQBitSet(QBit(1130)) then
        evt.SetMessage(
            "The temple I asked you to rebuild still stands in ruins.\n"
            .. "The people are deprived of their rightful religious solace, and you return to me empty-handed.\n"
            .. "Leave here and complete your mission!")
        return
    end

    evt.SetMessage(
        "Excellent work!\n"
        .. "The temple has been rebuilt and the affront to the gods eased.\n"
        .. "For this service, I am happy to promote all clerics to priests, "
        .. "and I grant honorary priest status to all non-clerics.\n"
        .. "Congratulations!")
    ClearQBit(QBit(1129))
    evt.SetNPCTopic(801, 1, 1350)
    AddValue(131307, 2)
    evt.ForPlayer(Players.All)
    AddValue(Experience, 15000)

    for _, player in ipairs(PartyMembers()) do
        if PlayerClassMatches(player, EnrothClericClassId) then
            SetPlayerClass(player, EnrothPriestClassId)
            SetQBit(QBit(1647))
        else
            SetQBit(QBit(1648))
        end
    end
end)

ReplaceGlobalEvent(1351, "Anthony Stone High Priest promotion", function()
    evt.ForPlayer(Players.All)

    if IsQBitSet(QBit(1132)) then
        evt.SetMessage(
            "You are successful!\n"
            .. "It looks like I will have to keep my promise and make more irregular, early promotions.\n"
            .. "I do so with pleasure.\n"
            .. "I hereby promote all priests to high priests, and all honorary priests to honorary high priests.")

        for _, player in ipairs(PartyMembers()) do
            if PlayerClassMatches(player, EnrothPriestClassId) then
                SetPlayerClass(player, EnrothHighPriestClassId)
                SetQBit(QBit(1649))
            else
                SetQBit(QBit(1650))
            end
        end

        AddValue(327915, 5)
        ClearQBit(QBit(1131))
        evt.ForPlayer(Players.All)
        AddValue(Experience, 30000)
        evt.SetNPCTopic(801, 1, 1352)
    elseif HasItem(2054) then
        evt.SetMessage(
            "I see that you have recovered the chalice!\n"
            .. "Good work, but you still need to ensconce it in the temple.\n"
            .. "Take it there at once and return to me for your promotion!")
    else
        evt.SetMessage("The monks still have the chalice, and our temple is still without it.\nWhy do you delay?")
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
