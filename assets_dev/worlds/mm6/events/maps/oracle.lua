-- Oracle of Enroth
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {51},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {"trekscon", "trekscrn"},
    spriteNames = {"mcryst01"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Panel", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    if IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(1, DoorAction.Trigger)
        evt.StatusText("Stand by…")
    end
end, "Panel")

RegisterEvent(2, "Legacy event 2", function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.SetDoorState(2, DoorAction.Trigger)
        evt.SetLight(48, 1)
        evt.SetLight(49, 1)
        evt.SetLight(50, 1)
        evt.SetLight(51, 1)
        SetValue(MapVar(7), 1)
        return
    end
    evt.SetLight(49, 0)
    evt.SetLight(50, 0)
    evt.SetLight(48, 0)
    evt.SetLight(51, 0)
    SetValue(MapVar(7), 0)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(3, "Oracle", function()
    evt.EnterHouse(451) -- Tell James if you see this 451
end, "Oracle")

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(2, DoorAction.Open)
end)

RegisterEvent(5, "Legacy event 5", function()
    local function RestoreMemoryModule()
        evt.SetSprite(4, 1, "mcryst01")
        evt.SetLight(63, 1)
        AddValue(Experience, 100000)
        evt.StatusText("\"+100,000 Experience\"")
        if IsQBitSet(QBit(1124)) and IsQBitSet(QBit(1125)) and IsQBitSet(QBit(1126)) and IsQBitSet(QBit(1127)) then
            evt.SetNPCTopic(793, 0, 1389) -- Oracle topic 0: Control Center
            evt.SetNPCTopic(793, 1, 0) -- Oracle topic 1 cleared
        end
    end

    if not IsAtLeast(MapVar(8), 1) then
        return
    end
    if IsQBitSet(QBit(1304)) then -- NPC
        evt.StatusText("Memory module restored.")
        return
    end
    evt.ForPlayer(Players.All)
    if HasItem(2170) then -- Memory Crystal Alpha
        if not IsQBitSet(QBit(1124)) then -- Oracle
            RemoveItem(2170) -- Memory Crystal Alpha
            SetQBit(QBit(1124)) -- Oracle
            ClearQBit(QBit(1215)) -- Quest item bits for seer
            SetQBit(QBit(1304)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2171) then -- Memory Crystal Beta
        if not IsQBitSet(QBit(1125)) then -- Oracle
            RemoveItem(2171) -- Memory Crystal Beta
            SetQBit(QBit(1125)) -- Oracle
            ClearQBit(QBit(1216)) -- Quest item bits for seer
            SetQBit(QBit(1304)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2172) then -- Memory Crystal Delta
        if not IsQBitSet(QBit(1126)) then -- Oracle
            RemoveItem(2172) -- Memory Crystal Delta
            SetQBit(QBit(1126)) -- Oracle
            ClearQBit(QBit(1217)) -- Quest item bits for seer
            SetQBit(QBit(1304)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2173) then -- Memory Crystal Epsilon
        if IsQBitSet(QBit(1127)) then -- Oracle
            evt.StatusText("Memory module restored.")
            return
        end
        RemoveItem(2173) -- Memory Crystal Epsilon
        SetQBit(QBit(1127)) -- Oracle
        ClearQBit(QBit(1218)) -- Quest item bits for seer
        SetQBit(QBit(1304)) -- NPC
        RestoreMemoryModule()
        return
    end
    evt.StatusText("Insert Memory module to activate Melian.")
end)

RegisterEvent(6, "Legacy event 6", function()
    if IsAtLeast(MapVar(8), 1) then
        evt.SetTexture(436, "trekscon")
        SetValue(MapVar(2), 1)
    end
end)

RegisterEvent(7, "Legacy event 7", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    if IsAtLeast(MapVar(2), 1) then
        evt.SetTexture(436, "trekscrn")
        SetValue(MapVar(2), 0)
    end
end)

RegisterEvent(8, "Legacy event 8", function()
    if IsAtLeast(MapVar(8), 1) then
        evt.SetLight(1, 1)
        evt.SetLight(2, 1)
        evt.SetLight(3, 1)
        evt.SetLight(4, 1)
        evt.SetLight(5, 1)
        evt.SetLight(6, 1)
        evt.SetLight(7, 1)
        evt.SetLight(9, 1)
        evt.SetLight(10, 1)
        evt.SetLight(11, 1)
        evt.SetLight(12, 1)
        evt.SetLight(13, 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
    end
end)

RegisterEvent(9, "Legacy event 9", function()
    if IsAtLeast(MapVar(8), 1) then
        evt.SetLight(1, 0)
        evt.SetLight(2, 0)
        evt.SetLight(3, 0)
        evt.SetLight(4, 0)
        evt.SetLight(5, 0)
        evt.SetLight(6, 0)
        evt.SetLight(7, 0)
        evt.SetLight(9, 0)
        evt.SetLight(10, 0)
        evt.SetLight(11, 0)
        evt.SetLight(12, 0)
        evt.SetLight(13, 0)
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
    end
end)

RegisterEvent(10, "Legacy event 10", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    if not IsAtLeast(MapVar(3), 1) then
        evt.SetLight(17, 1)
        evt.SetLight(18, 1)
        evt.SetLight(19, 1)
        evt.SetLight(20, 1)
        evt.SetLight(21, 1)
        evt.SetLight(22, 1)
        evt.SetLight(23, 1)
        evt.SetLight(24, 1)
        SetValue(MapVar(3), 1)
        return
    end
    evt.SetLight(17, 0)
    evt.SetLight(18, 0)
    evt.SetLight(19, 0)
    evt.SetLight(20, 0)
    evt.SetLight(21, 0)
    evt.SetLight(22, 0)
    evt.SetLight(23, 0)
    evt.SetLight(24, 0)
    SetValue(MapVar(3), 0)
end)

RegisterEvent(11, "Legacy event 11", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    if not IsAtLeast(MapVar(4), 1) then
        evt.SetLight(25, 1)
        evt.SetLight(26, 1)
        evt.SetLight(27, 1)
        evt.SetLight(29, 1)
        evt.SetLight(29, 1)
        evt.SetLight(30, 1)
        evt.SetLight(31, 1)
        evt.SetLight(32, 1)
        SetValue(MapVar(4), 1)
        return
    end
    evt.SetLight(25, 0)
    evt.SetLight(26, 0)
    evt.SetLight(27, 0)
    evt.SetLight(28, 0)
    evt.SetLight(29, 0)
    evt.SetLight(30, 0)
    evt.SetLight(31, 0)
    evt.SetLight(32, 0)
    SetValue(MapVar(4), 0)
end)

RegisterEvent(12, "Legacy event 12", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    if not IsAtLeast(MapVar(5), 1) then
        evt.SetLight(33, 1)
        evt.SetLight(34, 1)
        evt.SetLight(35, 1)
        evt.SetLight(36, 1)
        evt.SetLight(37, 1)
        evt.SetLight(38, 1)
        evt.SetLight(39, 1)
        evt.SetLight(40, 1)
        SetValue(MapVar(5), 1)
        return
    end
    evt.SetLight(33, 0)
    evt.SetLight(34, 0)
    evt.SetLight(35, 0)
    evt.SetLight(36, 0)
    evt.SetLight(37, 0)
    evt.SetLight(38, 0)
    evt.SetLight(39, 0)
    evt.SetLight(40, 0)
    SetValue(MapVar(5), 0)
end)

RegisterEvent(13, "Legacy event 13", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    if not IsAtLeast(MapVar(6), 1) then
        evt.SetLight(41, 1)
        evt.SetLight(42, 1)
        evt.SetLight(43, 1)
        evt.SetLight(44, 1)
        evt.SetLight(45, 1)
        evt.SetLight(46, 1)
        SetValue(MapVar(6), 1)
        return
    end
    evt.SetLight(41, 0)
    evt.SetLight(42, 0)
    evt.SetLight(43, 0)
    evt.SetLight(44, 0)
    evt.SetLight(45, 0)
    evt.SetLight(46, 0)
    SetValue(MapVar(6), 0)
end)

RegisterEvent(14, "Panel", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.SetLight(52, 1)
        evt.SetLight(53, 1)
        evt.SetLight(54, 1)
        evt.SetLight(55, 1)
        evt.SetLight(56, 1)
        evt.SetLight(57, 1)
        evt.SetLight(58, 1)
        evt.SetLight(59, 1)
        evt.SetLight(60, 1)
        evt.SetLight(61, 1)
        evt.SetLight(62, 1)
        SetValue(MapVar(8), 1)
        evt.StatusText("Power on.  Status:  All systems functional.")
        return
    end
    evt.SetLight(52, 0)
    evt.SetLight(53, 0)
    evt.SetLight(54, 0)
    evt.SetLight(55, 0)
    evt.SetLight(56, 0)
    evt.SetLight(57, 0)
    evt.SetLight(58, 0)
    evt.SetLight(59, 0)
    evt.SetLight(60, 0)
    evt.SetLight(61, 0)
    evt.SetLight(62, 0)
    evt.StatusText("Power off.  Status:  All systems shut down.")
    SetValue(MapVar(8), 0)
end, "Panel")

RegisterEvent(15, "Legacy event 15", function()
    local function RestoreMemoryModule()
        evt.SetSprite(3, 1, "mcryst01")
        evt.SetLight(64, 1)
        AddValue(Experience, 100000)
        evt.StatusText("\"+100,000 Experience\"")
        if IsQBitSet(QBit(1124)) and IsQBitSet(QBit(1125)) and IsQBitSet(QBit(1126)) and IsQBitSet(QBit(1127)) then
            evt.SetNPCTopic(793, 0, 1389) -- Oracle topic 0: Control Center
            evt.SetNPCTopic(793, 1, 0) -- Oracle topic 1 cleared
        end
    end

    if not IsAtLeast(MapVar(8), 1) then
        return
    end
    if IsQBitSet(QBit(1305)) then -- NPC
        evt.StatusText("Memory module restored.")
        return
    end
    evt.ForPlayer(Players.All)
    if HasItem(2170) then -- Memory Crystal Alpha
        if not IsQBitSet(QBit(1124)) then -- Oracle
            RemoveItem(2170) -- Memory Crystal Alpha
            SetQBit(QBit(1124)) -- Oracle
            ClearQBit(QBit(1215)) -- Quest item bits for seer
            SetQBit(QBit(1305)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2171) then -- Memory Crystal Beta
        if not IsQBitSet(QBit(1125)) then -- Oracle
            RemoveItem(2171) -- Memory Crystal Beta
            SetQBit(QBit(1125)) -- Oracle
            ClearQBit(QBit(1216)) -- Quest item bits for seer
            SetQBit(QBit(1305)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2172) then -- Memory Crystal Delta
        if not IsQBitSet(QBit(1126)) then -- Oracle
            RemoveItem(2172) -- Memory Crystal Delta
            SetQBit(QBit(1126)) -- Oracle
            ClearQBit(QBit(1217)) -- Quest item bits for seer
            SetQBit(QBit(1305)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2173) then -- Memory Crystal Epsilon
        if IsQBitSet(QBit(1127)) then -- Oracle
            evt.StatusText("Memory module restored.")
            return
        end
        RemoveItem(2173) -- Memory Crystal Epsilon
        SetQBit(QBit(1127)) -- Oracle
        ClearQBit(QBit(1218)) -- Quest item bits for seer
        SetQBit(QBit(1305)) -- NPC
        RestoreMemoryModule()
        return
    end
    evt.StatusText("Insert Memory module to activate Melian.")
end)

RegisterEvent(16, "Legacy event 16", function()
    local function RestoreMemoryModule()
        evt.SetSprite(2, 1, "mcryst01")
        evt.SetLight(65, 1)
        AddValue(Experience, 100000)
        evt.StatusText("\"+100,000 Experience\"")
        if IsQBitSet(QBit(1124)) and IsQBitSet(QBit(1125)) and IsQBitSet(QBit(1126)) and IsQBitSet(QBit(1127)) then
            evt.SetNPCTopic(793, 0, 1389) -- Oracle topic 0: Control Center
            evt.SetNPCTopic(793, 1, 0) -- Oracle topic 1 cleared
        end
    end

    if not IsAtLeast(MapVar(8), 1) then
        return
    end
    if IsQBitSet(QBit(1306)) then -- NPC
        evt.StatusText("Memory module restored.")
        return
    end
    evt.ForPlayer(Players.All)
    if HasItem(2170) then -- Memory Crystal Alpha
        if not IsQBitSet(QBit(1124)) then -- Oracle
            RemoveItem(2170) -- Memory Crystal Alpha
            SetQBit(QBit(1124)) -- Oracle
            ClearQBit(QBit(1215)) -- Quest item bits for seer
            SetQBit(QBit(1306)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2171) then -- Memory Crystal Beta
        if not IsQBitSet(QBit(1125)) then -- Oracle
            RemoveItem(2171) -- Memory Crystal Beta
            SetQBit(QBit(1125)) -- Oracle
            ClearQBit(QBit(1216)) -- Quest item bits for seer
            SetQBit(QBit(1306)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2172) then -- Memory Crystal Delta
        if not IsQBitSet(QBit(1126)) then -- Oracle
            RemoveItem(2172) -- Memory Crystal Delta
            SetQBit(QBit(1126)) -- Oracle
            ClearQBit(QBit(1217)) -- Quest item bits for seer
            SetQBit(QBit(1306)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2173) then -- Memory Crystal Epsilon
        if IsQBitSet(QBit(1127)) then -- Oracle
            evt.StatusText("Memory module restored.")
            return
        end
        RemoveItem(2173) -- Memory Crystal Epsilon
        SetQBit(QBit(1127)) -- Oracle
        ClearQBit(QBit(1218)) -- Quest item bits for seer
        SetQBit(QBit(1306)) -- NPC
        RestoreMemoryModule()
        return
    end
    evt.StatusText("Insert Memory module to activate Melian.")
end)

RegisterEvent(17, "Legacy event 17", function()
    local function RestoreMemoryModule()
        evt.SetSprite(1, 1, "mcryst01")
        evt.SetLight(66, 1)
        AddValue(Experience, 100000)
        evt.StatusText("\"+100,000 Experience\"")
        if IsQBitSet(QBit(1124)) and IsQBitSet(QBit(1125)) and IsQBitSet(QBit(1126)) and IsQBitSet(QBit(1127)) then
            evt.SetNPCTopic(793, 0, 1389) -- Oracle topic 0: Control Center
            evt.SetNPCTopic(793, 1, 0) -- Oracle topic 1 cleared
        end
    end

    if not IsAtLeast(MapVar(8), 1) then
        return
    end
    if IsQBitSet(QBit(1307)) then -- NPC
        evt.StatusText("Memory module restored.")
        return
    end
    evt.ForPlayer(Players.All)
    if HasItem(2170) then -- Memory Crystal Alpha
        if not IsQBitSet(QBit(1124)) then -- Oracle
            RemoveItem(2170) -- Memory Crystal Alpha
            SetQBit(QBit(1124)) -- Oracle
            ClearQBit(QBit(1215)) -- Quest item bits for seer
            SetQBit(QBit(1307)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2171) then -- Memory Crystal Beta
        if not IsQBitSet(QBit(1125)) then -- Oracle
            RemoveItem(2171) -- Memory Crystal Beta
            SetQBit(QBit(1125)) -- Oracle
            ClearQBit(QBit(1216)) -- Quest item bits for seer
            SetQBit(QBit(1307)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2172) then -- Memory Crystal Delta
        if not IsQBitSet(QBit(1126)) then -- Oracle
            RemoveItem(2172) -- Memory Crystal Delta
            SetQBit(QBit(1126)) -- Oracle
            ClearQBit(QBit(1217)) -- Quest item bits for seer
            SetQBit(QBit(1307)) -- NPC
            RestoreMemoryModule()
            return
        end
    end
    if HasItem(2173) then -- Memory Crystal Epsilon
        if IsQBitSet(QBit(1127)) then -- Oracle
            evt.StatusText("Memory module restored.")
            return
        end
        RemoveItem(2173) -- Memory Crystal Epsilon
        SetQBit(QBit(1127)) -- Oracle
        ClearQBit(QBit(1218)) -- Quest item bits for seer
        SetQBit(QBit(1307)) -- NPC
        RestoreMemoryModule()
        return
    end
    evt.StatusText("Insert Memory module to activate Melian.")
end)

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(12182, 5379, 320, 1024, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(51, "Legacy event 51", function()
    if IsQBitSet(QBit(1304)) then -- NPC
        evt.SetSprite(4, 1, "mcryst01")
        if IsQBitSet(QBit(1305)) then -- NPC
            evt.SetSprite(3, 1, "mcryst01")
            if IsQBitSet(QBit(1306)) then -- NPC
                evt.SetSprite(2, 1, "mcryst01")
                if IsQBitSet(QBit(1307)) then -- NPC
                    evt.SetSprite(1, 1, "mcryst01")
                end
                return
            elseif IsQBitSet(QBit(1307)) then -- NPC
                evt.SetSprite(1, 1, "mcryst01")
            else
                return
            end
        elseif IsQBitSet(QBit(1306)) then -- NPC
            evt.SetSprite(2, 1, "mcryst01")
            if IsQBitSet(QBit(1307)) then -- NPC
                evt.SetSprite(1, 1, "mcryst01")
            end
            return
        elseif IsQBitSet(QBit(1307)) then -- NPC
            evt.SetSprite(1, 1, "mcryst01")
        else
            return
        end
    elseif IsQBitSet(QBit(1305)) then -- NPC
        evt.SetSprite(3, 1, "mcryst01")
        if IsQBitSet(QBit(1306)) then -- NPC
            evt.SetSprite(2, 1, "mcryst01")
            if IsQBitSet(QBit(1307)) then -- NPC
                evt.SetSprite(1, 1, "mcryst01")
            end
            return
        elseif IsQBitSet(QBit(1307)) then -- NPC
            evt.SetSprite(1, 1, "mcryst01")
        else
            return
        end
    elseif IsQBitSet(QBit(1306)) then -- NPC
        evt.SetSprite(2, 1, "mcryst01")
        if IsQBitSet(QBit(1307)) then -- NPC
            evt.SetSprite(1, 1, "mcryst01")
        end
        return
    elseif IsQBitSet(QBit(1307)) then -- NPC
        evt.SetSprite(1, 1, "mcryst01")
    else
        return
    end
end)

