-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "thronheim"
map.scripts = {}

map.scripts["foradworld.scr"] = {
    source = "FORADWORLD.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["npc244.scr"] = {
    source = "NPC244.scr",
    registered_triggers = {
        { line = 87, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npcshopkeeper.scr"] = {
    source = "NPCSHOPKEEPER.scr",
    registered_triggers = {
        { line = 47, message = "Use", callback = "OnUse" },
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
