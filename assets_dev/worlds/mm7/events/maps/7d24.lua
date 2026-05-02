-- Stone City
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 200, 201},
    onLeave = {},
    openedChestIds = {
    [176] = {0},
    [177] = {1},
    [178] = {2},
    [179] = {3},
    [180] = {4},
    [181] = {5},
    [182] = {6},
    [183] = {7},
    [184] = {8},
    [185] = {9},
    [186] = {10},
    [187] = {11},
    [188] = {12},
    [189] = {13},
    [190] = {14},
    [191] = {15},
    [192] = {16},
    [193] = {17},
    [194] = {18},
    [195] = {19},
    },
    textureNames = {"cwb1"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(611)) then return end -- Chose the path of Light
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(151, "Button", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Button")

RegisterEvent(152, "Button", function()
    evt.SetDoorState(10, DoorAction.Open)
end, "Button")

RegisterEvent(153, "Button", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Button")

RegisterEvent(154, "Button", function()
    evt.SetDoorState(11, DoorAction.Open)
end, "Button")

RegisterEvent(176, "Cabinet", function()
    evt.OpenChest(0)
end, "Cabinet")

RegisterEvent(177, "Cabinet", function()
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(178, "Cabinet", function()
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(179, "Cabinet", function()
    evt.OpenChest(3)
end, "Cabinet")

RegisterEvent(180, "Cabinet", function()
    evt.OpenChest(4)
end, "Cabinet")

RegisterEvent(181, "Cabinet", function()
    evt.OpenChest(5)
end, "Cabinet")

RegisterEvent(182, "Cabinet", function()
    evt.OpenChest(6)
end, "Cabinet")

RegisterEvent(183, "Cabinet", function()
    evt.OpenChest(7)
end, "Cabinet")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(196, "Take a Drink", function()
    evt.StatusText("Refreshing")
end, "Take a Drink")

RegisterEvent(197, "Take a Drink", function()
    evt.StatusText("Refreshing")
end, "Take a Drink")

RegisterEvent(198, "Take a Drink", function()
    evt.StatusText("Refreshing")
end, "Take a Drink")

RegisterEvent(199, "Bookcase", function()
    evt.StatusText("Nothing Here")
end, "Bookcase")

RegisterEvent(200, "Ore Vein", function()
    if IsAtLeast(MapVar(16), 1) then return end
    local randomStep = PickRandomOption(200, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    end
    SetValue(MapVar(16), 1)
    evt.SetTexture(2, "cwb1")
end, "Ore Vein")

RegisterEvent(201, "Ore Vein", function()
    if IsAtLeast(MapVar(17), 1) then return end
    local randomStep = PickRandomOption(201, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    end
    SetValue(MapVar(17), 1)
    evt.SetTexture(3, "cwb1")
end, "Ore Vein")

RegisterEvent(415, "Obelisk", function()
    if IsQBitSet(QBit(689)) then return end -- Visited Obelisk in Area 39
    evt.StatusText("___d___d")
    SetAutonote(322) -- Obelisk message #14: ___d___d
    evt.ForPlayer(Players.All)
    SetQBit(QBit(689)) -- Visited Obelisk in Area 39
end, "Obelisk")

RegisterEvent(416, "Enter the Throne Room", function()
    if not HasAward(Award(3)) then -- Removed goblins from Castle Harmondale
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        evt.StatusText("The Door is Locked")
        return
    end
    evt.EnterHouse(216) -- Throne Room
end, "Enter the Throne Room")

RegisterEvent(417, "The Balanced Axe", function()
    evt.EnterHouse(17) -- The Balanced Axe
end, "The Balanced Axe")

RegisterEvent(418, "The Balanced Axe", nil, "The Balanced Axe")

RegisterEvent(419, "The Polished Pauldron", function()
    evt.EnterHouse(57) -- The Polished Pauldron
end, "The Polished Pauldron")

RegisterEvent(420, "The Polished Pauldron", nil, "The Polished Pauldron")

RegisterEvent(421, "Delicate Things", function()
    evt.EnterHouse(93) -- Delicate Things
end, "Delicate Things")

RegisterEvent(422, "Delicate Things", nil, "Delicate Things")

RegisterEvent(423, "Potent Potions & Brews", function()
    evt.EnterHouse(124) -- Potent Potions & Brews
end, "Potent Potions & Brews")

RegisterEvent(424, "Potent Potions & Brews", nil, "Potent Potions & Brews")

RegisterEvent(425, "Temple of Stone", function()
    evt.EnterHouse(321) -- Temple of Stone
end, "Temple of Stone")

RegisterEvent(426, "Temple of Stone", nil, "Temple of Stone")

RegisterEvent(427, "War College", function()
    evt.EnterHouse(1579) -- War College
end, "War College")

RegisterEvent(428, "War College", nil, "War College")

RegisterEvent(429, "Grogg's Grog", function()
    evt.EnterHouse(252) -- Grogg's Grog
end, "Grogg's Grog")

RegisterEvent(430, "Grogg's Grog", nil, "Grogg's Grog")

RegisterEvent(431, "Mineral Wealth", function()
    evt.EnterHouse(293) -- Mineral Wealth
end, "Mineral Wealth")

RegisterEvent(432, "Mineral Wealth", nil, "Mineral Wealth")

RegisterEvent(433, "Master Guild of Earth", function()
    evt.EnterHouse(148) -- Master Guild of Earth
end, "Master Guild of Earth")

RegisterEvent(434, "Master Guild of Earth", nil, "Master Guild of Earth")

RegisterEvent(435, "Cabinet", function()
    evt.EnterHouse(1051) -- Keenedge Residence
end, "Cabinet")

RegisterEvent(436, "Cabinet", function()
    evt.EnterHouse(1052) -- Seline's House
end, "Cabinet")

RegisterEvent(437, "Cabinet", function()
    evt.EnterHouse(1053) -- Welman Residence
end, "Cabinet")

RegisterEvent(438, "Cabinet", function()
    evt.EnterHouse(1054) -- Thain's House
end, "Cabinet")

RegisterEvent(439, "Cabinet", function()
    evt.EnterHouse(1055) -- Gizmo's
end, "Cabinet")

RegisterEvent(440, "Cabinet", function()
    evt.EnterHouse(1056) -- Spark's House
end, "Cabinet")

RegisterEvent(441, "Cabinet", function()
    evt.EnterHouse(1057) -- Thorinson Residence
end, "Cabinet")

RegisterEvent(442, "Cabinet", function()
    evt.EnterHouse(1058) -- Urthsmite Residence
end, "Cabinet")

RegisterEvent(443, "Cabinet", function()
    evt.EnterHouse(216) -- Throne Room
end, "Cabinet")

RegisterEvent(444, "House", nil, "House")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(780) -- Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1)
    SetValue(MapVar(6), 2)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Stone City", function()
    evt.MoveToMap(-2384, 3064, 2091, 0, 0, 0, 0, 0, "out11.odm")
end, "Leave Stone City")

RegisterEvent(502, "Leave Stone City", function()
    evt.MoveToMap(522, -808, 1, 1024, 0, 0, 0, 0, "7d35.blv")
end, "Leave Stone City")

