-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "bootcamp"
map.scripts = {}

map.scripts["bc_manager.scr"] = {
    source = "BC_MANAGER.scr",
    registered_triggers = {
        { line = 63, message = "fight", callback = "StartFight" },
        { line = 64, message = "open", callback = "StartOpen" },
        { line = 132, message = "open", callback = "StartOpen" },
        { line = 152, message = "fight", callback = "StartFight" },
        { line = 169, message = "fight", callback = "StartFight" },
    },
    movement_commands = {
    },
}
map.scripts["bc_treasurechest.scr"] = {
    source = "BC_TREASURECHEST.scr",
    registered_triggers = {
        { line = 19, message = "open", callback = "PlayOpenAnim" },
    },
    movement_commands = {
    },
}
map.scripts["bootgive.scr"] = {
    source = "BOOTGIVE.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
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
map.scripts["npc436.scr"] = {
    source = "NPC436.scr",
    registered_triggers = {
        { line = 85, message = "Leave", callback = "OnLeave" },
        { line = 86, message = "Use", callback = "OnUse" },
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
