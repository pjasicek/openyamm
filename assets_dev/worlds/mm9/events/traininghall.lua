-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "traininghall"
map.scripts = {}

map.scripts["th_jousttrellborg.scr"] = {
    source = "TH_JOUSTTRELLBORG.scr",
    registered_triggers = {
        { line = 66, message = "Go", callback = "Start" },
        { line = 67, message = "Stop", callback = "TurnOff" },
        { line = 68, message = "BackPos", callback = "StartAnimations" },
    },
    movement_commands = {
    },
}
map.scripts["th_lobbyghouls.scr"] = {
    source = "TH_LOBBYGHOULS.scr",
    registered_triggers = {
        { line = 86, message = "Go", callback = "RunUpStairs" },
        { line = 87, message = "Drop", callback = "DropGhouls" },
    },
    movement_commands = {
        { line = 57, command = "SetPos", arguments = "hMyObject, nNumX, nNumY, nNumZ" },
    },
}
map.scripts["th_lookouttrellborg.scr"] = {
    source = "TH_LOOKOUTTRELLBORG.scr",
    registered_triggers = {
        { line = 88, message = "Go", callback = "Start" },
        { line = 89, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["th_meantrellborg.scr"] = {
    source = "TH_MEANTRELLBORG.scr",
    registered_triggers = {
        { line = 86, message = "Go", callback = "Start" },
        { line = 87, message = "Stop", callback = "TurnOff" },
        { line = 88, message = "Switch", callback = "ResetSwitch" },
        { line = 89, message = "Throw", callback = "CheckStart" },
    },
    movement_commands = {
    },
}
map.scripts["th_orcsgossip.scr"] = {
    source = "TH_ORCSGOSSIP.scr",
    registered_triggers = {
        { line = 67, message = "Go", callback = "Start" },
        { line = 68, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["th_targetmgr.scr"] = {
    source = "TH_TARGETMGR.scr",
    registered_triggers = {
        { line = 29, message = "hit", callback = "OnTargetHit" },
        { line = 31, message = "openall", callback = "RaiseTargets" },
        { line = 32, message = "closeall", callback = "LowerTargets" },
    },
    movement_commands = {
    },
}
map.scripts["th_targetring.scr"] = {
    source = "TH_TARGETRING.scr",
    registered_triggers = {
        { line = 27, message = "on", callback = "TurnOn" },
        { line = 28, message = "off", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["th_trainingorccommander.scr"] = {
    source = "TH_TRAININGORCCOMMANDER.scr",
    registered_triggers = {
        { line = 55, message = "Train", callback = "Start" },
        { line = 56, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["th_trainingorcobserver.scr"] = {
    source = "TH_TRAININGORCOBSERVER.scr",
    registered_triggers = {
        { line = 71, message = "Train", callback = "Start" },
        { line = 72, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["th_trainingorcs.scr"] = {
    source = "TH_TRAININGORCS.scr",
    registered_triggers = {
        { line = 67, message = "Train", callback = "Start" },
        { line = 68, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["trainingenter.scr"] = {
    source = "TRAININGENTER.scr",
    registered_triggers = {
        { line = 60, message = "Break", callback = "OnBreak" },
    },
    movement_commands = {
    },
}
map.scripts["traininghallexit.scr"] = {
    source = "TRAININGHALLEXIT.scr",
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
