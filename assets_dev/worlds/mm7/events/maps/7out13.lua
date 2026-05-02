-- Tatalia
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 454},
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
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(612)) then -- Chose the path of Dark
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
    end
end)

RegisterEvent(3, "The Missing Link", function()
    evt.EnterHouse(55) -- The Missing Link
end, "The Missing Link")

RegisterEvent(4, "The Missing Link", nil, "The Missing Link")

RegisterEvent(5, "Dry Saddles", function()
    evt.EnterHouse(466) -- Dry Saddles
end, "Dry Saddles")

RegisterEvent(6, "Dry Saddles", nil, "Dry Saddles")

RegisterEvent(7, "Narwhale", function()
    evt.EnterHouse(491) -- Narwhale
end, "Narwhale")

RegisterEvent(8, "Narwhale", nil, "Narwhale")

RegisterEvent(9, "The Order of Tatalia", function()
    evt.EnterHouse(319) -- The Order of Tatalia
end, "The Order of Tatalia")

RegisterEvent(10, "The Order of Tatalia", nil, "The Order of Tatalia")

RegisterEvent(11, "Training Essentials", function()
    evt.EnterHouse(1577) -- Training Essentials
end, "Training Essentials")

RegisterEvent(12, "Training Essentials", nil, "Training Essentials")

RegisterEvent(13, "The Loyal Mercenary", function()
    evt.EnterHouse(250) -- The Loyal Mercenary
end, "The Loyal Mercenary")

RegisterEvent(14, "The Loyal Mercenary", nil, "The Loyal Mercenary")

RegisterEvent(15, "The Depository", function()
    evt.EnterHouse(291) -- The Depository
end, "The Depository")

RegisterEvent(16, "The Depository", nil, "The Depository")

RegisterEvent(17, "Master Guild of Mind", function()
    evt.EnterHouse(160) -- Master Guild of Mind
end, "Master Guild of Mind")

RegisterEvent(18, "Master Guild of Mind", nil, "Master Guild of Mind")

RegisterEvent(19, "Vander's Blades & Bows", function()
    evt.EnterHouse(15) -- Vander's Blades & Bows
end, "Vander's Blades & Bows")

RegisterEvent(20, "Vander's Blades & Bows", nil, "Vander's Blades & Bows")

RegisterEvent(21, "Alloyed Weapons", function()
    evt.EnterHouse(19) -- Alloyed Weapons
end, "Alloyed Weapons")

RegisterEvent(22, "Alloyed Weapons", nil, "Alloyed Weapons")

RegisterEvent(23, "Alloyed Armor and Shields", function()
    evt.EnterHouse(59) -- Alloyed Armor and Shields
end, "Alloyed Armor and Shields")

RegisterEvent(24, "Alloyed Armor and Shields", nil, "Alloyed Armor and Shields")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Steele Residence", function()
    evt.EnterHouse(1025) -- Steele Residence
end, "Steele Residence")

RegisterEvent(53, "Conscience Home", function()
    evt.EnterHouse(1026) -- Conscience Home
end, "Conscience Home")

RegisterEvent(54, "Everil's House", function()
    evt.EnterHouse(1027) -- Everil's House
end, "Everil's House")

RegisterEvent(57, "Tricia's House", function()
    evt.EnterHouse(1030) -- Tricia's House
end, "Tricia's House")

RegisterEvent(58, "Isram's House", function()
    evt.EnterHouse(1031) -- Isram's House
end, "Isram's House")

RegisterEvent(59, "Stonecleaver Residence", function()
    evt.EnterHouse(1032) -- Stonecleaver Residence
end, "Stonecleaver Residence")

RegisterEvent(61, "Calindra's Home", function()
    evt.EnterHouse(1034) -- Calindra's Home
end, "Calindra's Home")

RegisterEvent(62, "Brother Bombah's", function()
    evt.EnterHouse(1035) -- Brother Bombah's
end, "Brother Bombah's")

RegisterEvent(63, "Redding Residence", function()
    evt.EnterHouse(1036) -- Redding Residence
end, "Redding Residence")

RegisterEvent(65, "Fist's House", function()
    evt.EnterHouse(1038) -- Fist's House
end, "Fist's House")

RegisterEvent(66, "Wacko's", function()
    evt.EnterHouse(1039) -- Wacko's
end, "Wacko's")

RegisterEvent(67, "Weldric's Home", function()
    evt.EnterHouse(1040) -- Weldric's Home
end, "Weldric's Home")

RegisterEvent(69, "Visconti Residence", function()
    evt.EnterHouse(1042) -- Visconti Residence
end, "Visconti Residence")

RegisterEvent(70, "Arin Residence", function()
    evt.EnterHouse(1043) -- Arin Residence
end, "Arin Residence")

RegisterEvent(73, "Sampson Residence", function()
    evt.EnterHouse(1046) -- Sampson Residence
end, "Sampson Residence")

RegisterEvent(75, "Taren's House", function()
    evt.EnterHouse(1048) -- Taren's House
end, "Taren's House")

RegisterEvent(76, "Moore Residence", function()
    evt.EnterHouse(1049) -- Moore Residence
end, "Moore Residence")

RegisterEvent(77, "Rothham's House", function()
    evt.EnterHouse(1050) -- Rothham's House
end, "Rothham's House")

RegisterEvent(78, "Greydawn Residence", function()
    evt.EnterHouse(1005) -- Greydawn Residence
end, "Greydawn Residence")

RegisterEvent(79, "Stormeye's House", function()
    evt.EnterHouse(1006) -- Stormeye's House
end, "Stormeye's House")

RegisterEvent(80, "Bremen Residence", function()
    evt.EnterHouse(1007) -- Bremen Residence
end, "Bremen Residence")

RegisterEvent(81, "Riverstone House", function()
    evt.EnterHouse(989) -- Riverstone House
end, "Riverstone House")

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
    if IsQBitSet(QBit(582)) then -- Placed Golem left leg
        return
    elseif IsQBitSet(QBit(733)) then -- Right arm - I lost it
        return
    else
        SetQBit(QBit(733)) -- Right arm - I lost it
        return
    end
end, "Chest ")

RegisterEvent(201, "Well", nil, "Well")

RegisterEvent(202, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(21)) then
        if not IsAutonoteSet(285) then -- 20 points of temporary Armor Class from the well in the northern village in Tatalia.
            SetAutonote(285) -- 20 points of temporary Armor Class from the well in the northern village in Tatalia.
        end
        AddValue(ArmorClassBonus, 20)
        SetPlayerBit(PlayerBit(21))
        evt.StatusText("+20 AC (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(203, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(20)) then
        if not IsAutonoteSet(284) then -- 20 points of temporary Air resistance from the well in the eastern section of Tidewater in Tatalia.
            SetAutonote(284) -- 20 points of temporary Air resistance from the well in the eastern section of Tidewater in Tatalia.
        end
        AddValue(AirResistanceBonus, 20)
        SetPlayerBit(PlayerBit(20))
        evt.StatusText("+20 Air Resistance (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(204, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(19)) then
        if not IsAutonoteSet(283) then -- 2 points of permanent Speed from the well in the western section of Tidewater in Tatalia.
            SetAutonote(283) -- 2 points of permanent Speed from the well in the western section of Tidewater in Tatalia.
        end
        AddValue(BaseSpeed, 2)
        SetPlayerBit(PlayerBit(19))
        evt.StatusText("+2 Speed (Permanent)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(205, "The Mercenary Guild ", nil, "The Mercenary Guild ")

RegisterEvent(206, "Tidewater Caverns", nil, "Tidewater Caverns")

RegisterEvent(207, "Lord Markham's Manor", nil, "Lord Markham's Manor")

RegisterEvent(208, "Tatalia", nil, "Tatalia")

RegisterEvent(209, "East to Steadwick", nil, "East to Steadwick")

RegisterEvent(210, "Wharf", nil, "Wharf")

RegisterEvent(211, "Temple", nil, "Temple")

RegisterEvent(212, "Stables", nil, "Stables")

RegisterEvent(213, "Stone", nil, "Stone")

RegisterEvent(214, "Drink", function()
    if not IsAtLeast(DiseasedYellow, 0) then
        if IsAtLeast(DiseasedRed, 0) then
            evt.StatusText("You decide it would be a bad idea to try that again.")
            return
        elseif IsAtLeast(Unconscious, 0) then
            evt.StatusText("You decide it would be a bad idea to try that again.")
        else
            local randomStep = PickRandomOption(214, 4, {5, 7, 9})
            if randomStep == 5 then
                SetValue(DiseasedYellow, 0)
            elseif randomStep == 7 then
                SetValue(DiseasedRed, 0)
            elseif randomStep == 9 then
                SetValue(Unconscious, 0)
            end
            evt.StatusText("You do not feel well.")
        end
    return
    end
    evt.StatusText("You decide it would be a bad idea to try that again.")
end, "Drink")

RegisterEvent(215, "North ", nil, "North ")

RegisterEvent(401, "Altar", function()
    if not IsQBitSet(QBit(561)) then return end -- Visit the three stonehenge monoliths in Tatalia, the Evenmorn Islands, and Avlee, then return to Anthony Green in the Tularean Forest.
    if IsQBitSet(QBit(562)) then -- Visited all stonehenges
        return
    elseif IsQBitSet(QBit(564)) then -- Visited stonehenge 2 (area 13)
        return
    else
        evt.ForPlayer(Players.All)
        SetQBit(QBit(564)) -- Visited stonehenge 2 (area 13)
        evt.ForPlayer(Players.All)
        SetQBit(QBit(757)) -- Congratulations - For Blinging
        ClearQBit(QBit(757)) -- Congratulations - For Blinging
        if IsQBitSet(QBit(563)) and IsQBitSet(QBit(565)) then -- Visited stonehenge 1 (area 9)
            evt.ForPlayer(Players.All)
            SetQBit(QBit(562)) -- Visited all stonehenges
        else
        end
        return
    end
end, "Altar")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if IsQBitSet(QBit(714)) then return end -- Place item 618 in out13(statue)
    if not IsQBitSet(QBit(712)) then return end -- Retrieve the three statuettes and place them on the shrines in the Bracada Desert, Tatalia, and Avlee, then return to Thom Lumbra in the Tularean Forest.
    evt.ForPlayer(Players.All)
    if HasItem(1420) then -- Eagle Statuette
        evt.SetSprite(25, 1, "0")
        RemoveItem(1420) -- Eagle Statuette
        SetQBit(QBit(714)) -- Place item 618 in out13(statue)
    end
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(687)) then return end -- Visited Obelisk in Area 13
    evt.StatusText("e_laru_a")
    SetAutonote(320) -- Obelisk message #12: e_laru_a
    evt.ForPlayer(Players.All)
    SetQBit(QBit(687)) -- Visited Obelisk in Area 13
end, "Obelisk")

RegisterEvent(454, "Legacy event 454", function()
    if not IsQBitSet(QBit(526)) then return end -- Accepted Fireball wand from Malwick
    if IsQBitSet(QBit(702)) then -- Finished with Malwick & Assc.
        return
    elseif IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
        return
    elseif IsQBitSet(QBit(694)) then -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
        if IsAtLeast(Counter(5), 672) then
            evt.ForPlayer(Players.All)
            SetQBit(QBit(695)) -- Failed either goto or do guild quest
            evt.SpeakNPC(437) -- Messenger
        end
        return
    elseif IsQBitSet(QBit(693)) then -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
        if IsAtLeast(Counter(5), 336) then
            evt.ForPlayer(Players.All)
            SetQBit(QBit(695)) -- Failed either goto or do guild quest
            evt.SpeakNPC(437) -- Messenger
        end
        return
    else
        return
    end
end)

RegisterEvent(455, "Legacy event 455", nil)

RegisterEvent(500, "Legacy event 500", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if evt.CheckSeason(1) then return end
    if evt.CheckSeason(0) then
    end
end)

RegisterEvent(501, "Enter the Wine Cellar", function()
    evt.MoveToMap(601, -512, 1, 1024, 0, 0, 156, 1, "7d16.blv")
end, "Enter the Wine Cellar")

RegisterEvent(502, "Enter the Mercenary Guild", function()
    if IsQBitSet(QBit(526)) then -- Accepted Fireball wand from Malwick
        if IsQBitSet(QBit(702)) then -- Finished with Malwick & Assc.
            evt.MoveToMap(886, 2601, 1, 474, 0, 0, 154, 1, "\t7d20.blv")
            return
        elseif IsQBitSet(QBit(695)) then -- Failed either goto or do guild quest
            evt.SetNPCGreeting(438, 283) -- Niles Stantley greeting 283
            ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            evt.SpeakNPC(438) -- Niles Stantley
            return
        elseif IsQBitSet(QBit(693)) then -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
            if IsAtLeast(Counter(5), 336) then
                evt.ForPlayer(Players.All)
                SetQBit(QBit(695)) -- Failed either goto or do guild quest
                evt.SetNPCGreeting(438, 283) -- Niles Stantley greeting 283
                ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
                ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            end
            evt.SpeakNPC(438) -- Niles Stantley
            return
        elseif IsQBitSet(QBit(694)) then -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            if IsAtLeast(Counter(5), 672) then
                evt.ForPlayer(Players.All)
                SetQBit(QBit(695)) -- Failed either goto or do guild quest
                evt.SetNPCGreeting(438, 283) -- Niles Stantley greeting 283
                ClearQBit(QBit(693)) -- Go to the Mercenary Guild in Tatalia and talk to Niles Stantley within two weeks. - Goto Merc Guild
                ClearQBit(QBit(694)) -- Steal the Tapestry from your associate's Castle and return it to Niles Stantley in the Mercenary Guild in Tatalia. - Do the Merc Guild Quest
            end
            evt.SpeakNPC(438) -- Niles Stantley
        else
            evt.MoveToMap(886, 2601, 1, 474, 0, 0, 154, 1, "\t7d20.blv")
        end
    return
    end
    evt.MoveToMap(886, 2601, 1, 474, 0, 0, 154, 1, "\t7d20.blv")
end, "Enter the Mercenary Guild")

RegisterEvent(503, "Enter the Tidewater Caverns", function()
    evt.MoveToMap(-1944, -2052, 1, 0, 0, 0, 155, 1, "\t7d17.blv")
end, "Enter the Tidewater Caverns")

RegisterEvent(504, "Enter Lord Markham's Manor", function()
    evt.MoveToMap(-33, -600, 1, 512, 0, 0, 0, 0, "\t7d18.blv")
end, "Enter Lord Markham's Manor")

RegisterEvent(505, "Enter the Cave", function()
    evt.MoveToMap(-2568, -143, 97, 257, 0, 0, 0, 0, "mdt09.blv")
end, "Enter the Cave")

