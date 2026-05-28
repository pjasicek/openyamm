-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "arslegardcity"
map.scripts = {}

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
map.scripts["doorlock.scr"] = {
    source = "DOORLOCK.scr",
    registered_triggers = {
        { line = 57, message = "use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["fateman.scr"] = {
    source = "FATEMAN.scr",
    registered_triggers = {
        { line = 452, message = "Lose", callback = "OnLose" },
        { line = 453, message = "Cam2", callback = "OnCam2" },
        { line = 454, message = "cam3", callback = "OnCam3" },
        { line = 455, message = "FadeOut", callback = "Close" },
        { line = 456, message = "Done", callback = "OnDone" },
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
map.scripts["hanndl.scr"] = {
    source = "HANNDL.scr",
    registered_triggers = {
        { line = 238, message = "Speak", callback = "Speak1" },
        { line = 239, message = "Speak9", callback = "OnSpeak9" },
        { line = 240, message = "Speak10", callback = "OnSpeak10" },
        { line = 241, message = "Speak11", callback = "OnSpeak11" },
        { line = 242, message = "Speak12", callback = "OnSpeak12" },
        { line = 243, message = "Speak13", callback = "OnSpeak13" },
        { line = 244, message = "Speak14", callback = "OnSpeak14" },
        { line = 245, message = "Speak15", callback = "OnSpeak15" },
        { line = 246, message = "Speak16", callback = "OnSpeak16" },
        { line = 247, message = "Speak17", callback = "OnSpeak17" },
    },
    movement_commands = {
    },
}
map.scripts["losecam1.scr"] = {
    source = "LOSECAM1.scr",
    registered_triggers = {
        { line = 73, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 48, command = "MoveToPos", arguments = "xpos Ypos Zpos 100 OnArrive1" },
        { line = 64, command = "SetPos", arguments = "g_hmyobject MyX MyY MyZ DoNothing" },
    },
}
map.scripts["losecam2.scr"] = {
    source = "LOSECAM2.scr",
    registered_triggers = {
        { line = 70, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 45, command = "MoveToPos", arguments = "xpos Ypos Zpos 150 OnArrive1" },
        { line = 61, command = "SetPos", arguments = "g_hmyobject MyX MyY MyZ DoNothing" },
    },
}
map.scripts["losecam3.scr"] = {
    source = "LOSECAM3.scr",
    registered_triggers = {
        { line = 73, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 47, command = "MoveToPos", arguments = "xpos Ypos Zpos 100 OnArrive1" },
        { line = 62, command = "SetPos", arguments = "g_hmyobject MyX MyY MyZ DoNothing" },
    },
}
map.scripts["loseman.scr"] = {
    source = "LOSEMAN.scr",
    registered_triggers = {
        { line = 113, message = "Lose", callback = "OnLose" },
        { line = 114, message = "Cam2", callback = "OnCam2" },
        { line = 115, message = "cam3", callback = "OnCam3" },
        { line = 116, message = "FadeOut", callback = "Close" },
    },
    movement_commands = {
    },
}
map.scripts["njamchase.scr"] = {
    source = "NJAMCHASE.scr",
    registered_triggers = {
        { line = 79, message = "Chase", callback = "OnChase" },
    },
    movement_commands = {
    },
}
map.scripts["npc3.scr"] = {
    source = "NPC3.scr",
    registered_triggers = {
        { line = 237, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
        { line = 198, command = "MoveToPos", arguments = "32 1438 8100" },
    },
}
map.scripts["npc334.scr"] = {
    source = "NPC334.scr",
    registered_triggers = {
        { line = 88, message = "Use", callback = "OnUse" },
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
map.scripts["writman.scr"] = {
    source = "WRITMAN.scr",
    registered_triggers = {
        { line = 284, message = "Lose", callback = "OnLose" },
        { line = 285, message = "Cam2", callback = "OnCam2" },
        { line = 286, message = "cam3", callback = "OnCam3" },
        { line = 287, message = "FadeOut", callback = "Close" },
        { line = 292, message = "Done", callback = "OnDone" },
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
