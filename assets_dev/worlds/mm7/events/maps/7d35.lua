-- Nighon Tunnels
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {197, 198, 199},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
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
    textureNames = {"cwb1"},
    spriteNames = {},
    castSpellIds = {6, 15, 18, 24},
    timers = {
    { eventId = 452, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 454, repeating = true, intervalGameMinutes = 4, remainingGameMinutes = 4 },
    { eventId = 456, repeating = true, intervalGameMinutes = 3.5, remainingGameMinutes = 3.5 },
    },
})

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
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

RegisterEvent(196, "Legacy event 196", function()
    if IsQBitSet(QBit(740)) then return end -- Dwarf Bones - I lost it
    AddValue(InventoryItem(1428), 1428) -- Zokarr IV's Skull
    SetQBit(QBit(740)) -- Dwarf Bones - I lost it
end)

RegisterEvent(197, "Legacy event 197", function()
    if IsAtLeast(MapVar(16), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(16), 1)
    evt.SetTexture(2, "cwb1")
end)

RegisterEvent(198, "Legacy event 198", function()
    if IsAtLeast(MapVar(17), 1) then return end
    local randomStep = PickRandomOption(198, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(17), 1)
    evt.SetTexture(3, "cwb1")
end)

RegisterEvent(199, "Legacy event 199", function()
    if IsAtLeast(MapVar(18), 1) then return end
    local randomStep = PickRandomOption(199, 2, {2, 4, 6, 8, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(5, 0, 50)
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    elseif randomStep == 8 then
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
    end
    SetValue(MapVar(18), 1)
    evt.SetTexture(4, "cwb1")
end)

RegisterEvent(451, "Legacy event 451", function()
    evt.MoveToMap(1168, 9584, -143, 0, 0, 0, 0, 0)
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.MoveToMap(1232, 6896, -384, 0, 0, 0, 0, 0)
    evt.CastSpell(6, 7, 4, 13891, 229, 161, 13891, 4912, 161) -- Fireball
    evt.CastSpell(6, 7, 4, 14618, 857, 161, 9284, 857, 161) -- Fireball
end)

RegisterEvent(454, "Legacy event 454", function()
    evt.CastSpell(18, 8, 4, -9861, -3949, -479, -9861, -106, -479) -- Lightning Bolt
end)

RegisterEvent(455, "Legacy event 455", function()
    evt.CastSpell(15, 4, 4, -10624, 3456, -639, -10624, 3456, -639) -- Sparks
end)

RegisterEvent(456, "Legacy event 456", function()
    if evt.CheckSkill(33, 3, 40) then return end
    evt.CastSpell(24, 5, 4, 12023, 15154, -639, 11704, 15854, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 11398, 15726, -639, 11673, 15051, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 11066, 15649, -639, 11360, 14922, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 11179, 14849, -639, 11047, 15637, -479) -- Poison Spray
    evt.CastSpell(24, 5, 4, 10704, 15259, -639, 11620, 15422, -479) -- Poison Spray
end)

RegisterEvent(501, "Leave the Cave", function()
    evt.MoveToMap(-4324, 1811, 3905, 172, 0, 0, 48, 0, "7d07.blv")
end, "Leave the Cave")

RegisterEvent(502, "Leave the Cave", function()
    evt.MoveToMap(-7766, 7703, -1535, 1792, 0, 0, 0, 0, "7d24.blv")
end, "Leave the Cave")

