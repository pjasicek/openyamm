-- Dragonsand
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {106},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    [77] = {3},
    [78] = {4},
    [79] = {5},
    [108] = {6, 7},
    },
    contextActions = {
    [50] = { kind = "enter_house", source = "opcode", houseId = 1366, targetName = "House" },
    [51] = { kind = "enter_house", source = "opcode", houseId = 1377, targetName = "House" },
    [52] = { kind = "enter_house", source = "opcode", houseId = 1388, targetName = "House" },
    [53] = { kind = "enter_house", source = "opcode", houseId = 1398, targetName = "House" },
    [54] = { kind = "enter_house", source = "opcode", houseId = 1408, targetName = "House" },
    [55] = { kind = "enter_house", source = "opcode", houseId = 1417, targetName = "House" },
    [56] = { kind = "enter_house", source = "opcode", houseId = 1602, targetName = "Tent" },
    [57] = { kind = "enter_house", source = "opcode", houseId = 1604, targetName = "Tent" },
    [58] = { kind = "enter_house", source = "opcode", houseId = 1603, targetName = "Tent" },
    [59] = { kind = "enter_house", source = "opcode", houseId = 1605, targetName = "Tent" },
    [60] = { kind = "enter_house", source = "opcode", houseId = 1606, targetName = "Tent" },
    [75] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [76] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [77] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [78] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [79] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 420, targetName = "Tomb of VARN" },
    [91] = { kind = "travel", source = "opcode", targetMap = "oute3.odm", targetName = "New Sorpigal" },
    [92] = { kind = "enter_dungeon", source = "opcode", targetMap = "znwc.blv", targetName = "New World Computing" },
    [100] = { kind = "fountain", source = "title" },
    [101] = { kind = "fountain", source = "title" },
    [102] = { kind = "fountain", source = "title" },
    [103] = { kind = "shrine", source = "title" },
    [105] = { kind = "use_pedestal", source = "title" },
    [107] = { kind = "obelisk", source = "title" },
    [108] = { kind = "open_chest", source = "opcode", chestIds = {6, 7} },
    },
    learnedEffect = {
    [100] = { autonote = 426, effect = "+10 Elemental resistance permanent" },
    [101] = { autonote = 427, effect = "+10 Seven statistics permanent" },
    [102] = { autonote = 428, effect = "+50 Hit points temporary" },
    },
    textureNames = {},
    spriteNames = {"ped03"},
    castSpellIds = {},
    timers = {
    { eventId = 65535, sourceEventId = 102, triggerStep = 8, origin = "legacy", triggerKind = "long", scheduleKind = "weekly" },
    },
})

RegisterNoOpEvent(1, "rock", "rock")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1366) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1377) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1388) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1398) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1408) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1417) -- House
end, "House")

RegisterEvent(56, "Tent", function()
    evt.EnterHouse(1602) -- Tent
end, "Tent")

RegisterEvent(57, "Tent", function()
    evt.EnterHouse(1604) -- Tent
end, "Tent")

RegisterEvent(58, "Tent", function()
    evt.EnterHouse(1603) -- Tent
end, "Tent")

RegisterEvent(59, "Tent", function()
    evt.EnterHouse(1605) -- Tent
end, "Tent")

RegisterEvent(60, "Tent", function()
    evt.EnterHouse(1606) -- Tent
end, "Tent")

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(77, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(78, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(79, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(90, nil, function()
    evt.MoveToMap(-9734, -19201, 772, 512, 0, 0, 420, 1, "pyramid.blv") -- Tomb of VARN
end)

RegisterEvent(91, nil, function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 0, 0, "oute3.odm") -- New Sorpigal
end)

RegisterEvent(92, nil, function()
    evt.MoveToMap(-640, 512, -416, 512, 0, 0, 0, 0, "znwc.blv") -- New World Computing
end)

RegisterEvent(100, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(63)) then
        AddValue(FireResistance, 10)
        AddValue(AirResistance, 10)
        AddValue(WaterResistance, 10)
        AddValue(EarthResistance, 10)
        SetPlayerBit(PlayerBit(63))
        SetValue(MapVar(0), 0)
        evt.StatusText("+10 Elemental resistance permanent.")
        SetAutonote(426) -- 10 Points of permanent fire, electricity, cold, and poison resistance from the fountain on the east island in Dragonsand.
        return
    end
    SetValue(MapVar(0), 0)
end, "Drink from Fountain")

RegisterEvent(101, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(64)) then
        AddValue(BaseMight, 10)
        AddValue(BaseIntellect, 10)
        AddValue(BasePersonality, 10)
        AddValue(BaseEndurance, 10)
        AddValue(BaseSpeed, 10)
        AddValue(BaseAccuracy, 10)
        AddValue(BaseLuck, 10)
        SetPlayerBit(PlayerBit(64))
        SetValue(MapVar(0), 0)
        evt.StatusText("+10 Seven statistics permanent.")
        SetAutonote(427) -- 10 Points of permanent might, accuracy, speed, endurance, personality, intellect, and luck from the fountain on the south island in Dragonsand.
        return
    end
    SetValue(MapVar(0), 0)
end, "Drink from Fountain")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(428) -- 50 Hit points restored from fountain on the northwest island in Dragonsand.
        return
    end
    SubtractValue(MapVar(2), 1)
    AddValue(CurrentHealth, 50)
    evt.StatusText("+50 Hit points temporary.")
    SetAutonote(428) -- 50 Hit points restored from fountain on the northwest island in Dragonsand.
end, "Drink from Fountain")

RegisterEvent(103, "Shrine of the Gods", function()
    if not IsPlayerBitSet(PlayerBit(70)) then
        AddValue(FireResistance, 20)
        AddValue(AirResistance, 20)
        AddValue(WaterResistance, 20)
        AddValue(EarthResistance, 20)
        AddValue(SpiritResistance, 20)
        AddValue(MindResistance, 20)
        AddValue(BodyResistance, 20)
        AddValue(BaseMight, 20)
        AddValue(BaseIntellect, 20)
        AddValue(BasePersonality, 20)
        AddValue(BaseEndurance, 20)
        AddValue(BaseSpeed, 20)
        AddValue(BaseAccuracy, 20)
        AddValue(BaseLuck, 20)
        SetPlayerBit(PlayerBit(70))
    end
    SetValue(MapVar(1), 0)
    evt.PlaySound(42797, 0, 0)
    evt.StatusText("+20 to all stats permanent.")
end, "Shrine of the Gods")

RegisterEvent(105, "Pedestal", function()
    if HasItem(2073) then -- Eagle Statuette
        RemoveItem(2073) -- Eagle Statuette
        evt.SetSprite(321, 1, "ped03")
        SetQBit(QBit(1248)) -- NPC
        if not IsQBitSet(QBit(1247)) then return end -- NPC
        if not IsQBitSet(QBit(1246)) then return end -- NPC
        if not IsQBitSet(QBit(1249)) then return end -- NPC
        if IsQBitSet(QBit(1250)) then -- NPC
            evt.MoveNPC(872, 0) -- Twillen -> removed
            evt.MoveNPC(826, 1342) -- Twillen -> House
        end
        return
    elseif HasItem(2072) then -- Wolf Statuette
        if not IsQBitSet(QBit(1249)) then return end -- NPC
        RemoveItem(2072) -- Wolf Statuette
        evt.SetSprite(321, 1, "ped03")
        SetQBit(QBit(1248)) -- NPC
        if not IsQBitSet(QBit(1247)) then return end -- NPC
        if not IsQBitSet(QBit(1246)) then return end -- NPC
        if not IsQBitSet(QBit(1249)) then return end -- NPC
        if IsQBitSet(QBit(1250)) then -- NPC
            evt.MoveNPC(872, 0) -- Twillen -> removed
            evt.MoveNPC(826, 1342) -- Twillen -> House
        end
        return
    else
        return
    end
end, "Pedestal")

RegisterEvent(106, nil, function()
    if IsQBitSet(QBit(1248)) then -- NPC
        evt.SetSprite(321, 1, "ped03")
    end
end)

RegisterEvent(107, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1389)) -- NPC
        SetAutonote(447) -- Obelisk Message # 6: erbthieaeuu,_o'd
    end
    if continueStep ~= nil then return end
    evt.SetMessage("\"The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            erbthieaeuu,_o'd\"")
    evt._PressAnyKey(107, 2)
end, "Obelisk")

RegisterEvent(108, "rock", function()
    if IsAtLeast(MapVar(3), 1) then
        evt.OpenChest(6)
        if IsQBitSet(QBit(1399)) then return end -- NPC
        AddValue(Gold, 250000)
        SetValue(MapVar(3), 1)
        SetQBit(QBit(1399)) -- NPC
        return
    elseif IsQBitSet(QBit(1399)) then -- NPC
        evt.OpenChest(7)
    elseif IsQBitSet(QBit(1385)) then -- NPC
        if not IsQBitSet(QBit(1386)) then return end -- NPC
        if not IsQBitSet(QBit(1387)) then return end -- NPC
        if not IsQBitSet(QBit(1388)) then return end -- NPC
        if not IsQBitSet(QBit(1389)) then return end -- NPC
        if not IsQBitSet(QBit(1390)) then return end -- NPC
        if not IsQBitSet(QBit(1391)) then return end -- NPC
        if not IsQBitSet(QBit(1392)) then return end -- NPC
        if not IsQBitSet(QBit(1393)) then return end -- NPC
        if not IsQBitSet(QBit(1394)) then return end -- NPC
        if not IsQBitSet(QBit(1395)) then return end -- NPC
        if not IsQBitSet(QBit(1396)) then return end -- NPC
        if not IsQBitSet(QBit(1397)) then return end -- NPC
        if not IsQBitSet(QBit(1398)) then return end -- NPC
        evt.OpenChest(6)
        if IsQBitSet(QBit(1399)) then return end -- NPC
        AddValue(Gold, 250000)
        SetValue(MapVar(3), 1)
        SetQBit(QBit(1399)) -- NPC
        return
    else
        return
    end
end, "rock")

RegisterEvent(65535, "", function()
    SetValue(MapVar(2), 20)
end)

