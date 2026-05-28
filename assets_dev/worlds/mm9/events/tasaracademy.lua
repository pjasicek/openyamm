-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "tasaracademy"
map.scripts = {}

map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["bookofrules.scr"] = {
    source = "BOOKOFRULES.scr",
    registered_triggers = {
        { line = 69, message = "Use", callback = "Onuse" },
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
map.scripts["proptrigger.scr"] = {
    source = "PROPTRIGGER.scr",
    registered_triggers = {
        { line = 64, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["skillbook.scr"] = {
    source = "SKILLBOOK.scr",
    registered_triggers = {
        { line = 195, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["tasarbook.scr"] = {
    source = "TASARBOOK.scr",
    registered_triggers = {
        { line = 138, message = "Use", callback = "OnUse" },
        { line = 153, message = "Use", callback = "OnUse" },
        { line = 154, message = "Visible1", callback = "OnVisible" },
    },
    movement_commands = {
    },
}
map.scripts["tasarchalice.scr"] = {
    source = "TASARCHALICE.scr",
    registered_triggers = {
        { line = 35, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["tasarguardduty.scr"] = {
    source = "TASARGUARDDUTY.scr",
    registered_triggers = {
        { line = 138, message = "use", callback = "OnOffDuty" },
    },
    movement_commands = {
        { line = 84, command = "Setpos", arguments = "g_hobject PosX PosY PosZ" },
        { line = 116, command = "Setpos", arguments = "g_hobject StartPosX StartPosY StartPosZ" },
    },
}
map.scripts["tasarstudent.scr"] = {
    source = "TASARSTUDENT.scr",
    registered_triggers = {
        { line = 26, message = "Hate", callback = "OnHate" },
    },
    movement_commands = {
    },
}
map.scripts["tasartable.scr"] = {
    source = "TASARTABLE.scr",
    registered_triggers = {
        { line = 164, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["tasarteacher.scr"] = {
    source = "TASARTEACHER.scr",
    registered_triggers = {
        { line = 64, message = "Fight", callback = "OnSpawn" },
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
