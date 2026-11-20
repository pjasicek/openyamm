-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The three pillar keys inserted on earlier visits open the inner doors again: the map's own load event resets the
-- count of inserted keys, so they would stay shut (§3.2).
RegisterMapOnLoadEvent(60001, "MAW pillar doors", function()
    if IsAtLeast(MapVar(17), 1) and IsAtLeast(MapVar(18), 1) and IsAtLeast(MapVar(19), 1) then
        evt.SetDoorState(1, DoorAction.Open)
        evt.SetDoorState(2, DoorAction.Open)
    end
end)

-- The Wall of Mist: arriving in its middle part, the party is invisible for ten hours (zzMaw-Spells.lua:732-737).
-- Grandmaster Invisibility at skill 10 lasts ten hours.
RegisterMapOnLoadEvent(60002, "MAW Wall of Mist invisibility", function()
    local x = evt.GetPartyPosition()
    if x > -4698 and x < 2906 then
        evt.CastSpell(19, 4, 10, 0, 0, 0, 0, 0, 0)
    end
end)
