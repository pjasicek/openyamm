-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "yanmirsfort"
map.scripts = {}

map.scripts["propanim.scr"] = {
    source = "PROPANIM.scr",
    registered_triggers = {
        { line = 42, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["writ.scr"] = {
    source = "WRIT.scr",
    registered_triggers = {
        { line = 71, message = "Use", callback = "Onuse" },
        { line = 81, message = "init", callback = "OnInit" },
    },
    movement_commands = {
    },
}
map.scripts["yanmir.scr"] = {
    source = "YANMIR.scr",
    registered_triggers = {
        { line = 51, message = "Use", callback = "DoNothing" },
        { line = 52, message = "Trigger", callback = "DoNothing" },
    },
    movement_commands = {
    },
}
map.scripts["yanmir_camera.scr"] = {
    source = "YANMIR_CAMERA.scr",
    registered_triggers = {
        { line = 63, message = "ON", callback = "TurnOn" },
        { line = 64, message = "OFF", callback = "OnTurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["yanmir_endofworld.scr"] = {
    source = "YANMIR_ENDOFWORLD.scr",
    registered_triggers = {
        { line = 76, message = "OutOfWorld", callback = "OnOutOfWorld" },
    },
    movement_commands = {
    },
}
map.scripts["yanmirbase.scr"] = {
    source = "YANMIRBASE.scr",
    registered_triggers = {
        { line = 526, message = "Squish", callback = "Begin" },
        { line = 527, message = "PlayerRanAway", callback = "OnPlayerRanAway" },
        { line = 528, message = "TimeToDie", callback = "OnTimeToDie" },
        { line = 529, message = "DestroyFloor", callback = "DestroyFloor" },
    },
    movement_commands = {
        { line = 144, command = "SetPos", arguments = "hDust,g_posX,g_posY,g_posZ" },
    },
}
map.scripts["yanmirchild.scr"] = {
    source = "YANMIRCHILD.scr",
    registered_triggers = {
        { line = 32, message = "use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["yanmirfort_bugspawn.scr"] = {
    source = "YANMIRFORT_BUGSPAWN.scr",
    registered_triggers = {
        { line = 87, message = "RespawnMe", callback = "OnRespawnMe" },
    },
    movement_commands = {
    },
}
map.scripts["yanmirhidden.scr"] = {
    source = "YANMIRHIDDEN.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["yanmirkey.scr"] = {
    source = "YANMIRKEY.scr",
    registered_triggers = {
        { line = 21, message = "use", callback = "GiveKeyToPlayer" },
    },
    movement_commands = {
    },
}
map.scripts["yanmirtrap.scr"] = {
    source = "YANMIRTRAP.scr",
    registered_triggers = {
        { line = 24, message = "SupportBroken", callback = "CheckCount" },
    },
    movement_commands = {
    },
}
map.scripts["yf_explodingfloor.scr"] = {
    source = "YF_EXPLODINGFLOOR.scr",
    registered_triggers = {
        { line = 48, message = "Fall", callback = "DelayAction" },
    },
    movement_commands = {
    },
}
map.scripts["yf_fallingfloor.scr"] = {
    source = "YF_FALLINGFLOOR.scr",
    registered_triggers = {
        { line = 95, message = "Disappear", callback = "DelayAction" },
    },
    movement_commands = {
        { line = 75, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 1000, StopHere" },
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
