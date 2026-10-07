-- MMMerge map supplement: Colony Zod key pickup and Roland release state.

local function ApplyRolandReleasedState()
    evt.SetSprite(20, 1, "0")
    evt.SetFacetBit(1, FacetBits.Untouchable, true)
    evt.SetFacetBit(1, FacetBits.Invisible, true)
end

ReplaceMapEvent(376, nil, function()
    if not HasItemAnywhere(1463) then
        GiveItem(1463) -- Colony Zod Key
    end

    SetQBit(QBit(752)) -- Talked to Roland
    AddValue(History(26), 0)
    ApplyRolandReleasedState()
    evt.SpeakNPC(626)
end)

RegisterMapOnLoadEvent(65027, "Restore Roland release state", function()
    if IsQBitSet(QBit(752)) then
        ApplyRolandReleasedState()
    end
end)
