-- MMMerge map supplement: Temple of the Moon evil altar.

ReplaceMapEvent(24, "Evil Altar", function()
    if IsQBitSet(QBit(1047)) then -- 23 D13, Given when Altar is desecrated
        return
    end

    evt.SetTexture(-949, "d6flora")
    evt.SetTexture(-947, "d6flora")
    evt.SetTexture(-927, "d6flora")
    evt.SetTexture(-928, "d6flora")
    evt.SetTexture(-929, "d6flora")
    evt.SetTexture(-948, "d6flora")
    evt.SetTexture(-945, "d6flora")
    evt.SetTexture(-946, "d6flora")
    evt.SetTexture(-944, "d6flora")
    evt.SetTexture(-943, "d6flora")
    evt.SetTexture(-942, "d6flora")
    evt.StatusText("+5 Personality permanent to Druids and Clerics.")

    for playerIndex = 0, evt.GetPartyMemberCount() - 1 do
        if PlayerClassMatches(playerIndex, {"Cleric", "Druid"}) or IsAtLeast(MapVar(7), 1) then
            evt.ForPlayer(playerIndex)
            AddValue(BasePersonality, 5)
        end
    end

    SetQBit(QBit(1047)) -- 23 D13, Given when Altar is desecrated
end, "Evil Altar")
