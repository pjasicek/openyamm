-- Supreme Temple of Baa
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapEvents = {34},
    onLoad = {33},
    onLeave = {},
    openedChestIds = {
    [17] = {1},
    [18] = {2},
    [19] = {3},
    [20] = {4},
    [21] = {5},
    [22] = {6},
    [23] = {7},
    [24] = {8},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "title" },
    [2] = { kind = "open_door", source = "title" },
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "opcode" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "opcode" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "opcode" },
    [12] = { kind = "use_switch", source = "title" },
    [13] = { kind = "use_switch", source = "title" },
    [14] = { kind = "use_switch", source = "title" },
    [15] = { kind = "use_switch", source = "title" },
    [16] = { kind = "open_door", source = "opcode" },
    [17] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [18] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [19] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [20] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [21] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [22] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [23] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [24] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [30] = { kind = "open_door", source = "opcode" },
    [31] = { kind = "passage", source = "opcode", targetMap = "sewer.blv", targetName = "Free Haven Sewer" },
    [32] = { kind = "generic_event", source = "opcode" },
    [34] = { kind = "secret_event", source = "heuristic", hidden = true },
    [35] = { kind = "leave_dungeon", source = "opcode", targetMap = "outa3.odm", targetName = "Hermit's Isle" },
    [37] = { kind = "secret_event", source = "heuristic", hidden = true },
    [40] = { kind = "shrine", source = "title" },
    [41] = { kind = "shrine", source = "title" },
    [42] = { kind = "shrine", source = "title" },
    [43] = { kind = "shrine", source = "title" },
    [44] = { kind = "shrine", source = "title" },
    [45] = { kind = "shrine", source = "title" },
    [46] = { kind = "shrine", source = "title" },
    },
    textureNames = {},
    spriteNames = {"crysdisc"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, nil, function()
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, nil, function()
    evt.SetDoorState(9, DoorAction.Close)
end)

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, nil, function()
    evt.SetDoorState(11, DoorAction.Close)
end)

RegisterEvent(12, "Switch", function()
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Switch")

RegisterEvent(13, "Switch", function()
    evt.SetDoorState(17, DoorAction.Trigger)
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(14, DoorAction.Trigger)
end, "Switch")

RegisterEvent(14, "Switch", function()
    evt.SetDoorState(18, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Switch")

RegisterEvent(15, "Switch", function()
    evt.SetDoorState(19, DoorAction.Trigger)
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(14, DoorAction.Trigger)
end, "Switch")

RegisterEvent(16, nil, function()
    evt.SetDoorState(20, DoorAction.Close)
end)

RegisterEvent(17, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(18, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(19, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(20, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(21, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(22, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(23, "Chest", function()
    evt.OpenChest(7)
    evt.SetDoorState(5, DoorAction.Close)
end, "Chest")

RegisterEvent(24, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(30, nil, function()
    evt.SetDoorState(21, DoorAction.Open)
end)

RegisterEvent(31, "Cylinder", function()
    SetQBit(QBit(1200)) -- NPC
    evt.MoveToMap(-9110, -5381, 17, 1536, 0, 0, 0, 0, "sewer.blv") -- Free Haven Sewer
end, "Cylinder")

RegisterEvent(32, "Oracle Memory Crystal", function()
    if IsQBitSet(QBit(1077)) then return end -- 53 T6, Given when characters take the Oracle Crystal from the altar.
    SetQBit(QBit(1077)) -- 53 T6, Given when characters take the Oracle Crystal from the altar.
    evt.SetMessage("Exit")
    evt.SetSprite(132, 1, "crysdisc")
    AddValue(InventoryItem(2170), 2170) -- Memory Crystal Alpha
    SetQBit(QBit(1215)) -- Quest item bits for seer
end, "Oracle Memory Crystal")

RegisterEvent(33, nil, function()
    if IsQBitSet(QBit(1077)) then -- 53 T6, Given when characters take the Oracle Crystal from the altar.
        evt.SetSprite(132, 1, "crysdisc")
    end
end)

RegisterEvent(34, nil, function()
    evt.DamagePlayer(Players.All, const.Damage.Magic, 1000)
end)

RegisterEvent(35, "Exit", function()
    evt.MoveToMap(-19914, -18118, 65, 1536, 0, 0, 0, 0, "outa3.odm") -- Hermit's Isle
end, "Exit")

RegisterEvent(36, nil, function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    AddValue(InventoryItem(1656), 1656) -- Death Mace
end)

RegisterEvent(37, nil, function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.SummonMonsters(3, 1, 1, -416, 416, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier A, count 1, pos=(-416, 416, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, -576, 0, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier A, count 1, pos=(-576, 0, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, -416, -416, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier B, count 1, pos=(-416, -416, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 2, 1, 0, -576, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier B, count 1, pos=(0, -576, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 416, -416, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier C, count 1, pos=(416, -416, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 3, 1, 576, 0, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier C, count 1, pos=(576, 0, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 416, 416, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier A, count 1, pos=(416, 416, -1016), actor group 0, no unique actor name
    evt.SummonMonsters(3, 1, 1, 0, 576, -1016, 0, 0) -- encounter slot 3 "ElemFire" tier A, count 1, pos=(0, 576, -1016), actor group 0, no unique actor name
    SetValue(MapVar(3), 1)
end)

RegisterEvent(40, "Altar of Fire", function()
    if not IsQBitSet(QBit(1339)) then -- NPC
        SetQBit(QBit(1339)) -- NPC
        evt.DamagePlayer(Players.All, const.Damage.Magic, 75)
        evt.StatusText("Trial by Fire")
        return
    end
    evt.StatusText("Trial by Fire")
end, "Altar of Fire")

RegisterEvent(41, "Altar of Cold", function()
    if not IsQBitSet(QBit(1340)) then -- NPC
        SetQBit(QBit(1340)) -- NPC
        evt.DamagePlayer(Players.All, const.Damage.Air, 75)
        evt.StatusText("Trial by Cold")
        return
    end
    evt.StatusText("Trial by Cold")
end, "Altar of Cold")

RegisterEvent(42, "Altar of Pain", function()
    if not IsQBitSet(QBit(1341)) then -- NPC
        SetQBit(QBit(1341)) -- NPC
        evt.DamagePlayer(Players.All, const.Damage.Magic, 75)
        evt.StatusText("Altar of Pain")
        return
    end
    evt.StatusText("Altar of Pain")
end, "Altar of Pain")

RegisterEvent(43, "Shrine of Fire", function()
    if IsQBitSet(QBit(1342)) then return end -- NPC
    if IsQBitSet(QBit(1339)) then -- NPC
        if IsQBitSet(QBit(1340)) then -- NPC
            if IsQBitSet(QBit(1341)) then -- NPC
                evt.StatusText("+10 Fire resistance permanent.")
                AddValue(FireResistance, 10)
                SetQBit(QBit(1342)) -- NPC
                return
            end
        end
    end
    evt.StatusText("You're not worthy!")
end, "Shrine of Fire")

RegisterEvent(44, "Shrine of Air", function()
    if IsQBitSet(QBit(1343)) then return end -- NPC
    if IsQBitSet(QBit(1339)) then -- NPC
        if IsQBitSet(QBit(1340)) then -- NPC
            if IsQBitSet(QBit(1341)) then -- NPC
                evt.StatusText("+10 Electric resistance permanent.")
                AddValue(AirResistance, 10)
                SetQBit(QBit(1343)) -- NPC
                return
            end
        end
    end
    evt.StatusText("You're not worthy!")
end, "Shrine of Air")

RegisterEvent(45, "Shrine of Water", function()
    if IsQBitSet(QBit(1344)) then return end -- NPC
    if IsQBitSet(QBit(1339)) then -- NPC
        if IsQBitSet(QBit(1340)) then -- NPC
            if IsQBitSet(QBit(1341)) then -- NPC
                evt.StatusText("+10 Cold resistance permanent.")
                AddValue(WaterResistance, 10)
                SetQBit(QBit(1344)) -- NPC
                return
            end
        end
    end
    evt.StatusText("You're not worthy!")
end, "Shrine of Water")

RegisterEvent(46, "Shrine of Earth", function()
    if IsQBitSet(QBit(1345)) then return end -- NPC
    if IsQBitSet(QBit(1339)) then -- NPC
        if IsQBitSet(QBit(1340)) then -- NPC
            if IsQBitSet(QBit(1341)) then -- NPC
                evt.StatusText("+10 Magic resistance permanent.")
                AddValue(FireResistance, 10)
                SetQBit(QBit(1345)) -- NPC
                return
            end
        end
    end
    evt.StatusText("You're not worthy!")
end, "Shrine of Earth")

