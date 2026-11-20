-- MMMerge map supplement: Free Haven sewer rescue follower state.

ReplaceMapEvent(8, "Bed", function()
    if IsQBitSet(QBit(1194)) -- Captured the Prince of Thieves.
        or not IsQBitSet(QBit(1122)) then -- Capture the Prince of Thieves and bring him to Lord Stone.
        return
    end

    SetQBit(QBit(1701)) -- Replacement for NPCs 17 ver. 6
    SetQBit(QBit(1194)) -- Captured the Prince of Thieves.
    AddFollowerNpc(802)
    evt.SpeakNPC(802)
end, "Bed")
