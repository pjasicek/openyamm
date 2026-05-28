-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "thjorgardcity"
map.scripts = {}

map.scripts["bankorb.scr"] = {
    source = "BANKORB.scr",
    registered_triggers = {
        { line = 179, message = "Use", callback = "ONUse" },
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
map.scripts["foradworld.scr"] = {
    source = "FORADWORLD.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["greatbookkey.scr"] = {
    source = "GREATBOOKKEY.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
        { line = 75, message = "appear", callback = "OnAppear" },
    },
    movement_commands = {
    },
}
map.scripts["npc161.scr"] = {
    source = "NPC161.scr",
    registered_triggers = {
        { line = 180, message = "Use", callback = "OnUse" },
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
map.scripts["npc378.scr"] = {
    source = "NPC378.scr",
    registered_triggers = {
        { line = 281, message = "Use", callback = "OnUse" },
        { line = 282, message = "Appear", callback = "OnAppear" },
        { line = 283, message = "Appear2", callback = "OnAppear2" },
    },
    movement_commands = {
        { line = 108, command = "setpos", arguments = "g_hobject -2806 1240 5040" },
        { line = 144, command = "setpos", arguments = "g_hmyobject MyX MyY MyZ" },
        { line = 165, command = "setpos", arguments = "g_hmyobject XPos YPos ZPos" },
    },
}
map.scripts["npc4.scr"] = {
    source = "NPC4.scr",
    registered_triggers = {
        { line = 151, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc416.scr"] = {
    source = "NPC416.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc5.scr"] = {
    source = "NPC5.scr",
    registered_triggers = {
        { line = 129, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc7.scr"] = {
    source = "NPC7.scr",
    registered_triggers = {
        { line = 450, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["orbtrigger.scr"] = {
    source = "ORBTRIGGER.scr",
    registered_triggers = {
        { line = 32, message = "Use", callback = "OnUse" },
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
map.scripts["randverretainer.scr"] = {
    source = "RANDVERRETAINER.scr",
    registered_triggers = {
        { line = 75, message = "Use", callback = "Onblabber" },
    },
    movement_commands = {
    },
}
map.scripts["retainer.scr"] = {
    source = "RETAINER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
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
map.scripts["townportal.scr"] = {
    source = "TOWNPORTAL.scr",
    registered_triggers = {
        { line = 103, message = "Use", callback = "OnUse" },
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
