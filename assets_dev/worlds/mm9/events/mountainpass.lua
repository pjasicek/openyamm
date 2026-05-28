-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "mountainpass"
map.scripts = {}

map.scripts["mountainpass.scr"] = {
    source = "MOUNTAINPASS.scr",
    registered_triggers = {
        { line = 61, message = "Use", callback = "OnStep" },
    },
    movement_commands = {
    },
}
map.scripts["mp_imp.scr"] = {
    source = "MP_IMP.scr",
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
