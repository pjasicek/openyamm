-- The Tidewater Caverns
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 65535, 65534, 65533},
    onLeave = {},
    openedChestIds = {
    [176] = {1, 0},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {"c2b"},
    spriteNames = {},
    castSpellIds = {15, 32},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    SetValue(MapVar(2), 1)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(4, "Legacy event 4", function()
    if IsAtLeast(MapVar(2), 1) then return end
    evt.SetDoorState(4, DoorAction.Trigger)
    if evt.CheckSkill(31, 3, 40) then
        if not evt.CheckSkill(33, 3, 40) then
            evt.CastSpell(32, 15, 4, -512, 3936, 246, 608, 3936, 246) -- Ice Blast
            return
        end
        evt.StatusText("You Successfully disarm the trap")
    end
    evt.CastSpell(32, 15, 4, -512, 3936, 246, 608, 3936, 246) -- Ice Blast
end)

RegisterEvent(5, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Door")

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(5, DoorAction.Open)
    SetValue(MapVar(2), 0)
end)

RegisterEvent(8, "Legacy event 8", function()
    SetValue(MapVar(2), 1)
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(176, "Chest", function()
    if not IsQBitSet(QBit(1607)) then -- Promoted to Priest
        if not IsQBitSet(QBit(1608)) then -- Promoted to Honorary Priest
            evt.OpenChest(1)
            SetQBit(QBit(730)) -- Map to Evenmorn - I lost it
            return
        end
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Ore Vein", function()
    if IsAtLeast(MapVar(16), 1) then return end
    local randomStep = PickRandomOption(196, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(16), 1)
    evt.SetTexture(2, "c2b")
end, "Ore Vein")

RegisterEvent(197, "Ore Vein", function()
    if IsAtLeast(MapVar(17), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(17), 1)
    evt.SetTexture(3, "c2b")
end, "Ore Vein")

RegisterEvent(198, "Ore Vein", function()
    if IsAtLeast(MapVar(18), 1) then return end
    local randomStep = PickRandomOption(198, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        evt.StatusText("Cave In !")
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(18), 1)
    evt.SetTexture(4, "c2b")
end, "Ore Vein")

RegisterEvent(416, "Legacy event 416", function()
    evt.CastSpell(15, 4, 3, -7008, 4352, 850, 0, 0, 0) -- Sparks
end)

RegisterEvent(501, "Leave the Tidewater Caverns", function()
    evt.MoveToMap(-19112, 2248, 49, 896, 0, 0, 0, 0, "7out13.odm")
end, "Leave the Tidewater Caverns")

RegisterEvent(65535, "", function()
    if IsAtLeast(MapVar(16), 1) then
        evt.SetTexture(2, "c2b")
    end
end)

RegisterEvent(65534, "", function()
    if IsAtLeast(MapVar(17), 1) then
        evt.SetTexture(3, "c2b")
    end
end)

RegisterEvent(65533, "", function()
    if IsAtLeast(MapVar(18), 1) then
        evt.SetTexture(4, "c2b")
    end
end)

