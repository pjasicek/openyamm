-- Eel Infested Waters
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535},
    onLeave = {},
    openedChestIds = {
    [58] = {1},
    [59] = {2},
    },
    contextActions = {
    [2] = { kind = "enter_house", source = "opcode", houseId = 108, targetName = "Little Charms" },
    [4] = { kind = "enter_house", source = "opcode", houseId = 328, targetName = "Abdul's Discount House of Worship" },
    [5] = { kind = "enter_house", source = "opcode", houseId = 262, targetName = "An Arrow's Flight" },
    [7] = { kind = "enter_house", source = "opcode", houseId = 263, targetName = "A Stone's Throw" },
    [9] = { kind = "enter_house", source = "opcode", houseId = 504, targetName = "Tigershark" },
    [10] = { kind = "enter_house", source = "opcode", houseId = 503, targetName = "Cirrus" },
    [50] = { kind = "enter_house", source = "opcode", houseId = 1226, targetName = "House" },
    [51] = { kind = "enter_house", source = "opcode", houseId = 1241, targetName = "House" },
    [52] = { kind = "enter_house", source = "opcode", houseId = 1256, targetName = "House" },
    [53] = { kind = "enter_house", source = "opcode", houseId = 1271, targetName = "House" },
    [54] = { kind = "enter_house", source = "opcode", houseId = 1286, targetName = "House" },
    [55] = { kind = "enter_house", source = "opcode", houseId = 1301, targetName = "House" },
    [56] = { kind = "enter_house", source = "opcode", houseId = 1314, targetName = "House" },
    [57] = { kind = "enter_house", source = "opcode", houseId = 1326, targetName = "House" },
    [58] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [59] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 419, targetName = "Castle Alamos" },
    [100] = { kind = "fountain", source = "title" },
    [101] = { kind = "fountain", source = "title" },
    [226] = { kind = "generic_event", source = "opcode" },
    [227] = { kind = "obelisk", source = "title" },
    [261] = { kind = "shrine", source = "title" },
    },
    learnedEffect = {
    [100] = { autonote = 405, effect = "+20 Elemental resistance temporary" },
    [101] = { autonote = 406, effect = "+20 Magic resistance temporary" },
    },
    textureNames = {},
    spriteNames = {"swrdstx"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, "Little Charms", function()
    evt.EnterHouse(108) -- Little Charms
end, "Little Charms")

RegisterEvent(3, "Little Charms", nil, "Little Charms")

RegisterEvent(4, "Abdul's Discount House of Worship", function()
    evt.EnterHouse(328) -- Abdul's Discount House of Worship
end, "Abdul's Discount House of Worship")

RegisterEvent(5, "An Arrow's Flight", function()
    evt.EnterHouse(262) -- An Arrow's Flight
end, "An Arrow's Flight")

RegisterEvent(6, "An Arrow's Flight", nil, "An Arrow's Flight")

RegisterEvent(7, "A Stone's Throw", function()
    evt.EnterHouse(263) -- A Stone's Throw
end, "A Stone's Throw")

RegisterEvent(8, "A Stone's Throw", nil, "A Stone's Throw")

RegisterEvent(9, "Tigershark", function()
    evt.EnterHouse(504) -- Tigershark
end, "Tigershark")

RegisterEvent(10, "Cirrus", function()
    evt.EnterHouse(503) -- Cirrus
end, "Cirrus")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1226) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1241) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1256) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1271) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1286) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1301) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1314) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1326) -- House
end, "House")

RegisterEvent(58, nil, function()
    evt.OpenChest(1)
end)

RegisterEvent(59, nil, function()
    evt.OpenChest(2)
end)

RegisterEvent(90, nil, function()
    evt.MoveToMap(-2921, 13139, 225, 1536, 0, 0, 419, 1, "cd1.blv") -- Castle Alamos
end)

RegisterEvent(100, "Drink from Fountain.", function()
    if not IsAtLeast(FireResistanceBonus, 20) then
        SetValue(FireResistanceBonus, 20)
        SetValue(AirResistanceBonus, 20)
        SetValue(WaterResistanceBonus, 20)
        SetValue(EarthResistanceBonus, 20)
        evt.StatusText("+20 Elemental resistance temporary.")
        SetAutonote(405) -- 20 Points of temporary fire, electricity, cold, and poison resistance from the southwest fountain in the Eel Infested Waters.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from Fountain.")

RegisterEvent(101, "Drink from Fountain.", function()
    if not IsAtLeast(WaterResistanceBonus, 20) then
        SetValue(WaterResistanceBonus, 20)
        evt.StatusText("+20 Magic resistance temporary.")
        SetAutonote(406) -- 20 Points of temporary magic resistance from the southeast fountain in the Eel Infested Waters.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from Fountain.")

RegisterEvent(226, nil, function()
    if IsQBitSet(QBit(1337)) then -- NPC
        return
    end
    if not IsAtLeast(ActualMight, 200) then
        evt.FaceExpression(51)
        evt.StatusText("The Sword won't budge!")
        return
    end
    SetQBit(QBit(1337)) -- NPC
    AddValue(InventoryItem(2023), 2023) -- Excalibur
    evt.SetSprite(99, 1, "swrdstx")
end)

RegisterEvent(227, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1396)) -- NPC
        SetAutonote(454) -- Obelisk Message # 13: oon_htfdorstusl_
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            oon_htfdorstusl_")
    evt._PressAnyKey(227, 2)
end, "Obelisk")

RegisterEvent(261, "Shrine of Poison", function()
    if not IsAtLeast(MonthIs, 10) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1241)) then -- NPC
            SetQBit(QBit(1241)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(EarthResistance, 10)
            evt.StatusText("+10 Poison resistance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(EarthResistance, 3)
        evt.StatusText("+3 Poison resistance permanent")
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Poison")

RegisterEvent(65535, "", function()
    if not IsQBitSet(QBit(1337)) then return end -- NPC
    evt.SetSprite(99, 1, "swrdstx")
end)

