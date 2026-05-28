-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "sturmfordcity"
map.scripts = {}

map.scripts["akeretainer.scr"] = {
    source = "AKERETAINER.scr",
    registered_triggers = {
        { line = 52, message = "Use", callback = "Onblabber" },
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
map.scripts["beathag.scr"] = {
    source = "BEATHAG.scr",
    registered_triggers = {
        { line = 69, message = "break", callback = "Onbreak" },
        { line = 70, message = "use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["bjarni.scr"] = {
    source = "BJARNI.scr",
    registered_triggers = {
        { line = 241, message = "Use", callback = "OnUse" },
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
map.scripts["erccspeech.scr"] = {
    source = "ERCCSPEECH.scr",
    registered_triggers = {
        { line = 85, message = "Blabber", callback = "OnBlabber" },
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
map.scripts["ludwigvan.scr"] = {
    source = "LUDWIGVAN.scr",
    registered_triggers = {
        { line = 63, message = "Use", callback = "OnUse" },
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
map.scripts["npc48.scr"] = {
    source = "NPC48.scr",
    registered_triggers = {
        { line = 160, message = "Use", callback = "Onblabber" },
        { line = 161, message = "Start", callback = "OnWander" },
        { line = 162, message = "GoHome", callback = "OnHome" },
        { line = 163, message = "GotoJail", callback = "OnJail" },
    },
    movement_commands = {
        { line = 138, command = "setpos", arguments = "g_hmyobject xPos yPos zPos" },
    },
}
map.scripts["npc49.scr"] = {
    source = "NPC49.scr",
    registered_triggers = {
        { line = 51, message = "Use", callback = "Onblabber" },
    },
    movement_commands = {
        { line = 40, command = "setpos", arguments = "g_hmyobject xPos yPos zPos" },
    },
}
map.scripts["npc50.scr"] = {
    source = "NPC50.scr",
    registered_triggers = {
        { line = 46, message = "Use", callback = "Onblabber" },
    },
    movement_commands = {
    },
}
map.scripts["npc61.scr"] = {
    source = "NPC61.scr",
    registered_triggers = {
        { line = 173, message = "Use", callback = "OnUse" },
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
map.scripts["propanim.scr"] = {
    source = "PROPANIM.scr",
    registered_triggers = {
        { line = 42, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["randverrun.scr"] = {
    source = "RANDVERRUN.scr",
    registered_triggers = {
        { line = 128, message = "run", callback = "OnRudeExit2" },
        { line = 130, message = "use", callback = "Onuse" },
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
map.scripts["spieslikeus.scr"] = {
    source = "SPIESLIKEUS.scr",
    registered_triggers = {
        { line = 52, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["sturmgaardinn.scr"] = {
    source = "STURMGAARDINN.scr",
    registered_triggers = {
        { line = 71, message = "break", callback = "Onbreak" },
        { line = 72, message = "use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["sturmguard.scr"] = {
    source = "STURMGUARD.scr",
    registered_triggers = {
        { line = 80, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
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
map.scripts["tryggvaspeech.scr"] = {
    source = "TRYGGVASPEECH.scr",
    registered_triggers = {
        { line = 115, message = "blabber", callback = "Onblabber" },
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
