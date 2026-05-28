-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "darkpassageway"
map.scripts = {}

map.scripts["darkp_bridgepuzzle.scr"] = {
    source = "DARKP_BRIDGEPUZZLE.scr",
    registered_triggers = {
        { line = 133, message = "HitA", callback = "HitA" },
        { line = 134, message = "HitB", callback = "HitB" },
        { line = 135, message = "HitC", callback = "HitC" },
        { line = 136, message = "HitD", callback = "HitD" },
        { line = 137, message = "Reset", callback = "Reset" },
    },
    movement_commands = {
    },
}
map.scripts["darkp_bridgereset.scr"] = {
    source = "DARKP_BRIDGERESET.scr",
    registered_triggers = {
        { line = 41, message = "Use", callback = "MoveMe" },
        { line = 42, message = "Stop", callback = "TurnSwitchOff" },
    },
    movement_commands = {
    },
}
map.scripts["darkp_canyonswitch.scr"] = {
    source = "DARKP_CANYONSWITCH.scr",
    registered_triggers = {
        { line = 86, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["darkp_npcdie.scr"] = {
    source = "DARKP_NPCDIE.scr",
    registered_triggers = {
        { line = 31, message = "Wince", callback = "TakeHit" },
        { line = 32, message = "destroy", callback = "Die" },
    },
    movement_commands = {
    },
}
map.scripts["darkp_raisingbridge.scr"] = {
    source = "DARKP_RAISINGBRIDGE.scr",
    registered_triggers = {
        { line = 61, message = "Move", callback = "MoveMe" },
    },
    movement_commands = {
        { line = 35, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 180, StopHere" },
        { line = 44, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 180, StopHere" },
    },
}
map.scripts["darkp_raisingswitch.scr"] = {
    source = "DARKP_RAISINGSWITCH.scr",
    registered_triggers = {
        { line = 48, message = "Use", callback = "MoveMe" },
        { line = 49, message = "Stop", callback = "TurnSwitchOff" },
    },
    movement_commands = {
    },
}
map.scripts["darkp_warrior.scr"] = {
    source = "DARKP_WARRIOR.scr",
    registered_triggers = {
        { line = 40, message = "HitNpc", callback = "BeginSequence" },
    },
    movement_commands = {
    },
}
map.scripts["dp_cagemonster.scr"] = {
    source = "DP_CAGEMONSTER.scr",
    registered_triggers = {
        { line = 25, message = "on", callback = "TurnOn" },
        { line = 26, message = "off", callback = "TurnOff" },
        { line = 28, message = "go", callback = "OpenCage" },
        { line = 59, message = "go", callback = "OpenCage" },
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
map.scripts["magiccarpet.scr"] = {
    source = "MAGICCARPET.scr",
    registered_triggers = {
        { line = 37, message = "Use", callback = "StartRising" },
        { line = 107, message = "Use", callback = "StartRising" },
    },
    movement_commands = {
    },
}
map.scripts["npc338.scr"] = {
    source = "NPC338.scr",
    registered_triggers = {
        { line = 104, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["passagegemstone.scr"] = {
    source = "PASSAGEGEMSTONE.scr",
    registered_triggers = {
        { line = 38, message = "use", callback = "ShineLight" },
        { line = 39, message = "trigger", callback = "ReleaseMonsters" },
        { line = 100, message = "use", callback = "ShineLight" },
    },
    movement_commands = {
    },
}
map.scripts["passagelaser.scr"] = {
    source = "PASSAGELASER.scr",
    registered_triggers = {
        { line = 29, message = "rotate", callback = "Rotate" },
    },
    movement_commands = {
    },
}
map.scripts["passagemirror.scr"] = {
    source = "PASSAGEMIRROR.scr",
    registered_triggers = {
        { line = 53, message = "use", callback = "Rotate" },
        { line = 54, message = "off", callback = "TakeFocus" },
        { line = 55, message = "trigger", callback = "GiveFocus" },
    },
    movement_commands = {
        { line = 71, command = "Rotate", arguments = "0,1,0, dA, 180, DoNothing" },
    },
}
map.scripts["spawnnjamcameo.scr"] = {
    source = "SPAWNNJAMCAMEO.scr",
    registered_triggers = {
        { line = 122, message = "Spawn", callback = "Onspawn" },
        { line = 123, message = "KillNjam", callback = "Vanish2c" },
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
