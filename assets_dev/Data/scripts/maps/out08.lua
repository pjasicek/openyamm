-- Ravage Roaming
-- generated from legacy EVT/STR

SetMapMetadata({
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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 479, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterEvent(4, "Legacy event 4", function()
    if not IsQBitSet(QBit(23)) then return end -- Allied with Minotaurs. Rescue the Minotaurs done.
    evt.SetFacetBit(10, FacetBits.Invisible, 0)
    evt.SetFacetBit(10, FacetBits.Untouchable, 0)
    evt.SetFacetBit(11, FacetBits.Untouchable, 1)
    evt.SetFacetBit(11, FacetBits.Invisible, 1)
    return
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Xevius's Residence", function()
    evt.EnterHouse(397) -- Xevius's Residence
    return
end, "Xevius's Residence")

RegisterEvent(12, "Xevius's Residence", nil, "Xevius's Residence")

RegisterEvent(13, "Vish's House", function()
    evt.EnterHouse(398) -- Vish's House
    return
end, "Vish's House")

RegisterEvent(14, "Vish's House", nil, "Vish's House")

RegisterEvent(15, "Sail's Shack", function()
    evt.EnterHouse(399) -- Sail's Shack
    return
end, "Sail's Shack")

RegisterEvent(16, "Sail's Shack", nil, "Sail's Shack")

RegisterEvent(17, "Pordo's Hovel", function()
    evt.EnterHouse(400) -- Pordo's Hovel
    return
end, "Pordo's Hovel")

RegisterEvent(18, "Pordo's Hovel", nil, "Pordo's Hovel")

RegisterEvent(19, "Galvinus's Home", function()
    evt.EnterHouse(401) -- Galvinus's Home
    return
end, "Galvinus's Home")

RegisterEvent(20, "Galvinus's Home", nil, "Galvinus's Home")

RegisterEvent(23, "Cagnor's Shop", function()
    evt.EnterHouse(452) -- Cagnor's Shop
    return
end, "Cagnor's Shop")

RegisterEvent(24, "Cagnor's Shop", nil, "Cagnor's Shop")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
    return
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
    return
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
    return
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
    return
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
    return
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
    return
end, "Chest")

RegisterEvent(87, "Open Crate", function()
    evt.OpenChest(6)
    return
end, "Open Crate")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Rock", function()
    evt.OpenChest(9)
    return
end, "Rock")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
    return
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
    return
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    SetQBit(QBit(168)) -- Found the treasure of the Dread Pirate Stanley!
    return
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
    return
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
    return
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
    return
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
    return
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(BaseEndurance, 16) then
        AddValue(BaseEndurance, 2)
        evt.StatusText("Endurance +2 (Permanent)")
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(193)) then return end -- Obelisk Area 8
    evt.StatusText("amonghiss")
    SetAutonote(20) -- Obelisk message #4: amonghiss
    SetQBit(QBit(193)) -- Obelisk Area 8
    return
end, "Obelisk")

RegisterEvent(183, "Mist", function()
    evt.EnterHouse(66) -- Mist
    return
end, "Mist")

RegisterEvent(184, "Mist", nil, "Mist")

RegisterEvent(191, "Bull's Eye Inn", function()
    evt.EnterHouse(114) -- Bull's Eye Inn
    return
end, "Bull's Eye Inn")

RegisterEvent(192, "Bull's Eye Inn", nil, "Bull's Eye Inn")

RegisterEvent(401, "Balthazar Lair", nil, "Balthazar Lair")

RegisterEvent(402, "Barbarian Fortress", nil, "Barbarian Fortress")

RegisterEvent(403, "The Crypt of Korbu", nil, "The Crypt of Korbu")

RegisterEvent(404, "Church of Eep", nil, "Church of Eep")

RegisterEvent(405, "Gate to the Plane of Water", nil, "Gate to the Plane of Water")

RegisterEvent(406, "Sealed Crate", nil, "Sealed Crate")

RegisterEvent(450, "Legacy event 450", nil)

RegisterEvent(479, "Legacy event 479", function()
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
    return
end)

RegisterEvent(501, "Enter the Balthazar Lair", function()
    evt.MoveToMap(1, -100, -85, 1540, 0, 0, 207, 0, "d24.blv")
    return
end, "Enter the Balthazar Lair")

RegisterEvent(502, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(-2284, 1847, 1, 1024, 0, 0, 208, 0, "d25.blv")
    return
end, "Enter the Barbarian Fortress")

RegisterEvent(503, "Enter the Crypt of Korbu", function()
    evt.MoveToMap(-4436, -6538, 317, 512, 0, 0, 0, 0, "d26.blv")
    return
end, "Enter the Crypt of Korbu")

RegisterEvent(504, "Enter the Balthazar Lair", function()
    evt.MoveToMap(832, 849, 44, 1548, 0, 0, 243, 1, "d24.blv")
    return
end, "Enter the Balthazar Lair")

RegisterEvent(505, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(614, 1858, 1, 0, 0, 0, 208, 0, "d25.blv")
    return
end, "Enter the Barbarian Fortress")

RegisterEvent(506, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(628, -1274, 1, 0, 0, 0, 208, 0, "d25.blv")
    return
end, "Enter the Barbarian Fortress")

RegisterEvent(507, "Enter the Barbarian Fortress", function()
    evt.MoveToMap(-2284, -1353, 1, 1024, 0, 0, 208, 0, "d25.blv")
    return
end, "Enter the Barbarian Fortress")

RegisterEvent(508, "Enter the Plane of Water", function()
    evt.MoveToMap(-6144, -20528, 1, 512, 0, 0, 223, 0, "ElemW.odm")
    return
end, "Enter the Plane of Water")

RegisterEvent(509, "Enter the Church of Eep", function()
    evt.MoveToMap(-21, 5, 1, 0, 0, 0, 0, 0, "D46.blv")
    return
end, "Enter the Church of Eep")
