-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "dungeonofsecrets"
map.scripts = {}

map.scripts["npc417.scr"] = {
    source = "NPC417.scr",
    registered_triggers = {
        { line = 99, message = "Use", callback = "OnUse" },
        { line = 100, message = "DoTrap", callback = "OnTrap" },
        { line = 101, message = "RemoveTrap", callback = "OnRemove" },
        { line = 102, message = "done", callback = "OnFinish" },
        { line = 112, message = "Use", callback = "OnUse" },
        { line = 113, message = "DoTrap", callback = "OnTrap" },
        { line = 114, message = "RemoveTrap", callback = "OnRemove" },
        { line = 115, message = "done", callback = "OnFinish" },
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
