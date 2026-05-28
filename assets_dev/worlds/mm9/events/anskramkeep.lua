-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "anskramkeep"
map.scripts = {}

map.scripts["ak_giantimp.scr"] = {
    source = "AK_GIANTIMP.scr",
    registered_triggers = {
        { line = 22, message = "appear", callback = "Appear" },
    },
    movement_commands = {
    },
}
map.scripts["ak_giantimpguard.scr"] = {
    source = "AK_GIANTIMPGUARD.scr",
    registered_triggers = {
        { line = 21, message = "appear", callback = "Appear" },
    },
    movement_commands = {
    },
}
map.scripts["ak_impgate.scr"] = {
    source = "AK_IMPGATE.scr",
    registered_triggers = {
        { line = 179, message = "spawn", callback = "Spawn" },
    },
    movement_commands = {
    },
}
map.scripts["anskrammainline.scr"] = {
    source = "ANSKRAMMAINLINE.scr",
    registered_triggers = {
        { line = 37, message = "Use", callback = "Onuse" },
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
map.scripts["dungeonjukebox.scr"] = {
    source = "DUNGEONJUKEBOX.scr",
    registered_triggers = {
        { line = 61, message = "Play", callback = "PlaySound" },
        { line = 62, message = "RandomOff", callback = "TurnRandomOff" },
        { line = 63, message = "RandomOn", callback = "TurnRandomOn" },
        { line = 64, message = "On", callback = "TurnOn" },
        { line = 65, message = "Off", callback = "TurnOff" },
    },
    movement_commands = {
        { line = 110, command = "SetPOS", arguments = "hMe, x,y,z" },
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
map.scripts["propanim.scr"] = {
    source = "PROPANIM.scr",
    registered_triggers = {
        { line = 42, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["spawncreature.scr"] = {
    source = "SPAWNCREATURE.scr",
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
