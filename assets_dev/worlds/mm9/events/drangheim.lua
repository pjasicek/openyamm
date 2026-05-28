-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "drangheim"
map.scripts = {}

map.scripts["dolly.scr"] = {
    source = "DOLLY.scr",
    registered_triggers = {
        { line = 75, message = "Use", callback = "Onuse" },
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
map.scripts["foradworld.scr"] = {
    source = "FORADWORLD.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["herbs.scr"] = {
    source = "HERBS.scr",
    registered_triggers = {
        { line = 76, message = "Use", callback = "Onuse" },
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
map.scripts["npc91.scr"] = {
    source = "NPC91.scr",
    registered_triggers = {
        { line = 97, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["npc92.scr"] = {
    source = "NPC92.scr",
    registered_triggers = {
        { line = 88, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["npc93.scr"] = {
    source = "NPC93.scr",
    registered_triggers = {
        { line = 87, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["plow.scr"] = {
    source = "PLOW.scr",
    registered_triggers = {
        { line = 75, message = "Use", callback = "Onuse" },
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
map.scripts["realbook.scr"] = {
    source = "REALBOOK.scr",
    registered_triggers = {
        { line = 68, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["shopkeeper.scr"] = {
    source = "SHOPKEEPER.scr",
    registered_triggers = {
        { line = 50, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
        { line = 70, command = "SetPos", arguments = "g_hMyObject -6415 544 4768" },
    },
}
map.scripts["tm_hardrock.scr"] = {
    source = "TM_HARDROCK.scr",
    registered_triggers = {
        { line = 65, message = "OneDown", callback = "OneDown" },
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
