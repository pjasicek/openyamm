-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "dookscastle"
map.scripts = {}

map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["dc_sargent.scr"] = {
    source = "DC_SARGENT.scr",
    registered_triggers = {
        { line = 122, message = "StartUp", callback = "StartUp" },
    },
    movement_commands = {
    },
}
map.scripts["dookguardbasic.scr"] = {
    source = "DOOKGUARDBASIC.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["dooksleepgaurd.scr"] = {
    source = "DOOKSLEEPGAURD.scr",
    registered_triggers = {
        { line = 114, message = "WakeUp", callback = "WakeUp" },
    },
    movement_commands = {
    },
}
map.scripts["npc415.scr"] = {
    source = "NPC415.scr",
    registered_triggers = {
        { line = 84, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["scurrycreature.scr"] = {
    source = "SCURRYCREATURE.scr",
    registered_triggers = {
        { line = 38, message = "Hide", callback = "GoHide" },
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
