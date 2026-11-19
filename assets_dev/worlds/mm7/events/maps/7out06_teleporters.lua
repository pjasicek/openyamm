-- The original event shares two destinations between two pressure plates.
-- The temple and shops each have a return plate beside their matching outbound plate.
ReplaceMapEvent(303, "Shops", function()
    evt.MoveToMap(-14208, -6992, 1344, 1024, 0, 0, 0, 0)
end, "Shops")

RegisterEvent(318, "Temple of Light", function()
    evt.MoveToMap(3000, 17248, 1600, 512, 0, 0, 0, 0)
end, "Temple of Light")
SetMapContextAction(318, {kind = "teleport", source = "authored"})

-- Register destination hints on the remaining pressure plates.
RegisterEvent(301, "Celeste Gate", nil, "Celeste Gate")
RegisterEvent(306, "Tavern", nil, "Tavern")
RegisterEvent(308, "Guilds", nil, "Guilds")
RegisterEvent(310, "School of Sorcery", nil, "School of Sorcery")
RegisterEvent(312, "Docks", nil, "Docks")
RegisterEvent(313, "Random Teleporter", nil, "Random Teleporter")
RegisterEvent(315, "Stables", nil, "Stables")

for _, eventId in ipairs({302, 304, 305, 307, 309, 311, 314, 316, 317}) do
    RegisterEvent(eventId, "To Main Square", nil, "To Main Square")
end

-- The original random and Celeste gate platforms had no sign hints.
RegisterEvent(470, "Random Teleporter", nil, "Random Teleporter")
RegisterEvent(471, "Celeste Gate", nil, "Celeste Gate")
