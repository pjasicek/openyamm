-- Zokarr's Tomb
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Door")

RegisterEvent(176, "Legacy event 176", function()
    evt.OpenChest(1)
end)

RegisterEvent(177, "Legacy event 177", function()
    evt.OpenChest(2)
end)

RegisterEvent(178, "Legacy event 178", function()
    evt.OpenChest(3)
end)

RegisterEvent(179, "Legacy event 179", function()
    evt.OpenChest(4)
end)

RegisterEvent(180, "Legacy event 180", function()
    evt.OpenChest(5)
end)

RegisterEvent(181, "Legacy event 181", function()
    evt.OpenChest(6)
end)

RegisterEvent(182, "Legacy event 182", function()
    evt.OpenChest(7)
end)

RegisterEvent(183, "Legacy event 183", function()
    evt.OpenChest(8)
end)

RegisterEvent(184, "Legacy event 184", function()
    evt.OpenChest(9)
end)

RegisterEvent(185, "Legacy event 185", function()
    evt.OpenChest(10)
end)

RegisterEvent(186, "Legacy event 186", function()
    evt.OpenChest(11)
end)

RegisterEvent(187, "Legacy event 187", function()
    evt.OpenChest(12)
end)

RegisterEvent(188, "Legacy event 188", function()
    evt.OpenChest(13)
end)

RegisterEvent(189, "Legacy event 189", function()
    evt.OpenChest(14)
end)

RegisterEvent(190, "Legacy event 190", function()
    evt.OpenChest(15)
end)

RegisterEvent(191, "Legacy event 191", function()
    evt.OpenChest(16)
end)

RegisterEvent(192, "Legacy event 192", function()
    evt.OpenChest(17)
end)

RegisterEvent(193, "Legacy event 193", function()
    evt.OpenChest(18)
end)

RegisterEvent(194, "Legacy event 194", function()
    evt.OpenChest(19)
end)

RegisterEvent(195, "Legacy event 195", function()
    evt.OpenChest(0)
end)

RegisterEvent(376, "Legacy event 376", function()
    if IsQBitSet(QBit(539)) then -- Find the lost meditation spot in the Dwarven Barrows.
        evt.SpeakNPC(394) -- Bartholomew Hume
    end
end)

RegisterEvent(377, "Legacy event 377", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(577)) then -- Barrow downs. Returned the bones of the Dwarf King. Arch Druid promo quest.
        return
    elseif IsQBitSet(QBit(566)) then -- Retrieve the bones of the Dwarf King from the tunnels between Stone City and Nighon and place them in their proper resting place in the Barrow Downs, then return to Anthony Green in the Tularean Forest.
        if HasItem(1428) then -- Zokarr IV's Skull
            RemoveItem(1428) -- Zokarr IV's Skull
            SetQBit(QBit(577)) -- Barrow downs. Returned the bones of the Dwarf King. Arch Druid promo quest.
            evt.ForPlayer(Players.All)
            SetQBit(QBit(757)) -- Congratulations - For Blinging
            ClearQBit(QBit(757)) -- Congratulations - For Blinging
            ClearQBit(QBit(740)) -- Dwarf Bones - I lost it
        end
        return
    else
        return
    end
end)

RegisterEvent(451, "Pillar", function()
    SetValue(MapVar(2), 1)
end, "Pillar")

RegisterEvent(452, "Pillar", function()
    SetValue(MapVar(3), 1)
end, "Pillar")

RegisterEvent(453, "Pillar", function()
    SetValue(MapVar(4), 1)
end, "Pillar")

RegisterEvent(454, "Pillar", function()
    SetValue(MapVar(5), 1)
end, "Pillar")

RegisterEvent(455, "Door", function()
    evt.SetDoorState(5, DoorAction.Trigger)
end, "Door")

RegisterEvent(456, "Legacy event 456", function()
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end)

RegisterEvent(501, "Legacy event 501", function()
    local randomStep = PickRandomOption(501, 1, {1, 1, 1, 3, 3, 3})
    if randomStep == 1 then
        evt.MoveToMap(335, -1064, 1, 768, 0, 0, 0, 0)
        return
    elseif randomStep == 3 then
        evt.MoveToMap(-426, 281, -15, 1664, 0, 0, 0, 0)
        return
    end
end)

