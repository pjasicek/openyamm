-- Ravage Roaming
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapFaceMask = 0x08000000,
    onLoad = {1, 2, 3, 4},
    onLeave = {6, 7, 8, 9, 10},
    openedChestIds = {
    [81] = {0},
    [82] = {1},
    [83] = {2},
    [84] = {3},
    [85] = {4},
    [86] = {5},
    [87] = {6},
    [88] = {7},
    [89] = {8},
    [90] = {9},
    [91] = {10},
    [92] = {11},
    [93] = {12},
    [94] = {13},
    [95] = {14},
    [96] = {15},
    [97] = {16},
    [98] = {17},
    [99] = {18},
    [100] = {19},
    },
    contextActions = {
    [11] = { kind = "enter_house", source = "opcode", houseId = 619, targetName = "Xevius's Residence" },
    [13] = { kind = "enter_house", source = "opcode", houseId = 620, targetName = "Vish's House" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 621, targetName = "Sail's Shack" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 622, targetName = "Pordo's Hovel" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 623, targetName = "Galvinus's Home" },
    [23] = { kind = "enter_house", source = "opcode", houseId = 674, targetName = "Cagnor's Shop" },
    [81] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [82] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [83] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [84] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [85] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [86] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [87] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [88] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [89] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [90] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [91] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [92] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [93] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [94] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [95] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [96] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [97] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [98] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [99] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [100] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [101] = { kind = "well", source = "title" },
    [102] = { kind = "well", source = "title" },
    [103] = { kind = "well", source = "title" },
    [150] = { kind = "obelisk", source = "title" },
    [183] = { kind = "enter_house", source = "opcode", houseId = 482, targetName = "Mist" },
    [191] = { kind = "enter_house", source = "opcode", houseId = 235, targetName = "Bull's Eye Inn" },
    [501] = { kind = "enter_dungeon", source = "opcode", targetMap = "d24.blv", targetName = "Balthazar Lair" },
    [502] = { kind = "enter_dungeon", source = "opcode", targetMap = "d25.blv", targetName = "Barbarian Fortress" },
    [503] = { kind = "enter_dungeon", source = "opcode", targetMap = "d26.blv", targetName = "The Crypt of Korbu" },
    [504] = { kind = "enter_dungeon", source = "opcode", targetMap = "d24.blv", targetName = "Balthazar Lair" },
    [505] = { kind = "enter_dungeon", source = "opcode", targetMap = "d25.blv", targetName = "Barbarian Fortress" },
    [506] = { kind = "enter_dungeon", source = "opcode", targetMap = "d25.blv", targetName = "Barbarian Fortress" },
    [507] = { kind = "enter_dungeon", source = "opcode", targetMap = "d25.blv", targetName = "Barbarian Fortress" },
    [508] = { kind = "travel", source = "opcode", targetMap = "elemw.odm", targetName = "Plane of Water" },
    [509] = { kind = "enter_dungeon", source = "opcode", targetMap = "d46.blv", targetName = "Church of Eep" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 479, sourceEventId = 479, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    },
})

RegisterNoOpEvent(1, nil)

RegisterNoOpEvent(2, nil)

RegisterNoOpEvent(3, nil)

RegisterEvent(4, nil, function()
    if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.SetFacetBit(10, FacetBits.Invisible, 0)
        evt.SetFacetBit(10, FacetBits.Untouchable, 0)
        evt.SetFacetBit(11, FacetBits.Untouchable, 1)
        evt.SetFacetBit(11, FacetBits.Invisible, 1)
    end
end)

RegisterNoOpEvent(6, nil)

RegisterNoOpEvent(7, nil)

RegisterNoOpEvent(8, nil)

RegisterNoOpEvent(9, nil)

RegisterNoOpEvent(10, nil)

RegisterEvent(11, "Xevius's Residence", function()
    evt.EnterHouse(619) -- Xevius's Residence
end, "Xevius's Residence")

RegisterEvent(12, "Xevius's Residence", nil, "Xevius's Residence")

RegisterEvent(13, "Vish's House", function()
    evt.EnterHouse(620) -- Vish's House
end, "Vish's House")

RegisterEvent(14, "Vish's House", nil, "Vish's House")

RegisterEvent(15, "Sail's Shack", function()
    evt.EnterHouse(621) -- Sail's Shack
end, "Sail's Shack")

RegisterEvent(16, "Sail's Shack", nil, "Sail's Shack")

RegisterEvent(17, "Pordo's Hovel", function()
    evt.EnterHouse(622) -- Pordo's Hovel
end, "Pordo's Hovel")

RegisterEvent(18, "Pordo's Hovel", nil, "Pordo's Hovel")

RegisterEvent(19, "Galvinus's Home", function()
    evt.EnterHouse(623) -- Galvinus's Home
end, "Galvinus's Home")

RegisterEvent(20, "Galvinus's Home", nil, "Galvinus's Home")

RegisterEvent(23, "Cagnor's Shop", function()
    evt.EnterHouse(674) -- Cagnor's Shop
end, "Cagnor's Shop")

RegisterEvent(24, "Cagnor's Shop", nil, "Cagnor's Shop")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Open Crate", function()
    evt.OpenChest(6)
end, "Open Crate")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Rock", function()
    evt.OpenChest(9)
end, "Rock")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(101, "Drink from the well", function()
    if not IsAtLeast(MapVar(31), 2) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(BankGold, 99) then
            evt.StatusText("Refreshing")
        else
            AddValue(Gold, 200)
            AddValue(MapVar(31), 1)
        end
    return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(BaseEndurance, 16) then
        AddValue(BaseEndurance, 2)
        evt.StatusText("Endurance +2 (Permanent)")
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(193)) then return end -- Obelisk Area 8
    evt.StatusText("amonghiss")
    SetAutonote(11) -- Obelisk message #4: amonghiss
    SetQBit(QBit(193)) -- Obelisk Area 8
end, "Obelisk")

RegisterEvent(183, "Mist", function()
    evt.EnterHouse(482) -- Mist
end, "Mist")

RegisterEvent(184, "Mist", nil, "Mist")

RegisterEvent(191, "Bull's Eye Inn", function()
    evt.EnterHouse(235) -- Bull's Eye Inn
end, "Bull's Eye Inn")

RegisterEvent(192, "Bull's Eye Inn", nil, "Bull's Eye Inn")

RegisterEvent(401, "Balthazar Lair", nil, "Balthazar Lair")

RegisterEvent(402, "Barbarian Fortress", nil, "Barbarian Fortress")

RegisterEvent(403, "The Crypt of Korbu", nil, "The Crypt of Korbu")

RegisterEvent(404, "Church of Eep", nil, "Church of Eep")

RegisterEvent(405, "Gate to the Plane of Water", nil, "Gate to the Plane of Water")

RegisterEvent(406, "Sealed Crate", nil, "Sealed Crate")

RegisterEvent(450, nil, nil)

RegisterEvent(479, nil, function()
    local randomStep = PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.PlaySound(322, 7296, -5280)
    elseif randomStep == 4 then
        evt.PlaySound(322, -1580, -4064)
    elseif randomStep == 6 then
        evt.PlaySound(322, -11808, -3392)
    elseif randomStep == 8 then
        evt.PlaySound(322, -10816, 4352)
    elseif randomStep == 10 then
        evt.PlaySound(322, -1280, 3776)
    end
end)

RegisterEvent(501, "Enter the Balthazar Lair", function()
    evt.MoveToMap(1, -100, -85, 1540, 0, 0, 344, 1, "d24.blv") -- Balthazar Lair
end, "Enter the Balthazar Lair")

RegisterEvent(502, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(-2284, 1847, 1, 1024, 0, 0, 367, 1, "d25.blv") -- Barbarian Fortress
end, "Enter the Barbarian Fortress")

RegisterEvent(503, "Enter the Crypt of Korbu", function()
    evt.MoveToMap(-4436, -6538, 317, 512, 0, 0, 0, 1, "d26.blv") -- The Crypt of Korbu
end, "Enter the Crypt of Korbu")

RegisterEvent(504, "Enter the Balthazar Lair", function()
    evt.MoveToMap(832, 849, 44, 1548, 0, 0, 344, 1, "d24.blv") -- Balthazar Lair
end, "Enter the Balthazar Lair")

RegisterEvent(505, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(614, 1858, 1, 0, 0, 0, 367, 1, "d25.blv") -- Barbarian Fortress
end, "Enter the Barbarian Fortress")

RegisterEvent(506, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(628, -1274, 1, 0, 0, 0, 367, 1, "d25.blv") -- Barbarian Fortress
end, "Enter the Barbarian Fortress")

RegisterEvent(507, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(-2284, -1353, 1, 1024, 0, 0, 367, 1, "d25.blv") -- Barbarian Fortress
end, "Enter the Barbarian Fortress")

RegisterEvent(508, "Enter the Plane of Water", function()
    evt.MoveToMap(-6144, -20528, 1, 512, 0, 0, 348, 1, "elemw.odm") -- Plane of Water
end, "Enter the Plane of Water")

RegisterEvent(509, "Enter the Church of Eep", function()
    evt.MoveToMap(-21, 5, 1, 0, 0, 0, 0, 1, "d46.blv") -- Church of Eep
end, "Enter the Church of Eep")

