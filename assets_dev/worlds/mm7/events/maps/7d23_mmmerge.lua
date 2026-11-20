-- MMMerge map supplement: The Lincoln initial containment field actors.

RegisterMapOnLoadEvent(65023, "MMMerge 7d23 monster group state", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, false)
    evt.SetMonGroupBit(56, MonsterBits.Invisible, true)
end)

ReplaceMapEvent(501, "Leave the Lincoln", function()
    if not MM7.AllPartyMembersHaveWetsuit() then
        evt.StatusText("You must all be wearing your wetsuits to exit the ship")
        return
    end

    evt.MoveToMap(-7005, 7856, 225, 128, 0, 0, 0, 8, "7out15.odm")
end, "Leave the Lincoln")
