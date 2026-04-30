-- Murmurwoods
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
    spriteNames = {"on"},
    castSpellIds = {},
    timers = {
    { eventId = 451, repeating = true, intervalGameMinutes = 15, remainingGameMinutes = 15 },
    { eventId = 452, repeating = true, intervalGameMinutes = 12.5, remainingGameMinutes = 12.5 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(40)) then -- Found and Rescued Cauri Blackthorne
        evt.SetSprite(20, 0, "on")
        evt.SetSprite(21, 0, "on")
        evt.SetSprite(22, 0, "on")
        evt.SetSprite(23, 0, "on")
        evt.SetSprite(24, 0, "on")
        if IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
            evt.SetMonGroupBit(39, MonsterBits.Hostile, 1) -- actor group 39: Cleric of the Sun
            evt.SetMonGroupBit(40, MonsterBits.Hostile, 1) -- actor group 40: Cleric of the Sun
            return
        elseif IsQBitSet(QBit(230)) then -- You have Pissed off the clerics
            evt.SetMonGroupBit(39, MonsterBits.Hostile, 1) -- actor group 39: Cleric of the Sun
            evt.SetMonGroupBit(40, MonsterBits.Hostile, 1) -- actor group 40: Cleric of the Sun
            return
        else
            return
        end
    elseif IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.SetMonGroupBit(39, MonsterBits.Hostile, 1) -- actor group 39: Cleric of the Sun
        evt.SetMonGroupBit(40, MonsterBits.Hostile, 1) -- actor group 40: Cleric of the Sun
        return
    elseif IsQBitSet(QBit(230)) then -- You have Pissed off the clerics
        evt.SetMonGroupBit(39, MonsterBits.Hostile, 1) -- actor group 39: Cleric of the Sun
        evt.SetMonGroupBit(40, MonsterBits.Hostile, 1) -- actor group 40: Cleric of the Sun
        return
    else
        return
    end
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Ravensight Residence", function()
    evt.EnterHouse(388) -- Ravensight Residence
    return
end, "Ravensight Residence")

RegisterEvent(12, "Ravensight Residence", nil, "Ravensight Residence")

RegisterEvent(13, "Dreamwright Residence", function()
    evt.EnterHouse(389) -- Dreamwright Residence
    return
end, "Dreamwright Residence")

RegisterEvent(14, "Dreamwright Residence", nil, "Dreamwright Residence")

RegisterEvent(15, "Snowtree Residence", function()
    evt.EnterHouse(390) -- Snowtree Residence
    return
end, "Snowtree Residence")

RegisterEvent(16, "Snowtree Residence", nil, "Snowtree Residence")

RegisterEvent(17, "Dantillion's Residence", function()
    evt.EnterHouse(391) -- Dantillion's Residence
    return
end, "Dantillion's Residence")

RegisterEvent(18, "Dantillion's Residence", nil, "Dantillion's Residence")

RegisterEvent(19, "Mithrit Residence", function()
    evt.EnterHouse(392) -- Mithrit Residence
    return
end, "Mithrit Residence")

RegisterEvent(20, "Mithrit Residence", nil, "Mithrit Residence")

RegisterEvent(21, "Tonk Residence", function()
    evt.EnterHouse(393) -- Tonk Residence
    return
end, "Tonk Residence")

RegisterEvent(22, "Tonk Residence", nil, "Tonk Residence")

RegisterEvent(23, "Keenedge Residence", function()
    evt.EnterHouse(394) -- Keenedge Residence
    return
end, "Keenedge Residence")

RegisterEvent(24, "Keenedge Residence", nil, "Keenedge Residence")

RegisterEvent(25, "Treasurestone Residence", function()
    evt.EnterHouse(395) -- Treasurestone Residence
    return
end, "Treasurestone Residence")

RegisterEvent(26, "Treasurestone Residence", nil, "Treasurestone Residence")

RegisterEvent(27, "Sampson Residence", function()
    evt.EnterHouse(396) -- Sampson Residence
    return
end, "Sampson Residence")

RegisterEvent(28, "Sampson Residence", nil, "Sampson Residence")

RegisterEvent(29, "Verish's House", function()
    evt.EnterHouse(482) -- Verish's House
    return
end, "Verish's House")

RegisterEvent(30, "Verish's House", nil, "Verish's House")

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

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
    return
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
    return
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    return
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    return
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
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
    evt.StatusText("That was not so refreshing")
    SetValue(PoisonedRed, 0)
    if IsAutonoteSet(263) then return end -- Well near the Temple of the Sun in the Murmurwoods is poison!
    SetAutonote(263) -- Well near the Temple of the Sun in the Murmurwoods is poison!
    return
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(BasePersonality, 16) then
        AddValue(BasePersonality, 2)
        evt.StatusText("Personality +2 (Permanent)")
        SetAutonote(265) -- Well in the Ravage Roaming region gives a permanent Endurance bonus up to an Endurance of 16.
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(131, "Legacy event 131", function()
    if IsQBitSet(QBit(69)) then return end -- Ancient Troll Homeland Found
    if not IsQBitSet(QBit(68)) then return end -- Find the Ancient Troll Homeland and return to Volog Sandwind in the Ironsand Desert. - Given By ? In area 4
    evt.ForPlayer(Players.All)
    if not HasItem(0) then return end -- 0
    RemoveItem(0) -- 0
    SetQBit(QBit(69)) -- Ancient Troll Homeland Found
    return
end)

RegisterEvent(132, "Statue", function()
    evt.ForPlayer(Players.All)
    if not HasItem(339) then return end -- Stone to Flesh
    evt.SpeakNPC(55) -- Cauri Blackthorne
    SetQBit(QBit(40)) -- Found and Rescued Cauri Blackthorne
    RemoveItem(339) -- Stone to Flesh
    SetQBit(QBit(430)) -- Roster Character In Party 31
    evt.SetSprite(20, 0, "on")
    return
end, "Statue")

RegisterEvent(133, "Statue", function()
    evt.ForPlayer(Players.All)
    if not HasItem(339) then return end -- Stone to Flesh
    evt.SpeakNPC(59) -- Dark Elf Pilgrim
    RemoveItem(339) -- Stone to Flesh
    evt.SetSprite(21, 0, "on")
    return
end, "Statue")

RegisterEvent(134, "Statue", function()
    evt.ForPlayer(Players.All)
    if not HasItem(339) then return end -- Stone to Flesh
    evt.SpeakNPC(59) -- Dark Elf Pilgrim
    RemoveItem(339) -- Stone to Flesh
    evt.SetSprite(22, 0, "on")
    return
end, "Statue")

RegisterEvent(135, "Statue", function()
    evt.ForPlayer(Players.All)
    if not HasItem(339) then return end -- Stone to Flesh
    evt.SpeakNPC(59) -- Dark Elf Pilgrim
    RemoveItem(339) -- Stone to Flesh
    evt.SetSprite(23, 0, "on")
    return
end, "Statue")

RegisterEvent(136, "Statue", function()
    evt.ForPlayer(Players.All)
    if not HasItem(339) then return end -- Stone to Flesh
    evt.SpeakNPC(59) -- Dark Elf Pilgrim
    RemoveItem(339) -- Stone to Flesh
    evt.SetSprite(24, 0, "on")
    return
end, "Statue")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(192)) then return end -- Obelisk Area 7
    evt.StatusText("pearswhil")
    SetAutonote(22) -- Obelisk message #6: pearswhil
    SetQBit(QBit(192)) -- Obelisk Area 7
    return
end, "Obelisk")

RegisterEvent(191, "Traveler's Rest", function()
    evt.EnterHouse(113) -- Traveler's Rest
    return
end, "Traveler's Rest")

RegisterEvent(192, "Traveler's Rest", nil, "Traveler's Rest")

RegisterEvent(201, "Guild of Light", function()
    evt.EnterHouse(142) -- Guild of Light
    return
end, "Guild of Light")

RegisterEvent(202, "Guild of Light", nil, "Guild of Light")

RegisterEvent(401, "The Temple of the Sun", nil, "The Temple of the Sun")

RegisterEvent(402, "A Druid Circle", nil, "A Druid Circle")

RegisterEvent(403, "Ancient Troll Home", nil, "Ancient Troll Home")

RegisterEvent(404, "Gate to the Plane of Air", nil, "Gate to the Plane of Air")

RegisterEvent(450, "Well", nil, "Well")

RegisterEvent(451, "Legacy event 451", function()
    local randomStep = PickRandomOption(451, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.PlaySound(351, 14784, 10304)
    elseif randomStep == 4 then
        evt.PlaySound(351, 17152, 5440)
    elseif randomStep == 6 then
        evt.PlaySound(351, -5696, 7040)
    elseif randomStep == 8 then
        evt.PlaySound(351, -17920, 15360)
    elseif randomStep == 10 then
        evt.PlaySound(351, -16256, -576)
    elseif randomStep == 12 then
        evt.PlaySound(351, -2880, -5248)
    end
    local randomStep = PickRandomOption(451, 15, {15, 17, 19, 21, 23, 25})
    if randomStep == 15 then
        evt.PlaySound(342, 16448, 15340)
    elseif randomStep == 17 then
        evt.PlaySound(335, 11200, 15040)
    elseif randomStep == 19 then
        evt.PlaySound(336, 1440, 6016)
    elseif randomStep == 21 then
        evt.PlaySound(337, 9728, -3584)
    elseif randomStep == 23 then
        evt.PlaySound(338, 5568, -12224)
    elseif randomStep == 25 then
        evt.PlaySound(340, 18048, -11968)
    end
    return
end)

RegisterEvent(452, "Legacy event 452", function()
    local randomStep = PickRandomOption(452, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.PlaySound(343, -11392, 13248)
    elseif randomStep == 4 then
        evt.PlaySound(342, -7744, -4992)
    elseif randomStep == 6 then
        evt.PlaySound(346, -16512, -2048)
    elseif randomStep == 8 then
        evt.PlaySound(345, -11456, 10112)
    elseif randomStep == 10 then
        evt.PlaySound(339, -19136, 16000)
    elseif randomStep == 12 then
        evt.PlaySound(340, -4160, -19840)
    end
    local randomStep = PickRandomOption(452, 15, {15, 17, 19, 21, 23, 25})
    if randomStep == 15 then
        evt.PlaySound(340, 4672, 18176)
    elseif randomStep == 17 then
        evt.PlaySound(335, -4096, -12736)
    elseif randomStep == 19 then
        evt.PlaySound(336, -2816, -9088)
    elseif randomStep == 21 then
        evt.PlaySound(337, 320, -12352)
    elseif randomStep == 23 then
        evt.PlaySound(338, -896, 14976)
    elseif randomStep == 25 then
        evt.PlaySound(339, 15552, 13568)
    end
    return
end)

RegisterEvent(454, "Legacy event 454", function()
    if IsQBitSet(QBit(240)) then return end -- for riki
    AddValue(InventoryItem(332), 332) -- Lloyd's Beacon
    SetQBit(QBit(240)) -- for riki
    return
end)

RegisterEvent(455, "Tree", function()
    if HasItem(186) then -- Diamond
        RemoveItem(186) -- Diamond
        AddValue(InventoryItem(656), 656) -- Horseshoe
        return
    elseif HasItem(185) then -- Ruby
        RemoveItem(185) -- Ruby
        AddValue(InventoryItem(271), 271) -- Rejuvenation
        return
    elseif HasItem(184) then -- Sapphire
        RemoveItem(184) -- Sapphire
        AddValue(Gold, 2000)
        return
    elseif HasItem(183) then -- Emerald
        RemoveItem(183) -- Emerald
        AddValue(InventoryItem(655), 655) -- Green Apple
        return
    elseif HasItem(182) then -- Topaz
        RemoveItem(182) -- Topaz
        local randomStep = PickRandomOption(455, 42, {43, 45, 47, 49, 51})
        if randomStep == 43 then
            evt.GiveItem(3, ItemType.Weapon_)
        elseif randomStep == 45 then
            evt.GiveItem(3, ItemType.Armor_)
        elseif randomStep == 47 then
            evt.GiveItem(3, ItemType.Scroll_)
        elseif randomStep == 49 then
            evt.GiveItem(3, ItemType.Ring_)
        elseif randomStep == 51 then
            evt.GiveItem(3, ItemType.Misc)
        end
        return
    elseif HasItem(181) then -- Amethyst
        RemoveItem(181) -- Amethyst
        AddValue(InventoryItem(183), 183) -- Emerald
        return
    elseif HasItem(180) then -- Amber
        RemoveItem(180) -- Amber
        AddValue(InventoryItem(250), 250) -- Swift Potion
        return
    elseif HasItem(179) then -- Citrine
        RemoveItem(179) -- Citrine
        AddValue(InventoryItem(181), 181) -- Amethyst
        return
    elseif HasItem(178) then -- Iolite
        RemoveItem(178) -- Iolite
        AddValue(InventoryItem(132), 132) -- Walking Boots
        return
    elseif HasItem(177) then -- Zircon
        RemoveItem(177) -- Zircon
        AddValue(InventoryItem(179), 179) -- Citrine
        return
    else
        return
    end
end, "Tree")

RegisterEvent(501, "Enter the Temple of the Sun", function()
    evt.MoveToMap(-768, -768, 96, 280, 0, 0, 205, 0, "d22.blv")
    return
end, "Enter the Temple of the Sun")

RegisterEvent(502, "Enter the Druid Circle", function()
    evt.MoveToMap(235, 2980, 673, 1536, 0, 0, 206, 0, "d23.blv")
    return
end, "Enter the Druid Circle")

RegisterEvent(503, "Enter the Plane of Air", function()
    evt.MoveToMap(5376, -12240, 1133, 512, 0, 0, 222, 0, "ElemA.odm")
    return
end, "Enter the Plane of Air")

RegisterEvent(504, "Enter the Ancient Troll Home", function()
    if not IsQBitSet(QBit(69)) then -- Ancient Troll Homeland Found
        SetQBit(QBit(69)) -- Ancient Troll Homeland Found
    end
    evt.MoveToMap(448, -224, 0, 512, 0, 0, 0, 0, "D43.blv")
    return
end, "Enter the Ancient Troll Home")

