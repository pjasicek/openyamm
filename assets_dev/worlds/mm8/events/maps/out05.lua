-- Garrote Gorge
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
    { eventId = 131, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    { eventId = 479, repeating = true, intervalGameMinutes = 12.5, remainingGameMinutes = 12.5 },
    { eventId = 490, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.SetMonGroupBit(22, MonsterBits.Hostile, 1) -- actor group 22: spawn Dragon Hunter A
        evt.SetMonGroupBit(23, MonsterBits.Hostile, 1) -- actor group 23: spawn Dragon Hunter A
        evt.SetMonGroupBit(24, MonsterBits.Hostile, 1) -- actor group 24: Dragonslayer, spawn Dragon Hunter A, spawn Dragon Hunter B
        return
    elseif IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: spawn Wimpy Dragon A
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
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

RegisterEvent(11, "Stormlance Residence", function()
    evt.EnterHouse(538) -- Stormlance Residence
end, "Stormlance Residence")

RegisterEvent(12, "Stormlance Residence", nil, "Stormlance Residence")

RegisterEvent(13, "Morningstar Residence", function()
    evt.EnterHouse(539) -- Morningstar Residence
end, "Morningstar Residence")

RegisterEvent(14, "Morningstar Residence", nil, "Morningstar Residence")

RegisterEvent(15, "Foestryke Residence", function()
    evt.EnterHouse(540) -- Foestryke Residence
end, "Foestryke Residence")

RegisterEvent(16, "Foestryke Residence", nil, "Foestryke Residence")

RegisterEvent(17, "Ironfist Residence", function()
    evt.EnterHouse(541) -- Ironfist Residence
end, "Ironfist Residence")

RegisterEvent(18, "Ironfist Residence", nil, "Ironfist Residence")

RegisterEvent(19, "Avalon's Residence", function()
    evt.EnterHouse(562) -- Avalon's Residence
end, "Avalon's Residence")

RegisterEvent(20, "Avalon's Residence", nil, "Avalon's Residence")

RegisterEvent(21, "Arin Residence", function()
    evt.EnterHouse(563) -- Arin Residence
end, "Arin Residence")

RegisterEvent(22, "Arin Residence", nil, "Arin Residence")

RegisterEvent(23, "Lightsworn Residence", function()
    evt.EnterHouse(564) -- Lightsworn Residence
end, "Lightsworn Residence")

RegisterEvent(24, "Lightsworn Residence", nil, "Lightsworn Residence")

RegisterEvent(25, "Otterton Residence", function()
    evt.EnterHouse(565) -- Otterton Residence
end, "Otterton Residence")

RegisterEvent(26, "Otterton Residence", nil, "Otterton Residence")

RegisterEvent(27, "Calandril's Residence", function()
    evt.EnterHouse(566) -- Calandril's Residence
end, "Calandril's Residence")

RegisterEvent(28, "Calandril's Residence", nil, "Calandril's Residence")

RegisterEvent(29, "Maker Residence", function()
    evt.EnterHouse(567) -- Maker Residence
end, "Maker Residence")

RegisterEvent(30, "Maker Residence", nil, "Maker Residence")

RegisterEvent(31, "Slayer Residence", function()
    evt.EnterHouse(568) -- Slayer Residence
end, "Slayer Residence")

RegisterEvent(32, "Slayer Residence", nil, "Slayer Residence")

RegisterEvent(33, "Kern Residence", function()
    evt.EnterHouse(569) -- Kern Residence
end, "Kern Residence")

RegisterEvent(34, "Kern Residence", nil, "Kern Residence")

RegisterEvent(35, "Jeni Residence", function()
    evt.EnterHouse(570) -- Jeni Residence
end, "Jeni Residence")

RegisterEvent(36, "Jeni Residence", nil, "Jeni Residence")

RegisterEvent(37, "Weldrick's Home", function()
    evt.EnterHouse(571) -- Weldrick's Home
end, "Weldrick's Home")

RegisterEvent(38, "Weldrick's Home", nil, "Weldrick's Home")

RegisterEvent(39, "Nelix's House", function()
    evt.EnterHouse(699) -- Nelix's House
end, "Nelix's House")

RegisterEvent(40, "Nelix's House", nil, "Nelix's House")

RegisterEvent(41, "Tempus' House", function()
    evt.EnterHouse(700) -- Tempus' House
end, "Tempus' House")

RegisterEvent(42, "Tempus' House", nil, "Tempus' House")

RegisterEvent(43, "Reaverston Residence", function()
    evt.EnterHouse(542) -- Reaverston Residence
end, "Reaverston Residence")

RegisterEvent(44, "Reaverston Residence", nil, "Reaverston Residence")

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

RegisterEvent(91, "Flowers", function()
    evt.OpenChest(10)
end, "Flowers")

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
    if not IsAtLeast(MapVar(31), 2) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(BankGold, 99) then
            evt.StatusText("Refreshing")
        else
            AddValue(Gold, 200)
            AddValue(MapVar(31), 1)
            SetAutonote(217) -- Well at the Dragon Hunters Camp in Garrote Gorge gives 200 gold if the total gold on party and in the bank is less than 100.
        end
    return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(FireResistance, 10) then
        AddValue(FireResistance, 2)
        evt.StatusText("Fire Resistance +2 (Permanent)")
        SetAutonote(218) -- Well at the Dragon Hunters Camp in Garrote Gorge gives a permanent Fire Resistance bonus up to a Fire Resistance of 10.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    if not IsAtLeast(BaseAccuracy, 16) then
        AddValue(BaseAccuracy, 2)
        evt.StatusText("Accuracy +2 (Permanent)")
        SetAutonote(219) -- Well at the Dragon Hunters Camp in Garrote Gorge gives a permanent Accuracy bonus up to an Accuracy of 16.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(131, "Legacy event 131", function()
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        goto step_18
    end
    if IsQBitSet(QBit(155)) then -- Killed all Dragons in Garrote Gorge Area
        goto step_18
    end
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 189, 0, false) then -- monster 189 "Hatchling"; all matching actors defeated
        goto step_5
    end
    goto step_18
    ::step_5::
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 190, 0, false) then -- monster 190 "Dragonette"; all matching actors defeated
        goto step_7
    end
    goto step_18
    ::step_7::
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 191, 0, false) then -- monster 191 "Young Dragon"; all matching actors defeated
        goto step_9
    end
    goto step_18
    ::step_9::
    if IsQBitSet(QBit(156)) then -- Questbit set for Riki
        goto step_14
    end
    SetQBit(QBit(156)) -- Questbit set for Riki
    evt.SummonMonsters(2, 1, 1, -30272, -16512, 0, 1, 0) -- encounter slot 2 "Wimpy Dragon" tier A, count 1, pos=(-30272, -16512, 0), actor group 1, no unique actor name
    evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
    goto step_18
    ::step_14::
    SetQBit(QBit(155)) -- Killed all Dragons in Garrote Gorge Area
    SetQBit(QBit(225)) -- dead questbit for internal use(bling)
    ClearQBit(QBit(225)) -- dead questbit for internal use(bling)
    evt.StatusText("You have killed all of the Dragons")
    ::step_18::
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        goto step_35
    end
    if IsQBitSet(QBit(158)) then -- Killed all Dragon Hunters in Garrote Gorge wilderness area
        goto step_35
    end
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 42, 0, false) then -- monster 42 "Dragon Hunter"; all matching actors defeated
        goto step_22
    end
    goto step_35
    ::step_22::
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 43, 0, false) then -- monster 43 "Crusader"; all matching actors defeated
        goto step_24
    end
    goto step_35
    ::step_24::
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 44, 0, false) then -- monster 44 "Dragonslayer"; all matching actors defeated
        goto step_26
    end
    goto step_35
    ::step_26::
    if IsQBitSet(QBit(159)) then -- Questbit set for Riki
        goto step_31
    end
    SetQBit(QBit(159)) -- Questbit set for Riki
    evt.SummonMonsters(3, 1, 1, -30272, -16512, 0, 2, 0) -- encounter slot 3 "Dragon Hunter" tier A, count 1, pos=(-30272, -16512, 0), actor group 2, no unique actor name
    evt.SetMonGroupBit(2, MonsterBits.Invisible, 1)
    goto step_35
    ::step_31::
    SetQBit(QBit(158)) -- Killed all Dragon Hunters in Garrote Gorge wilderness area
    SetQBit(QBit(225)) -- dead questbit for internal use(bling)
    ClearQBit(QBit(225)) -- dead questbit for internal use(bling)
    evt.StatusText("You have killed all of the Dragon Hunters")
    ::step_35::
    if IsQBitSet(QBit(75)) then -- Killed all Dragon Slayers in southwest encampment in Area 5
        goto step_39
    end
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 24, 0, false) then -- actor group 24: Dragonslayer, spawn Dragon Hunter A, spawn Dragon Hunter B; all matching actors defeated
        SetQBit(QBit(75)) -- Killed all Dragon Slayers in southwest encampment in Area 5
    end
    ::step_39::
    if IsQBitSet(QBit(200)) then -- Sword of Whistlebone - I lost it
        goto step_43
    end
    if evt.CheckMonstersKilled(ActorKillCheck.UniqueNameId, 2, 1, false) then -- unique actor 2 "Jeric Whistlebone"; at least 1 matching actor defeated
        goto step_42
    end
    goto step_43
    ::step_42::
    SetQBit(QBit(200)) -- Sword of Whistlebone - I lost it
    ::step_43::
    do return end
end)

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(190)) then return end -- Obelisk Area 5
    evt.StatusText("theunicornkin")
    SetAutonote(8) -- Obelisk message #1: theunicornkin
    SetQBit(QBit(190)) -- Obelisk Area 5
end, "Obelisk")

RegisterEvent(171, "Lance's Spears", function()
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.EnterHouse(4) -- Lance's Spears
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Lance's Spears")

RegisterEvent(172, "Lance's Spears", nil, "Lance's Spears")

RegisterEvent(173, "Plated Protection", function()
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.EnterHouse(39) -- Plated Protection
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Plated Protection")

RegisterEvent(174, "Plated Protection", nil, "Plated Protection")

RegisterEvent(175, "Wards and Pendants", function()
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.EnterHouse(79) -- Wards and Pendants
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Wards and Pendants")

RegisterEvent(176, "Wards and Pendants", nil, "Wards and Pendants")

RegisterEvent(181, "Guild Caravans", function()
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.EnterHouse(455) -- Guild Caravans
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Guild Caravans")

RegisterEvent(182, "Guild Caravans", nil, "Guild Caravans")

RegisterEvent(185, "Sacred Steel", function()
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.EnterHouse(306) -- Sacred Steel
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Sacred Steel")

RegisterEvent(186, "Sacred Steel", nil, "Sacred Steel")

RegisterEvent(187, "Godric's Gauntlet", function()
    if not IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.EnterHouse(1567) -- Godric's Gauntlet
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Godric's Gauntlet")

RegisterEvent(188, "Godric's Gauntlet", nil, "Godric's Gauntlet")

RegisterEvent(191, "Dragon's Blood Inn", function()
    evt.EnterHouse(232) -- Dragon's Blood Inn
end, "Dragon's Blood Inn")

RegisterEvent(192, "Dragon's Blood Inn", nil, "Dragon's Blood Inn")

RegisterEvent(401, "Dragon Hunter Camp", nil, "Dragon Hunter Camp")

RegisterEvent(402, "Dragon Cave", nil, "Dragon Cave")

RegisterEvent(403, "Naga Vault", nil, "Naga Vault")

RegisterEvent(404, "Grand Temple of Eep", nil, "Grand Temple of Eep")

RegisterEvent(405, "Tent", nil, "Tent")

RegisterEvent(450, "Well", nil, "Well")

RegisterEvent(479, "Legacy event 479", function()
    PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
end)

RegisterEvent(490, "Legacy event 490", function()
    local randomStep = PickRandomOption(490, 2, {2, 2, 3, 3, 3, 3})
    if randomStep == 2 then
        evt.PlaySound(325, 11520, -13664)
    end
end)

RegisterEvent(501, "Enter the Dragon Hunter's Camp", function()
    evt.MoveToMap(-1216, 1888, 1, 1536, 0, 0, 361, 1, "d16.blv") -- Dragon Hunter's Camp
end, "Enter the Dragon Hunter's Camp")

RegisterEvent(502, "Enter the Dragon Cave", function()
    evt.MoveToMap(223, -8, 170, 1088, 0, 0, 362, 1, "d17.blv") -- Dragon Cave
end, "Enter the Dragon Cave")

RegisterEvent(503, "Enter the Naga Vault", function()
    evt.MoveToMap(-500, -1567, -63, 512, 0, 0, 363, 1, "d18.blv") -- Naga Vault
end, "Enter the Naga Vault")

RegisterEvent(504, "Enter the Grand Temple of Eep", function()
    evt.MoveToMap(-2812, 726, 1, 1536, 0, 0, 0, 1, "d44.blv") -- Grand Temple of Eep
end, "Enter the Grand Temple of Eep")

