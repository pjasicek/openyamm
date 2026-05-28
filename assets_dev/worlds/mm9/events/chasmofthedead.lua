-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "chasmofthedead"
map.scripts = {}

map.scripts["autoresurrect.scr"] = {
    source = "AUTORESURRECT.scr",
    registered_triggers = {
        { line = 83, message = "TMSG_RESURRECT", callback = "OnResurrect" },
    },
    movement_commands = {
    },
}
map.scripts["chasm_ghostspawner.scr"] = {
    source = "CHASM_GHOSTSPAWNER.scr",
    registered_triggers = {
        { line = 36, message = "spawn", callback = "SpawnCreature" },
    },
    movement_commands = {
    },
}
map.scripts["cronakiga.scr"] = {
    source = "CRONAKIGA.scr",
    registered_triggers = {
        { line = 101, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["lichinstructions.scr"] = {
    source = "LICHINSTRUCTIONS.scr",
    registered_triggers = {
        { line = 46, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["mummyawaken.scr"] = {
    source = "MUMMYAWAKEN.scr",
    registered_triggers = {
        { line = 61, message = "awaken", callback = "WakeUp" },
    },
    movement_commands = {
    },
}
map.scripts["offrailtrigger.scr"] = {
    source = "OFFRAILTRIGGER.scr",
    registered_triggers = {
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
