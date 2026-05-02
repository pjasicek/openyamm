-- Erathia
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 401, 500},
    onLeave = {2},
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
    [169] = {18, 19},
    [170] = {0},
    },
    textureNames = {},
    spriteNames = {"0", "7tree19", "7tree20", "7tree21", "7tree25", "7tree28", "7tree30", "tree26", "tree27", "tree37"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if not IsQBitSet(QBit(184)) then -- Balthazar Town Portal
        SetQBit(QBit(184)) -- Balthazar Town Portal
        evt.SetMonGroupBit(57, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(58, MonsterBits.Hostile, 1)
        return
    end
    evt.SetMonGroupBit(57, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(58, MonsterBits.Hostile, 1)
end)

RegisterEvent(2, "Legacy event 2", function()
    if IsQBitSet(QBit(700)) then return end -- Killed all Erathian Griffins
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 279, 0, false) then return end -- monster 279 "Griffin"; all matching actors defeated
    if not evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 280, 0, false) then return end -- monster 280 "Hunting Griffin"; all matching actors defeated
    if evt.CheckMonstersKilled(ActorKillCheck.MonsterId, 281, 0, false) then -- monster 281 "Royal Griffin"; all matching actors defeated
        evt.ForPlayer(Players.All)
        SetQBit(QBit(700)) -- Killed all Erathian Griffins
    end
end)

RegisterEvent(3, "Queen Catherine's Smithy", function()
    evt.EnterHouse(49) -- Queen Catherine's Smithy
end, "Queen Catherine's Smithy")

RegisterEvent(4, "Queen Catherine's Smithy", nil, "Queen Catherine's Smithy")

RegisterEvent(5, "Her Majesty's Magics", function()
    evt.EnterHouse(86) -- Her Majesty's Magics
end, "Her Majesty's Magics")

RegisterEvent(6, "Her Majesty's Magics", nil, "Her Majesty's Magics")

RegisterEvent(7, "Lead Transformations", function()
    evt.EnterHouse(118) -- Lead Transformations
end, "Lead Transformations")

RegisterEvent(8, "Lead Transformations", nil, "Lead Transformations")

RegisterEvent(9, "Royal Steeds", function()
    evt.EnterHouse(462) -- Royal Steeds
end, "Royal Steeds")

RegisterEvent(10, "Royal Steeds", nil, "Royal Steeds")

RegisterEvent(11, "Lady Catherine", function()
    evt.EnterHouse(486) -- Lady Catherine
end, "Lady Catherine")

RegisterEvent(12, "Lady Catherine", nil, "Lady Catherine")

RegisterEvent(13, "House of Solace", function()
    evt.EnterHouse(312) -- House of Solace
end, "House of Solace")

RegisterEvent(14, "House of Solace", nil, "House of Solace")

RegisterEvent(15, "In Her Majesty's Service", function()
    evt.EnterHouse(1572) -- In Her Majesty's Service
end, "In Her Majesty's Service")

RegisterEvent(16, "In Her Majesty's Service", nil, "In Her Majesty's Service")

RegisterEvent(17, "Steadwick Townhall", function()
    evt.EnterHouse(204) -- Steadwick Townhall
end, "Steadwick Townhall")

RegisterEvent(18, "Steadwick Townhall", nil, "Steadwick Townhall")

RegisterEvent(19, "Griffin's Rest", function()
    evt.EnterHouse(241) -- Griffin's Rest
end, "Griffin's Rest")

RegisterEvent(20, "Griffin's Rest", nil, "Griffin's Rest")

RegisterEvent(21, "Bank of Erathia", function()
    evt.EnterHouse(287) -- Bank of Erathia
end, "Bank of Erathia")

RegisterEvent(22, "Bank of Erathia", nil, "Bank of Erathia")

RegisterEvent(23, "Paramount Guild of Spirit", function()
    evt.EnterHouse(155) -- Paramount Guild of Spirit
end, "Paramount Guild of Spirit")

RegisterEvent(24, "Paramount Guild of Spirit", nil, "Paramount Guild of Spirit")

RegisterEvent(25, "Adept Guild of Mind", function()
    evt.EnterHouse(159) -- Adept Guild of Mind
end, "Adept Guild of Mind")

RegisterEvent(26, "Adept Guild of Mind", nil, "Adept Guild of Mind")

RegisterEvent(27, "Master Guild of Body", function()
    evt.EnterHouse(166) -- Master Guild of Body
end, "Master Guild of Body")

RegisterEvent(28, "Master Guild of Body", nil, "Master Guild of Body")

RegisterEvent(29, "The Queen's Forge", function()
    evt.EnterHouse(10) -- The Queen's Forge
end, "The Queen's Forge")

RegisterEvent(30, "The Queen's Forge", nil, "The Queen's Forge")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Guthwulf's Home", function()
    evt.EnterHouse(910) -- Guthwulf's Home
end, "Guthwulf's Home")

RegisterEvent(53, "Wolverton Residence", function()
    evt.EnterHouse(911) -- Wolverton Residence
end, "Wolverton Residence")

RegisterEvent(54, "House 271", function()
    evt.EnterHouse(912) -- House 271
end, "House 271")

RegisterEvent(55, "House 272", function()
    evt.EnterHouse(913) -- House 272
end, "House 272")

RegisterEvent(56, "House 273", function()
    evt.EnterHouse(914) -- House 273
end, "House 273")

RegisterEvent(57, "Castro's House", function()
    evt.EnterHouse(915) -- Castro's House
end, "Castro's House")

RegisterEvent(59, "Laraselle Residence", function()
    evt.EnterHouse(916) -- Laraselle Residence
end, "Laraselle Residence")

RegisterEvent(60, "Sourbrow Home", function()
    evt.EnterHouse(917) -- Sourbrow Home
end, "Sourbrow Home")

RegisterEvent(62, "Agraynel Residence", function()
    evt.EnterHouse(919) -- Agraynel Residence
end, "Agraynel Residence")

RegisterEvent(65, "House 282", function()
    evt.EnterHouse(920) -- House 282
end, "House 282")

RegisterEvent(66, "Tish Residence", function()
    evt.EnterHouse(921) -- Tish Residence
end, "Tish Residence")

RegisterEvent(67, "Talion House", function()
    evt.EnterHouse(922) -- Talion House
end, "Talion House")

RegisterEvent(68, "Ravenhill Residence", function()
    evt.EnterHouse(923) -- Ravenhill Residence
end, "Ravenhill Residence")

RegisterEvent(69, "Cardrin Residence", function()
    evt.EnterHouse(924) -- Cardrin Residence
end, "Cardrin Residence")

RegisterEvent(71, "Gareth's Home", function()
    evt.EnterHouse(926) -- Gareth's Home
end, "Gareth's Home")

RegisterEvent(72, "Forgewright Residence", function()
    evt.EnterHouse(927) -- Forgewright Residence
end, "Forgewright Residence")

RegisterEvent(73, "Pretty House", function()
    evt.EnterHouse(928) -- Pretty House
end, "Pretty House")

RegisterEvent(74, "Lotts Familly Home", function()
    evt.EnterHouse(929) -- Lotts Familly Home
end, "Lotts Familly Home")

RegisterEvent(76, "Julian's Home", function()
    evt.EnterHouse(931) -- Julian's Home
end, "Julian's Home")

RegisterEvent(77, "Eversmyle Residence", function()
    evt.EnterHouse(932) -- Eversmyle Residence
end, "Eversmyle Residence")

RegisterEvent(78, "Dirthmoore Residence", function()
    evt.EnterHouse(933) -- Dirthmoore Residence
end, "Dirthmoore Residence")

RegisterEvent(81, "Heartsworn Home", function()
    evt.EnterHouse(936) -- Heartsworn Home
end, "Heartsworn Home")

RegisterEvent(82, "Cardron Residence", function()
    evt.EnterHouse(937) -- Cardron Residence
end, "Cardron Residence")

RegisterEvent(84, "Thrush Residence", function()
    evt.EnterHouse(939) -- Thrush Residence
end, "Thrush Residence")

RegisterEvent(85, "Hillier Residence", function()
    evt.EnterHouse(940) -- Hillier Residence
end, "Hillier Residence")

RegisterEvent(86, "Quixote Residence", function()
    evt.EnterHouse(941) -- Quixote Residence
end, "Quixote Residence")

RegisterEvent(87, "Org House", function()
    evt.EnterHouse(942) -- Org House
end, "Org House")

RegisterEvent(88, "Talreish Residence", function()
    evt.EnterHouse(943) -- Talreish Residence
end, "Talreish Residence")

RegisterEvent(89, "Barnes Home", function()
    evt.EnterHouse(944) -- Barnes Home
end, "Barnes Home")

RegisterEvent(90, "Havest Residence", function()
    evt.EnterHouse(945) -- Havest Residence
end, "Havest Residence")

RegisterEvent(91, "Tent", nil, "Tent")

RegisterEvent(92, "Hut", nil, "Hut")

RegisterEvent(93, "Ravenswood Residence", function()
    evt.EnterHouse(1128) -- Ravenswood Residence
end, "Ravenswood Residence")

RegisterEvent(94, "Blayze's", function()
    evt.EnterHouse(1129) -- Blayze's
end, "Blayze's")

RegisterEvent(95, "Norris' House", function()
    evt.EnterHouse(1130) -- Norris' House
end, "Norris' House")

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

RegisterEvent(169, "Chest ", function()
    if not IsQBitSet(QBit(756)) then -- Finished ArcoMage Quest - Get the treasure
        evt.OpenChest(18)
        return
    end
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

RegisterEvent(203, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(3)) then
        if not IsAutonoteSet(264) then -- 2 points of permanent Might from the well in the northwest section of Steadwick.
            SetAutonote(264) -- 2 points of permanent Might from the well in the northwest section of Steadwick.
        end
        AddValue(BaseMight, 2)
        SetPlayerBit(PlayerBit(3))
        evt.StatusText("+2 Might (Permanent)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(204, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(5)) then
        if not IsAutonoteSet(266) then -- 20 points of temporary Body Resistance from the well south of the Steadwick Town Hall.
            SetAutonote(266) -- 20 points of temporary Body Resistance from the well south of the Steadwick Town Hall.
        end
        AddValue(BodyResistanceBonus, 20)
        SetPlayerBit(PlayerBit(5))
        evt.StatusText("+20 Body Resistance (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(205, "Drink from the Well", function()
    if not IsAtLeast(DiseasedYellow, 0) then
        if IsAtLeast(DiseasedRed, 0) then
            if not IsAutonoteSet(265) then -- Disease cured at the eastern well in Steadwick.
                SetAutonote(265) -- Disease cured at the eastern well in Steadwick.
            end
            SetValue(MapVar(1), 0)
            evt.StatusText("Disease Cured")
            return
        elseif IsAtLeast(Unconscious, 0) then
            if not IsAutonoteSet(265) then -- Disease cured at the eastern well in Steadwick.
                SetAutonote(265) -- Disease cured at the eastern well in Steadwick.
            end
            SetValue(MapVar(1), 0)
            evt.StatusText("Disease Cured")
        else
            evt.StatusText("Refreshing!")
        end
    return
    end
    if not IsAutonoteSet(265) then -- Disease cured at the eastern well in Steadwick.
        SetAutonote(265) -- Disease cured at the eastern well in Steadwick.
    end
    SetValue(MapVar(1), 0)
    evt.StatusText("Disease Cured")
end, "Drink from the Well")

RegisterEvent(207, "Fountain", nil, "Fountain")

RegisterEvent(208, "Drink from the Fountain", function()
    if not IsPlayerBitSet(PlayerBit(6)) then
        if not IsAutonoteSet(267) then -- 50 points of temporary Might from the central fountain in Steadwick.
            SetAutonote(267) -- 50 points of temporary Might from the central fountain in Steadwick.
        end
        AddValue(MightBonus, 50)
        SetPlayerBit(PlayerBit(6))
        evt.StatusText("+50 Might (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Fountain")

RegisterEvent(209, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(4)) then
        if not IsAutonoteSet(263) then -- 10 points of temporary Accuracy from the well in the village northeast of Steadwick.
            SetAutonote(263) -- 10 points of temporary Accuracy from the well in the village northeast of Steadwick.
        end
        AddValue(AccuracyBonus, 10)
        SetPlayerBit(PlayerBit(4))
        evt.StatusText("+10 Accuracy (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(210, "Drink from the Fountain", function()
    if not IsPlayerBitSet(PlayerBit(7)) then
        if not IsAutonoteSet(268) then -- 5 points of temporary Personality from the trough in front of the Steadwick Town Hall.
            SetAutonote(268) -- 5 points of temporary Personality from the trough in front of the Steadwick Town Hall.
        end
        AddValue(PersonalityBonus, 5)
        SetPlayerBit(PlayerBit(7))
        evt.StatusText("+5 Personality (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Fountain")

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

RegisterEvent(401, "Legacy event 401", function()
    if IsQBitSet(QBit(541)) then -- Crack the code in the School of Sorcery in the Bracada Desert to reveal the location of the Tomb of Ashwar Nog'Nogoth. Discover the tomb's location, enter it, and then return it to Stephan Sand in the Pit.
        evt.SetFacetBit(10, FacetBits.Untouchable, 1)
        evt.SetFacetBit(10, FacetBits.Invisible, 1)
    end
end)

RegisterEvent(402, "Button", function()
    SetValue(MapVar(11), 1)
    evt.PlaySound(42313, 14328, -21624)
end, "Button")

RegisterEvent(403, "Button", function()
    if not IsAtLeast(MapVar(11), 1) then
        SetValue(MapVar(11), 0)
        evt.PlaySound(42314, 14328, -21624)
        return
    end
    SetValue(MapVar(11), 2)
    evt.PlaySound(42314, 14328, -21624)
end, "Button")

RegisterEvent(404, "Button", function()
    if not IsAtLeast(MapVar(11), 2) then
        SetValue(MapVar(11), 0)
        evt.PlaySound(42315, 14328, -21624)
        return
    end
    SetValue(MapVar(11), 3)
    evt.PlaySound(42315, 14328, -21624)
end, "Button")

RegisterEvent(405, "Button", function()
    if not IsAtLeast(MapVar(11), 3) then
        SetValue(MapVar(11), 0)
        evt.PlaySound(42316, 14328, -21624)
        return
    end
    SetValue(MapVar(11), 4)
    evt.PlaySound(42316, 14328, -21624)
end, "Button")

RegisterEvent(406, "Button", function()
    if IsAtLeast(MapVar(11), 5) then
        return
    end
    if not IsAtLeast(MapVar(11), 4) then
        SetValue(MapVar(11), 0)
        evt.PlaySound(42317, 14328, -21624)
        return
    end
    SetValue(MapVar(11), 5)
    evt.ForPlayer(Players.All)
    SetQBit(QBit(569)) -- Solved the code puzzle. Ninja promo quest
    evt.SetFacetBit(16, FacetBits.Untouchable, 1)
    evt.SetFacetBit(17, FacetBits.Invisible, 0)
    evt.SetFacetBit(16, FacetBits.Invisible, 1)
    ClearQBit(QBit(726)) -- Scroll of Waves - I lost it
    ClearQBit(QBit(727)) -- Cipher - I lost it
    evt.PlaySound(42317, 14328, -21624)
end, "Button")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if not IsPlayerBitSet(PlayerBit(24)) then
        AddValue(BaseLuck, 10)
        evt.StatusText("+10 Luck(Permanent)")
        SetPlayerBit(PlayerBit(24))
        return
    end
    evt.StatusText("You Pray")
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(677)) then return end -- Visited Obelisk in Area 3
    evt.StatusText("ininhil_")
    SetAutonote(310) -- Obelisk message #2: ininhil_
    evt.ForPlayer(Players.All)
    SetQBit(QBit(677)) -- Visited Obelisk in Area 3
end, "Obelisk")

RegisterEvent(454, "Docks", nil, "Docks")

RegisterEvent(455, "Plaza", nil, "Plaza")

RegisterEvent(456, "Castle Gryphonheart", nil, "Castle Gryphonheart")

RegisterEvent(457, "Fort Riverstride", nil, "Fort Riverstride")

RegisterEvent(458, "East to Harmondale", nil, "East to Harmondale")

RegisterEvent(459, "North to Deyja Moors", nil, "North to Deyja Moors")

RegisterEvent(460, "West to Tatalia", nil, "West to Tatalia")

RegisterEvent(461, "South to the Bracada Desert", nil, "South to the Bracada Desert")

RegisterEvent(462, "City of Steadwick", nil, "City of Steadwick")

RegisterEvent(463, "Temple", nil, "Temple")

RegisterEvent(464, "Guilds", nil, "Guilds")

RegisterEvent(465, "Stables", nil, "Stables")

RegisterEvent(466, "Sewer", nil, "Sewer")

RegisterEvent(495, "Dreamwright Residence", function()
    evt.EnterHouse(1131) -- Dreamwright Residence
end, "Dreamwright Residence")

RegisterEvent(496, "Wain Manor", function()
    evt.EnterHouse(1132) -- Wain Manor
end, "Wain Manor")

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(2) then
        goto step_16
    end
    if evt.CheckSeason(3) then
        goto step_20
    end
    evt.SetSprite(5, 1, "7tree19")
    evt.SetSprite(6, 1, "7tree25")
    evt.SetSprite(7, 1, "7tree28")
    evt.SetSprite(10, 1, "0")
    goto step_34
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
    goto step_33
    ::step_14::
    evt.StatusText("Fruit Tree")
    goto step_33
    ::step_16::
    evt.SetSprite(5, 1, "7tree20")
    evt.SetSprite(6, 1, "tree26")
    goto step_23
    ::step_20::
    evt.SetSprite(5, 1, "7tree21")
    evt.SetSprite(6, 1, "tree27")
    ::step_23::
    evt.SetSprite(7, 1, "7tree30")
    evt.SetSprite(10, 0, "0")
    evt.SetSprite(51, 1, "7tree30")
    evt.SetSprite(52, 1, "7tree30")
    evt.SetSprite(53, 1, "7tree30")
    evt.SetSprite(54, 1, "7tree30")
    evt.SetSprite(55, 1, "7tree30")
    evt.SetSprite(56, 1, "7tree30")
    evt.SetSprite(57, 1, "7tree30")
    evt.SetSprite(58, 1, "7tree30")
    ::step_33::
    do return end
    ::step_34::
    if IsAtLeast(MapVar(52), 1) then
        goto step_37
    end
    evt.SetSprite(51, 1, "0")
    goto step_38
    ::step_37::
    evt.SetSprite(51, 1, "0")
    ::step_38::
    if IsAtLeast(MapVar(53), 1) then
        goto step_41
    end
    evt.SetSprite(52, 1, "0")
    goto step_42
    ::step_41::
    evt.SetSprite(52, 1, "0")
    ::step_42::
    if IsAtLeast(MapVar(54), 1) then
        goto step_45
    end
    evt.SetSprite(53, 1, "0")
    goto step_46
    ::step_45::
    evt.SetSprite(53, 1, "0")
    ::step_46::
    if IsAtLeast(MapVar(55), 1) then
        goto step_49
    end
    evt.SetSprite(54, 1, "0")
    goto step_50
    ::step_49::
    evt.SetSprite(54, 1, "0")
    ::step_50::
    if IsAtLeast(MapVar(56), 1) then
        goto step_53
    end
    evt.SetSprite(55, 1, "0")
    goto step_54
    ::step_53::
    evt.SetSprite(55, 1, "0")
    ::step_54::
    if IsAtLeast(MapVar(57), 1) then
        goto step_57
    end
    evt.SetSprite(56, 1, "0")
    goto step_58
    ::step_57::
    evt.SetSprite(56, 1, "0")
    ::step_58::
    if IsAtLeast(MapVar(58), 1) then
        goto step_61
    end
    evt.SetSprite(57, 1, "0")
    goto step_62
    ::step_61::
    evt.SetSprite(57, 1, "0")
    ::step_62::
    if IsAtLeast(MapVar(59), 1) then
        goto step_65
    end
    evt.SetSprite(58, 1, "0")
    goto step_66
    ::step_65::
    evt.SetSprite(58, 1, "0")
    ::step_66::
    goto step_8
end)

RegisterEvent(501, "Enter The Erathian Sewer", function()
    evt.MoveToMap(28, -217, 1, 512, 0, 0, 136, 1, "d01.blv")
end, "Enter The Erathian Sewer")

RegisterEvent(502, "Enter Fort Riverstride", function()
    evt.MoveToMap(64, -448, 1, 512, 0, 0, 137, 1, "\t7d31.blv")
end, "Enter Fort Riverstride")

RegisterEvent(503, "Enter Castle Gryphonheart", function()
    evt.MoveToMap(768, 0, 1, 1024, 0, 0, 127, 1, "\t7d33.blv")
end, "Enter Castle Gryphonheart")

RegisterEvent(504, "Door", function()
    if not HasItem(1462) then -- Catherine's Key
        evt.StatusText("This Door is Locked")
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.MoveToMap(-6314, -618, 1873, 1024, 0, 0, 127, 1, "\t7d33.blv")
end, "Door")

RegisterEvent(505, "Enter Fort Riverstride", function()
    evt.MoveToMap(-1262, 587, -1215, 1024, 0, 0, 137, 1, "\t7d31.blv")
end, "Enter Fort Riverstride")

RegisterEvent(506, "Enter The Erathian Sewer", function()
    evt.MoveToMap(6647, 3511, -511, 1024, 0, 0, 136, 1, "d01.blv")
end, "Enter The Erathian Sewer")

RegisterEvent(507, "Enter The Erathian Sewer", function()
    evt.MoveToMap(-6507, 10205, -383, 512, 0, 0, 136, 1, "d01.blv")
end, "Enter The Erathian Sewer")

RegisterEvent(508, "Enter", function()
    evt.MoveToMap(-111, -25, 1, 640, 0, 0, 0, 0, "mdt11.blv")
end, "Enter")

RegisterEvent(509, "Enter", function()
    evt.MoveToMap(-104, 128, 1, 0, 0, 0, 0, 0, "mdt14.blv")
end, "Enter")

