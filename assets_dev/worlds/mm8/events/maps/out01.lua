-- Dagger Wound Island
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapFaceMask = 0x08000000,
    onLoad = {1, 2, 3, 4},
    onLeave = {6, 7, 8, 9, 10},
    openedChestIds = {
    [81] = {0, 3},
    [82] = {1},
    [83] = {2},
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
    [11] = { kind = "enter_house", source = "opcode", houseId = 761, targetName = "Hiss' Hut" },
    [13] = { kind = "enter_house", source = "opcode", houseId = 776, targetName = "Rohtnax's House" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 784, targetName = "Tisk's Hut" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 792, targetName = "Thadin's House" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 795, targetName = "House of Ich" },
    [21] = { kind = "enter_house", source = "opcode", houseId = 798, targetName = "Languid's Hut" },
    [23] = { kind = "enter_house", source = "opcode", houseId = 804, targetName = "House of Thistle" },
    [25] = { kind = "enter_house", source = "opcode", houseId = 813, targetName = "Zevah's Hut" },
    [27] = { kind = "enter_house", source = "opcode", houseId = 823, targetName = "Isthric's House" },
    [29] = { kind = "enter_house", source = "opcode", houseId = 833, targetName = "Bone's House" },
    [31] = { kind = "enter_house", source = "opcode", houseId = 843, targetName = "Lasatin's Hut" },
    [33] = { kind = "enter_house", source = "opcode", houseId = 852, targetName = "Menasaur's House" },
    [35] = { kind = "enter_house", source = "opcode", houseId = 860, targetName = "Husk's Hut" },
    [37] = { kind = "enter_house", source = "opcode", houseId = 866, targetName = "Talimere's Hut" },
    [39] = { kind = "enter_house", source = "opcode", houseId = 870, targetName = "House of Reshie" },
    [41] = { kind = "enter_house", source = "opcode", houseId = 873, targetName = "House" },
    [43] = { kind = "enter_house", source = "opcode", houseId = 876, targetName = "Long-Tail's Hut" },
    [45] = { kind = "enter_house", source = "opcode", houseId = 879, targetName = "Aislen's House" },
    [47] = { kind = "enter_house", source = "opcode", houseId = 882, targetName = "House of Grivic" },
    [49] = { kind = "enter_house", source = "opcode", houseId = 885, targetName = "Ush's Hut" },
    [81] = { kind = "open_chest", source = "opcode", chestIds = {0, 3} },
    [82] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [83] = { kind = "open_chest", source = "opcode", chestIds = {2} },
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
    [104] = { kind = "fountain", source = "title" },
    [150] = { kind = "obelisk", source = "title" },
    [171] = { kind = "enter_house", source = "opcode", houseId = 1, targetName = "True Mettle" },
    [173] = { kind = "enter_house", source = "opcode", houseId = 36, targetName = "The Tannery" },
    [175] = { kind = "enter_house", source = "opcode", houseId = 76, targetName = "Fearsome Fetishes" },
    [177] = { kind = "enter_house", source = "opcode", houseId = 110, targetName = "Herbal Elixirs" },
    [179] = { kind = "enter_house", source = "opcode", houseId = 182, targetName = "Cures and Curses" },
    [183] = { kind = "enter_house", source = "opcode", houseId = 479, targetName = "The Windling" },
    [185] = { kind = "enter_house", source = "opcode", houseId = 303, targetName = "Mystic Medicine" },
    [187] = { kind = "enter_house", source = "opcode", houseId = 1564, targetName = "Rites of Passage" },
    [191] = { kind = "enter_house", source = "opcode", houseId = 228, targetName = "The Grog and Grub" },
    [193] = { kind = "enter_house", source = "opcode", houseId = 281, targetName = "The Some Place Safe" },
    [197] = { kind = "enter_house", source = "opcode", houseId = 212, targetName = "Clan Leader's Hall" },
    [199] = { kind = "enter_house", source = "opcode", houseId = 1607, targetName = "The Adventurer's Inn" },
    [451] = { kind = "teleport", source = "heuristic" },
    [452] = { kind = "teleport", source = "heuristic" },
    [453] = { kind = "teleport", source = "heuristic" },
    [460] = { kind = "secret_event", source = "heuristic", hidden = true },
    [465] = { kind = "teleport", source = "heuristic" },
    [466] = { kind = "teleport", source = "heuristic" },
    [467] = { kind = "teleport", source = "heuristic" },
    [468] = { kind = "secret_event", source = "heuristic", hidden = true },
    [469] = { kind = "secret_event", source = "heuristic", hidden = true },
    [471] = { kind = "teleport", source = "heuristic" },
    [472] = { kind = "teleport", source = "heuristic" },
    [501] = { kind = "enter_dungeon", source = "opcode", targetMap = "d05.blv", targetName = "Abandoned Temple" },
    [502] = { kind = "enter_dungeon", source = "opcode", targetMap = "d06.blv", targetName = "Pirate Outpost" },
    [503] = { kind = "enter_dungeon", source = "opcode", targetMap = "d40.blv", targetName = "Uplifted Library" },
    [504] = { kind = "enter_dungeon", source = "opcode", targetMap = "d05.blv", targetName = "Abandoned Temple" },
    [505] = { kind = "enter_dungeon", source = "opcode", targetMap = "eleme.blv", targetName = "Plane of Earth" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 9, 136},
    timers = {
    { eventId = 456, sourceEventId = 456, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 30 },
    { eventId = 460, sourceEventId = 460, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 30 },
    { eventId = 463, sourceEventId = 463, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    { eventId = 468, sourceEventId = 468, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 40 },
    { eventId = 469, sourceEventId = 469, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 40 },
    { eventId = 479, sourceEventId = 479, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    { eventId = 500, sourceEventId = 500, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "daily", startHour = 10, startMinute = 0, startSecond = 0 },
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(2)) then -- Activate Area 1 teleporters 5 and 6.
        evt.SetFacetBit(10, FacetBits.Invisible, 0)
        evt.SetFacetBit(10, FacetBits.Untouchable, 0)
    end
end)

RegisterEvent(2, nil, function()
    if not IsQBitSet(QBit(6)) then -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
        evt.SetNPCGroupNews(12, 12) -- NPC group 12 "Misc Group for Riki(M2)" -> news 12: "Help us!  If we do not push the pirates off the island all will be lost!"
        evt.SetNPCGroupNews(13, 12) -- NPC group 13 "Misc Group for Riki(M3)" -> news 12: "Help us!  If we do not push the pirates off the island all will be lost!"
        if IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
            evt.SetFacetBit(25, FacetBits.Invisible, 0)
            evt.SetFacetBit(25, FacetBits.Untouchable, 0)
            evt.SetFacetBit(26, FacetBits.Untouchable, 1)
            return
        elseif IsQBitSet(QBit(38)) then -- Quest 36 is done.
            evt.SetFacetBit(25, FacetBits.Invisible, 0)
            evt.SetFacetBit(25, FacetBits.Untouchable, 0)
            evt.SetFacetBit(26, FacetBits.Untouchable, 1)
        else
            evt.SetFacetBit(25, FacetBits.Invisible, 1)
            evt.SetFacetBit(25, FacetBits.Untouchable, 1)
        end
    return
    end
    evt.SetFacetBit(20, FacetBits.Invisible, 1)
    evt.SetFacetBit(20, FacetBits.Untouchable, 1)
    evt.SetMonGroupBit(14, MonsterBits.Invisible, 1) -- actor group 14: Regnan Brigadier, spawn Wimpy Pirate Warrior Male A
    evt.SetMonGroupBit(10, MonsterBits.Invisible, 1) -- actor group 10: spawn Wimpy Pirate Warrior Male A
    evt.SetMonGroupBit(11, MonsterBits.Invisible, 1) -- actor group 11: spawn Wimpy Pirate Warrior Male A
    evt.SetNPCGroupNews(12, 13) -- NPC group 12 "Misc Group for Riki(M2)" -> news 13: "With the Pirate Outpost defeated our homes are once again safe!  Thank you!"
    evt.SetNPCGroupNews(13, 13) -- NPC group 13 "Misc Group for Riki(M3)" -> news 13: "With the Pirate Outpost defeated our homes are once again safe!  Thank you!"
    evt.SetNPCGroupNews(1, 2) -- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 2: "Our thanks for defeating the pirates!  Now if you could only do something about the mountain of fire!"
    evt.SetFacetBit(25, FacetBits.Invisible, 0)
    evt.SetFacetBit(25, FacetBits.Untouchable, 0)
    evt.SetFacetBit(26, FacetBits.Untouchable, 1)
end)

RegisterEvent(3, nil, function()
    if IsQBitSet(QBit(226)) then return end -- game Init stuff in area one
    SetQBit(QBit(226)) -- game Init stuff in area one
    SetQBit(QBit(306)) -- TP Buff Daggerwound islands
    SetQBit(QBit(401)) -- Roster Character In Party 2
    SetQBit(QBit(407)) -- Roster Character In Party 8
end)

RegisterNoOpEvent(4, nil)

RegisterNoOpEvent(6, nil)

RegisterNoOpEvent(7, nil)

RegisterNoOpEvent(8, nil)

RegisterNoOpEvent(9, nil)

RegisterNoOpEvent(10, nil)

RegisterEvent(11, "Hiss' Hut", function()
    evt.EnterHouse(761) -- Hiss' Hut
end, "Hiss' Hut")

RegisterEvent(12, "Hiss' Hut", nil, "Hiss' Hut")

RegisterEvent(13, "Rohtnax's House", function()
    evt.EnterHouse(776) -- Rohtnax's House
end, "Rohtnax's House")

RegisterEvent(14, "Rohtnax's House", nil, "Rohtnax's House")

RegisterEvent(15, "Tisk's Hut", function()
    evt.EnterHouse(784) -- Tisk's Hut
end, "Tisk's Hut")

RegisterEvent(16, "Tisk's Hut", nil, "Tisk's Hut")

RegisterEvent(17, "Thadin's House", function()
    evt.EnterHouse(792) -- Thadin's House
end, "Thadin's House")

RegisterEvent(18, "Thadin's House", nil, "Thadin's House")

RegisterEvent(19, "House of Ich", function()
    evt.EnterHouse(795) -- House of Ich
end, "House of Ich")

RegisterEvent(20, "House of Ich", nil, "House of Ich")

RegisterEvent(21, "Languid's Hut", function()
    evt.EnterHouse(798) -- Languid's Hut
end, "Languid's Hut")

RegisterEvent(22, "Languid's Hut", nil, "Languid's Hut")

RegisterEvent(23, "House of Thistle", function()
    evt.EnterHouse(804) -- House of Thistle
end, "House of Thistle")

RegisterEvent(24, "House of Thistle", nil, "House of Thistle")

RegisterEvent(25, "Zevah's Hut", function()
    evt.EnterHouse(813) -- Zevah's Hut
end, "Zevah's Hut")

RegisterEvent(26, "Zevah's Hut", nil, "Zevah's Hut")

RegisterEvent(27, "Isthric's House", function()
    evt.EnterHouse(823) -- Isthric's House
end, "Isthric's House")

RegisterEvent(28, "Isthric's House", nil, "Isthric's House")

RegisterEvent(29, "Bone's House", function()
    evt.EnterHouse(833) -- Bone's House
end, "Bone's House")

RegisterEvent(30, "Bone's House", nil, "Bone's House")

RegisterEvent(31, "Lasatin's Hut", function()
    evt.EnterHouse(843) -- Lasatin's Hut
end, "Lasatin's Hut")

RegisterEvent(32, "Lasatin's Hut", nil, "Lasatin's Hut")

RegisterEvent(33, "Menasaur's House", function()
    evt.EnterHouse(852) -- Menasaur's House
end, "Menasaur's House")

RegisterEvent(34, "Menasaur's House", nil, "Menasaur's House")

RegisterEvent(35, "Husk's Hut", function()
    evt.EnterHouse(860) -- Husk's Hut
end, "Husk's Hut")

RegisterEvent(36, "Husk's Hut", nil, "Husk's Hut")

RegisterEvent(37, "Talimere's Hut", function()
    evt.EnterHouse(866) -- Talimere's Hut
end, "Talimere's Hut")

RegisterEvent(38, "Talimere's Hut", nil, "Talimere's Hut")

RegisterEvent(39, "House of Reshie", function()
    evt.EnterHouse(870) -- House of Reshie
end, "House of Reshie")

RegisterEvent(40, "House of Reshie", nil, "House of Reshie")

RegisterEvent(41, "House", function()
    evt.EnterHouse(873) -- House
end, "House")

RegisterEvent(42, "House", nil, "House")

RegisterEvent(43, "Long-Tail's Hut", function()
    evt.EnterHouse(876) -- Long-Tail's Hut
end, "Long-Tail's Hut")

RegisterEvent(44, "Long-Tail's Hut", nil, "Long-Tail's Hut")

RegisterEvent(45, "Aislen's House", function()
    evt.EnterHouse(879) -- Aislen's House
end, "Aislen's House")

RegisterEvent(46, "Aislen's House", nil, "Aislen's House")

RegisterEvent(47, "House of Grivic", function()
    evt.EnterHouse(882) -- House of Grivic
end, "House of Grivic")

RegisterEvent(48, "House of Grivic", nil, "House of Grivic")

RegisterEvent(49, "Ush's Hut", function()
    evt.EnterHouse(885) -- Ush's Hut
end, "Ush's Hut")

RegisterEvent(50, "Ush's Hut", nil, "Ush's Hut")

RegisterEvent(81, "Chest", function()
    if not HasPlayer(2) then -- Fredrick Talimere
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(93, "Open Crate", function()
    evt.OpenChest(12)
end, "Open Crate")

RegisterEvent(94, "Open Crate", function()
    evt.OpenChest(13)
end, "Open Crate")

RegisterEvent(95, "Open Crate", function()
    evt.OpenChest(14)
end, "Open Crate")

RegisterEvent(96, "Open Crate", function()
    evt.OpenChest(15)
end, "Open Crate")

RegisterEvent(97, "Open Crate", function()
    evt.OpenChest(16)
end, "Open Crate")

RegisterEvent(98, "Open Crate", function()
    evt.OpenChest(17)
end, "Open Crate")

RegisterEvent(99, "Open Crate", function()
    evt.OpenChest(18)
end, "Open Crate")

RegisterEvent(100, "Open Crate", function()
    evt.OpenChest(19)
end, "Open Crate")

RegisterEvent(101, "Drink from the well", function()
    if not IsAtLeast(IntellectBonus, 15) then
        AddValue(IntellectBonus, 15)
        evt.StatusText("Intellect +15 (Temporary)")
        SetAutonote(206) -- Well in the village of Blood Drop on Dagger Wound Island gives a temporary Intellect bonus of 15.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(BaseLuck, 16) then
        AddValue(BaseLuck, 2)
        evt.StatusText("Luck +2 (Permanent)")
        SetAutonote(207) -- Well in the village of Blood Drop on Dagger Wound Island gives a permanent Luck bonus up to a Luck of 16.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    if not IsAtLeast(MapVar(31), 2) then
        if IsAtLeast(Gold, 99) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(BankGold, 99) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(BaseLuck, 14) then
            AddValue(Gold, 1000)
            AddValue(MapVar(31), 1)
            SetAutonote(208) -- Well in the village of Blood Drop on Dagger Wound Island gives 1000 gold if Luck is greater than 14 and total gold on party and in the bank is less than 100.
        else
            evt.StatusText("Refreshing")
        end
    return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(104, "Drink from the fountain", function()
    if not IsAtLeast(MaxHealth, 0) then
        AddValue(CurrentHealth, 25)
        evt.StatusText("Your Wounds begin to Heal")
        SetAutonote(209) -- Fountain in the village of Blood Drop on Dagger Wound Island restores Hit Points.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the fountain")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(186)) then return end -- Obelisk Area 1
    evt.StatusText("summerday")
    SetAutonote(16) -- Obelisk message #9: summerday
    SetQBit(QBit(186)) -- Obelisk Area 1
end, "Obelisk")

RegisterEvent(171, "True Mettle", function()
    evt.EnterHouse(1) -- True Mettle
end, "True Mettle")

RegisterEvent(172, "True Mettle", nil, "True Mettle")

RegisterEvent(173, "The Tannery", function()
    evt.EnterHouse(36) -- The Tannery
end, "The Tannery")

RegisterEvent(174, "The Tannery", nil, "The Tannery")

RegisterEvent(175, "Fearsome Fetishes", function()
    evt.EnterHouse(76) -- Fearsome Fetishes
end, "Fearsome Fetishes")

RegisterEvent(176, "Fearsome Fetishes", nil, "Fearsome Fetishes")

RegisterEvent(177, "Herbal Elixirs", function()
    evt.EnterHouse(110) -- Herbal Elixirs
end, "Herbal Elixirs")

RegisterEvent(178, "Herbal Elixirs", nil, "Herbal Elixirs")

RegisterEvent(179, "Cures and Curses", function()
    evt.EnterHouse(182) -- Cures and Curses
end, "Cures and Curses")

RegisterEvent(180, "Cures and Curses", nil, "Cures and Curses")

RegisterEvent(183, "The Windling", function()
    evt.EnterHouse(479) -- The Windling
end, "The Windling")

RegisterEvent(184, "The Windling", nil, "The Windling")

RegisterEvent(185, "Mystic Medicine", function()
    evt.EnterHouse(303) -- Mystic Medicine
end, "Mystic Medicine")

RegisterEvent(186, "Mystic Medicine", nil, "Mystic Medicine")

RegisterEvent(187, "Rites of Passage", function()
    evt.EnterHouse(1564) -- Rites of Passage
end, "Rites of Passage")

RegisterEvent(188, "Rites of Passage", nil, "Rites of Passage")

RegisterEvent(191, "The Grog and Grub", function()
    evt.EnterHouse(228) -- The Grog and Grub
end, "The Grog and Grub")

RegisterEvent(192, "The Grog and Grub", nil, "The Grog and Grub")

RegisterEvent(193, "The Some Place Safe", function()
    evt.EnterHouse(281) -- The Some Place Safe
end, "The Some Place Safe")

RegisterEvent(194, "The Some Place Safe", nil, "The Some Place Safe")

RegisterEvent(197, "Clan Leader's Hall", function()
    evt.EnterHouse(212) -- Clan Leader's Hall
end, "Clan Leader's Hall")

RegisterEvent(198, "Clan Leader's Hall", nil, "Clan Leader's Hall")

RegisterEvent(199, "The Adventurer's Inn", function()
    evt.EnterHouse(1607) -- The Adventurer's Inn
end, "The Adventurer's Inn")

RegisterEvent(200, "The Adventurer's Inn", nil, "The Adventurer's Inn")

RegisterEvent(401, "Abandoned Temple", nil, "Abandoned Temple")

RegisterEvent(402, "Regnan Pirate Outpost", nil, "Regnan Pirate Outpost")

RegisterEvent(403, "Uplifted Library", nil, "Uplifted Library")

RegisterEvent(404, "Gate to the Plane of Earth", nil, "Gate to the Plane of Earth")

RegisterEvent(405, "Pirate Ship", nil, "Pirate Ship")

RegisterEvent(406, "Pirate Ship", nil, "Pirate Ship")

RegisterEvent(407, "Pirate Ship", nil, "Pirate Ship")

RegisterEvent(408, "Landing Craft", nil, "Landing Craft")

RegisterEvent(449, "Fountain", nil, "Fountain")

RegisterEvent(450, "Well", nil, "Well")

RegisterEvent(451, nil, function()
    evt.MoveToMap(-480, 5432, 384, 512, 0, 0, 0, 0)
end)

RegisterEvent(452, nil, function()
    evt.MoveToMap(10123, 4488, 736, 0, 0, 0, 0, 0)
end)

RegisterEvent(453, nil, function()
    if not IsQBitSet(QBit(1)) then -- Activate Area 1 teleporters 3 and 4.
        evt.ForPlayer(Players.All)
        if not HasItem(617) then -- Power Stone
            evt.StatusText("You need a power stone to operate this teleporter")
            return
        end
        if IsQBitSet(QBit(8)) then -- Fredrick Talimere visited by player with crystal in their possesion.
            RemoveItem(617) -- Power Stone
            SetQBit(QBit(1)) -- Activate Area 1 teleporters 3 and 4.
            evt.MoveToMap(-21528, -1384, 0, 512, 0, 0, 0, 0)
        end
        return
    end
    evt.MoveToMap(-21528, -1384, 0, 512, 0, 0, 0, 0)
end)

RegisterEvent(454, "Abandoned Temple", function()
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Abandoned Temple")

RegisterEvent(455, nil, function()
    evt.ForPlayer(Players.All)
    SetValue(Eradicated, 0)
end)

RegisterEvent(456, nil, function()
    local randomStep = PickRandomOption(456, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -9216, -12848, 3000) -- Meteor Shower
    elseif randomStep == 4 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -9232, -7680, 3000) -- Meteor Shower
    elseif randomStep == 6 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -5872, -8832, 3000) -- Meteor Shower
    elseif randomStep == 8 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -7200, -4656, 3000) -- Meteor Shower
    elseif randomStep == 10 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -4960, -3440, 3000) -- Meteor Shower
    elseif randomStep == 12 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -3472, -6544, 3000) -- Meteor Shower
    end
    local randomStep = PickRandomOption(456, 14, {14, 16, 18, 22, 24, 26})
    if randomStep == 14 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -96, -3568, 3000) -- Meteor Shower
    elseif randomStep == 16 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 3184, -976, 3000) -- Meteor Shower
    elseif randomStep == 18 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 912, 544, 3000) -- Meteor Shower
    elseif randomStep == 22 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 2976, 2240, 3000) -- Meteor Shower
    elseif randomStep == 24 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 6144, 832, 3000) -- Meteor Shower
    elseif randomStep == 26 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 9376, -4416, 3000) -- Meteor Shower
    end
    local randomStep = PickRandomOption(456, 28, {28, 30, 32, 34, 36, 38})
    if randomStep == 28 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 12256, -8640, 3000) -- Meteor Shower
    elseif randomStep == 30 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 5136, -14192, 3000) -- Meteor Shower
    elseif randomStep == 32 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 6320, -15840, 3000) -- Meteor Shower
    elseif randomStep == 34 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 7584, -20016, 3000) -- Meteor Shower
    elseif randomStep == 36 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, -3504, -15744, 3000) -- Meteor Shower
    elseif randomStep == 38 then
        evt.CastSpell(9, 3, 11, 19872, -19824, 5084, 560, -9776, 3000) -- Meteor Shower
    end
end)

RegisterEvent(457, "Fire the Cannon !", function()
    evt.CastSpell(6, 1, 2, 8704, 2000, 686, 8704, 1965, 686) -- Fireball
    evt.CastSpell(136, 1, 2, 8704, 1950, 686, 8704, -2592, 686)
end, "Fire the Cannon !")

RegisterEvent(458, "Fire the Cannon !", function()
    evt.CastSpell(6, 1, 2, 15872, 1500, 686, 15872, -1000, 686) -- Fireball
    evt.CastSpell(136, 1, 2, 15872, 1440, 686, 15872, -3100, 686)
end, "Fire the Cannon !")

RegisterEvent(459, "Fire the Cannon !", function()
    evt.CastSpell(6, 1, 2, 18400, 3584, 652, 18522, 3584, 652) -- Fireball
    evt.CastSpell(136, 1, 2, 18522, 3584, 652, 22880, 3584, 100)
end, "Fire the Cannon !")

RegisterEvent(460, nil, function()
    if IsQBitSet(QBit(6)) then return end -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
    if not evt.CheckMonstersKilled(ActorKillCheck.UniqueNameId, 8, 1, true) then -- unique actor 8 "Lizardman Lookout"; at least 1 matching actor defeated
        evt.CastSpell(6, 1, 2, 15872, 1500, 686, 15872, -1000, 686) -- Fireball
        evt.CastSpell(136, 1, 2, 15872, 1440, 686, 15872, -3100, 100)
    end
    if evt.CheckMonstersKilled(ActorKillCheck.UniqueNameId, 9, 1, true) then return end -- unique actor 9 "Lizardman Lookout"; at least 1 matching actor defeated
    evt.CastSpell(6, 1, 2, 1536, 16400, 682, 1536, 16480, 682) -- Fireball
    evt.CastSpell(136, 1, 2, 1536, 16480, 682, 1536, 21528, 100)
end)

RegisterEvent(461, "Fire the Cannon !", function()
    evt.CastSpell(6, 1, 2, 1536, 16400, 682, 1536, 16480, 682) -- Fireball
    evt.CastSpell(136, 1, 2, 1536, 16480, 682, 1536, 21528, 100)
end, "Fire the Cannon !")

RegisterEvent(462, "Fire the Cannon !", function()
    evt.CastSpell(6, 1, 2, -520, 15360, 682, -610, 15360, 682) -- Fireball
    evt.CastSpell(136, 1, 2, -610, 15360, 682, -6320, 15360, 100)
end, "Fire the Cannon !")

RegisterEvent(463, nil, function()
    if IsQBitSet(QBit(6)) then return end -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 10, 0, true) then -- actor group 10: spawn Wimpy Pirate Warrior Male A; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.Group, 11, 0, true) then -- actor group 11: spawn Wimpy Pirate Warrior Male A; all matching actors defeated
            if not evt.CheckMonstersKilled(ActorKillCheck.Group, 12, 0, true) then -- actor group 12: spawn Lizardmen Warrior A; all matching actors defeated
                if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
                    evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                    evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                    evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                    evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                end
                return
            end
            evt.SummonMonsters(1, 2, 3, 5208, -736, 46, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(5208, -736, 46), actor group 12: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, 3120, 800, 226, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3120, 800, 226), actor group 12: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, 3480, -2656, 88, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3480, -2656, 88), actor group 12: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, 2080, -2248, 539, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(2080, -2248, 539), actor group 12: spawn Lizardmen Warrior A, no unique actor name
            if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
                evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            end
            return
        end
        evt.SummonMonsters(2, 2, 3, -2744, 4864, 176, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-2744, 4864, 176), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
        evt.SummonMonsters(2, 2, 3, -2984, 4208, 561, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-2984, 4208, 561), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
        evt.SummonMonsters(2, 2, 3, -3624, 4280, 400, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-3624, 4280, 400), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
        evt.SummonMonsters(2, 2, 3, -3504, 4992, 74, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-3504, 4992, 74), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
        if not evt.CheckMonstersKilled(ActorKillCheck.Group, 12, 0, true) then -- actor group 12: spawn Lizardmen Warrior A; all matching actors defeated
            if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
                evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            end
            return
        end
        evt.SummonMonsters(1, 2, 3, 5208, -736, 46, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(5208, -736, 46), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, 3120, 800, 226, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3120, 800, 226), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, 3480, -2656, 88, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3480, -2656, 88), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, 2080, -2248, 539, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(2080, -2248, 539), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
            evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
        end
        return
    end
    evt.SummonMonsters(2, 2, 3, 776, -66192, 0, 10, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(776, -66192, 0), actor group 10: spawn Wimpy Pirate Warrior Male A, no unique actor name
    evt.SummonMonsters(2, 2, 3, 0, -5608, 0, 10, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(0, -5608, 0), actor group 10: spawn Wimpy Pirate Warrior Male A, no unique actor name
    evt.SummonMonsters(2, 2, 3, -656, -5696, 23, 10, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-656, -5696, 23), actor group 10: spawn Wimpy Pirate Warrior Male A, no unique actor name
    evt.SummonMonsters(2, 2, 3, -1280, -5720, 0, 10, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-1280, -5720, 0), actor group 10: spawn Wimpy Pirate Warrior Male A, no unique actor name
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 11, 0, true) then -- actor group 11: spawn Wimpy Pirate Warrior Male A; all matching actors defeated
        if not evt.CheckMonstersKilled(ActorKillCheck.Group, 12, 0, true) then -- actor group 12: spawn Lizardmen Warrior A; all matching actors defeated
            if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
                evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
                evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            end
            return
        end
        evt.SummonMonsters(1, 2, 3, 5208, -736, 46, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(5208, -736, 46), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, 3120, 800, 226, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3120, 800, 226), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, 3480, -2656, 88, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3480, -2656, 88), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, 2080, -2248, 539, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(2080, -2248, 539), actor group 12: spawn Lizardmen Warrior A, no unique actor name
        if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
            evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
        end
        return
    end
    evt.SummonMonsters(2, 2, 3, -2744, 4864, 176, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-2744, 4864, 176), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
    evt.SummonMonsters(2, 2, 3, -2984, 4208, 561, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-2984, 4208, 561), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
    evt.SummonMonsters(2, 2, 3, -3624, 4280, 400, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-3624, 4280, 400), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
    evt.SummonMonsters(2, 2, 3, -3504, 4992, 74, 11, 0) -- encounter slot 2 "Wimpy Pirate Warrior Male" tier B, count 3, pos=(-3504, 4992, 74), actor group 11: spawn Wimpy Pirate Warrior Male A, no unique actor name
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 12, 0, true) then -- actor group 12: spawn Lizardmen Warrior A; all matching actors defeated
        if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
            evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
            evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
        end
        return
    end
    evt.SummonMonsters(1, 2, 3, 5208, -736, 46, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(5208, -736, 46), actor group 12: spawn Lizardmen Warrior A, no unique actor name
    evt.SummonMonsters(1, 2, 3, 3120, 800, 226, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3120, 800, 226), actor group 12: spawn Lizardmen Warrior A, no unique actor name
    evt.SummonMonsters(1, 2, 3, 3480, -2656, 88, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(3480, -2656, 88), actor group 12: spawn Lizardmen Warrior A, no unique actor name
    evt.SummonMonsters(1, 2, 3, 2080, -2248, 539, 12, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(2080, -2248, 539), actor group 12: spawn Lizardmen Warrior A, no unique actor name
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 13, 0, true) then -- actor group 13: spawn Lizardmen Warrior A; all matching actors defeated
        evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-896, 55504, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-104, 5328, 384), actor group 13: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-880, 4464, 510), actor group 13: spawn Lizardmen Warrior A, no unique actor name
        evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0) -- encounter slot 1 "Lizardmen Warrior" tier B, count 3, pos=(-1256, 5296, 241), actor group 13: spawn Lizardmen Warrior A, no unique actor name
    end
end)

RegisterEvent(464, "Sealed Crate", nil, "Sealed Crate")

RegisterEvent(465, nil, function()
    if not IsQBitSet(QBit(1)) then -- Activate Area 1 teleporters 3 and 4.
        evt.ForPlayer(Players.All)
        if not HasItem(617) then -- Power Stone
            evt.StatusText("You need a power stone to operate this teleporter")
            return
        end
        if IsQBitSet(QBit(8)) then -- Fredrick Talimere visited by player with crystal in their possesion.
            RemoveItem(617) -- Power Stone
            SetQBit(QBit(1)) -- Activate Area 1 teleporters 3 and 4.
            evt.MoveToMap(-12496, -9728, 160, 512, 0, 0, 0, 0)
        end
        return
    end
    evt.MoveToMap(-12496, -9728, 160, 512, 0, 0, 0, 0)
end)

RegisterEvent(466, nil, function()
    if not IsQBitSet(QBit(2)) then -- Activate Area 1 teleporters 5 and 6.
        evt.ForPlayer(Players.All)
        if not HasItem(618) then -- Power Stone
            evt.StatusText("You need a power stone to operate this teleporter")
            return
        end
        RemoveItem(618) -- Power Stone
        SetQBit(QBit(2)) -- Activate Area 1 teleporters 5 and 6.
    end
    evt.MoveToMap(-13912, 14096, 0, 512, 0, 0, 0, 0)
end)

RegisterEvent(467, nil, function()
    if not IsQBitSet(QBit(2)) then -- Activate Area 1 teleporters 5 and 6.
        evt.ForPlayer(Players.All)
        if not HasItem(618) then -- Power Stone
            evt.StatusText("You need a power stone to operate this teleporter")
            return
        end
        RemoveItem(618) -- Power Stone
        SetQBit(QBit(2)) -- Activate Area 1 teleporters 5 and 6.
    end
    evt.MoveToMap(-18952, 8608, 96, 1536, 0, 0, 0, 0)
end)

RegisterEvent(468, nil, function()
    if IsQBitSet(QBit(6)) then return end -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
    local randomStep = PickRandomOption(468, 3, {3, 5, 7, 9, 11})
    if randomStep == 3 then
        evt.CastSpell(6, 1, 2, 16433, -3164, 180, 15920, 2850, 977) -- Fireball
    elseif randomStep == 5 then
        evt.CastSpell(6, 1, 2, 16298, -3164, 180, 14789, 3735, 705) -- Fireball
    elseif randomStep == 7 then
        evt.CastSpell(6, 1, 2, 16168, -3164, 180, 13056, 3752, 736) -- Fireball
    elseif randomStep == 9 then
        evt.CastSpell(6, 1, 2, 16041, -3164, 180, 15926, 1274, 420) -- Fireball
    end
end)

RegisterEvent(469, nil, function()
    if IsQBitSet(QBit(6)) then return end -- Pirate Leader in Dagger Wound Pirate Outpost killed (quest given at Q Bit 5). Ends pirate/lizardman war on Dagger Wound. Shuts off pirate timer.
    local randomStep = PickRandomOption(469, 3, {3, 5, 7, 9, 11})
    if randomStep == 3 then
        evt.CastSpell(6, 1, 2, 1496, 21593, 180, 15920, 2850, 977) -- Fireball
    elseif randomStep == 5 then
        evt.CastSpell(6, 1, 2, 1634, 21593, 180, 14789, 3735, 705) -- Fireball
    elseif randomStep == 7 then
        evt.CastSpell(6, 1, 2, 1729, 21593, 180, 13056, 3752, 736) -- Fireball
    elseif randomStep == 9 then
        evt.CastSpell(6, 1, 2, 1891, 21593, 180, 15926, 1274, 420) -- Fireball
    end
end)

RegisterEvent(470, nil, nil)

RegisterEvent(471, nil, function()
    evt.MoveToMap(8760, 4408, 736, 1536, 0, 0, 0, 0)
    if IsQBitSet(QBit(227)) then return end -- Turn on Temple Bypass tele in area one
    SetQBit(QBit(227)) -- Turn on Temple Bypass tele in area one
end)

RegisterEvent(472, nil, function()
    if IsQBitSet(QBit(227)) then -- Turn on Temple Bypass tele in area one
        evt.MoveToMap(21216, 18680, 0, 1024, 0, 0, 0, 0)
    end
end)

RegisterEvent(479, nil, function()
    PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
end)

RegisterEvent(494, "Palm tree", function()
    if IsQBitSet(QBit(270)) then -- Reagent spout area 1
        return
    elseif IsAtLeast(DisarmTrapSkill, 3) then
        local randomStep = PickRandomOption(494, 4, {5, 7, 9, 11, 13})
        if randomStep == 5 then
            evt.SummonItem(200, 3896, 8080, 544, 1000, 1, true) -- Widowsweep Berries
        elseif randomStep == 7 then
            evt.SummonItem(205, 3896, 8080, 544, 1000, 1, true) -- Phima Root
        elseif randomStep == 9 then
            evt.SummonItem(210, 3896, 8080, 544, 1000, 1, true) -- Poppy Pod
        elseif randomStep == 11 then
            evt.SummonItem(215, 3896, 8080, 544, 1000, 1, true) -- Mushroom
        elseif randomStep == 13 then
            evt.SummonItem(220, 3896, 8080, 544, 1000, 1, true) -- Potion Bottle
        end
        SetQBit(QBit(270)) -- Reagent spout area 1
        return
    else
        return
    end
end, "Palm tree")

RegisterEvent(495, "Flower", function()
    if IsQBitSet(QBit(271)) then return end -- Reagent spout area 1
    if not IsAtLeast(DisarmTrapSkill, 5) then return end
    local randomStep = PickRandomOption(495, 4, {5, 7, 9, 11})
    if randomStep == 5 then
        evt.SummonItem(2138, -18832, 5840, 330, 1000, 1, true) -- Diary Page
    elseif randomStep == 7 then
        evt.SummonItem(2139, -18832, 5840, 330, 1000, 1, true) -- Page from Agar's Journal
    elseif randomStep == 9 then
        evt.SummonItem(2140, -18832, 5840, 330, 1000, 1, true) -- Remains of a Journal
    elseif randomStep == 11 then
        evt.SummonItem(2141, -18832, 5840, 330, 1000, 1, true) -- Letter from the Dragon Riders
    end
    SetQBit(QBit(271)) -- Reagent spout area 1
end, "Flower")

RegisterEvent(497, "Buoy", function()
    if IsQBitSet(QBit(268)) then return end -- Area 1 buoy
    if IsAtLeast(BaseLuck, 13) then
        SetQBit(QBit(268)) -- Area 1 buoy
        AddValue(SkillPoints, 2)
    end
end, "Buoy")

RegisterEvent(498, "Buoy", function()
    if IsQBitSet(QBit(269)) then return end -- Area 1 buoy
    if IsAtLeast(BaseLuck, 20) then
        SetQBit(QBit(269)) -- Area 1 buoy
        AddValue(SkillPoints, 5)
    end
end, "Buoy")

RegisterEvent(500, nil, function()
    if IsQBitSet(QBit(232)) then return end -- Set when you talk to S'ton
    SetQBit(QBit(232)) -- Set when you talk to S'ton
    evt.SpeakNPC(27) -- S'ton
end)

RegisterEvent(501, "Enter the Abandoned Temple", function()
    evt.MoveToMap(-3008, -1696, 2464, 512, 0, 0, 346, 1, "d05.blv") -- Abandoned Temple
end, "Enter the Abandoned Temple")

RegisterEvent(502, "Enter the Regnan Pirate Outpost", function()
    evt.MoveToMap(-7, -714, 1, 512, 0, 0, 349, 1, "d06.blv") -- Pirate Outpost
end, "Enter the Regnan Pirate Outpost")

RegisterEvent(503, "Enter the Uplifted Library", function()
    evt.MoveToMap(-592, 624, 0, 0, 0, 0, 0, 1, "d40.blv") -- Uplifted Library
end, "Enter the Uplifted Library")

RegisterEvent(504, "Enter the Abandoned Temple", function()
    evt.MoveToMap(12704, 2432, 385, 0, 0, 0, 346, 1, "d05.blv") -- Abandoned Temple
end, "Enter the Abandoned Temple")

RegisterEvent(505, "Enter the Plane of Earth", function()
    evt.MoveToMap(0, 0, 49, 512, 0, 0, 352, 1, "eleme.blv") -- Plane of Earth
end, "Enter the Plane of Earth")

