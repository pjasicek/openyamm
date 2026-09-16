-- Exact promotion eligibility for Jadame, including later recruits in mixed-world parties.
-- Quest gates and honorary awards retain the original MM8 first-character convention.

local promotions = {
    elf = {from = {8}, to = 9, bit = 1537, award = 20},
    troll = {from = {38}, to = 39, bit = 1538, honoraryBit = 1539},
    knight = {from = {16, 17}, to = 19, bit = 1540, honoraryBit = 1541, xp = 50000, honoraryXp = 35000},
    dragon = {from = {10}, to = 11, bit = 1543, honoraryBit = 1544},
    minotaur = {from = {20}, to = 21, bit = 1545, award = 29},
    cleric = {from = {4, 5}, to = 6, bit = 1546, award = 31},
    necromancer = {from = {44}, to = 45, bit = 1548, award = 35, jar = 628},
    vampire = {from = {40}, to = 41, bit = 1547, award = 33},
}

local function questCompleted(promotion)
    evt.ForPlayer(Players.Member0)
    return IsQBitSet(QBit(promotion.bit))
        or (promotion.honoraryBit ~= nil and IsQBitSet(QBit(promotion.honoraryBit)))
        or (promotion.award ~= nil and HasAward(Award(promotion.award)))
end

local function validateJars(promotion)
    if promotion.jar == nil then
        return true
    end

    for _, player in ipairs(PartyMembers()) do
        if PlayerClassMatches(player, promotion.from) and not PlayerHasItem(player, promotion.jar) then
            evt.SetMessage("The Necromancer in party slot " .. (player + 1)
                .. " needs a Lich Jar in their own inventory before the transformation can begin.")
            return false
        end
    end
    return true
end

local function promote(promotion, firstTime)
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if PlayerClassMatches(player, promotion.from) then
            SetValue(ClassId, promotion.to)
            SetQBit(QBit(promotion.bit))
            if firstTime then
                AddValue(Experience, promotion.xp or 35000)
            end
            if promotion.jar ~= nil then
                RemovePlayerItem(player, promotion.jar)
            end
        else
            if firstTime then
                AddValue(Experience, promotion.honoraryXp or 25000)
            end
            if promotion.award ~= nil then
                SetAward(Award(promotion.award))
            else
                SetQBit(QBit(promotion.honoraryBit))
            end
        end
    end
    evt.ForPlayer(Players.All)
end

local function requireItem(itemId, messageId)
    evt.ForPlayer(Players.All)
    if HasItem(itemId) then
        return true
    end
    evt.SetMessage(Game.NPCText[messageId])
    return false
end

ReplaceGlobalEvent(25, "Patriarch", function()
    evt.SetMessage(Game.NPCText[27])
    promote(promotions.elf, not questCompleted(promotions.elf))
    ClearQBit(QBit(39))
    SetQBit(QBit(40))
    SetQBit(QBit(430))
    evt.SetNPCTopic(42, 1, 38)
end)

ReplaceGlobalEvent(36, "Ancient Home Found!", function()
    evt.SetMessage(Game.NPCText[45])
    promote(promotions.troll, not questCompleted(promotions.troll))
    ClearQBit(QBit(68))
    evt.SetNPCTopic(43, 1, 612)
end)

ReplaceGlobalEvent(58, "Promotion to Champion", function()
    local firstTime = not questCompleted(promotions.knight)
    if firstTime and not requireItem(539, 85) then return end
    evt.SetMessage(Game.NPCText[IsQBitSet(QBit(22)) and 71 or 70])
    promote(promotions.knight, firstTime)
    if firstTime then RemoveItem(539) end
    ClearQBit(QBit(70))
    evt.SetNPCTopic(15, 2, 735)
    evt.SetNPCTopic(52, 2, 735)
end)

ReplaceGlobalEvent(62, "Sword of the Slayer", function()
    local firstTime = not questCompleted(promotions.dragon)
    if firstTime and not requireItem(540, 81) then return end
    evt.SetMessage(Game.NPCText[IsQBitSet(QBit(21)) and 80 or 79])
    promote(promotions.dragon, firstTime)
    if firstTime then RemoveItem(540) end
    ClearQBit(QBit(74))
    evt.SetNPCTopic(17, 2, 736)
    evt.SetNPCTopic(53, 2, 736)
end)

ReplaceGlobalEvent(71, "Quest", function()
    local firstTime = not questCompleted(promotions.minotaur)
    if firstTime and (not requireItem(541, 98) or not requireItem(732, 94)) then return end
    evt.SetMessage(Game.NPCText[95])
    promote(promotions.minotaur, firstTime)
    if firstTime then
        RemoveItem(541)
        RemoveItem(732)
    end
    ClearQBit(QBit(76))
    SetQBit(QBit(87))
    evt.SetNPCTopic(58, 0, 740)
end)

ReplaceGlobalEvent(81, "Prophecies of the Sun", function()
    local firstTime = not questCompleted(promotions.cleric)
    if firstTime and not requireItem(626, 106) then return end
    evt.SetMessage(Game.NPCText[107])
    promote(promotions.cleric, firstTime)
    if firstTime then RemoveItem(626) end
    ClearQBit(QBit(78))
    evt.SetNPCTopic(59, 2, 737)
end)

ReplaceGlobalEvent(89, "Promotion to Lich", function()
    local firstTime = not questCompleted(promotions.necromancer)
    if firstTime and not requireItem(611, 115) then return end
    if not validateJars(promotions.necromancer) then return end
    evt.SetMessage(Game.NPCText[firstTime and 116 or 925])
    promote(promotions.necromancer, firstTime)
    if firstTime then RemoveItem(611) end
    ClearQBit(QBit(82))
    evt.SetNPCTopic(61, 0, 742)
end)

ReplaceGlobalEvent(90, "Return of Korbu", function()
    local firstTime = not questCompleted(promotions.vampire)
    evt.ForPlayer(Players.All)
    if firstTime then
        if not HasItem(627) then
            evt.SetMessage(Game.NPCText[HasItem(612) and 112 or 151])
            return
        end
        if not requireItem(612, 111) then return end
    end
    evt.SetMessage(Game.NPCText[117])
    promote(promotions.vampire, firstTime)
    if firstTime then
        RemoveItem(627)
        RemoveItem(612)
    end
    ClearQBit(QBit(80))
    evt.SetNPCTopic(62, 1, 739)
end)

local repeatPromotions = {
    {733, "Promote Dark Elves", promotions.elf, 914, 915, 39},
    {734, "Promote Trolls", promotions.troll, 916, 917},
    {735, "Promote Knights", promotions.knight, 918, 919, 70},
    {736, "Promote Dragons", promotions.dragon, 920, 921},
    {737, "Promote Clerics", promotions.cleric, 922, 923},
    {738, "Promote Necromancers", promotions.necromancer, 924, 925},
    {739, "Promote Vampires", promotions.vampire, 926, 927},
    {740, "Promote Minotaurs", promotions.minotaur, 928, 929},
}

for _, entry in ipairs(repeatPromotions) do
    ReplaceGlobalEvent(entry[1], entry[2], function()
        local promotion = entry[3]
        if not questCompleted(promotion) then
            evt.SetMessage(Game.NPCText[entry[4]])
            return
        end
        if not validateJars(promotion) then return end
        promote(promotion, false)
        if entry[6] ~= nil then ClearQBit(QBit(entry[6])) end
        evt.SetMessage(Game.NPCText[entry[5]])
    end)
end
