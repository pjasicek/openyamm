-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "lichlab"
map.scripts = {}

map.scripts["autoresurrect.scr"] = {
    source = "AUTORESURRECT.scr",
    registered_triggers = {
        { line = 83, message = "TMSG_RESURRECT", callback = "OnResurrect" },
    },
    movement_commands = {
    },
}
map.scripts["book.scr"] = {
    source = "BOOK.scr",
    registered_triggers = {
        { line = 50, message = "Use", callback = "OnUse" },
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
map.scripts["converter.scr"] = {
    source = "CONVERTER.scr",
    registered_triggers = {
        { line = 59, message = "create", callback = "SpawnCreature" },
        { line = 60, message = "convert", callback = "TransformCreature" },
        { line = 105, message = "create", callback = "SpawnCreature" },
    },
    movement_commands = {
    },
}
map.scripts["elixircook.scr"] = {
    source = "ELIXIRCOOK.scr",
    registered_triggers = {
        { line = 45, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["giveelixir.scr"] = {
    source = "GIVEELIXIR.scr",
    registered_triggers = {
        { line = 48, message = "Use", callback = "OnUse" },
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
map.scripts["ilshealerroom.scr"] = {
    source = "ILSHEALERROOM.scr",
    registered_triggers = {
        { line = 206, message = "open", callback = "Onopen" },
        { line = 207, message = "close", callback = "Onclose" },
        { line = 208, message = "Fix", callback = "OnFix" },
    },
    movement_commands = {
    },
}
map.scripts["ilsshootingbook.scr"] = {
    source = "ILSSHOOTINGBOOK.scr",
    registered_triggers = {
        { line = 69, message = "Use", callback = "OnUse" },
        { line = 70, message = "Done", callback = "OnDone" },
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
map.scripts["lichengineprop.scr"] = {
    source = "LICHENGINEPROP.scr",
    registered_triggers = {
        { line = 11, message = "start", callback = "PowerUp" },
        { line = 29, message = "finish", callback = "PowerDown" },
        { line = 47, message = "start", callback = "PowerUp" },
    },
    movement_commands = {
    },
}
map.scripts["ll_flyingcreature.scr"] = {
    source = "LL_FLYINGCREATURE.scr",
    registered_triggers = {
        { line = 89, message = "Go", callback = "Triggered" },
    },
    movement_commands = {
    },
}
map.scripts["spawnloc.scr"] = {
    source = "SPAWNLOC.scr",
    registered_triggers = {
        { line = 30, message = "On", callback = "TurnOn" },
        { line = 61, message = "spawn", callback = "RequestSpawn" },
        { line = 62, message = "focus", callback = "RequestFocus" },
        { line = 63, message = "off", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["spawnmgr.scr"] = {
    source = "SPAWNMGR.scr",
    registered_triggers = {
        { line = 73, message = "SetLocation", callback = "SetLocation" },
        { line = 74, message = "Respawn", callback = "OnCreatureDied" },
        { line = 75, message = "ForceSpawn", callback = "SpawnCreature" },
        { line = 76, message = "Off", callback = "TurnOff" },
        { line = 77, message = "On", callback = "TurnOn" },
        { line = 153, message = "Respawn", callback = "OnCreatureDied" },
        { line = 164, message = "Respawn", callback = "AdjustTotals" },
    },
    movement_commands = {
    },
}
map.scripts["summoner.scr"] = {
    source = "SUMMONER.scr",
    registered_triggers = {
        { line = 53, message = "trigger", callback = "OnMinionDied" },
        { line = 54, message = "startup", callback = "SummonStarters" },
    },
    movement_commands = {
    },
}
map.scripts["switch.scr"] = {
    source = "SWITCH.scr",
    registered_triggers = {
        { line = 44, message = "Use", callback = "Onuse" },
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
