-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "frosgard"
map.scripts = {}

map.scripts["jumper.scr"] = {
    source = "JUMPER.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["npc221.scr"] = {
    source = "NPC221.scr",
    registered_triggers = {
        { line = 116, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["propanim.scr"] = {
    source = "PROPANIM.scr",
    registered_triggers = {
        { line = 42, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
