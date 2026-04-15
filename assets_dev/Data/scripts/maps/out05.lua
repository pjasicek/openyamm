-- Garrote Gorge
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4},
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
    if IsQBitSet(QBit(22)) then
        evt.SetMonGroupBit(22, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(23, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(24, MonsterBits.Hostile, 1)
        return
    elseif IsQBitSet(QBit(21)) then
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 1)
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
    evt.EnterHouse(316) -- Stormlance Residence
    return
end, "Stormlance Residence")

RegisterEvent(12, "Stormlance Residence", nil, "Stormlance Residence")

RegisterEvent(13, "Morningstar Residence", function()
    evt.EnterHouse(317) -- Morningstar Residence
    return
end, "Morningstar Residence")

RegisterEvent(14, "Morningstar Residence", nil, "Morningstar Residence")

RegisterEvent(15, "Foestryke Residence", function()
    evt.EnterHouse(318) -- Foestryke Residence
    return
end, "Foestryke Residence")

RegisterEvent(16, "Foestryke Residence", nil, "Foestryke Residence")

RegisterEvent(17, "Ironfist Residence", function()
    evt.EnterHouse(319) -- Ironfist Residence
    return
end, "Ironfist Residence")

RegisterEvent(18, "Ironfist Residence", nil, "Ironfist Residence")

RegisterEvent(19, "Avalon's Residence", function()
    evt.EnterHouse(340) -- Avalon's Residence
    return
end, "Avalon's Residence")

RegisterEvent(20, "Avalon's Residence", nil, "Avalon's Residence")

RegisterEvent(21, "Arin Residence", function()
    evt.EnterHouse(341) -- Arin Residence
    return
end, "Arin Residence")

RegisterEvent(22, "Arin Residence", nil, "Arin Residence")

RegisterEvent(23, "Lightsworn Residence", function()
    evt.EnterHouse(342) -- Lightsworn Residence
    return
end, "Lightsworn Residence")

RegisterEvent(24, "Lightsworn Residence", nil, "Lightsworn Residence")

RegisterEvent(25, "Otterton Residence", function()
    evt.EnterHouse(343) -- Otterton Residence
    return
end, "Otterton Residence")

RegisterEvent(26, "Otterton Residence", nil, "Otterton Residence")

RegisterEvent(27, "Calandril's Residence", function()
    evt.EnterHouse(344) -- Calandril's Residence
    return
end, "Calandril's Residence")

RegisterEvent(28, "Calandril's Residence", nil, "Calandril's Residence")

RegisterEvent(29, "Maker Residence", function()
    evt.EnterHouse(345) -- Maker Residence
    return
end, "Maker Residence")

RegisterEvent(30, "Maker Residence", nil, "Maker Residence")

RegisterEvent(31, "Slayer Residence", function()
    evt.EnterHouse(346) -- Slayer Residence
    return
end, "Slayer Residence")

RegisterEvent(32, "Slayer Residence", nil, "Slayer Residence")

RegisterEvent(33, "Kern Residence", function()
    evt.EnterHouse(347) -- Kern Residence
    return
end, "Kern Residence")

RegisterEvent(34, "Kern Residence", nil, "Kern Residence")

RegisterEvent(35, "Jeni Residence", function()
    evt.EnterHouse(348) -- Jeni Residence
    return
end, "Jeni Residence")

RegisterEvent(36, "Jeni Residence", nil, "Jeni Residence")

RegisterEvent(37, "Weldrick's Home", function()
    evt.EnterHouse(349) -- Weldrick's Home
    return
end, "Weldrick's Home")

RegisterEvent(38, "Weldrick's Home", nil, "Weldrick's Home")

RegisterEvent(39, "Nelix's House", function()
    evt.EnterHouse(480) -- Nelix's House
    return
end, "Nelix's House")

RegisterEvent(40, "Nelix's House", nil, "Nelix's House")

RegisterEvent(41, "Tempus' House", function()
    evt.EnterHouse(481) -- Tempus' House
    return
end, "Tempus' House")

RegisterEvent(42, "Tempus' House", nil, "Tempus' House")

RegisterEvent(43, "Reaverston Residence", function()
    evt.EnterHouse(320) -- Reaverston Residence
    return
end, "Reaverston Residence")

RegisterEvent(44, "Reaverston Residence", nil, "Reaverston Residence")

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

RegisterEvent(91, "Flowers", function()
    evt.OpenChest(10)
    return
end, "Flowers")

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
    if not IsAtLeast(MapVar(31), 2) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(NumBounties, 99) then
            evt.StatusText("Refreshing")
        else
            AddValue(Gold, 200)
            AddValue(MapVar(31), 1)
            AddValue(IsIntellectMoreThanBase, 256)
        end
    return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(FireResistance, 10) then
        AddValue(FireResistance, 2)
        evt.StatusText("Fire Resistance +2 (Permanent)")
        AddValue(IsIntellectMoreThanBase, 257)
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    if not IsAtLeast(BaseAccuracy, 16) then
        AddValue(BaseAccuracy, 2)
        evt.StatusText("Accuracy +2 (Permanent)")
        AddValue(IsIntellectMoreThanBase, 258)
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(131, "Legacy event 131", function()
    if IsQBitSet(QBit(22)) then
        if IsQBitSet(QBit(21)) then
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        elseif IsQBitSet(QBit(158)) then
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        else
            if evt.CheckMonstersKilled(2, 42, 0, false) then
                if evt.CheckMonstersKilled(2, 43, 0, false) then
                    if evt.CheckMonstersKilled(2, 44, 0, false) then
                        if not IsQBitSet(QBit(159)) then
                            SetQBit(QBit(159))
                            evt.SummonMonsters(3, 1, 1, -30272, -16512, 0, 2, 0)
                            evt.SetMonGroupBit(2, MonsterBits.Invisible, 1)
                            if not IsQBitSet(QBit(75)) then
                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                    SetQBit(QBit(75))
                                end
                            end
                            if IsQBitSet(QBit(200)) then return end
                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                            SetQBit(QBit(200))
                            return
                        end
                        SetQBit(QBit(158))
                        SetQBit(QBit(225))
                        ClearQBit(QBit(225))
                        evt.StatusText("You have killed all of the Dragon Hunters")
                    end
                end
            end
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        end
    elseif IsQBitSet(QBit(155)) then
        if IsQBitSet(QBit(21)) then
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        elseif IsQBitSet(QBit(158)) then
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        else
            if evt.CheckMonstersKilled(2, 42, 0, false) then
                if evt.CheckMonstersKilled(2, 43, 0, false) then
                    if evt.CheckMonstersKilled(2, 44, 0, false) then
                        if not IsQBitSet(QBit(159)) then
                            SetQBit(QBit(159))
                            evt.SummonMonsters(3, 1, 1, -30272, -16512, 0, 2, 0)
                            evt.SetMonGroupBit(2, MonsterBits.Invisible, 1)
                            if not IsQBitSet(QBit(75)) then
                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                    SetQBit(QBit(75))
                                end
                            end
                            if IsQBitSet(QBit(200)) then return end
                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                            SetQBit(QBit(200))
                            return
                        end
                        SetQBit(QBit(158))
                        SetQBit(QBit(225))
                        ClearQBit(QBit(225))
                        evt.StatusText("You have killed all of the Dragon Hunters")
                    end
                end
            end
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        end
    else
        if evt.CheckMonstersKilled(2, 189, 0, false) then
            if evt.CheckMonstersKilled(2, 190, 0, false) then
                if evt.CheckMonstersKilled(2, 191, 0, false) then
                    if not IsQBitSet(QBit(156)) then
                        SetQBit(QBit(156))
                        evt.SummonMonsters(2, 1, 1, -30272, -16512, 0, 1, 0)
                        evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
                        if IsQBitSet(QBit(21)) then
                            if not IsQBitSet(QBit(75)) then
                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                    SetQBit(QBit(75))
                                end
                            end
                            if IsQBitSet(QBit(200)) then return end
                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                            SetQBit(QBit(200))
                            return
                        elseif IsQBitSet(QBit(158)) then
                            if not IsQBitSet(QBit(75)) then
                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                    SetQBit(QBit(75))
                                end
                            end
                            if IsQBitSet(QBit(200)) then return end
                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                            SetQBit(QBit(200))
                            return
                        else
                            if evt.CheckMonstersKilled(2, 42, 0, false) then
                                if evt.CheckMonstersKilled(2, 43, 0, false) then
                                    if evt.CheckMonstersKilled(2, 44, 0, false) then
                                        if not IsQBitSet(QBit(159)) then
                                            SetQBit(QBit(159))
                                            evt.SummonMonsters(3, 1, 1, -30272, -16512, 0, 2, 0)
                                            evt.SetMonGroupBit(2, MonsterBits.Invisible, 1)
                                            if not IsQBitSet(QBit(75)) then
                                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                                    SetQBit(QBit(75))
                                                end
                                            end
                                            if IsQBitSet(QBit(200)) then return end
                                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                                            SetQBit(QBit(200))
                                            return
                                        end
                                        SetQBit(QBit(158))
                                        SetQBit(QBit(225))
                                        ClearQBit(QBit(225))
                                        evt.StatusText("You have killed all of the Dragon Hunters")
                                    end
                                end
                            end
                            if not IsQBitSet(QBit(75)) then
                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                    SetQBit(QBit(75))
                                end
                            end
                            if IsQBitSet(QBit(200)) then return end
                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                            SetQBit(QBit(200))
                            return
                        end
                    end
                    SetQBit(QBit(155))
                    SetQBit(QBit(225))
                    ClearQBit(QBit(225))
                    evt.StatusText("You have killed all of the Dragons")
                end
            end
        end
        if IsQBitSet(QBit(21)) then
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        elseif IsQBitSet(QBit(158)) then
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        else
            if evt.CheckMonstersKilled(2, 42, 0, false) then
                if evt.CheckMonstersKilled(2, 43, 0, false) then
                    if evt.CheckMonstersKilled(2, 44, 0, false) then
                        if not IsQBitSet(QBit(159)) then
                            SetQBit(QBit(159))
                            evt.SummonMonsters(3, 1, 1, -30272, -16512, 0, 2, 0)
                            evt.SetMonGroupBit(2, MonsterBits.Invisible, 1)
                            if not IsQBitSet(QBit(75)) then
                                if evt.CheckMonstersKilled(1, 24, 0, false) then
                                    SetQBit(QBit(75))
                                end
                            end
                            if IsQBitSet(QBit(200)) then return end
                            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
                            SetQBit(QBit(200))
                            return
                        end
                        SetQBit(QBit(158))
                        SetQBit(QBit(225))
                        ClearQBit(QBit(225))
                        evt.StatusText("You have killed all of the Dragon Hunters")
                    end
                end
            end
            if not IsQBitSet(QBit(75)) then
                if evt.CheckMonstersKilled(1, 24, 0, false) then
                    SetQBit(QBit(75))
                end
            end
            if IsQBitSet(QBit(200)) then return end
            if not evt.CheckMonstersKilled(4, 2, 1, false) then return end
            SetQBit(QBit(200))
            return
        end
    end
end)

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(190)) then return end
    evt.StatusText("theunicornkin")
    AddValue(IsIntellectMoreThanBase, 17)
    SetQBit(QBit(190))
    return
end, "Obelisk")

RegisterEvent(171, "Lance's Spears", function()
    if IsQBitSet(QBit(22)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.EnterHouse(4) -- Lance's Spears
    return
end, "Lance's Spears")

RegisterEvent(172, "Lance's Spears", nil, "Lance's Spears")

RegisterEvent(173, "Plated Protection", function()
    if IsQBitSet(QBit(22)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.EnterHouse(18) -- Plated Protection
    return
end, "Plated Protection")

RegisterEvent(174, "Plated Protection", nil, "Plated Protection")

RegisterEvent(175, "Wards and Pendants", function()
    if IsQBitSet(QBit(22)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.EnterHouse(32) -- Wards and Pendants
    return
end, "Wards and Pendants")

RegisterEvent(176, "Wards and Pendants", nil, "Wards and Pendants")

RegisterEvent(181, "Guild Caravans", function()
    if IsQBitSet(QBit(22)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.EnterHouse(57) -- Guild Caravans
    return
end, "Guild Caravans")

RegisterEvent(182, "Guild Caravans", nil, "Guild Caravans")

RegisterEvent(185, "Sacred Steel", function()
    if IsQBitSet(QBit(22)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.EnterHouse(77) -- Sacred Steel
    return
end, "Sacred Steel")

RegisterEvent(186, "Sacred Steel", nil, "Sacred Steel")

RegisterEvent(187, "Godric's Gauntlet", function()
    if IsQBitSet(QBit(22)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.EnterHouse(92) -- Godric's Gauntlet
    return
end, "Godric's Gauntlet")

RegisterEvent(188, "Godric's Gauntlet", nil, "Godric's Gauntlet")

RegisterEvent(191, "Dragon's Blood Inn", function()
    evt.EnterHouse(111) -- Dragon's Blood Inn
    return
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
    return
end)

RegisterEvent(490, "Legacy event 490", function()
    local randomStep = PickRandomOption(490, 2, {2, 2, 3, 3, 3, 3})
    if randomStep == 2 then
        evt.PlaySound(325, 11520, -13664)
    end
    return
end)

RegisterEvent(501, "Enter the Dragon Hunter's Camp", function()
    evt.MoveToMap(-1216, 1888, 1, 1536, 0, 0, 202, 0, "d16.blv")
    return
end, "Enter the Dragon Hunter's Camp")

RegisterEvent(502, "Enter the Dragon Cave", function()
    evt.MoveToMap(223, -8, 170, 1088, 0, 0, 203, 0, "d17.blv")
    return
end, "Enter the Dragon Cave")

RegisterEvent(503, "Enter the Naga Vault", function()
    evt.MoveToMap(-500, -1567, -63, 512, 0, 0, 204, 0, "d18.blv")
    return
end, "Enter the Naga Vault")

RegisterEvent(504, "Enter the Grand Temple of Eep", function()
    evt.MoveToMap(-2812, 726, 1, 1536, 0, 0, 0, 0, "D44.blv")
    return
end, "Enter the Grand Temple of Eep")

