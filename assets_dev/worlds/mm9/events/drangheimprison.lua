-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "drangheimprison"
map.scripts = {}

map.scripts["alarmcontrol.scr"] = {
    source = "ALARMCONTROL.scr",
    registered_triggers = {
        { line = 40, message = "Alarm", callback = "OnAlarm" },
    },
    movement_commands = {
    },
}
map.scripts["dp_patrol.scr"] = {
    source = "DP_PATROL.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["drangheimdoorman.scr"] = {
    source = "DRANGHEIMDOORMAN.scr",
    registered_triggers = {
        { line = 31, message = "open", callback = "OpenRoom" },
        { line = 32, message = "close", callback = "CloseRoom" },
    },
    movement_commands = {
    },
}
map.scripts["drangheimguardbasic.scr"] = {
    source = "DRANGHEIMGUARDBASIC.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["drangheiminterrogator.scr"] = {
    source = "DRANGHEIMINTERROGATOR.scr",
    registered_triggers = {
        { line = 93, message = "start", callback = "StartScript" },
        { line = 94, message = "outside", callback = "OnPrisonerOut" },
        { line = 95, message = "inside", callback = "OnPrisonerIn" },
        { line = 198, message = "start", callback = "StartScript" },
    },
    movement_commands = {
    },
}
map.scripts["drangheimprisoner.scr"] = {
    source = "DRANGHEIMPRISONER.scr",
    registered_triggers = {
        { line = 35, message = "followme", callback = "StartFollowing" },
        { line = 36, message = "return", callback = "EnterCell" },
        { line = 37, message = "leave", callback = "LeaveCell" },
        { line = 38, message = "use", callback = "OnPlayerRescue" },
    },
    movement_commands = {
    },
}
map.scripts["drangheimsmith.scr"] = {
    source = "DRANGHEIMSMITH.scr",
    registered_triggers = {
        { line = 66, message = "off", callback = "TurnOff" },
        { line = 67, message = "on", callback = "OnReturnedWeapon" },
    },
    movement_commands = {
    },
}
map.scripts["drangheimwarden.scr"] = {
    source = "DRANGHEIMWARDEN.scr",
    registered_triggers = {
        { line = 33, message = "open", callback = "OpenCell" },
        { line = 34, message = "close", callback = "CloseCell" },
        { line = 35, message = "change", callback = "ChangeCell" },
    },
    movement_commands = {
    },
}
map.scripts["guardhelp.scr"] = {
    source = "GUARDHELP.scr",
    registered_triggers = {
        { line = 91, message = "help", callback = "OnGiveHelp" },
    },
    movement_commands = {
    },
}
map.scripts["guardrude.scr"] = {
    source = "GUARDRUDE.scr",
    registered_triggers = {
        { line = 142, message = "Use", callback = "Onuse" },
        { line = 145, message = "Alarm", callback = "ONAlarm" },
    },
    movement_commands = {
    },
}
map.scripts["guardtonegate.scr"] = {
    source = "GUARDTONEGATE.scr",
    registered_triggers = {
        { line = 133, message = "Hello", callback = "PlayerIsHere" },
    },
    movement_commands = {
    },
}
map.scripts["npc419.scr"] = {
    source = "NPC419.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["npc427.scr"] = {
    source = "NPC427.scr",
    registered_triggers = {
        { line = 73, message = "Use", callback = "ONUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc90.scr"] = {
    source = "NPC90.scr",
    registered_triggers = {
        { line = 274, message = "Use", callback = "OnUse" },
        { line = 275, message = "Stop", callback = "OnSTop" },
    },
    movement_commands = {
        { line = 78, command = "setpos", arguments = "g_hMyObject -2525 948 397" },
        { line = 84, command = "setpos", arguments = "g_hMyObject -4253 817 -6191" },
        { line = 227, command = "setpos", arguments = "g_hmyobject xPos yPos zPos" },
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
