ReplaceMapEvent(1, nil, function()
    -- Rebuild the counter from the saved pillar flags on entry and after loading a save.
    local insertedKeys = 0
    for pillar = 17, 19 do
        if IsAtLeast(MapVar(pillar), 1) then
            insertedKeys = insertedKeys + 1
        end
    end
    SetValue(MapVar(20), insertedKeys)
    if insertedKeys == 3 then
        evt.SetDoorState(1, DoorAction.Open)
        evt.SetDoorState(2, DoorAction.Open)
    end

    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)
AppendMapOnLoadEvent(1)
