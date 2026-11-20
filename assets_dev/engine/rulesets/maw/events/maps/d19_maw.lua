-- MAW content of this map (devdocs/maw/MAPS_CONTENT.md): loaded after the world's events, for MAW games only.

-- The guild's inner door: Dyson Leyland need not be in the party once he has offered to join (his topic slot 3 is the
-- roster join event 634, offered when the Brazier or Skeleton Transformer quest is taken) (Maps/d19.lua:3-25).
-- Otherwise the base door, which still opens for the Necromancer and Temple alliances (§3.5).
local baseDoorEvent = evt.map[15]
ReplaceMapEvent(15, "Door", function()
    if evt.GetNPCTopic(11, 3) == 634 then -- Dyson Leland topic 3: Roster Join Event
        evt.SetDoorState(5, DoorAction.Open)
        return
    end

    baseDoorEvent()
end, "Door")
