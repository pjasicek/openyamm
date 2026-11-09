-- Authored Greywatch behavior. The build embeds this file after its generated registrations/data.
-- Regenerating geometry must preserve these handlers.
local handlers = {}

handlers[1] = function()
    local a = LG.outdoor.castle
    evt.MoveToMap(a[1], a[2], a[3], 1536, 0, 0, 0, 0, "lg01.odm")
end

handlers[2] = function()
    local a = LG.outdoor.cave
    evt.MoveToMap(a[1], a[2], a[3], 1024, 0, 0, 0, 0, "lg01.odm")
end

handlers[101] = function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end

handlers[102] = function()
    evt.SetDoorState(3, DoorAction.Open)
    SetValue(MapVar(3), 1)
    evt.StatusText("The lift gate opens. The passage to the entrance hall is unlatched.")
end

handlers[103] = function()
    evt.SetDoorState(4, DoorAction.Trigger)
end

handlers[104] = function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.StatusText("The latch is controlled from the records chamber.")
        return
    end
    evt.SetDoorState(5, DoorAction.Trigger)
end

handlers[105] = function()
    evt.SetDoorState(6, DoorAction.Trigger)
end
handlers[106] = handlers[105]

handlers[107] = function() evt.SetDoorState(7, DoorAction.Trigger) end
handlers[108] = function() evt.SetDoorState(8, DoorAction.Trigger) end

handlers[201] = function() evt.OpenChest(0) end
handlers[202] = function() evt.OpenChest(1) end
handlers[203] = function() evt.OpenChest(2) end
handlers[204] = function() evt.OpenChest(3) end

handlers[301] = function()
    if IsAtLeast(MapVar(1), 1) then return end
    SetValue(MapVar(1), 1)
    evt.CastSpell(6, 10, 2, 4200, 3072, 544, 2944, 3072, 544)
end

handlers[302] = function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    evt.CastSpell(2, 10, 1, -2080, 3072, 928, -1120, 3072, 928)
end
