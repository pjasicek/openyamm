-- Regna
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
    [11] = { kind = "enter_house", source = "opcode", houseId = 645, targetName = "Dragontracker Hall" },
    [13] = { kind = "enter_house", source = "opcode", houseId = 646, targetName = "Nirses Loot" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 647, targetName = "Burnkindle's Spoils" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 648, targetName = "Cleareye Hall" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 649, targetName = "Shadowrunner's Vault" },
    [21] = { kind = "enter_house", source = "opcode", houseId = 650, targetName = "Lifter's Lockup" },
    [23] = { kind = "enter_house", source = "opcode", houseId = 651, targetName = "Steelcoif Hall" },
    [25] = { kind = "enter_house", source = "opcode", houseId = 652, targetName = "Jawblower Manor" },
    [27] = { kind = "enter_house", source = "opcode", houseId = 653, targetName = "Marmon Domicile" },
    [29] = { kind = "enter_house", source = "opcode", houseId = 654, targetName = "One-eye's Lair" },
    [31] = { kind = "enter_house", source = "opcode", houseId = 655, targetName = "Paul's Estate" },
    [33] = { kind = "enter_house", source = "opcode", houseId = 656, targetName = "Terrence's Home" },
    [35] = { kind = "enter_house", source = "opcode", houseId = 657, targetName = "Ferne Lair" },
    [37] = { kind = "enter_house", source = "opcode", houseId = 658, targetName = "Pavel's Place" },
    [39] = { kind = "enter_house", source = "opcode", houseId = 659, targetName = "Nalani's Hall" },
    [41] = { kind = "enter_house", source = "opcode", houseId = 660, targetName = "Mercer Domicile" },
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
    [104] = { kind = "fountain", source = "title" },
    [150] = { kind = "obelisk", source = "title" },
    [171] = { kind = "enter_house", source = "opcode", houseId = 7, targetName = "Custom Cutlass" },
    [173] = { kind = "enter_house", source = "opcode", houseId = 42, targetName = "Karr Battlegear" },
    [175] = { kind = "enter_house", source = "opcode", houseId = 82, targetName = "Gifts of Regna" },
    [177] = { kind = "enter_house", source = "opcode", houseId = 114, targetName = "Poultices and Cures" },
    [179] = { kind = "enter_house", source = "opcode", houseId = 185, targetName = "Protective Magic" },
    [183] = { kind = "enter_house", source = "opcode", houseId = 484, targetName = "Spindrift" },
    [185] = { kind = "enter_house", source = "opcode", houseId = 309, targetName = "The Blessed Sea" },
    [191] = { kind = "enter_house", source = "opcode", houseId = 236, targetName = "Pirate's Rest" },
    [451] = { kind = "generic_event", source = "opcode" },
    [453] = { kind = "secret_event", source = "heuristic", hidden = true },
    [490] = { kind = "open_door", source = "title" },
    [501] = { kind = "enter_dungeon", source = "opcode", targetMap = "d31.blv", targetName = "Pirate Stronghold" },
    [502] = { kind = "enter_dungeon", source = "opcode", targetMap = "d32.blv", targetName = "Abandoned Pirate Keep" },
    [503] = { kind = "enter_dungeon", source = "opcode", targetMap = "d33.blv", targetName = "Passage Under Regna" },
    [504] = { kind = "enter_dungeon", source = "opcode", targetMap = "d34.blv", targetName = "Small Sub Pen" },
    [505] = { kind = "enter_dungeon", source = "opcode", targetMap = "d47.blv", targetName = "Old Loeb's Cave" },
    [506] = { kind = "enter_dungeon", source = "opcode", targetMap = "d33.blv", targetName = "Passage Under Regna" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 9, 18, 43},
    timers = {
    { eventId = 452, sourceEventId = 452, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 2 },
    { eventId = 479, sourceEventId = 479, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    },
})

RegisterNoOpEvent(1, nil)

RegisterNoOpEvent(2, nil)

RegisterNoOpEvent(3, nil)

RegisterNoOpEvent(4, nil)

RegisterNoOpEvent(6, nil)

RegisterNoOpEvent(7, nil)

RegisterNoOpEvent(8, nil)

RegisterNoOpEvent(9, nil)

RegisterNoOpEvent(10, nil)

RegisterEvent(11, "Dragontracker Hall", function()
    evt.EnterHouse(645) -- Dragontracker Hall
end, "Dragontracker Hall")

RegisterEvent(12, "Dragontracker Hall", nil, "Dragontracker Hall")

RegisterEvent(13, "Nirses Loot", function()
    evt.EnterHouse(646) -- Nirses Loot
end, "Nirses Loot")

RegisterEvent(14, "Nirses Loot", nil, "Nirses Loot")

RegisterEvent(15, "Burnkindle's Spoils", function()
    evt.EnterHouse(647) -- Burnkindle's Spoils
end, "Burnkindle's Spoils")

RegisterEvent(16, "Burnkindle's Spoils", nil, "Burnkindle's Spoils")

RegisterEvent(17, "Cleareye Hall", function()
    evt.EnterHouse(648) -- Cleareye Hall
end, "Cleareye Hall")

RegisterEvent(18, "Cleareye Hall", nil, "Cleareye Hall")

RegisterEvent(19, "Shadowrunner's Vault", function()
    evt.EnterHouse(649) -- Shadowrunner's Vault
end, "Shadowrunner's Vault")

RegisterEvent(20, "Shadowrunner's Vault", nil, "Shadowrunner's Vault")

RegisterEvent(21, "Lifter's Lockup", function()
    evt.EnterHouse(650) -- Lifter's Lockup
end, "Lifter's Lockup")

RegisterEvent(22, "Lifter's Lockup", nil, "Lifter's Lockup")

RegisterEvent(23, "Steelcoif Hall", function()
    evt.EnterHouse(651) -- Steelcoif Hall
end, "Steelcoif Hall")

RegisterEvent(24, "Steelcoif Hall", nil, "Steelcoif Hall")

RegisterEvent(25, "Jawblower Manor", function()
    evt.EnterHouse(652) -- Jawblower Manor
end, "Jawblower Manor")

RegisterEvent(26, "Jawblower Manor", nil, "Jawblower Manor")

RegisterEvent(27, "Marmon Domicile", function()
    evt.EnterHouse(653) -- Marmon Domicile
end, "Marmon Domicile")

RegisterEvent(28, "Marmon Domicile", nil, "Marmon Domicile")

RegisterEvent(29, "One-eye's Lair", function()
    evt.EnterHouse(654) -- One-eye's Lair
end, "One-eye's Lair")

RegisterEvent(30, "One-eye's Lair", nil, "One-eye's Lair")

RegisterEvent(31, "Paul's Estate", function()
    evt.EnterHouse(655) -- Paul's Estate
end, "Paul's Estate")

RegisterEvent(32, "Paul's Estate", nil, "Paul's Estate")

RegisterEvent(33, "Terrence's Home", function()
    evt.EnterHouse(656) -- Terrence's Home
end, "Terrence's Home")

RegisterEvent(34, "Terrence's Home", nil, "Terrence's Home")

RegisterEvent(35, "Ferne Lair", function()
    evt.EnterHouse(657) -- Ferne Lair
end, "Ferne Lair")

RegisterEvent(36, "Ferne Lair", nil, "Ferne Lair")

RegisterEvent(37, "Pavel's Place", function()
    evt.EnterHouse(658) -- Pavel's Place
end, "Pavel's Place")

RegisterEvent(38, "Pavel's Place", nil, "Pavel's Place")

RegisterEvent(39, "Nalani's Hall", function()
    evt.EnterHouse(659) -- Nalani's Hall
end, "Nalani's Hall")

RegisterEvent(40, "Nalani's Hall", nil, "Nalani's Hall")

RegisterEvent(41, "Mercer Domicile", function()
    evt.EnterHouse(660) -- Mercer Domicile
end, "Mercer Domicile")

RegisterEvent(42, "Mercer Domicile", nil, "Mercer Domicile")

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

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
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
    if not IsAtLeast(BaseSpeed, 16) then
        AddValue(BaseSpeed, 2)
        evt.StatusText("Speed +2 (Permanent)")
        SetAutonote(232) -- Well on the Island of Regna gives a permanent Speed bonus up to a Speed of 16.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(104, "Drink from the fountain", function()
    evt.StatusText("Refreshing")
    if IsQBitSet(QBit(304)) then return end -- TP Buff Regna
    SetQBit(QBit(304)) -- TP Buff Regna
end, "Drink from the fountain")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(194)) then return end -- Obelisk Area 13
    evt.StatusText("gholdsold")
    SetAutonote(9) -- Obelisk message #2: gholdsold
    SetQBit(QBit(194)) -- Obelisk Area 13
end, "Obelisk")

RegisterEvent(171, "Custom Cutlass", function()
    evt.EnterHouse(7) -- Custom Cutlass
end, "Custom Cutlass")

RegisterEvent(172, "Custom Cutlass", nil, "Custom Cutlass")

RegisterEvent(173, "Karr Battlegear", function()
    evt.EnterHouse(42) -- Karr Battlegear
end, "Karr Battlegear")

RegisterEvent(174, "Karr Battlegear", nil, "Karr Battlegear")

RegisterEvent(175, "Gifts of Regna", function()
    evt.EnterHouse(82) -- Gifts of Regna
end, "Gifts of Regna")

RegisterEvent(176, "Gifts of Regna", nil, "Gifts of Regna")

RegisterEvent(177, "Poultices and Cures", function()
    evt.EnterHouse(114) -- Poultices and Cures
end, "Poultices and Cures")

RegisterEvent(178, "Poultices and Cures", nil, "Poultices and Cures")

RegisterEvent(179, "Protective Magic", function()
    evt.EnterHouse(185) -- Protective Magic
end, "Protective Magic")

RegisterEvent(180, "Protective Magic", nil, "Protective Magic")

RegisterEvent(183, "Spindrift", function()
    evt.EnterHouse(484) -- Spindrift
end, "Spindrift")

RegisterEvent(184, "Spindrift", nil, "Spindrift")

RegisterEvent(185, "The Blessed Sea", function()
    evt.EnterHouse(309) -- The Blessed Sea
end, "The Blessed Sea")

RegisterEvent(186, "The Blessed Sea", nil, "The Blessed Sea")

RegisterEvent(191, "Pirate's Rest", function()
    evt.EnterHouse(236) -- Pirate's Rest
end, "Pirate's Rest")

RegisterEvent(192, "Pirate's Rest", nil, "Pirate's Rest")

RegisterEvent(401, "Pirate Stronghold", nil, "Pirate Stronghold")

RegisterEvent(402, "Abandoned Pirate Keep", nil, "Abandoned Pirate Keep")

RegisterEvent(403, "Tower", nil, "Tower")

RegisterEvent(404, "Small Sub Pen", nil, "Small Sub Pen")

RegisterEvent(405, "A Cave", nil, "A Cave")

RegisterEvent(406, "Regnan Ship", nil, "Regnan Ship")

RegisterEvent(407, "Sunk Regnan Ship", nil, "Sunk Regnan Ship")

RegisterEvent(449, "Fountain", nil, "Fountain")

RegisterEvent(450, "Well", nil, "Well")

RegisterEvent(451, "Fire the cannon !", function()
    if not IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
        evt.ForPlayer(Players.All)
        if HasItem(662) then -- Cannonball of Dominion
            RemoveItem(662) -- Cannonball of Dominion
            evt.ForPlayer(Players.Current)
            evt.StatusText("You hear a low rumbling noise")
            AddValue(MapVar(41), 1)
            evt.PlaySound(473, -12945, 12015)
            ClearQBit(QBit(224)) -- Cannonball of Dominion - I lost it
            return
        end
    end
    evt.StatusText("You do not see the right kind of ammunition anywhere")
end, "Fire the cannon !")

RegisterEvent(452, nil, function()
    if IsQBitSet(QBit(37)) then -- Regnan Pirate Fleet is sunk.
        return
    elseif IsAtLeast(MapVar(41), 3) then
        SetQBit(QBit(37)) -- Regnan Pirate Fleet is sunk.
        evt.MoveNPC(64, 899) -- Derrin Delver -> Hostel
        evt.MoveNPC(20, 900) -- Queen Catherine -> Hostel
        evt.MoveNPC(21, 900) -- King Roland -> Hostel
        AddValue(History(15), 0)
        SetValue(MapVar(41), 0)
        evt.SetFacetBit(31, FacetBits.Invisible, 0)
        evt.SetFacetBit(31, FacetBits.Untouchable, 0)
        evt.SetFacetBit(30, FacetBits.Invisible, 1)
        evt.SetFacetBit(30, FacetBits.Untouchable, 1)
        return
    elseif IsAtLeast(MapVar(41), 2) then
        AddValue(MapVar(41), 1)
        evt.CastSpell(9, 3, 4, -19692, 14204, 4000, -19692, 14204, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -16984, 15783, 4000, -16984, 15783, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -12333, 18364, 4000, -12333, 18364, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -13102, 20346, 4000, -13102, 20346, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -15489, 18406, 4000, -15489, 18406, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -19300, 18374, 4000, -19300, 18374, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -17229, 20297, 4000, -17229, 20297, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -13235, 20616, 4000, -13235, 20616, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -16787, 13839, 4000, -16787, 13839, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -12748, 14383, 4000, -12748, 14383, 0) -- Meteor Shower
        evt.CastSpell(9, 3, 4, -15107, 13092, 4000, -15107, 13092, 0) -- Meteor Shower
        evt.CastSpell(18, 3, 4, -16984, 15783, 4000, -16984, 15783, 0) -- Lightning Bolt
        evt.CastSpell(18, 3, 4, -12333, 18364, 4000, -12333, 18364, 0) -- Lightning Bolt
        evt.CastSpell(18, 3, 4, -13102, 20346, 4000, -13102, 20346, 0) -- Lightning Bolt
        evt.CastSpell(18, 3, 4, -15489, 18406, 4000, -15489, 18406, 0) -- Lightning Bolt
        evt.CastSpell(18, 3, 4, -19300, 18374, 4000, -19300, 18374, 0) -- Lightning Bolt
        evt.CastSpell(18, 3, 4, -17229, 20297, 4000, -17229, 20297, 0) -- Lightning Bolt
        evt.CastSpell(18, 3, 4, -13235, 20616, 4000, -13235, 20616, 0) -- Lightning Bolt
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -15743, 15989, 2731) -- Death Blossom
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -12022, 19402, 2728) -- Death Blossom
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -13168, 15608, 2725) -- Death Blossom
        evt.CastSpell(43, 3, 4, -13312, 12864, 2432, -14622, 15778, 2724) -- Death Blossom
        return
    elseif IsAtLeast(MapVar(41), 1) then
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13740, 2793) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13600, 13740, 2793) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13250, 13740, 2793) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13600, 2793) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13820, 3000) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13740, 2250) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13800, 2500) -- Fireball
        evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13100, 13740, 3000) -- Fireball
        AddValue(MapVar(41), 1)
        evt._SpecialJump(16778952, 208)
        evt.PlaySound(472, -13305, 12958)
        return
    else
        return
    end
end)

RegisterEvent(453, nil, function()
    evt.CastSpell(6, 3, 4, -13312, 12864, 2432, -13371, 13740, 2793) -- Fireball
end)

RegisterEvent(454, "Tree", function()
    if IsQBitSet(QBit(285)) then return end -- Got the Tele scroll in area 13
    AddValue(InventoryItem(341), 341) -- Telekinesis
    SetQBit(QBit(285)) -- Got the Tele scroll in area 13
end, "Tree")

RegisterEvent(479, nil, function()
    local randomStep = PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.PlaySound(351, -11712, -10784)
    elseif randomStep == 4 then
        evt.PlaySound(351, 5568, -16352)
    elseif randomStep == 6 then
        evt.PlaySound(351, -1248, 12480)
    elseif randomStep == 8 then
        evt.PlaySound(336, -800, -2432)
    elseif randomStep == 10 then
        evt.PlaySound(338, 3704, 1024)
    end
end)

RegisterEvent(490, "Door", function()
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    evt.StatusText("The door is locked")
end, "Door")

RegisterEvent(494, "Tree", function()
    if evt.CheckItemsCount(221, 271, 1) then
        evt.RemoveItems(221, 271, 1)
        AddValue(InventoryItem(220), 220) -- Potion Bottle
    end
end, "Tree")

RegisterEvent(501, "Enter the Pirate Stronghold", function()
    evt.MoveToMap(-554, 3682, 1, 520, 0, 0, 368, 1, "d31.blv") -- Pirate Stronghold
end, "Enter the Pirate Stronghold")

RegisterEvent(502, "Enter the Abandoned Pirate Keep", function()
    evt.MoveToMap(-6520, -6512, 129, 1024, 0, 0, 369, 1, "d32.blv") -- Abandoned Pirate Keep
end, "Enter the Abandoned Pirate Keep")

RegisterEvent(503, "Enter the Tower", function()
    if not IsQBitSet(QBit(197)) then -- Door to the passage under regna from the northern watch tower is unlocked
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(5892, 4632, 1853, 1536, 0, 0, 0, 1, "d33.blv") -- Passage Under Regna
end, "Enter the Tower")

RegisterEvent(504, "Enter the Cave", function()
    evt.MoveToMap(-28, -193, 57, 1024, 0, 0, 370, 3, "d34.blv") -- Small Sub Pen
end, "Enter the Cave")

RegisterEvent(505, "Enter the Cave", function()
    evt.MoveToMap(1328, -1576, 4, 1536, 0, 0, 0, 1, "d47.blv") -- Old Loeb's Cave
end, "Enter the Cave")

RegisterEvent(506, "Enter the Tower", function()
    if not IsQBitSet(QBit(198)) then -- Door to the passage under regna from the southern watch tower is unlocked
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(1926, -7682, 1572, 0, 0, 0, 0, 1, "d33.blv") -- Passage Under Regna
end, "Enter the Tower")

