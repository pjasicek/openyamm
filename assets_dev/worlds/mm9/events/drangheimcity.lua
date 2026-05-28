-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "drangheimcity"
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
map.scripts["npc109.scr"] = {
    source = "NPC109.scr",
    registered_triggers = {
        { line = 141, message = "Speak2", callback = "OnSpeak2" },
        { line = 142, message = "Speak4", callback = "OnSpeak4" },
        { line = 143, message = "Speak6", callback = "OnSpeak6" },
        { line = 144, message = "Fight", callback = "OnFight" },
        { line = 145, message = "Target", callback = "OnTarget" },
    },
    movement_commands = {
    },
}
map.scripts["npc110.scr"] = {
    source = "NPC110.scr",
    registered_triggers = {
        { line = 179, message = "Start", callback = "OnStart" },
        { line = 180, message = "Speak3", callback = "OnSpeak3" },
        { line = 181, message = "Speak5", callback = "OnSpeak5" },
        { line = 182, message = "Speak7", callback = "OnSpeak7" },
    },
    movement_commands = {
        { line = 157, command = "setpos", arguments = "g_hmyobject xPos yPos zPos" },
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
map.scripts["npc414.scr"] = {
    source = "NPC414.scr",
    registered_triggers = {
        { line = 98, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc87.scr"] = {
    source = "NPC87.scr",
    registered_triggers = {
        { line = 192, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc88.scr"] = {
    source = "NPC88.scr",
    registered_triggers = {
        { line = 134, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc89.scr"] = {
    source = "NPC89.scr",
    registered_triggers = {
        { line = 132, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc95.scr"] = {
    source = "NPC95.scr",
    registered_triggers = {
        { line = 108, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc96.scr"] = {
    source = "NPC96.scr",
    registered_triggers = {
        { line = 83, message = "Use", callback = "OnUse" },
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
