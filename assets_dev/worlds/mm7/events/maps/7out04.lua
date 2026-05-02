-- The Tularean Forest
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 401, 500},
    onLeave = {},
    openedChestIds = {
    [151] = {1},
    [152] = {2},
    [153] = {3},
    [154] = {4},
    [155] = {5},
    [156] = {6},
    [157] = {7},
    [158] = {8},
    [159] = {9},
    [160] = {10},
    [161] = {11},
    [162] = {12},
    [163] = {13},
    [164] = {14},
    [165] = {15},
    [166] = {16},
    [167] = {17},
    [168] = {18},
    [169] = {19},
    [170] = {0},
    },
    textureNames = {},
    spriteNames = {"0", "7tree07", "7tree08", "7tree09", "7tree25", "7tree30", "tree26", "tree27", "tree37"},
    castSpellIds = {},
    timers = {
    { eventId = 403, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if not IsQBitSet(QBit(180)) then -- Ravenshore Town Portal
        SetQBit(QBit(180)) -- Ravenshore Town Portal
    end
    if not IsQBitSet(QBit(553)) then -- Solved Tree quest
        evt.SetMonGroupBit(61, MonsterBits.Hostile, 1)
        return
    end
    evt.SetMonGroupBit(61, MonsterBits.Hostile, 0)
end)

RegisterEvent(3, "Chest ", function()
    evt.EnterHouse(51) -- Buckskins and Bucklers
end, "Chest ")

RegisterEvent(4, "Buckskins and Bucklers", nil, "Buckskins and Bucklers")

RegisterEvent(5, "Natural Magic", function()
    evt.EnterHouse(87) -- Natural Magic
end, "Natural Magic")

RegisterEvent(6, "Natural Magic", nil, "Natural Magic")

RegisterEvent(7, "The Bubbling Cauldron", function()
    evt.EnterHouse(119) -- The Bubbling Cauldron
end, "The Bubbling Cauldron")

RegisterEvent(8, "The Bubbling Cauldron", nil, "The Bubbling Cauldron")

RegisterEvent(9, "Hu's Stallions", function()
    evt.EnterHouse(463) -- Hu's Stallions
end, "Hu's Stallions")

RegisterEvent(10, "Hu's Stallions", nil, "Hu's Stallions")

RegisterEvent(11, "Sea Sprite", function()
    evt.EnterHouse(487) -- Sea Sprite
end, "Sea Sprite")

RegisterEvent(12, "Sea Sprite", nil, "Sea Sprite")

RegisterEvent(13, "Nature's Remedies", function()
    evt.EnterHouse(313) -- Nature's Remedies
end, "Nature's Remedies")

RegisterEvent(14, "Nature's Remedies", nil, "Nature's Remedies")

RegisterEvent(15, "The Proving Grounds", function()
    evt.EnterHouse(1573) -- The Proving Grounds
end, "The Proving Grounds")

RegisterEvent(16, "The Proving Grounds", nil, "The Proving Grounds")

RegisterEvent(17, "Pierpont Townhall", function()
    evt.EnterHouse(205) -- Pierpont Townhall
end, "Pierpont Townhall")

RegisterEvent(18, "Pierpont Townhall", nil, "Pierpont Townhall")

RegisterEvent(19, "Emerald Inn", function()
    evt.EnterHouse(242) -- Emerald Inn
end, "Emerald Inn")

RegisterEvent(20, "Emerald Inn", nil, "Emerald Inn")

RegisterEvent(21, "Nature's Stockpile", function()
    evt.EnterHouse(288) -- Nature's Stockpile
end, "Nature's Stockpile")

RegisterEvent(22, "Nature's Stockpile", nil, "Nature's Stockpile")

RegisterEvent(23, "Master Guild of Fire", function()
    evt.EnterHouse(130) -- Master Guild of Fire
end, "Master Guild of Fire")

RegisterEvent(24, "Master Guild of Fire", nil, "Master Guild of Fire")

RegisterEvent(25, "Master Guild of Air", function()
    evt.EnterHouse(136) -- Master Guild of Air
end, "Master Guild of Air")

RegisterEvent(26, "Master Guild of Air", nil, "Master Guild of Air")

RegisterEvent(27, "Adept Guild of Water", function()
    evt.EnterHouse(141) -- Adept Guild of Water
end, "Adept Guild of Water")

RegisterEvent(28, "Adept Guild of Water", nil, "Adept Guild of Water")

RegisterEvent(29, "Adept Guild of Earth", function()
    evt.EnterHouse(147) -- Adept Guild of Earth
end, "Adept Guild of Earth")

RegisterEvent(30, "Adept Guild of Earth", nil, "Adept Guild of Earth")

RegisterEvent(32, "Hunter's Lodge", function()
    evt.EnterHouse(11) -- Hunter's Lodge
end, "Hunter's Lodge")

RegisterEvent(33, "Hunter's Lodge", nil, "Hunter's Lodge")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Bith Residence", function()
    evt.EnterHouse(946) -- Bith Residence
end, "Bith Residence")

RegisterEvent(53, "Suretrail Home", function()
    evt.EnterHouse(947) -- Suretrail Home
end, "Suretrail Home")

RegisterEvent(54, "Silverpoint Residence", function()
    evt.EnterHouse(948) -- Silverpoint Residence
end, "Silverpoint Residence")

RegisterEvent(55, "Miyon's Home", function()
    evt.EnterHouse(949) -- Miyon's Home
end, "Miyon's Home")

RegisterEvent(56, "Green House", function()
    evt.EnterHouse(950) -- Green House
end, "Green House")

RegisterEvent(57, "Warlin Residence", function()
    evt.EnterHouse(951) -- Warlin Residence
end, "Warlin Residence")

RegisterEvent(58, "Dotes Residence", function()
    evt.EnterHouse(952) -- Dotes Residence
end, "Dotes Residence")

RegisterEvent(59, "Blueswan Home", function()
    evt.EnterHouse(953) -- Blueswan Home
end, "Blueswan Home")

RegisterEvent(60, "Treasurestone Home", function()
    evt.EnterHouse(954) -- Treasurestone Home
end, "Treasurestone Home")

RegisterEvent(61, "Windsong House", function()
    evt.EnterHouse(955) -- Windsong House
end, "Windsong House")

RegisterEvent(62, "Whitecap Residence", function()
    evt.EnterHouse(956) -- Whitecap Residence
end, "Whitecap Residence")

RegisterEvent(63, "Ottin House", function()
    evt.EnterHouse(957) -- Ottin House
end, "Ottin House")

RegisterEvent(64, "Black House", function()
    evt.EnterHouse(958) -- Black House
end, "Black House")

RegisterEvent(65, "Fiddlebone Residence", function()
    evt.EnterHouse(959) -- Fiddlebone Residence
end, "Fiddlebone Residence")

RegisterEvent(66, "Kerrid Residence", function()
    evt.EnterHouse(960) -- Kerrid Residence
end, "Kerrid Residence")

RegisterEvent(67, "Willowbark's Home", function()
    evt.EnterHouse(961) -- Willowbark's Home
end, "Willowbark's Home")

RegisterEvent(68, "House 324", function()
    evt.EnterHouse(962) -- House 324
end, "House 324")

RegisterEvent(69, "House 325", function()
    evt.EnterHouse(963) -- House 325
end, "House 325")

RegisterEvent(70, "House 326", function()
    evt.EnterHouse(964) -- House 326
end, "House 326")

RegisterEvent(71, "Benjamin's Home", function()
    evt.EnterHouse(965) -- Benjamin's Home
end, "Benjamin's Home")

RegisterEvent(72, "Stonewright Residence", function()
    evt.EnterHouse(966) -- Stonewright Residence
end, "Stonewright Residence")

RegisterEvent(73, "Weatherson's House", function()
    evt.EnterHouse(967) -- Weatherson's House
end, "Weatherson's House")

RegisterEvent(74, "Sower Residence", function()
    evt.EnterHouse(968) -- Sower Residence
end, "Sower Residence")

RegisterEvent(75, "Tent", nil, "Tent")

RegisterEvent(151, "Chest ", function()
    evt.OpenChest(1)
end, "Chest ")

RegisterEvent(152, "Chest ", function()
    evt.OpenChest(2)
end, "Chest ")

RegisterEvent(153, "Chest ", function()
    evt.OpenChest(3)
end, "Chest ")

RegisterEvent(154, "Chest ", function()
    evt.OpenChest(4)
end, "Chest ")

RegisterEvent(155, "Chest ", function()
    evt.OpenChest(5)
end, "Chest ")

RegisterEvent(156, "Chest ", function()
    evt.OpenChest(6)
end, "Chest ")

RegisterEvent(157, "Chest ", function()
    evt.OpenChest(7)
end, "Chest ")

RegisterEvent(158, "Chest ", function()
    evt.OpenChest(8)
end, "Chest ")

RegisterEvent(159, "Chest ", function()
    evt.OpenChest(9)
end, "Chest ")

RegisterEvent(160, "Chest ", function()
    evt.OpenChest(10)
end, "Chest ")

RegisterEvent(161, "Chest ", function()
    evt.OpenChest(11)
end, "Chest ")

RegisterEvent(162, "Chest ", function()
    evt.OpenChest(12)
end, "Chest ")

RegisterEvent(163, "Chest ", function()
    evt.OpenChest(13)
end, "Chest ")

RegisterEvent(164, "Chest ", function()
    evt.OpenChest(14)
end, "Chest ")

RegisterEvent(165, "Chest ", function()
    evt.OpenChest(15)
end, "Chest ")

RegisterEvent(166, "Chest ", function()
    evt.OpenChest(16)
end, "Chest ")

RegisterEvent(167, "Chest ", function()
    evt.OpenChest(17)
end, "Chest ")

RegisterEvent(168, "Chest ", function()
    evt.OpenChest(18)
end, "Chest ")

RegisterEvent(169, "Chest ", function()
    evt.OpenChest(19)
end, "Chest ")

RegisterEvent(170, "Chest ", function()
    evt.OpenChest(0)
end, "Chest ")

RegisterEvent(201, "Well", nil, "Well")

RegisterEvent(202, "Drink from the Well", function()
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

RegisterEvent(203, "Fountain", nil, "Fountain")

RegisterEvent(204, "Drink from the Fountain", function()
    if not IsPlayerBitSet(PlayerBit(8)) then
        if not IsAutonoteSet(269) then -- 50 points of temporary Earth resistance from the central fountain in Pierpont.
            SetAutonote(269) -- 50 points of temporary Earth resistance from the central fountain in Pierpont.
        end
        AddValue(EarthResistanceBonus, 50)
        SetPlayerBit(PlayerBit(8))
        evt.StatusText("+50 Earth Resistance (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Fountain")

RegisterEvent(205, "Castle Navan", nil, "Castle Navan")

RegisterEvent(251, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(52), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(52), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(51, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(252, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(53), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(53), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(52, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(253, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(54), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(54), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(53, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(254, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(55), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(55), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(54, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(255, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(56), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(56), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(55, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(256, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(57), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(57), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(56, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(257, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(58), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(58), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(57, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(258, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(59), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(59), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(58, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(259, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(60), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(60), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(59, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(260, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(61), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(61), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(60, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(261, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(62), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(62), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(61, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(401, "Legacy event 401", function()
    if IsQBitSet(QBit(649)) then -- Artifact Messenger only happens once
        if not IsQBitSet(QBit(591)) then return end -- Retrieve Gryphonheart's Trumpet from the battle in the Tularean Forest and return it to whichever side you choose.
        if IsAtLeast(MapVar(13), 1) then return end
        SetValue(MapVar(13), 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 0)
        evt.SetFacetBit(1, FacetBits.Invisible, 0)
        evt.SummonMonsters(2, 2, 3, -15752, 21272, 3273, 51, 0) -- encounter slot 2 "Elf Spearman" tier B, count 3, pos=(-15752, 21272, 3273), actor group 51, no unique actor name
        evt.SummonMonsters(2, 2, 5, -14000, 18576, 4250, 51, 0) -- encounter slot 2 "Elf Spearman" tier B, count 5, pos=(-14000, 18576, 4250), actor group 51, no unique actor name
        evt.SummonMonsters(2, 2, 10, -16016, 19280, 3284, 51, 0) -- encounter slot 2 "Elf Spearman" tier B, count 10, pos=(-16016, 19280, 3284), actor group 51, no unique actor name
        evt.SummonMonsters(3, 2, 30, -15752, 21272, 3273, 50, 0) -- encounter slot 3 "Fighter Chain" tier B, count 30, pos=(-15752, 21272, 3273), actor group 50, no unique actor name
        evt.SummonMonsters(3, 2, 9, -14000, 18576, 4250, 50, 0) -- encounter slot 3 "Fighter Chain" tier B, count 9, pos=(-14000, 18576, 4250), actor group 50, no unique actor name
        evt.SummonMonsters(3, 2, 10, -16016, 19280, 3284, 50, 0) -- encounter slot 3 "Fighter Chain" tier B, count 10, pos=(-16016, 19280, 3284), actor group 50, no unique actor name
        return
    elseif IsQBitSet(QBit(600)) then -- Talked to Catherine
        if IsQBitSet(QBit(589)) then -- Retrieve plans from Fort Riverstride and return them to Eldrich Parson in Castle Navan in the Tularean Forest.
            return
        elseif IsQBitSet(QBit(590)) then -- Rescue Loren Steel from the Tularean Caves in the Tularean Forest and return him to Queen Catherine.
            return
        else
            evt.SpeakNPC(412) -- Messenger
            AddValue(InventoryItem(1502), 1502) -- Message from Erathia
            SetQBit(QBit(649)) -- Artifact Messenger only happens once
            SetQBit(QBit(591)) -- Retrieve Gryphonheart's Trumpet from the battle in the Tularean Forest and return it to whichever side you choose.
            SetValue(MapVar(13), 0)
            if not IsQBitSet(QBit(591)) then return end -- Retrieve Gryphonheart's Trumpet from the battle in the Tularean Forest and return it to whichever side you choose.
            if IsAtLeast(MapVar(13), 1) then return end
            SetValue(MapVar(13), 1)
            evt.SetFacetBit(1, FacetBits.Untouchable, 0)
            evt.SetFacetBit(1, FacetBits.Invisible, 0)
            evt.SummonMonsters(2, 2, 3, -15752, 21272, 3273, 51, 0) -- encounter slot 2 "Elf Spearman" tier B, count 3, pos=(-15752, 21272, 3273), actor group 51, no unique actor name
            evt.SummonMonsters(2, 2, 5, -14000, 18576, 4250, 51, 0) -- encounter slot 2 "Elf Spearman" tier B, count 5, pos=(-14000, 18576, 4250), actor group 51, no unique actor name
            evt.SummonMonsters(2, 2, 10, -16016, 19280, 3284, 51, 0) -- encounter slot 2 "Elf Spearman" tier B, count 10, pos=(-16016, 19280, 3284), actor group 51, no unique actor name
            evt.SummonMonsters(3, 2, 30, -15752, 21272, 3273, 50, 0) -- encounter slot 3 "Fighter Chain" tier B, count 30, pos=(-15752, 21272, 3273), actor group 50, no unique actor name
            evt.SummonMonsters(3, 2, 9, -14000, 18576, 4250, 50, 0) -- encounter slot 3 "Fighter Chain" tier B, count 9, pos=(-14000, 18576, 4250), actor group 50, no unique actor name
            evt.SummonMonsters(3, 2, 10, -16016, 19280, 3284, 50, 0) -- encounter slot 3 "Fighter Chain" tier B, count 10, pos=(-16016, 19280, 3284), actor group 50, no unique actor name
            return
        end
    else
        return
    end
end)

RegisterEvent(402, "Legacy event 402", function()
    evt.SpeakNPC(392) -- The Oldest Tree
end)

RegisterEvent(403, "Legacy event 403", function()
    if IsQBitSet(QBit(553)) then -- Solved Tree quest
        evt.SetMonGroupBit(61, MonsterBits.Hostile, 0)
    end
end)

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if not IsPlayerBitSet(PlayerBit(25)) then
        AddValue(WaterResistance, 10)
        AddValue(FireResistance, 10)
        AddValue(AirResistance, 10)
        SetPlayerBit(PlayerBit(25))
        evt.StatusText("+10 Water, Fire, and Air Resistance(Permanent)")
        return
    end
    evt.StatusText("You Pray")
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(678)) then return end -- Visited Obelisk in Area 4
    evt.StatusText("redditoh")
    SetAutonote(311) -- Obelisk message #3: redditoh
    evt.ForPlayer(Players.All)
    SetQBit(QBit(678)) -- Visited Obelisk in Area 4
end, "Obelisk")

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(2) then
        goto step_16
    end
    if evt.CheckSeason(3) then
        goto step_20
    end
    evt.SetSprite(5, 1, "7tree07")
    evt.SetSprite(6, 1, "7tree25")
    evt.SetSprite(7, 1, "0")
    evt.SetSprite(10, 1, "0")
    goto step_37
    ::step_8::
    if evt.CheckSeason(1) then
        goto step_12
    end
    if evt.CheckSeason(0) then
        goto step_14
    end
    do return end
    ::step_12::
    evt.StatusText("You received an apple")
    goto step_36
    ::step_14::
    evt.StatusText("Fruit Tree")
    goto step_36
    ::step_16::
    evt.SetSprite(5, 1, "7tree08")
    evt.SetSprite(6, 1, "tree26")
    goto step_23
    ::step_20::
    evt.SetSprite(5, 1, "7tree09")
    evt.SetSprite(6, 1, "tree27")
    ::step_23::
    evt.SetSprite(7, 1, "0")
    evt.SetSprite(10, 0, "0")
    evt.SetSprite(51, 1, "7tree30")
    evt.SetSprite(52, 1, "7tree30")
    evt.SetSprite(53, 1, "7tree30")
    evt.SetSprite(54, 1, "7tree30")
    evt.SetSprite(55, 1, "7tree30")
    evt.SetSprite(56, 1, "7tree30")
    evt.SetSprite(57, 1, "7tree30")
    evt.SetSprite(58, 1, "7tree30")
    evt.SetSprite(59, 1, "7tree30")
    evt.SetSprite(60, 1, "7tree30")
    evt.SetSprite(61, 1, "7tree30")
    ::step_36::
    do return end
    ::step_37::
    if IsAtLeast(MapVar(52), 1) then
        goto step_40
    end
    evt.SetSprite(51, 1, "0")
    goto step_41
    ::step_40::
    evt.SetSprite(51, 1, "0")
    ::step_41::
    if IsAtLeast(MapVar(53), 1) then
        goto step_44
    end
    evt.SetSprite(52, 1, "0")
    goto step_45
    ::step_44::
    evt.SetSprite(52, 1, "0")
    ::step_45::
    if IsAtLeast(MapVar(54), 1) then
        goto step_48
    end
    evt.SetSprite(53, 1, "0")
    goto step_49
    ::step_48::
    evt.SetSprite(53, 1, "0")
    ::step_49::
    if IsAtLeast(MapVar(55), 1) then
        goto step_52
    end
    evt.SetSprite(54, 1, "0")
    goto step_53
    ::step_52::
    evt.SetSprite(54, 1, "0")
    ::step_53::
    if IsAtLeast(MapVar(56), 1) then
        goto step_56
    end
    evt.SetSprite(55, 1, "0")
    goto step_57
    ::step_56::
    evt.SetSprite(55, 1, "0")
    ::step_57::
    if IsAtLeast(MapVar(57), 1) then
        goto step_60
    end
    evt.SetSprite(56, 1, "0")
    goto step_61
    ::step_60::
    evt.SetSprite(56, 1, "0")
    ::step_61::
    if IsAtLeast(MapVar(58), 1) then
        goto step_64
    end
    evt.SetSprite(57, 1, "0")
    goto step_65
    ::step_64::
    evt.SetSprite(57, 1, "0")
    ::step_65::
    if IsAtLeast(MapVar(59), 1) then
        goto step_68
    end
    evt.SetSprite(58, 1, "0")
    goto step_69
    ::step_68::
    evt.SetSprite(58, 1, "0")
    ::step_69::
    if IsAtLeast(MapVar(60), 1) then
        goto step_72
    end
    evt.SetSprite(59, 1, "0")
    goto step_73
    ::step_72::
    evt.SetSprite(59, 1, "0")
    ::step_73::
    if IsAtLeast(MapVar(61), 1) then
        goto step_76
    end
    evt.SetSprite(60, 1, "0")
    goto step_77
    ::step_76::
    evt.SetSprite(60, 1, "0")
    ::step_77::
    if IsAtLeast(MapVar(62), 1) then
        goto step_80
    end
    evt.SetSprite(61, 1, "0")
    goto step_81
    ::step_80::
    evt.SetSprite(61, 1, "0")
    ::step_81::
    goto step_8
end)

RegisterEvent(501, "Barrel", function()
    evt.MoveToMap(0, -1589, 225, 512, 0, 0, 128, 1, "7d32.blv")
end, "Barrel")

RegisterEvent(502, "Enter Castle Navan", function()
    evt.MoveToMap(2071, 448, 1, 1024, 0, 0, 138, 1, "7d08.blv")
end, "Enter Castle Navan")

RegisterEvent(503, "Enter Clanker's Laboratory", function()
    if not IsQBitSet(QBit(710)) then -- Archibald in Clankers Lab now
        evt.MoveToMap(0, -709, 1, 512, 0, 0, 139, 1, "\t7d12.blv")
        evt.SpeakNPC(427) -- Archibald Ironfist
        return
    end
    evt.SpeakNPC(427) -- Archibald Ironfist
end, "Enter Clanker's Laboratory")

