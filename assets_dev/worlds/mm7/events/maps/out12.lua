-- The Land of the Giants
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
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
    contextActions = {
    [52] = { kind = "enter_house", source = "opcode", houseId = 1150, targetName = "Lasiter's Home" },
    [151] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [152] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [153] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [154] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [155] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [156] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [157] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [158] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [159] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [160] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [161] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [162] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [163] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [164] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [165] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [166] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [167] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [168] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [169] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [170] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [202] = { kind = "well", source = "title" },
    [205] = { kind = "well", source = "title" },
    [452] = { kind = "travel", source = "opcode", targetMap = "7out02.odm", targetName = "Harmondale" },
    [453] = { kind = "obelisk", source = "title" },
    [501] = { kind = "enter_dungeon", source = "opcode", targetMap = "7d27.blv", targetName = "Colony Zod" },
    [502] = { kind = "enter_dungeon", source = "opcode", targetMap = "7d36.blv", targetName = "Tunnels to Eeofol" },
    [503] = { kind = "enter_dungeon", source = "opcode", targetMap = "mdt12.blv", targetName = "The Dragon Caves" },
    [504] = { kind = "enter_dungeon", source = "opcode", targetMap = "mdt12.blv", targetName = "The Dragon Caves" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(775)) then -- Area 12 Archibald only once
        return
    elseif IsQBitSet(QBit(616)) then -- Go to Colony Zod in the Land of the Giants and slay Xenofex then return to Resurectra in Castle Lambent in Celeste.
        SetQBit(QBit(775)) -- Area 12 Archibald only once
        evt.SetNPCGreeting(462, 316) -- Archibald Ironfist greeting: ::You receive a telepathic message:: My…Lords. My name is Archibald Ironfist. You've probably heard of me--it is I who, up until recently, was the ruler of the Pit. With my retirement, I find myself no longer concerned with the affairs of state. I know that we were adversaries, but I am forced to ask for your help. In return, I think I can help you.I see that you're on your way to do battle with the devils, and I want to make sure it goes well. With the aid of equipment I have found in my new laboratory, I have discovered that my brother Roland, husband to Queen Catherine of Erathia, remains imprisoned by the devils in their foul, ah, dwelling.Please rescue him! Not even I can bear to think of my brother in those conditions! To help you along, I offer this weapon. It was...found by my loyal servant sergeant Piridak, amongst my advisor's personal belongings. I hope it helps.
        evt.SpeakNPC(462) -- Archibald Ironfist
        AddValue(InventoryItem(866), 866) -- Blaster
        return
    elseif IsQBitSet(QBit(635)) then -- Go to Colony Zod in the Land of the Giants and slay Xenofex then return to Kastore in the Pit.
        evt.SetNPCGreeting(462, 317) -- Archibald Ironfist greeting: ::You receive a telepathic message:: My friends. I know you are working with my old advisors, but I must ask for your help one more time.With the aid of equipment I have found in my new laboratory, I have discovered that my brother Roland, husband to Queen Catherine of Erathia, remains imprisoned by the devils in their foul, ah, dwelling. I overheard that you're on your way to do battle with them (this equipment really is wonderful), and I want to make sure it goes well. My brother has stolen the key to their leader's chambers, and has hidden it in the beastly cage they're keeping him in. Please rescue him! Not even I can bear to think of my brother in those conditions! To help you along, I offer this weapon. It was...found by my loyal servant sergeant Piridak, amongst my advisor's personal belongings. I hope it helps.
        SetQBit(QBit(775)) -- Area 12 Archibald only once
        evt.SpeakNPC(462) -- Archibald Ironfist
        AddValue(InventoryItem(866), 866) -- Blaster
    else
        SetQBit(QBit(775)) -- Area 12 Archibald only once
        evt.SetNPCGreeting(462, 316) -- Archibald Ironfist greeting: ::You receive a telepathic message:: My…Lords. My name is Archibald Ironfist. You've probably heard of me--it is I who, up until recently, was the ruler of the Pit. With my retirement, I find myself no longer concerned with the affairs of state. I know that we were adversaries, but I am forced to ask for your help. In return, I think I can help you.I see that you're on your way to do battle with the devils, and I want to make sure it goes well. With the aid of equipment I have found in my new laboratory, I have discovered that my brother Roland, husband to Queen Catherine of Erathia, remains imprisoned by the devils in their foul, ah, dwelling.Please rescue him! Not even I can bear to think of my brother in those conditions! To help you along, I offer this weapon. It was...found by my loyal servant sergeant Piridak, amongst my advisor's personal belongings. I hope it helps.
        evt.SpeakNPC(462) -- Archibald Ironfist
        AddValue(InventoryItem(866), 866) -- Blaster
    end
return
end)

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Lasiter's Home", function()
    evt.EnterHouse(1150) -- Lasiter's Home
end, "Lasiter's Home")

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
    if not IsAtLeast(MapVar(2), 1) then
        AddValue(MightBonus, 100)
        SetValue(MapVar(2), 1)
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(203, "Colony Zod", nil, "Colony Zod")

RegisterEvent(204, "Tunnel Entrance", nil, "Tunnel Entrance")

RegisterEvent(205, "Well", function()
    if not IsAtLeast(Gold, 5000) then
        if not IsAtLeast(Gold, 4999) then
            return
        end
        SubtractValue(Gold, 4999)
        evt.StatusText("You make a wish")
        return
    end
    if not IsAtLeast(Gold, 5000) then
        return
    end
    SubtractValue(Gold, 5000)
    local randomStep = PickRandomOption(205, 4, {5, 14, 22})
    if randomStep == 5 then
        local randomStep = PickRandomOption(205, 6, {7, 9, 11, 12})
        if randomStep == 7 then
            SetValue(MapVar(0), 0)
        elseif randomStep == 9 then
            SetValue(Age, 0)
            AddValue(Experience, 5000)
        elseif randomStep == 12 then
            SetValue(Eradicated, 0)
        end
    elseif randomStep == 14 then
        local randomStep = PickRandomOption(205, 15, {16, 18, 20})
        if randomStep == 16 then
            AddValue(AirResistanceBonus, 50)
        elseif randomStep == 18 then
            AddValue(FireResistanceBonus, 50)
        elseif randomStep == 20 then
            SetValue(MajorCondition, 0)
        end
    elseif randomStep == 22 then
        local randomStep = PickRandomOption(205, 23, {24, 26, 28})
        if randomStep == 24 then
            AddValue(Gold, 10000)
        elseif randomStep == 26 then
            AddValue(SkillPoints, 10)
        elseif randomStep == 28 then
            SubtractValue(ArmorClassBonus, 50)
        end
    end
    evt.StatusText("You make a wish")
end, "Well")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    SetQBit(QBit(758)) -- Visited The Land of the giants
    evt.MoveToMap(7598, -5250, 129, 1024, 0, 0, 0, 0, "7out02.odm") -- Harmondale
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(686)) then return end -- Visited Obelisk in Area 12
    evt.StatusText("veoseo_l")
    SetAutonote(319) -- Obelisk message #11: veoseo_l
    evt.ForPlayer(Players.All)
    SetQBit(QBit(686)) -- Visited Obelisk in Area 12
end, "Obelisk")

RegisterEvent(500, nil, function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if evt.CheckSeason(1) then return end
    if evt.CheckSeason(0) then
    end
end)

RegisterEvent(501, "Enter Colony Zod", function()
    evt.MoveToMap(2648, -1372, 1, 1024, 0, 0, 153, 1, "7d27.blv") -- Colony Zod
end, "Enter Colony Zod")

RegisterEvent(502, "Enter the Cave", function()
    evt.MoveToMap(9165, 15139, -583, 24, 0, 0, 48, 0, "7d36.blv") -- Tunnels to Eeofol
end, "Enter the Cave")

RegisterEvent(503, "Enter the Cave", function()
    evt.MoveToMap(-54, 3470, 1, 1536, 0, 0, 0, 0, "mdt12.blv") -- The Dragon Caves
end, "Enter the Cave")

RegisterEvent(504, "Enter the Cave", function()
    evt.MoveToMap(19341, 21323, 1, 256, 0, 0, 0, 0, "mdt12.blv") -- The Dragon Caves
end, "Enter the Cave")

