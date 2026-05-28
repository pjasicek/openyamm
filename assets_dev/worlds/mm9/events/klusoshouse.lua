-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "klusoshouse"
map.scripts = {}

map.scripts["blackheart.scr"] = {
    source = "BLACKHEART.scr",
    registered_triggers = {
        { line = 77, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["klusoshidden.scr"] = {
    source = "KLUSOSHIDDEN.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["klusospatrol.scr"] = {
    source = "KLUSOSPATROL.scr",
    registered_triggers = {
        { line = 54, message = "start", callback = "TraverseBegin" },
        { line = 55, message = "charge", callback = "HuntPlayer" },
    },
    movement_commands = {
    },
}
map.scripts["klusossleeper.scr"] = {
    source = "KLUSOSSLEEPER.scr",
    registered_triggers = {
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
