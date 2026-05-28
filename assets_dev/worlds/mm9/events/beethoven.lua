-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "beethoven"
map.scripts = {}

map.scripts["bottlefollow.scr"] = {
    source = "BOTTLEFOLLOW.scr",
    registered_triggers = {
    },
    movement_commands = {
        { line = 100, command = "Rotate", arguments = "0,1,0, ANGLE_DIST, ANGLE_RATE, DoNothing" },
        { line = 104, command = "MoveDir", arguments = "0,nDir,0, FLOAT_DIST, FLOAT_RATE, FloatLoop" },
        { line = 120, command = "SetPOS", arguments = "hMe, xMe,yMe,zMe" },
        { line = 134, command = "SetPOS", arguments = "hMe, xMe,yMe,zMe" },
    },
}
map.scripts["coffinmummy.scr"] = {
    source = "COFFINMUMMY.scr",
    registered_triggers = {
        { line = 46, message = "awaken", callback = "WakeUp" },
    },
    movement_commands = {
    },
}
map.scripts["coffinraise.scr"] = {
    source = "COFFINRAISE.scr",
    registered_triggers = {
        { line = 17, message = "raise", callback = "OnRaise" },
        { line = 18, message = "open", callback = "OnRaise" },
    },
    movement_commands = {
    },
}
map.scripts["ludwigsmanuscript.scr"] = {
    source = "LUDWIGSMANUSCRIPT.scr",
    registered_triggers = {
        { line = 78, message = "Use", callback = "Onuse" },
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
