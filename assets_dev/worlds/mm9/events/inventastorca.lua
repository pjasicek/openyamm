-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "inventastorca"
map.scripts = {}

map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["greenparty.scr"] = {
    source = "GREENPARTY.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["is_dyingnpc.scr"] = {
    source = "IS_DYINGNPC.scr",
    registered_triggers = {
        { line = 24, message = "Die", callback = "NpcDie" },
    },
    movement_commands = {
    },
}
map.scripts["is_ficky.scr"] = {
    source = "IS_FICKY.scr",
    registered_triggers = {
        { line = 89, message = "Scatter", callback = "scatter" },
    },
    movement_commands = {
    },
}
map.scripts["is_fickyflock.scr"] = {
    source = "IS_FICKYFLOCK.scr",
    registered_triggers = {
        { line = 120, message = "Go", callback = "Go" },
    },
    movement_commands = {
    },
}
map.scripts["is_killinglich.scr"] = {
    source = "IS_KILLINGLICH.scr",
    registered_triggers = {
        { line = 32, message = "Kill", callback = "KillNpc" },
    },
    movement_commands = {
    },
}
map.scripts["kingkong.scr"] = {
    source = "KINGKONG.scr",
    registered_triggers = {
        { line = 41, message = "ForceBreak", callback = "RushCage" },
        { line = 42, message = "ForceFall", callback = "FallThrough" },
        { line = 43, message = "ForceAttack", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["orb.scr"] = {
    source = "ORB.scr",
    registered_triggers = {
        { line = 49, message = "use", callback = "OnUse" },
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
map.scripts["spook.scr"] = {
    source = "SPOOK.scr",
    registered_triggers = {
        { line = 63, message = "Play", callback = "PlaySound" },
        { line = 64, message = "PlayHere", callback = "PlaySoundHere" },
        { line = 65, message = "RandomOff", callback = "TurnRandomOff" },
        { line = 66, message = "RandomOn", callback = "TurnRandomOn" },
        { line = 67, message = "On", callback = "TurnOn" },
        { line = 68, message = "Off", callback = "TurnOff" },
    },
    movement_commands = {
        { line = 126, command = "SetPOS", arguments = "hMe, x,y,z" },
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
