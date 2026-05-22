-- MMMerge global supplement: MM7 quest follower behavior.

AppendGlobalEvent(858, function()
    MM7.RemoveRescuedDwarfFollowers()
end)

for offset = 0, 6 do
    local npcId = 399 + offset
    local eventId = 859 + offset

    AppendGlobalEvent(eventId, function()
        AddFollowerNpc(npcId)
    end)
end

RegisterGlobalNpcEnterHook(65070, "MMMerge Dwarf King follower cleanup", function(context)
    if context.npcId == 398 then
        MM7.RemoveRescuedDwarfFollowers()
    end
end)

RegisterGlobalHouseTopicClickHook(65071, "MMMerge Antagarich Arcomage deck requirement", function(context)
    local actionId = context.houseActionId

    if actionId ~= HouseAction.TavernArcomagePlay then
        return
    end

    if HasItemAnywhere(MM7.ArcomageDeckItemId) then
        return
    end

    evt.SetHookBlocked(true, "You must have your own card deck to play here.")
end)

RegisterGlobalNpcEnterHook(65073, "MMMerge Dragon Hatchling topics", function(context)
    if context == nil or context.npcId ~= 396 then
        return
    end

    local npcId = 396
    evt.SetNPCTopic(npcId, 0, 789) -- Dragon
    evt.SetNPCTopic(npcId, 1, 0)
    evt.SetNPCTopic(npcId, 2, 0)
    evt.SetNPCTopic(npcId, 3, 0)
end)

RegisterGlobalNpcEnterHook(65074, "MMMerge William Lasker topics", function(context)
    if context == nil or context.npcId ~= 354 then
        return
    end

    if MM7.AnyQBit({1562, 1563}) then
        evt.SetNPCTopic(354, 0, 0)
        evt.SetNPCTopic(354, 1, 0)
    elseif IsQBitSet(QBit(531)) then
        evt.SetNPCTopic(354, 0, 795)
        evt.SetNPCTopic(354, 1, 797)
    elseif MM7.AnyQBit({1560, 1561}) then
        evt.SetNPCTopic(354, 0, 795)
        evt.SetNPCTopic(354, 1, 796)
    elseif IsQBitSet(QBit(530)) then
        evt.SetNPCTopic(354, 0, 795)
        evt.SetNPCTopic(354, 1, 0)
    else
        evt.SetNPCTopic(354, 0, 794)
        evt.SetNPCTopic(354, 1, 0)
    end
end)

ReplaceGlobalEvent(789, "MMMerge Dragon Hatchling", function()
    if MM7.GetCrossVar("DragonJoined", 0) ~= 0 then
        evt.SimpleMessage("The dragon is already traveling with you.")
        return
    end

    if MM7.GetCrossVar("DragonGrown", 0) ~= 0 then
        AddFollowerNpc(396)
        MM7.SetCrossVar("DragonJoined", 1)
        evt.SetNPCName(396, "Dragon")
        evt.SimpleMessage("The grown dragon joins your company.")
        return
    end

    if not IsAtLeast(Food, 5) then
        evt.SimpleMessage("The hatchling is hungry, but you need five food to feed it.")
        return
    end

    SubtractValue(Food, 5)

    local firstFeed = MM7.GetCrossVar("DragonFirstFeedMinutes", 0)
    if firstFeed == 0 then
        MM7.SetCrossVar("DragonFirstFeedMinutes", CurrentGameMinutes())
    end

    local foodEaten = MM7.GetCrossVar("DragonFood", 0) + 5
    MM7.SetCrossVar("DragonFood", foodEaten)

    if foodEaten >= 100 and CurrentGameMinutes() >= MM7.GetCrossVar("DragonFirstFeedMinutes", CurrentGameMinutes()) + 28 * 24 * 60 then
        MM7.SetCrossVar("DragonGrown", 1)
        evt.SimpleMessage("The hatchling has grown enough to travel with you.")
    else
        evt.SimpleMessage("The hatchling eats the food.")
    end
end)

ReplaceGlobalEvent(794, "MMMerge Rogue promotion start", function()
    MM7.PromotionMessage(Game.NPCText[993])
    SetQBit(QBit(530))
    evt.SetNPCTopic(354, 0, 795)
end)

ReplaceGlobalEvent(795, "MMMerge Rogue promotion", function()
    if MM7.AnyQBit({1560, 1561}) then
        MM7.CompletePromotion({
            from = 34,
            to = 35,
            promotedExperience = 15000,
            qbits = {1560, 1561},
            firstMessage = Game.NPCText[995],
        })
        return
    end

    local result = MM7.CompletePromotion({
        from = 34,
        to = 35,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        gold = 5000,
        qbits = {1560, 1561},
        firstMessage = Game.NPCText[995],
        refuseMessage = Game.NPCText[994],
        condition = function() return MM7.HasPartyItem(1426) end,
    })

    if result == 1 then
        MM7.TakePartyItem(1426)
        ClearQBit(QBit(724))
        ClearQBit(QBit(530))
        evt.SetNPCTopic(354, 1, 796)
        evt.SetNPCTopic(354, 0, 795)
    end
end)

ReplaceGlobalEvent(796, "MMMerge Spy promotion gate", function()
    if IsQBitSet(QBit(611)) then
        SetQBit(QBit(531))
        evt.SetNPCTopic(354, 1, 797)
        MM7.PromotionMessage(Game.NPCText[998])
    elseif IsQBitSet(QBit(612)) then
        MM7.PromotionMessage(Game.NPCText[996])
    else
        MM7.PromotionMessage(Game.NPCText[997])
    end
end)

ReplaceGlobalEvent(797, "MMMerge Spy promotion", function()
    local result = MM7.CompletePromotion({
        from = 35,
        to = 37,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        gold = 15000,
        qbits = {1562, 1563},
        firstMessage = Game.NPCText[1002],
        repeatMessage = Game.NPCText[1002],
        refuseMessage = Game.NPCText[1001],
        condition = function() return IsQBitSet(QBit(532)) end,
    })

    if result == 1 then
        ClearQBit(QBit(531))
        evt.SetNPCGreeting(354, 154)
    elseif result == 0 and IsQBitSet(QBit(568)) then
        MM7.PromotionMessage(Game.NPCText[1000])
    end
end)

ReplaceGlobalEvent(800, "MMMerge Assassin promotion", function()
    local result = MM7.CompletePromotion({
        from = 35,
        to = 36,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        gold = 15000,
        qbits = {1564, 1565},
        reputation = 10,
        firstMessage = Game.NPCText[1010],
        repeatMessage = Game.NPCText[1010],
        refuseMessage = Game.NPCText[1009],
        condition = function() return MM7.HasPartyItem(1342) end,
    })

    if result == 1 then
        MM7.TakePartyItem(1342)
        ClearQBit(QBit(725))
        ClearQBit(QBit(533))
        evt.SetNPCGreeting(355, 157)
    end
end)

ReplaceGlobalEvent(801, "MMMerge Crusader promotion start", function()
    MM7.PromotionMessage(Game.NPCText[1012])
    AddFollowerNpc(356)
    SetQBit(QBit(534))
    SetQBit(QBit(1684))
    evt.MoveNPC(356, 0)
    evt.SetNPCTopic(356, 0, 802)
end)

ReplaceGlobalEvent(802, "MMMerge Crusader promotion", function()
    local result = MM7.CompletePromotion({
        from = 26,
        to = 27,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        qbits = {1590, 1591},
        reputation = -5,
        firstMessage = Game.NPCText[1013],
        repeatMessage = Game.NPCText[1013],
        refuseMessage = Game.NPCText[1014],
        condition = function() return IsQBitSet(QBit(535)) end,
    })

    if result == 1 then
        ClearQBit(QBit(534))
        ClearQBit(QBit(1684))
        evt.MoveNPC(356, 941)
        evt.SetNPCTopic(356, 0, 803)
        evt.SetNPCTopic(356, 1, 802)
        evt.SetNPCGreeting(356, 158)
        RemoveFollowerNpc(356)
    end
end)

ReplaceGlobalEvent(803, "MMMerge Hero promotion gate", function()
    if IsQBitSet(QBit(611)) then
        MM7.PromotionMessage(Game.NPCText[1015])
        SetQBit(QBit(536))
        evt.SetNPCTopic(356, 0, 804)
        evt.SetNPCGreeting(356, 158)
        evt.MoveNPC(393, 1158)
    elseif IsQBitSet(QBit(612)) then
        MM7.PromotionMessage(Game.NPCText[1016])
    else
        MM7.PromotionMessage(Game.NPCText[1017])
    end
end)

ReplaceGlobalEvent(804, "MMMerge Hero promotion", function()
    local result = MM7.CompletePromotion({
        from = 27,
        to = 28,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1592, 1593},
        reputation = -10,
        firstMessage = Game.NPCText[1018],
        repeatMessage = Game.NPCText[1018],
        refuseMessage = Game.NPCText[1019],
        condition = function() return IsQBitSet(QBit(1685)) end,
    })

    if result == 1 then
        RemoveFollowerNpc(393)
        ClearQBit(QBit(536))
        ClearQBit(QBit(1685))
        evt.MoveNPC(393, 941)
        evt.SetNPCGreeting(356, 161)
    elseif result == 0 then
        SetQBit(QBit(536))
    end
end)

AppendGlobalEvent(805, function()
    if (IsQBitSet(QBit(611)) or IsQBitSet(QBit(612))) and not (IsQBitSet(QBit(1592)) or IsQBitSet(QBit(1594))) then
        AddFollowerNpc(393)
    end
end)

ReplaceGlobalEvent(807, "MMMerge Villain promotion", function()
    local result = MM7.CompletePromotion({
        from = 27,
        to = 29,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1594, 1595},
        reputation = 10,
        firstMessage = Game.NPCText[1029],
        repeatMessage = Game.NPCText[1029],
        refuseMessage = Game.NPCText[1030],
        condition = function() return IsQBitSet(QBit(1685)) end,
    })

    if result == 1 then
        RemoveFollowerNpc(393)
        ClearQBit(QBit(538))
        ClearQBit(QBit(1685))
        evt.SetNPCGreeting(357, 165)
    end
end)

ReplaceGlobalEvent(810, "MMMerge Initiate promotion", function()
    local message = Game.NPCText[1032]

    local result = MM7.CompletePromotion({
        from = 22,
        to = 23,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        qbits = {1572, 1573},
        firstMessage = message,
        repeatMessage = message,
    })

    ClearQBit(QBit(539))
    evt.SetNPCTopic(377, 0, 810)
    evt.SetNPCTopic(377, 1, 811)
    evt.SetNPCTopic(394, 0, 810)
    evt.SetNPCTopic(394, 1, 811)
end)

ReplaceGlobalEvent(811, "MMMerge Master promotion gate", function()
    if IsQBitSet(QBit(611)) then
        SetQBit(QBit(540))
        evt.SetNPCTopic(377, 1, 812)
        evt.SetNPCTopic(394, 1, 812)
        MM7.PromotionMessage(Game.NPCText[1034])
    elseif IsQBitSet(QBit(612)) then
        MM7.PromotionMessage(Game.NPCText[1035])
    else
        MM7.PromotionMessage(Game.NPCText[1036])
    end
end)

ReplaceGlobalEvent(812, "MMMerge Master promotion", function()
    local result = MM7.CompletePromotion({
        from = 23,
        to = 24,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1574, 1575},
        reputation = -10,
        firstMessage = Game.NPCText[1072],
        repeatMessage = Game.NPCText[1072],
        refuseMessage = Game.NPCText[1073],
        condition = function() return IsQBitSet(QBit(755)) or MM7.HasPartyItem(1332) end,
    })

    if result ~= 0 then
        ClearQBit(QBit(540))
    end

    if result == 1 then
        evt.SetNPCGreeting(377, 167)
    end
end)

ReplaceGlobalEvent(814, "MMMerge Ninja promotion", function()
    local result = MM7.CompletePromotion({
        from = 23,
        to = 25,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1576, 1577},
        reputation = -10,
        firstMessage = Game.NPCText[1080],
        repeatMessage = Game.NPCText[1080],
        refuseMessage = Game.NPCText[1078],
        condition = function() return IsQBitSet(QBit(754)) end,
    })

    if result ~= 0 then
        ClearQBit(QBit(541))
    elseif IsQBitSet(QBit(569)) then
        MM7.PromotionMessage(Game.NPCText[1079])
    end

    if result == 1 then
        evt.SetNPCGreeting(378, 170)
    end
end)

ReplaceGlobalEvent(816, "MMMerge Master Archer promotion", function()
    local result = MM7.CompletePromotion({
        from = 1,
        to = 2,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1586, 1587},
        reputation = -10,
        firstMessage = Game.NPCText[1085],
        repeatMessage = Game.NPCText[1085],
        refuseMessage = Game.NPCText[1086],
        condition = function() return MM7.HasPartyItem(1344) end,
    })

    if result == 1 then
        MM7.GivePartyItem(1345)
        MM7.TakePartyItem(1344)
        evt.SetNPCGreeting(379, 172)
        ClearQBit(QBit(542))
    end
end)

ReplaceGlobalEvent(818, "MMMerge Warrior Mage promotion", function()
    local result = MM7.CompletePromotion({
        from = 0,
        to = 1,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        gold = 7500,
        qbits = {1584, 1585},
        reputation = -10,
        firstMessage = Game.NPCText[1088],
        repeatMessage = Game.NPCText[1088],
        refuseMessage = Game.NPCText[1089],
        condition = function() return IsQBitSet(QBit(570)) end,
    })

    if result == 1 then
        ClearQBit(QBit(543))
        evt.SetNPCTopic(380, 1, 819)
    end
end)

ReplaceGlobalEvent(819, "MMMerge Sniper promotion gate", function()
    if IsQBitSet(QBit(612)) then
        evt.SetNPCTopic(380, 1, 820)
        SetQBit(QBit(544))
        MM7.PromotionMessage(Game.NPCText[1090])
    elseif IsQBitSet(QBit(611)) then
        MM7.PromotionMessage(Game.NPCText[1092])
    else
        MM7.PromotionMessage(Game.NPCText[1091])
    end
end)

ReplaceGlobalEvent(820, "MMMerge Sniper promotion", function()
    local result = MM7.CompletePromotion({
        from = 1,
        to = 3,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1588, 1589},
        reputation = 10,
        firstMessage = Game.NPCText[1093],
        repeatMessage = Game.NPCText[1093],
        refuseMessage = Game.NPCText[1094],
        condition = function() return MM7.HasPartyItem(1344) end,
    })

    if result == 1 then
        MM7.GivePartyItem(1345)
        MM7.TakePartyItem(1344)
        evt.SetNPCGreeting(380, 174)
        ClearQBit(QBit(544))
    elseif result == 0 then
        SetQBit(QBit(544))
    end
end)

ReplaceGlobalEvent(821, "MMMerge Champion promotion gate", function()
    if MM7.AnyQBit({1566, 1567}) then
        if MM7.CheckPromotionSide(611, 612, Game.NPCText[1095], Game.NPCText[1097], Game.NPCText[1096]) then
            SetQBit(QBit(545))
            evt.SetNPCTopic(381, 0, 822)
        end
    else
        MM7.PromotionMessage(Game.NPCText[1098])
    end
end)

ReplaceGlobalEvent(822, "MMMerge Champion promotion", function()
    local result = MM7.CompletePromotion({
        from = 17,
        to = 19,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1568, 1569},
        reputation = -10,
        firstMessage = Game.NPCText[1099],
        repeatMessage = Game.NPCText[1099],
        refuseMessage = Game.NPCText[1100],
        condition = function() return IsAtLeast(ArenaWinsKnight, 5) end,
    })

    if result == 1 then
        ClearQBit(QBit(545))
        evt.SetNPCGreeting(381, 176)
    end
end)

ReplaceGlobalEvent(824, "MMMerge Cavalier promotion", function()
    local result = MM7.CompletePromotion({
        from = 16,
        to = 17,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        qbits = {1566, 1567},
        reputation = -5,
        firstMessage = Game.NPCText[1102],
        repeatMessage = Game.NPCText[1102],
        refuseMessage = Game.NPCText[1103],
        condition = function() return IsQBitSet(QBit(652)) end,
    })

    if result == 1 then
        ClearQBit(QBit(546))
        evt.SetNPCTopic(382, 1, 825)
    end
end)

ReplaceGlobalEvent(825, "MMMerge Black Knight promotion gate", function()
    if MM7.CheckPromotionSide(612, 611, Game.NPCText[1104], Game.NPCText[1106], Game.NPCText[1105]) then
        SetQBit(QBit(547))
        evt.SetNPCTopic(382, 1, 826)
    end
end)

ReplaceGlobalEvent(826, "MMMerge Black Knight promotion", function()
    local result = MM7.CompletePromotion({
        from = 17,
        to = 18,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1570, 1571},
        reputation = -10,
        firstMessage = Game.NPCText[1107],
        repeatMessage = Game.NPCText[1107],
        refuseMessage = Game.NPCText[1108],
        condition = function() return IsQBitSet(QBit(572)) end,
    })

    if result == 1 then
        ClearQBit(QBit(547))
        evt.SetNPCGreeting(382, 178)
    end
end)

ReplaceGlobalEvent(827, "MMMerge Ranger Lord promotion gate", function()
    if MM7.AnyQBit({1578, 1579}) then
        if MM7.CheckPromotionSide(611, 612, Game.NPCText[1109], Game.NPCText[1112], Game.NPCText[1110]) then
            SetQBit(QBit(548))
            evt.SetNPCTopic(383, 0, 828)
        end
    else
        MM7.PromotionMessage(Game.NPCText[1111])
    end
end)

ReplaceGlobalEvent(828, "MMMerge Ranger Lord promotion", function()
    local result = MM7.CompletePromotion({
        from = 31,
        to = 33,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1580, 1581},
        reputation = -5,
        firstMessage = Game.NPCText[1115],
        repeatMessage = Game.NPCText[1115],
        refuseMessage = Game.NPCText[1113],
        condition = function() return IsQBitSet(QBit(553)) end,
    })

    if result == 1 then
        ClearQBit(QBit(548))
        evt.SetNPCGreeting(383, 180)
    elseif result == 2 then
        ClearQBit(QBit(548))
    elseif result == 0 and IsQBitSet(QBit(552)) then
        MM7.PromotionMessage(Game.NPCText[1114])
    end
end)

ReplaceGlobalEvent(830, "MMMerge Hunter promotion gate", function()
    if MM7.AnyQBit({1578, 1579}) then
        ClearQBit(QBit(549))
        MM7.CompletePromotion({
            from = 30,
            to = 31,
            promotedExperience = 30000,
            qbits = {1578, 1579},
            firstMessage = Game.NPCText[1123],
        })
        return
    end

    SetQBit(QBit(549))
    MM7.PromotionMessage(Game.NPCText[1116])
end)

ReplaceGlobalEvent(831, "MMMerge Bounty Hunter promotion gate", function()
    if MM7.CheckPromotionSide(612, 611, Game.NPCText[1118], Game.NPCText[1120], Game.NPCText[1119]) then
        SetQBit(QBit(550))
        evt.SetNPCTopic(384, 1, 832)
    end
end)

ReplaceGlobalEvent(832, "MMMerge Bounty Hunter promotion", function()
    local result = MM7.CompletePromotion({
        from = 31,
        to = 32,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1582, 1583},
        reputation = -10,
        firstMessage = Game.NPCText[1121],
        repeatMessage = Game.NPCText[1121],
        refuseMessage = Game.NPCText[1122],
        condition = function() return IsAtLeast(ArenaWinsPage, 10000) end,
    })

    if result == 1 then
        ClearQBit(QBit(550))
        evt.SetNPCGreeting(384, 182)
    end
end)

ReplaceGlobalEvent(833, "MMMerge Hunter promotion", function()
    MM7.CompletePromotion({
        from = 30,
        to = 31,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        qbits = {1578, 1579},
        firstMessage = Game.NPCText[1123],
    })
    ClearQBit(QBit(549))
    evt.SetNPCTopic(384, 0, 830)
    evt.SetNPCTopic(384, 1, 831)
end)

ReplaceGlobalEvent(836, "MMMerge Priest of Light gate", function()
    if MM7.AnyQBit({1607, 1608}) then
        if IsQBitSet(QBit(612)) then
            MM7.PromotionMessage(Game.NPCText[1130])
        elseif IsQBitSet(QBit(611)) then
            MM7.PromotionMessage(Game.NPCText[1127])
            SetQBit(QBit(554))
            evt.SetNPCTopic(385, 0, 837)
        else
            MM7.PromotionMessage(Game.NPCText[1128])
        end
    else
        MM7.PromotionMessage(Game.NPCText[1129])
    end
end)

ReplaceGlobalEvent(837, "MMMerge Priest of Light promotion", function()
    local result = MM7.CompletePromotion({
        from = 5,
        to = 6,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        gold = 10000,
        qbits = {1609, 1610},
        reputation = -10,
        firstMessage = Game.NPCText[1131],
        repeatMessage = Game.NPCText[1131],
        refuseMessage = Game.NPCText[1132],
        condition = function() return IsQBitSet(QBit(574)) end,
    })

    if result ~= 0 then
        ClearQBit(QBit(554))
    end

    if result == 1 then
        evt.SetNPCGreeting(385, 188)
    end
end)

ReplaceGlobalEvent(839, "MMMerge Priest promotion", function()
    local result = MM7.CompletePromotion({
        from = 4,
        to = 5,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        gold = 5000,
        qbits = {1607, 1608},
        reputation = -5,
        firstMessage = Game.NPCText[1134],
        repeatMessage = Game.NPCText[1134],
        refuseMessage = Game.NPCText[1135],
        condition = function() return MM7.HasPartyItem(1485) end,
    })

    if result == 1 then
        MM7.TakePartyItem(1485)
        ClearQBit(QBit(730))
        SetQBit(QBit(576))
        ClearQBit(QBit(555))
        evt.SetNPCTopic(386, 1, 840)
        evt.SetNPCTopic(386, 0, 839)
    elseif result == 2 then
        ClearQBit(QBit(555))
    end
end)

ReplaceGlobalEvent(840, "MMMerge Priest of Dark gate", function()
    if IsQBitSet(QBit(611)) then
        MM7.PromotionMessage(Game.NPCText[200])
    elseif IsQBitSet(QBit(612)) then
        MM7.PromotionMessage(Game.NPCText[1136])
        SetQBit(QBit(556))
        evt.SetNPCTopic(386, 1, 841)
    else
        MM7.PromotionMessage(Game.NPCText[1137])
    end
end)

ReplaceGlobalEvent(841, "MMMerge Priest of Dark promotion", function()
    local result = MM7.CompletePromotion({
        from = 5,
        to = 7,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        gold = 10000,
        qbits = {1611, 1612},
        reputation = -10,
        firstMessage = Game.NPCText[201],
        repeatMessage = Game.NPCText[201],
        refuseMessage = Game.NPCText[1138],
        condition = function() return IsQBitSet(QBit(575)) end,
    })

    if result ~= 0 then
        ClearQBit(QBit(556))
    end

    if result == 1 then
        evt.SetNPCGreeting(386, 190)
    end
end)

AppendGlobalEvent(842, function()
    AddFollowerNpc(MM7.GolemNpcId)
end)

ReplaceGlobalEvent(843, "MMMerge Wizard promotion", function()
    local result = MM7.CompletePromotion({
        from = 42,
        to = 43,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        qbits = {1619, 1620},
        reputation = -5,
        firstMessage = Game.NPCText[1140],
        repeatMessage = Game.NPCText[1140],
        refuseMessage = Game.NPCText[205],
        condition = function() return IsQBitSet(QBit(585)) or IsQBitSet(QBit(586)) end,
    })

    if result == 1 then
        ClearQBit(QBit(557))
        ClearQBit(QBit(731))
        ClearQBit(QBit(732))
        SetQBit(QBit(558))
        evt.SetNPCTopic(387, 1, 844)
        evt.SetNPCGreeting(395, 199)
    end
end)

ReplaceGlobalEvent(844, "MMMerge Archmage promotion gate", function()
    if MM7.CheckPromotionSide(611, 612, Game.NPCText[1141], Game.NPCText[1143], Game.NPCText[1142]) then
        SetQBit(QBit(559))
        evt.SetNPCTopic(387, 1, 845)
    end
end)

ReplaceGlobalEvent(845, "MMMerge Archmage promotion", function()
    local result = MM7.CompletePromotion({
        from = 43,
        to = 46,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        gold = 10000,
        qbits = {1621, 1622},
        firstMessage = Game.NPCText[1144],
        repeatMessage = Game.NPCText[1144],
        refuseMessage = Game.NPCText[1145],
        condition = function() return MM7.HasPartyItem(1289) end,
    })

    if result == 1 then
        MM7.TakePartyItem(1289)
        ClearQBit(QBit(559))
        ClearQBit(QBit(738))
        evt.SetNPCGreeting(387, 192)
    end
end)

ReplaceGlobalEvent(846, "MMMerge Lich promotion gate", function()
    local allowed = MM7.AnyQBit({1619, 1620}) or PlayerClassMatches(0, {44, 45})

    if not allowed then
        MM7.PromotionMessage(Game.NPCText[1147])
        return
    end

    if IsQBitSet(QBit(612)) then
        SetQBit(QBit(560))
        evt.SetNPCTopic(388, 0, 847)
        MM7.PromotionMessage(Game.NPCText[1146])
    elseif IsQBitSet(QBit(611)) then
        MM7.PromotionMessage(Game.NPCText[1149])
    else
        MM7.PromotionMessage(Game.NPCText[1148])
    end
end)

ReplaceGlobalEvent(847, "MMMerge Lich promotion", function()
    local memberCount = evt.GetPartyMemberCount()
    local promotedCount = 0
    local honoraryCount = 0
    local consumedJarCount = 0

    for playerIndex = 0, memberCount - 1 do
        local classId = GetPlayerClass(playerIndex)
        local jarItem = 0

        if PlayerHasItem(playerIndex, 1417) then
            jarItem = 1417
        elseif classId == 47 and PlayerHasItem(playerIndex, 628) then
            jarItem = 628
        end

        if jarItem ~= 0 then
            RemovePlayerItem(playerIndex, jarItem)
            consumedJarCount = consumedJarCount + 1

            if PlayerClassMatches(playerIndex, {43, 44, 47}) then
                if ApplyLichTransformation(playerIndex) then
                    promotedCount = promotedCount + 1
                    ApplyPlayerRewards(playerIndex, {Experience = 40000})
                end
            else
                honoraryCount = honoraryCount + 1

                if not IsQBitSet(QBit(1624)) then
                    ApplyPlayerRewards(playerIndex, {Experience = 40000})
                end

                MM7.AddPartyGold(1500)
            end
        end
    end

    if consumedJarCount == 0 then
        MM7.PromotionMessage(Game.NPCText[1151])
        return
    end

    SetQBit(QBit(1624))

    if promotedCount > 0 then
        SetQBit(QBit(1623))
    end

    ClearQBit(QBit(560))
    ClearQBit(QBit(741))
    evt.SetNPCTopic(388, 0, 0)
    evt.SetNPCGreeting(388, 194)

    if promotedCount > 0 then
        MM7.PromotionMessage(Game.NPCText[1150])
    elseif honoraryCount > 0 then
        MM7.PromotionMessage(Game.NPCText[1150])
    else
        MM7.PromotionMessage(Game.NPCText[1151])
    end
end)

ReplaceGlobalEvent(849, "MMMerge Great Druid promotion", function()
    local result = MM7.CompletePromotion({
        from = 12,
        to = 13,
        promotedExperience = 30000,
        nonPromotedExperience = 15000,
        qbits = {1613, 1614},
        reputation = -5,
        firstMessage = Game.NPCText[1155],
        repeatMessage = Game.NPCText[1155],
        refuseMessage = Game.NPCText[1153],
        condition = function() return IsQBitSet(QBit(562)) end,
    })

    if result == 1 then
        ClearQBit(QBit(561))
        evt.SetNPCTopic(389, 1, 850)
    elseif result == 0 and (IsQBitSet(QBit(563)) or IsQBitSet(QBit(564)) or IsQBitSet(QBit(565))) then
        MM7.PromotionMessage(Game.NPCText[1154])
    end
end)

ReplaceGlobalEvent(850, "MMMerge Arch Druid promotion cross-path", function()
    if not MM7.AnyQBit({1613, 1614}) then
        MM7.PromotionMessage(Game.NPCText[1152])
        return
    end

    if MM7.CheckPromotionSide(611, 612, Game.NPCText[1156], Game.NPCText[1158], Game.NPCText[1157]) then
        SetQBit(QBit(566))
        evt.SetNPCTopic(389, 1, 851)
        return
    end

    if IsQBitSet(QBit(612)) then
        SetQBit(QBit(566))
        evt.SetNPCTopic(389, 1, 851)
    end
end)

ReplaceGlobalEvent(851, "MMMerge Arch Druid promotion", function()
    local result = MM7.CompletePromotion({
        from = 13,
        to = 15,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1615, 1616},
        reputation = -10,
        firstMessage = Game.NPCText[1159],
        repeatMessage = Game.NPCText[1159],
        refuseMessage = Game.NPCText[1160],
        condition = function() return IsQBitSet(QBit(577)) end,
    })

    if result == 1 then
        ClearQBit(QBit(566))
        evt.SetNPCGreeting(389, 196)
    end
end)

ReplaceGlobalEvent(852, "MMMerge Warlock promotion cross-path", function()
    if not MM7.AnyQBit({1613, 1614}) then
        MM7.PromotionMessage(Game.NPCText[1162])
        return
    end

    if MM7.CheckPromotionSide(612, 611, Game.NPCText[1161], Game.NPCText[1164], Game.NPCText[1163]) then
        SetQBit(QBit(567))
        evt.SetNPCTopic(390, 0, 853)
        return
    end

    if IsQBitSet(QBit(611)) then
        SetQBit(QBit(567))
        evt.SetNPCTopic(390, 0, 853)
    end
end)

ReplaceGlobalEvent(853, "MMMerge Warlock promotion", function()
    local result = MM7.CompletePromotion({
        from = 13,
        to = 14,
        promotedExperience = 80000,
        nonPromotedExperience = 40000,
        qbits = {1617, 1618},
        reputation = -10,
        firstMessage = Game.NPCText[1165],
        repeatMessage = Game.NPCText[1165],
        refuseMessage = Game.NPCText[1166],
        condition = function() return MM7.HasPartyItem(1449) end,
    })

    if result == 1 then
        ClearQBit(QBit(567))
        ClearQBit(QBit(739))
        evt.SetNPCGreeting(390, 198)
        SetQBit(QBit(1687))
        MM7.TakePartyItem(1449)
        AddFollowerNpc(396)
    end
end)

ReplaceGlobalEvent(950, "MMMerge Blaster skill", function()
    evt.ForPlayer(Players.All)
    if not IsAtLeast(BlasterSkill, 1) then
        SetValue(BlasterSkill, SkillJoinedMask.Normal + 1)
    end
end)

ReplaceGlobalEvent(1778, "MMMerge Verdant important matter", function()
    CrossContinents.HandleVerdantIntro()
end)

ReplaceGlobalEvent(1781, "MMMerge Verdant dimension doors", function()
    CrossContinents.ExplainDimensionDoors()
end)

ReplaceGlobalEvent(1782, "MMMerge Verdant Jadame", function()
    CrossContinents.ExplainCurrentContinent(1)
end)

ReplaceGlobalEvent(1783, "MMMerge Verdant Antagarich", function()
    CrossContinents.ExplainCurrentContinent(2)
end)

ReplaceGlobalEvent(1784, "MMMerge Verdant Enroth", function()
    CrossContinents.ExplainCurrentContinent(3)
end)

ReplaceGlobalEvent(1785, "MMMerge Verdant Runaway Chaos", function()
    CrossContinents.ExplainRunawayChaos()
end)

ReplaceGlobalEvent(1786, "MMMerge Verdant Controlled Breach", function()
    CrossContinents.ExplainControlledBreach()
end)

ReplaceGlobalEvent(1787, "MMMerge Verdant next step", function()
    CrossContinents.ExplainNextStep()
end)

ReplaceGlobalEvent(1788, "MMMerge Verdant connector stone", function()
    CrossContinents.HandleConnectorStone()
end)

ReplaceGlobalEvent(513, "MMMerge Malwick conditional ambush", function()
    MM7.SummonMalwickAmbush(false)
end)

ReplaceGlobalEvent(514, "MMMerge Malwick forced ambush", function()
    MM7.SummonMalwickAmbush(true)
end)

ReplaceGlobalEvent(769, "MMMerge Malwick wand", function()
    evt.SetHeldItem(947, {
        identified = true,
        charges = 30,
        maxCharges = 30,
    })
end)

ReplaceGlobalEvent(783, "MMMerge Cast Off to Harmondale", function()
    ClearQBit(QBit(528))
    evt.MoveNPC(340, 215)
    evt.SetNPCGreeting(340, 320)
    evt.SetNPCTopic(340, 3, 0)
    AdvanceGameMinutes(14 * 24 * 60)
    evt.MoveToMap(-17331, 12547, 465, 1024, 0, 0, 0, 0, "7out02.odm")
end)

AppendGlobalEvent(875, function()
    MM7.RemoveLorenFollowersIfResolved()
end)

AppendGlobalEvent(876, function()
    MM7.RemoveLorenFollowersIfResolved()
end)

AppendGlobalEvent(884, function()
    if IsQBitSet(QBit(1696)) then
        AddFollowerNpc(MM7.FakeLorenNpcId)
    end
end)

AppendGlobalEvent(885, function()
    MM7.RemoveLorenFollowersIfResolved()
end)

AppendGlobalEvent(886, function()
    MM7.RemoveLorenFollowersIfResolved()
end)

AppendGlobalEvent(891, function()
    RemoveFollowerNpc(MM7.JudgeFairweatherNpcId)
    AddFollowerNpc(MM7.JudgeSleenNpcId)
end)

AppendGlobalEvent(893, function()
    RemoveFollowerNpc(MM7.JudgeSleenNpcId)
    AddFollowerNpc(MM7.JudgeFairweatherNpcId)
end)

local previousGlobalEvent920 = evt.global[920]
ReplaceGlobalEvent(920, "MMMerge Resurectra final task complete", function(...)
    local completingFinalTask = HasItem(1407) -- Oscillation Overthruster

    if previousGlobalEvent920 ~= nil then
        previousGlobalEvent920(...)
    end

    if completingFinalTask then
        ClearQBit(QBit(642)) -- Return the Oscillation Overthruster to Resurectra.
        MM7.MarkAntagarichEndgameComplete()
    end
end)

local previousGlobalEvent922 = evt.global[922]
ReplaceGlobalEvent(922, "MMMerge Kastore final task complete", function(...)
    local completingFinalTask = HasItem(1407) -- Oscillation Overthruster

    if previousGlobalEvent922 ~= nil then
        previousGlobalEvent922(...)
    end

    if completingFinalTask then
        MM7.MarkAntagarichEndgameComplete()
    end
end)
