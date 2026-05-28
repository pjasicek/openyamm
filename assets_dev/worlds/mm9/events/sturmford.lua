-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "sturmford"
map.scripts = {}

map.scripts["ak_disable.scr"] = {
    source = "AK_DISABLE.scr",
    registered_triggers = {
        { line = 132, message = "Drawbridge", callback = "OnDraw" },
        { line = 133, message = "Portcullis", callback = "ONPortcullis" },
    },
    movement_commands = {
    },
}
map.scripts["destructon.scr"] = {
    source = "DESTRUCTON.scr",
    registered_triggers = {
        { line = 37, message = "DamageOn", callback = "OnDamageOn" },
    },
    movement_commands = {
    },
}
map.scripts["doorlock.scr"] = {
    source = "DOORLOCK.scr",
    registered_triggers = {
        { line = 57, message = "use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["foradworld.scr"] = {
    source = "FORADWORLD.scr",
    registered_triggers = {
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
