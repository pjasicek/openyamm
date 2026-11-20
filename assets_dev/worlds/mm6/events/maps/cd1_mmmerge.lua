-- Castle Alamos password plate and memory crystal pickup.

ReplaceMapEvent(59, "Memory Crystal Beta", function()
    if IsQBitSet(QBit(1078)) then return end
    SetQBit(QBit(1078))
    evt.SetSprite(394, 1, "crysdisc")
    AddValue(InventoryItem(2171), 2171) -- Memory Crystal Beta
    SetQBit(QBit(1216)) -- Quest item bits for seer
end, "Memory Crystal Beta")

ReplaceMapEvent(69, nil, function(continueStep)
    if continueStep == 4 then
        evt.MoveToMap(-3136, 2240, 224, 1024, 0, 0, 0, 0)
        evt.StatusText("Wrong!")
        return
    end

    if continueStep == 23 then
        SetValue(MapVar(8), 1)
        evt.StatusText("Ok!")
        return
    end

    if continueStep ~= nil then
        return
    end

    -- MapVar(6) records reading the fifth-letter clue, not solving the password.
    if IsAtLeast(MapVar(8), 1) then
        return
    end

    evt.SimpleMessage("Restricted area - Keep out.")
    evt.AskQuestion(69, 4, 14, 23, 15, 16, "What's the password?", {"JBARD", "jbard"})
    return nil
end)
