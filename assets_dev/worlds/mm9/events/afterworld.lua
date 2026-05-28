-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "afterworld"
map.scripts = {}

map.scripts["afterworldcam1.scr"] = {
    source = "AFTERWORLDCAM1.scr",
    registered_triggers = {
        { line = 47, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 31, command = "MoveToPos", arguments = "xpos Ypos Zpos nSpeed OnArrive" },
    },
}
map.scripts["battlecam1.scr"] = {
    source = "BATTLECAM1.scr",
    registered_triggers = {
        { line = 47, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 31, command = "MoveToPos", arguments = "xpos Ypos Zpos nSpeed OnArrive" },
    },
}
map.scripts["givetake.scr"] = {
    source = "GIVETAKE.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc336.scr"] = {
    source = "NPC336.scr",
    registered_triggers = {
        { line = 321, message = "use", callback = "OnUse" },
        { line = 326, message = "Reborn", callback = "OnReborn" },
        { line = 327, message = "Done", callback = "OnDone" },
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
map.scripts["proptrigger.scr"] = {
    source = "PROPTRIGGER.scr",
    registered_triggers = {
        { line = 64, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["tm_hardrock.scr"] = {
    source = "TM_HARDROCK.scr",
    registered_triggers = {
        { line = 65, message = "OneDown", callback = "OneDown" },
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
