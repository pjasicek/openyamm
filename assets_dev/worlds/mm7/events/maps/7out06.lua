-- The Bracada Desert
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {222},
    onLeave = {2},
    openedChestIds = {
    [201] = {1},
    [202] = {2},
    [203] = {3},
    [204] = {4},
    [205] = {5},
    [206] = {6},
    [207] = {7},
    [208] = {8},
    [209] = {9},
    [210] = {10},
    [211] = {11},
    [212] = {12},
    [213] = {13},
    [214] = {14},
    [215] = {15},
    [216] = {16},
    [217] = {17},
    [218] = {18},
    [219] = {19},
    [220] = {0},
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Chest ", nil, "Chest ")

RegisterEvent(2, "Legacy event 2", function()
    if IsQBitSet(QBit(701)) then return end -- Killed all Bracada Desert Griffins
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 279, 0, false) then return end -- monster 279 "Griffin"; all matching actors defeated
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 280, 0, false) then return end -- monster 280 "Hunting Griffin"; all matching actors defeated
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 281, 0, false) then -- monster 281 "Royal Griffin"; all matching actors defeated
        evt.ForPlayer(Players.All)
        SetQBit(QBit(701)) -- Killed all Bracada Desert Griffins
    end
end)

RegisterEvent(50, "Legacy event 50", nil)

RegisterEvent(98, "Dock", nil, "Dock")

RegisterEvent(99, "Enchantress", function()
    evt.EnterHouse(488) -- Enchantress
end, "Enchantress")

RegisterEvent(100, "Enchantress", nil, "Enchantress")

RegisterEvent(101, "Artifacts & Antiquities", function()
    evt.EnterHouse(89) -- Artifacts & Antiquities
end, "Artifacts & Antiquities")

RegisterEvent(102, "Artifacts & Antiquities", nil, "Artifacts & Antiquities")

RegisterEvent(103, "Edmond's Ampules", function()
    evt.EnterHouse(121) -- Edmond's Ampules
end, "Edmond's Ampules")

RegisterEvent(104, "Edmond's Ampules", nil, "Edmond's Ampules")

RegisterEvent(105, "Crystal Caravans", function()
    evt.EnterHouse(465) -- Crystal Caravans
end, "Crystal Caravans")

RegisterEvent(106, "Crystal Caravans", nil, "Crystal Caravans")

RegisterEvent(107, "Temple of Light", function()
    evt.EnterHouse(315) -- Temple of Light
end, "Temple of Light")

RegisterEvent(108, "Temple of Light", nil, "Temple of Light")

RegisterEvent(109, "Familiar Place", function()
    evt.EnterHouse(244) -- Familiar Place
end, "Familiar Place")

RegisterEvent(110, "Familiar Place", nil, "Familiar Place")

RegisterEvent(111, "Master Guild of Water", function()
    evt.EnterHouse(142) -- Master Guild of Water
end, "Master Guild of Water")

RegisterEvent(112, "Master Guild of Water", nil, "Master Guild of Water")

RegisterEvent(113, "Guild of Illumination", function()
    evt.EnterHouse(171) -- Guild of Illumination
end, "Guild of Illumination")

RegisterEvent(114, "Guild of Illumination", nil, "Guild of Illumination")

RegisterEvent(150, "House", nil, "House")

RegisterEvent(151, "Smiling Jack's", function()
    evt.EnterHouse(1110) -- Smiling Jack's
end, "Smiling Jack's")

RegisterEvent(152, "Pederton Residence", function()
    evt.EnterHouse(1111) -- Pederton Residence
end, "Pederton Residence")

RegisterEvent(153, "Applebee Manor", function()
    evt.EnterHouse(1112) -- Applebee Manor
end, "Applebee Manor")

RegisterEvent(154, "Lightsworn Residence", function()
    evt.EnterHouse(1113) -- Lightsworn Residence
end, "Lightsworn Residence")

RegisterEvent(155, "Alashandra's Home", function()
    evt.EnterHouse(1114) -- Alashandra's Home
end, "Alashandra's Home")

RegisterEvent(156, "Gayle's", function()
    evt.EnterHouse(1115) -- Gayle's
end, "Gayle's")

RegisterEvent(157, "Brigham's Home", function()
    evt.EnterHouse(1116) -- Brigham's Home
end, "Brigham's Home")

RegisterEvent(158, "Rowan's House", function()
    evt.EnterHouse(1117) -- Rowan's House
end, "Rowan's House")

RegisterEvent(159, "Brand's Home", function()
    evt.EnterHouse(1118) -- Brand's Home
end, "Brand's Home")

RegisterEvent(160, "Benson Residence", function()
    evt.EnterHouse(1119) -- Benson Residence
end, "Benson Residence")

RegisterEvent(161, "Zimm's House", function()
    evt.EnterHouse(1120) -- Zimm's House
end, "Zimm's House")

RegisterEvent(162, "Stone House", function()
    evt.EnterHouse(1136) -- Stone House
end, "Stone House")

RegisterEvent(163, "Watershed Residence", function()
    evt.EnterHouse(1137) -- Watershed Residence
end, "Watershed Residence")

RegisterEvent(164, "Hollyfield Residence", function()
    evt.EnterHouse(1138) -- Hollyfield Residence
end, "Hollyfield Residence")

RegisterEvent(165, "Sweet Residence", function()
    evt.EnterHouse(1139) -- Sweet Residence
end, "Sweet Residence")

RegisterEvent(201, "Chest ", function()
    evt.OpenChest(1)
end, "Chest ")

RegisterEvent(202, "Chest ", function()
    evt.OpenChest(2)
end, "Chest ")

RegisterEvent(203, "Chest ", function()
    evt.OpenChest(3)
end, "Chest ")

RegisterEvent(204, "Chest ", function()
    evt.OpenChest(4)
end, "Chest ")

RegisterEvent(205, "Chest ", function()
    evt.OpenChest(5)
end, "Chest ")

RegisterEvent(206, "Chest ", function()
    evt.OpenChest(6)
end, "Chest ")

RegisterEvent(207, "Chest ", function()
    evt.OpenChest(7)
end, "Chest ")

RegisterEvent(208, "Chest ", function()
    evt.OpenChest(8)
end, "Chest ")

RegisterEvent(209, "Chest ", function()
    evt.OpenChest(9)
end, "Chest ")

RegisterEvent(210, "Chest ", function()
    evt.OpenChest(10)
end, "Chest ")

RegisterEvent(211, "Chest ", function()
    evt.OpenChest(11)
end, "Chest ")

RegisterEvent(212, "Chest ", function()
    evt.OpenChest(12)
end, "Chest ")

RegisterEvent(213, "Chest ", function()
    evt.OpenChest(13)
end, "Chest ")

RegisterEvent(214, "Chest ", function()
    evt.OpenChest(14)
end, "Chest ")

RegisterEvent(215, "Chest ", function()
    evt.OpenChest(15)
end, "Chest ")

RegisterEvent(216, "Chest ", function()
    evt.OpenChest(16)
end, "Chest ")

RegisterEvent(217, "Chest ", function()
    evt.OpenChest(17)
end, "Chest ")

RegisterEvent(218, "Chest ", function()
    evt.OpenChest(18)
end, "Chest ")

RegisterEvent(219, "Chest ", function()
    evt.OpenChest(19)
    if IsQBitSet(QBit(583)) then -- Placed Golem head
        return
    elseif IsQBitSet(QBit(731)) then -- Golem Head - I lost it
        return
    else
        SetQBit(QBit(731)) -- Golem Head - I lost it
        return
    end
end, "Chest ")

RegisterEvent(220, "Chest ", function()
    evt.OpenChest(0)
    if IsQBitSet(QBit(584)) then -- Placed Golem Abbey normal head
        return
    elseif IsQBitSet(QBit(732)) then -- Abby normal head - I lost it
        return
    else
        SetQBit(QBit(732)) -- Abby normal head - I lost it
        return
    end
end, "Chest ")

RegisterEvent(222, "Legacy event 222", function()
    if IsQBitSet(QBit(612)) then -- Chose the path of Dark
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(61, MonsterBits.Hostile, 1)
        return
    elseif IsQBitSet(QBit(782)) then -- Your friends are mad at you
        if IsAtLeast(Counter(10), 720) then
            ClearQBit(QBit(782)) -- Your friends are mad at you
            SetValue(MapVar(6), 0)
            evt.SetMonGroupBit(56, MonsterBits.Hostile, 0)
            evt.SetMonGroupBit(61, MonsterBits.Hostile, 1)
            return
        end
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(61, MonsterBits.Hostile, 1)
        return
    elseif IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(61, MonsterBits.Hostile, 1)
        return
    else
        evt.SetMonGroupBit(61, MonsterBits.Hostile, 1)
        return
    end
end)

RegisterEvent(301, "Legacy event 301", function()
    evt.MoveToMap(-9711, 8872, 2400, 512, 0, 0, 0, 0)
end)

RegisterEvent(302, "Legacy event 302", function()
    evt.MoveToMap(-5648, 15992, 0, 1536, 0, 0, 0, 0)
end)

RegisterEvent(303, "Legacy event 303", function()
    evt.MoveToMap(3000, 17248, 1600, 512, 0, 0, 0, 0)
    evt.MoveToMap(-14208, -6992, 1344, 1024, 0, 0, 0, 0)
end)

RegisterEvent(304, "Legacy event 304", function()
    evt.MoveToMap(-4608, 16032, 1, 1536, 0, 0, 0, 0)
end)

RegisterEvent(305, "Legacy event 305", function()
    evt.MoveToMap(-6664, 15040, 0, 1536, 0, 0, 0, 0)
end)

RegisterEvent(306, "Legacy event 306", function()
    evt.MoveToMap(-17624, 20360, 800, 1536, 0, 0, 0, 0)
end)

RegisterEvent(307, "Legacy event 307", function()
    evt.MoveToMap(-5616, 14992, 0, 1536, 0, 0, 0, 0)
end)

RegisterEvent(308, "Legacy event 308", function()
    evt.MoveToMap(-16064, 8944, 800, 1024, 0, 0, 0, 0)
end)

RegisterEvent(309, "Legacy event 309", function()
    evt.MoveToMap(-4592, 15000, 0, 1536, 0, 0, 0, 0)
end)

RegisterEvent(310, "Legacy event 310", function()
    evt.MoveToMap(6464, -19280, 1376, 512, 0, 0, 0, 0)
end)

RegisterEvent(311, "Legacy event 311", function()
    evt.MoveToMap(-7160, 13976, 0, 1536, 0, 0, 0, 0)
end)

RegisterEvent(312, "Legacy event 312", function()
    evt.MoveToMap(17656, -20704, 800, 0, 0, 0, 0, 0)
end)

RegisterEvent(313, "Legacy event 313", function()
    local randomStep = PickRandomOption(313, 1, {1, 3, 5, 7, 9, 11})
    if randomStep == 1 then
        evt.MoveToMap(-3040, 992, 1120, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 3 then
        evt.MoveToMap(-14848, -18144, 0, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 5 then
        evt.MoveToMap(18112, -8736, 182, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 7 then
        evt.MoveToMap(16288, 17504, 0, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 9 then
        evt.MoveToMap(-16192, 10752, 0, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 11 then
        evt.MoveToMap(-8192, -64, 0, 0, 0, 0, 0, 0)
        return
    end
end)

RegisterEvent(314, "Legacy event 314", function()
    evt.MoveToMap(-7360, 13504, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(315, "Legacy event 315", function()
    evt.MoveToMap(9208, 18608, 0, 1536, 0, 0, 0, 0)
end)

RegisterEvent(316, "Legacy event 316", function()
    evt.MoveToMap(-4800, 14552, 0, 1024, 0, 0, 0, 0)
end)

RegisterEvent(317, "Legacy event 317", function()
    evt.MoveToMap(-6192, 12744, 0, 0, 0, 0, 0, 0)
end)

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if IsQBitSet(QBit(715)) then return end -- Place item 619 in out06(statue)
    if not IsQBitSet(QBit(712)) then return end -- Retrieve the three statuettes and place them on the shrines in the Bracada Desert, Tatalia, and Avlee, then return to Thom Lumbra in the Tularean Forest.
    evt.ForPlayer(Players.All)
    if HasItem(1421) then -- Angel Statuette
        evt.SetSprite(25, 1, "0")
        RemoveItem(1421) -- Angel Statuette
        SetQBit(QBit(715)) -- Place item 619 in out06(statue)
    end
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(680)) then return end -- Visited Obelisk in Area 6
    evt.StatusText(" ts_rehmu")
    SetAutonote(313) -- Obelisk message #5: ts_rehmu
    evt.ForPlayer(Players.All)
    SetQBit(QBit(680)) -- Visited Obelisk in Area 6
end, "Obelisk")

RegisterEvent(454, "School of Sorcery", nil, "School of Sorcery")

RegisterEvent(455, "Red Dwarf Mines", nil, "Red Dwarf Mines")

RegisterEvent(456, "Well", nil, "Well")

RegisterEvent(457, "Drink from the Well", function()
    if not IsAtLeast(BankGold, 99) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAtLeast(MapVar(21), 1) then
            evt.StatusText("Refreshing!")
            return
        else
            AddValue(Gold, 200)
            SetValue(MapVar(21), 1)
            evt.StatusText("Refreshing!")
            return
        end
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(458, "Drink from the Well", function()
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(459, "Well", function()
    if not IsAtLeast(Gold, 100) then
        SubtractValue(Gold, 99)
        evt.StatusText("You make a wish")
    end
    SubtractValue(Gold, 100)
    local randomStep = PickRandomOption(459, 5, {6, 16})
    if randomStep == 6 then
        local randomStep = PickRandomOption(459, 7, {8, 10, 12, 14})
        if randomStep == 8 then
            SetValue(DiseasedGreen, 0)
        elseif randomStep == 10 then
            AddValue(EarthResistanceBonus, 20)
        elseif randomStep == 12 then
            evt.DamagePlayer(7, 1, 50)
        elseif randomStep == 14 then
            SetValue(Asleep, 0)
        end
    elseif randomStep == 16 then
        local randomStep = PickRandomOption(459, 17, {18, 20, 22})
        if randomStep == 18 then
            AddValue(Gold, 250)
        elseif randomStep == 20 then
            SetValue(Eradicated, 0)
        elseif randomStep == 22 then
            local randomStep = PickRandomOption(459, 23, {24, 34})
            if randomStep == 24 then
                local randomStep = PickRandomOption(459, 25, {26, 28, 30, 32})
                if randomStep == 26 then
                    AddValue(MightBonus, 20)
                elseif randomStep == 28 then
                    AddValue(IntellectBonus, 20)
                elseif randomStep == 30 then
                    AddValue(PersonalityBonus, 20)
                elseif randomStep == 32 then
                    AddValue(EnduranceBonus, 20)
                end
            elseif randomStep == 34 then
                local randomStep = PickRandomOption(459, 35, {36, 38, 40})
                if randomStep == 36 then
                    AddValue(AccuracyBonus, 20)
                elseif randomStep == 38 then
                    AddValue(SpeedBonus, 20)
                elseif randomStep == 40 then
                    AddValue(LuckBonus, 20)
                end
            end
        end
    end
    evt.StatusText("You make a wish")
end, "Well")

RegisterEvent(460, "Drink", function()
    if not IsAtLeast(PoisonedYellow, 0) then
        if IsAtLeast(PoisonedRed, 0) then
            evt.StatusText("hmmm, You decide against it.")
            return
        elseif IsAtLeast(Paralyzed, 0) then
            evt.StatusText("hmmm, You decide against it.")
        else
            local randomStep = PickRandomOption(460, 4, {5, 7, 9})
            if randomStep == 5 then
                SetValue(PoisonedYellow, 0)
            elseif randomStep == 7 then
                SetValue(PoisonedRed, 0)
            elseif randomStep == 9 then
                SetValue(Paralyzed, 0)
            end
            evt.StatusText("Suddenly, You Don't Feel too Well")
        end
    return
    end
    evt.StatusText("hmmm, You decide against it.")
end, "Drink")

RegisterEvent(461, "Drink from the Fountain", function()
    if not IsPlayerBitSet(PlayerBit(13)) then
        if not IsAutonoteSet(274) then -- 25 points of temporary Intellect and Personality from the fountain outside the School of Sorcery in the Bracada Desert.
            SetAutonote(274) -- 25 points of temporary Intellect and Personality from the fountain outside the School of Sorcery in the Bracada Desert.
        end
        AddValue(PersonalityBonus, 25)
        AddValue(IntellectBonus, 25)
        SetPlayerBit(PlayerBit(13))
        evt.StatusText("+25 Intellect and Personality (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Fountain")

RegisterEvent(462, "Temple", nil, "Temple")

RegisterEvent(463, "Shops", nil, "Shops")

RegisterEvent(464, "Tavern", nil, "Tavern")

RegisterEvent(465, "Guilds", nil, "Guilds")

RegisterEvent(466, "School of Sorcery", nil, "School of Sorcery")

RegisterEvent(467, "Docks", nil, "Docks")

RegisterEvent(468, "Stables", nil, "Stables")

RegisterEvent(469, "To Main Square", nil, "To Main Square")

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if evt.CheckSeason(1) then return end
    if evt.CheckSeason(0) then
    end
end)

RegisterEvent(501, "Enter the School of Sorcery", function()
    evt.MoveToMap(2, -1341, -159, 512, 0, 0, 142, 1, "\t7d14.blv")
end, "Enter the School of Sorcery")

RegisterEvent(502, "Enter the Red Dwarf Mines", function()
    evt.MoveToMap(26, 6, 1, 512, 0, 0, 143, 1, "7d34.blv")
end, "Enter the Red Dwarf Mines")

RegisterEvent(503, "Legacy event 503", function()
    if IsQBitSet(QBit(611)) or IsQBitSet(QBit(612)) then -- Chose the path of Light
        evt.MoveToMap(-6790, 1095, 33, 0, 0, 0, 0, 0, "7d25.blv")
    end
end)

