-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "guberlandcity"
map.scripts = {}

map.scripts["abriel.scr"] = {
    source = "ABRIEL.scr",
    registered_triggers = {
        { line = 254, message = "walk1", callback = "OnWalk1" },
        { line = 255, message = "speak4", callback = "OnSpeak4" },
        { line = 256, message = "speak6", callback = "OnSpeak6" },
        { line = 257, message = "speak8", callback = "OnSpeak8" },
        { line = 258, message = "Speak14", callback = "OnSpeak14" },
        { line = 259, message = "Speak17", callback = "OnSpeak17" },
        { line = 260, message = "Speak19", callback = "OnSpeak19" },
        { line = 261, message = "Exit", callback = "OnExit" },
        { line = 262, message = "Walk2", callback = "OnWalk2" },
        { line = 263, message = "CastCall", callback = "OnCastCall" },
        { line = 264, message = "Bow", callback = "OnBow" },
    },
    movement_commands = {
    },
}
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
map.scripts["leffery.scr"] = {
    source = "LEFFERY.scr",
    registered_triggers = {
        { line = 137, message = "Start", callback = "OnStart" },
        { line = 138, message = "Speak12", callback = "OnSpeak12" },
        { line = 139, message = "speak14", callback = "OnSpeak14" },
        { line = 140, message = "target", callback = "OnTarget" },
        { line = 141, message = "Exit", callback = "OnExit" },
        { line = 142, message = "Walk2", callback = "OnWalk2" },
        { line = 143, message = "CastCall", callback = "OnCastCall" },
        { line = 144, message = "Bow", callback = "OnBow" },
    },
    movement_commands = {
    },
}
map.scripts["narrator.scr"] = {
    source = "NARRATOR.scr",
    registered_triggers = {
        { line = 251, message = "start", callback = "Onstart" },
        { line = 252, message = "stop", callback = "OnStop" },
        { line = 253, message = "Speak9", callback = "OnSpeak9" },
        { line = 254, message = "Speak21", callback = "OnSpeak21" },
        { line = 255, message = "Speak22", callback = "OnSpeak22" },
        { line = 256, message = "Speak27", callback = "OnSpeak27" },
    },
    movement_commands = {
    },
}
map.scripts["npc127.scr"] = {
    source = "NPC127.scr",
    registered_triggers = {
        { line = 222, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc128.scr"] = {
    source = "NPC128.scr",
    registered_triggers = {
        { line = 161, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc129.scr"] = {
    source = "NPC129.scr",
    registered_triggers = {
        { line = 171, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc131.scr"] = {
    source = "NPC131.scr",
    registered_triggers = {
        { line = 82, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc141.scr"] = {
    source = "NPC141.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["npc142.scr"] = {
    source = "NPC142.scr",
    registered_triggers = {
        { line = 107, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
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
map.scripts["propanim.scr"] = {
    source = "PROPANIM.scr",
    registered_triggers = {
        { line = 42, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["ralof.scr"] = {
    source = "RALOF.scr",
    registered_triggers = {
        { line = 297, message = "start", callback = "OnStart" },
        { line = 298, message = "Speak11", callback = "OnSpeak11" },
        { line = 299, message = "Speak13", callback = "OnSpeak13" },
        { line = 300, message = "Speak16", callback = "OnSpeak16" },
        { line = 301, message = "Speak18", callback = "OnSpeak18" },
        { line = 302, message = "Speak20", callback = "OnSpeak20" },
        { line = 303, message = "Exit", callback = "OnExit" },
        { line = 304, message = "Walk2", callback = "OnWalk2" },
        { line = 305, message = "Speak24", callback = "OnSpeak24" },
        { line = 306, message = "Speak26", callback = "OnSpeak26" },
        { line = 307, message = "CastCall", callback = "OnCastCall" },
        { line = 308, message = "Bow", callback = "OnBow" },
        { line = 309, message = "Wince", callback = "OnWince" },
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
map.scripts["trislan.scr"] = {
    source = "TRISLAN.scr",
    registered_triggers = {
        { line = 235, message = "Walk1", callback = "OnWalk1" },
        { line = 236, message = "Speak5", callback = "OnSpeak5" },
        { line = 237, message = "Speak7", callback = "OnSpeak7" },
        { line = 238, message = "Walk2", callback = "OnWalk2" },
        { line = 239, message = "exit", callback = "Onexit" },
        { line = 240, message = "Speak23", callback = "OnSpeak23" },
        { line = 241, message = "Speak25", callback = "OnSpeak25" },
        { line = 242, message = "Die", callback = "OnDie" },
        { line = 243, message = "CastCall", callback = "OnCastCall" },
        { line = 244, message = "Bow", callback = "OnBow" },
    },
    movement_commands = {
    },
}
map.scripts["wilam.scr"] = {
    source = "WILAM.scr",
    registered_triggers = {
        { line = 153, message = "Start", callback = "OnStart" },
        { line = 154, message = "Speak9", callback = "OnSpeak9" },
        { line = 155, message = "target", callback = "OnTarget" },
        { line = 156, message = "Attention", callback = "OnAttention" },
        { line = 157, message = "Exit", callback = "OnExit" },
        { line = 158, message = "walk2", callback = "OnWalk2" },
        { line = 159, message = "CastCall", callback = "OnCastCall" },
        { line = 160, message = "Bow", callback = "OnBow" },
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
