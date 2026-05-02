-- Emerald Island
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {100},
    onLeave = {},
    openedChestIds = {
    [118] = {1},
    [119] = {2},
    [120] = {3},
    [121] = {4},
    [122] = {5},
    [123] = {6},
    [124] = {7},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {43},
    timers = {
    },
})

RegisterEvent(1, "Welcome to Emerald Isle", nil, "Welcome to Emerald Isle")

RegisterEvent(2, "Crate", function()
    evt.EnterHouse(8) -- The Knight's Blade
end, "Crate")

RegisterEvent(3, "Crate", nil, "Crate")

RegisterEvent(4, "Button", function()
    evt.EnterHouse(43) -- Erik's Armory
end, "Button")

RegisterEvent(5, "Button", nil, "Button")

RegisterEvent(6, "Emerald Enchantments", function()
    evt.EnterHouse(84) -- Emerald Enchantments
end, "Emerald Enchantments")

RegisterEvent(7, "Emerald Enchantments", nil, "Emerald Enchantments")

RegisterEvent(8, "The Blue Bottle", function()
    evt.EnterHouse(116) -- The Blue Bottle
end, "The Blue Bottle")

RegisterEvent(9, "The Blue Bottle", nil, "The Blue Bottle")

RegisterEvent(10, "Healer's Tent", function()
    evt.EnterHouse(310) -- Healer's Tent
end, "Healer's Tent")

RegisterEvent(11, "Healer's Tent", nil, "Healer's Tent")

RegisterEvent(12, "Island Training Grounds", function()
    evt.EnterHouse(1570) -- Island Training Grounds
end, "Island Training Grounds")

RegisterEvent(13, "Island Training Grounds", nil, "Island Training Grounds")

RegisterEvent(14, "Two Palms Tavern", function()
    evt.EnterHouse(239) -- Two Palms Tavern
end, "Two Palms Tavern")

RegisterEvent(15, "Two Palms Tavern", nil, "Two Palms Tavern")

RegisterEvent(16, "Initiate Guild of Fire", function()
    evt.EnterHouse(128) -- Initiate Guild of Fire
end, "Initiate Guild of Fire")

RegisterEvent(17, "Initiate Guild of Fire", nil, "Initiate Guild of Fire")

RegisterEvent(18, "Initiate Guild of Air", function()
    evt.EnterHouse(134) -- Initiate Guild of Air
end, "Initiate Guild of Air")

RegisterEvent(19, "Initiate Guild of Air", nil, "Initiate Guild of Air")

RegisterEvent(20, "Initiate Guild of Spirit", function()
    evt.EnterHouse(152) -- Initiate Guild of Spirit
end, "Initiate Guild of Spirit")

RegisterEvent(21, "Initiate Guild of Spirit", nil, "Initiate Guild of Spirit")

RegisterEvent(22, "Initiate Guild of Body", function()
    evt.EnterHouse(164) -- Initiate Guild of Body
end, "Initiate Guild of Body")

RegisterEvent(23, "Initiate Guild of Body", nil, "Initiate Guild of Body")

RegisterEvent(24, "The Lady Margaret", function()
    evt.EnterHouse(1168) -- The Lady Margaret
end, "The Lady Margaret")

RegisterEvent(25, "Lady Margaret", nil, "Lady Margaret")

RegisterEvent(49, "House", nil, "House")

RegisterEvent(50, "Donna Wyrith's Residence", function()
    evt.EnterHouse(1167) -- Donna Wyrith's Residence
end, "Donna Wyrith's Residence")

RegisterEvent(51, "Mia Lucille' Home", function()
    evt.EnterHouse(1170) -- Mia Lucille' Home
end, "Mia Lucille' Home")

RegisterEvent(52, "Vandalir Residence", function()
    evt.EnterHouse(1171) -- Vandalir Residence
end, "Vandalir Residence")

RegisterEvent(53, "House 227", function()
    evt.EnterHouse(1172) -- House 227
end, "House 227")

RegisterEvent(54, "House 228", function()
    evt.EnterHouse(1173) -- House 228
end, "House 228")

RegisterEvent(55, "House 229", function()
    evt.EnterHouse(1174) -- House 229
end, "House 229")

RegisterEvent(56, "Carolyn Weathers' House", function()
    evt.EnterHouse(1183) -- Carolyn Weathers' House
end, "Carolyn Weathers' House")

RegisterEvent(57, "Tellmar Residence", function()
    evt.EnterHouse(1184) -- Tellmar Residence
end, "Tellmar Residence")

RegisterEvent(58, "House 241", function()
    evt.EnterHouse(1185) -- House 241
end, "House 241")

RegisterEvent(59, "House 242", function()
    evt.EnterHouse(1186) -- House 242
end, "House 242")

RegisterEvent(60, "House 254", function()
    evt.EnterHouse(1198) -- House 254
end, "House 254")

RegisterEvent(61, "House 255", function()
    evt.EnterHouse(1199) -- House 255
end, "House 255")

RegisterEvent(62, "House 255", function()
    evt.EnterHouse(1199) -- House 255
end, "House 255")

RegisterEvent(63, "Anvil", nil, "Anvil")

RegisterEvent(64, "Cart", nil, "Cart")

RegisterEvent(65, "Keg", nil, "Keg")

RegisterEvent(66, "Markham's Headquarters", function()
    evt.EnterHouse(1163) -- Markham's Headquarters
end, "Markham's Headquarters")

RegisterEvent(67, "Markham's Headquarters", nil, "Markham's Headquarters")

RegisterEvent(68, "Guilds", nil, "Guilds")

RegisterEvent(69, "Shops", nil, "Shops")

RegisterEvent(70, "Lord Markham", nil, "Lord Markham")

RegisterEvent(100, "Legacy event 100", function()
    if IsQBitSet(QBit(519)) then -- Finished Scavenger Hunt
        return
    elseif IsQBitSet(QBit(518)) then -- Return a wealthy hat to the Judge on Emerald Island.
        return
    elseif IsQBitSet(QBit(517)) then -- Return a musical instrument to the Judge on Emerald Island.
        return
    elseif IsQBitSet(QBit(516)) then -- Return a floor tile to the Judge on Emerald Island.
        return
    elseif IsQBitSet(QBit(515)) then -- Return a longbow to the Judge on Emerald Island.
        return
    elseif IsQBitSet(QBit(514)) then -- Return a seashell to the Judge on Emerald Island.
        return
    elseif IsQBitSet(QBit(513)) then -- Return a red potion to the Judge on Emerald Island.
        return
    else
        SetQBit(QBit(518)) -- Return a wealthy hat to the Judge on Emerald Island.
        SetQBit(QBit(517)) -- Return a musical instrument to the Judge on Emerald Island.
        SetQBit(QBit(516)) -- Return a floor tile to the Judge on Emerald Island.
        SetQBit(QBit(515)) -- Return a longbow to the Judge on Emerald Island.
        SetQBit(QBit(514)) -- Return a seashell to the Judge on Emerald Island.
        SetQBit(QBit(513)) -- Return a red potion to the Judge on Emerald Island.
        evt.ShowMovie("\"intro post\"", true)
        return
    end
end)

RegisterEvent(101, "Enter The Temple of the Moon", function()
    evt.MoveToMap(-1208, -4225, 366, 320, 0, 0, 131, 1, "7d06.blv")
end, "Enter The Temple of the Moon")

RegisterEvent(102, "Enter the Dragon's Cave", function()
    evt.MoveToMap(752, 2229, 1, 1012, 0, 0, 133, 1, "7d28.blv")
end, "Enter the Dragon's Cave")

RegisterEvent(109, "Well", nil, "Well")

RegisterEvent(110, "Drink from the Well", function()
    if not IsAtLeast(FireResistanceBonus, 50) then
        SetValue(FireResistanceBonus, 50)
        evt.StatusText("+50 Fire Resistance temporary.")
        SetAutonote(258) -- 50 points of temporary Fire resistance from the central town well on Emerald Island.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(111, "Legacy event 111", function()
    SetValue(MapVar(2), 30)
    SetValue(MapVar(3), 30)
end)

RegisterEvent(112, "Drink from the Well", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        return
    end
    SubtractValue(MapVar(2), 1)
    AddValue(CurrentHealth, 5)
    SetAutonote(259) -- 5 Hit Points regained from the well east of the Temple on Emerald Island.
    evt.StatusText("+5 Hit points restored.")
end, "Drink from the Well")

RegisterEvent(113, "Drink from the Well", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(260) -- 5 Spell Points regained from the well west of the Temple on Emerald Island.
        return
    end
    SubtractValue(MapVar(3), 1)
    AddValue(CurrentSpellPoints, 5)
    evt.StatusText("+5 Spell points restored.")
    SetAutonote(260) -- 5 Spell Points regained from the well west of the Temple on Emerald Island.
end, "Drink from the Well")

RegisterEvent(114, "Drink from the Well", function()
    if not IsAtLeast(BaseLuck, 15) then
        if not IsAtLeast(MapVar(4), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(4), 1)
        AddValue(BaseLuck, 2)
        evt.StatusText("+2 Luck permanent")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(115, "Drink from the Well", function()
    if not IsAtLeast(MapVar(6), 3) then
        if IsAtLeast(MapVar(5), 1) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAtLeast(Gold, 201) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAtLeast(BaseLuck, 15) then
            AddValue(MapVar(5), 1)
            AddValue(Gold, 1000)
            AddValue(MapVar(6), 1)
        else
            evt.StatusText("Refreshing!")
        end
    return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(118, "Crate", function()
    evt.OpenChest(1)
end, "Crate")

RegisterEvent(119, "Crate", function()
    evt.OpenChest(2)
end, "Crate")

RegisterEvent(120, "Crate", function()
    evt.OpenChest(3)
end, "Crate")

RegisterEvent(121, "Crate", function()
    evt.OpenChest(4)
end, "Crate")

RegisterEvent(122, "Crate", function()
    evt.OpenChest(5)
end, "Crate")

RegisterEvent(123, "Crate", function()
    evt.OpenChest(6)
end, "Crate")

RegisterEvent(124, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(200, "Legacy event 200", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(358) -- Margaret the Docent
end)

RegisterEvent(201, "Legacy event 201", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(359) -- Margaret the Docent
end)

RegisterEvent(202, "Legacy event 202", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(360) -- Margaret the Docent
end)

RegisterEvent(203, "Legacy event 203", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(361) -- Margaret the Docent
end)

RegisterEvent(204, "Legacy event 204", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(362) -- Margaret the Docent
end)

RegisterEvent(205, "Legacy event 205", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(363) -- Margaret the Docent
end)

RegisterEvent(206, "Legacy event 206", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(364) -- Margaret the Docent
end)

RegisterEvent(207, "Legacy event 207", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(365) -- Margaret the Docent
end)

RegisterEvent(208, "Legacy event 208", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(366) -- Margaret the Docent
end)

RegisterEvent(209, "Legacy event 209", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(367) -- Margaret the Docent
end)

RegisterEvent(210, "Legacy event 210", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(368) -- Margaret the Docent
end)

RegisterEvent(211, "Legacy event 211", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(369) -- Margaret the Docent
end)

RegisterEvent(212, "Legacy event 212", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(370) -- Margaret the Docent
end)

RegisterEvent(213, "Legacy event 213", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(371) -- Margaret the Docent
end)

RegisterEvent(214, "Legacy event 214", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(372) -- Margaret the Docent
end)

RegisterEvent(215, "Legacy event 215", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(373) -- Margaret the Docent
end)

RegisterEvent(216, "Legacy event 216", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(374) -- Margaret the Docent
end)

RegisterEvent(217, "Legacy event 217", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(375) -- Margaret the Docent
end)

RegisterEvent(218, "Legacy event 218", function()
    if IsQBitSet(QBit(529)) then return end -- No more docent babble
    evt.SpeakNPC(376) -- Margaret the Docent
end)

RegisterEvent(219, "Button", function()
    evt.CastSpell(43, 10, 4, 10495, 17724, 2370, 10495, 24144, 4500) -- Death Blossom
end, "Button")

RegisterEvent(220, "Legacy event 220", function()
    if evt.CheckMonstersKilled(ActorKillCheck.Group, 71, 0, false) then -- actor group 71; all matching actors defeated
        evt.SummonMonsters(1, 1, 10, -336, 14512, 0, 71, 0) -- encounter slot 1 "Dragonfly" tier A, count 10, pos=(-336, 14512, 0), actor group 71, no unique actor name
        evt.SummonMonsters(1, 2, 5, 16, 16352, 90, 71, 0) -- encounter slot 1 "Dragonfly" tier B, count 5, pos=(16, 16352, 90), actor group 71, no unique actor name
        evt.SummonMonsters(1, 1, 10, 480, 18288, 6, 71, 0) -- encounter slot 1 "Dragonfly" tier A, count 10, pos=(480, 18288, 6), actor group 71, no unique actor name
    end
end)

