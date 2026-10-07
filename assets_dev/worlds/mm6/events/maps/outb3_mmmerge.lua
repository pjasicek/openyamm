-- MMMerge map supplement: Dragonsand Dimension Door and per-character Shrine of the Gods blessings.

RegisterMapOnLoadEvent(65020, "Migrate Shrine of the Gods blessings", function()
    -- Older saves recorded blessings by party slot instead of on the character.
    for playerIndex = 0, 4 do
        local name = "ShrineOfGodsBlessed" .. tostring(playerIndex)
        if evt.GetMapVar(name, 0) ~= 0 then
            if playerIndex < evt.GetPartyMemberCount() then
                evt.ForPlayer(playerIndex)
                SetPlayerBit(PlayerBit(70))
            end
            evt.SetMapVar(name, 0)
        end
    end
    evt.ForPlayer(Players.Current)
end)

ReplaceMapEvent(103, "Shrine of the Gods", function()
    local playerIndex = evt.GetCurrentPlayerIndex()

    if playerIndex < 0 then
        return
    end

    evt.ForPlayer(Players.Current)

    if IsPlayerBitSet(PlayerBit(70)) then
        SetValue(MajorCondition, 0)
        return
    end

    SetPlayerBit(PlayerBit(70))
    AddValue(FireResistance, 20)
    AddValue(AirResistance, 20)
    AddValue(WaterResistance, 20)
    AddValue(EarthResistance, 20)
    AddValue(SpiritResistance, 20)
    AddValue(MindResistance, 20)
    AddValue(BodyResistance, 20)
    AddValue(BaseMight, 20)
    AddValue(BaseIntellect, 20)
    AddValue(BasePersonality, 20)
    AddValue(BaseEndurance, 20)
    AddValue(BaseSpeed, 20)
    AddValue(BaseAccuracy, 20)
    AddValue(BaseLuck, 20)
    evt.PlaySound(42797, 0, 0)
    evt.StatusText("+20 to all stats permanent.")
end, "Shrine of the Gods")

AppendMapEvent(105, function()
    MM6.OpenDimensionDoor()
end)
