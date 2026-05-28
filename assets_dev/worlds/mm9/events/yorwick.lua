-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "yorwick"
map.scripts = {}

map.scripts["battlecam1.scr"] = {
    source = "BATTLECAM1.scr",
    registered_triggers = {
        { line = 47, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 31, command = "MoveToPos", arguments = "xpos Ypos Zpos nSpeed OnArrive" },
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
map.scripts["hidemodel.scr"] = {
    source = "HIDEMODEL.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["marysheep.scr"] = {
    source = "MARYSHEEP.scr",
    registered_triggers = {
        { line = 52, message = "RuntoMe", callback = "OnRun" },
        { line = 53, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc312.scr"] = {
    source = "NPC312.scr",
    registered_triggers = {
        { line = 81, message = "Use", callback = "OnUse" },
        { line = 82, message = "Target", callback = "ONTarget" },
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
map.scripts["shopkeeper.scr"] = {
    source = "SHOPKEEPER.scr",
    registered_triggers = {
        { line = 50, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
        { line = 70, command = "SetPos", arguments = "g_hMyObject -6415 544 4768" },
    },
}
map.scripts["svenspeech.scr"] = {
    source = "SVENSPEECH.scr",
    registered_triggers = {
        { line = 312, message = "Done", callback = "OnDone" },
        { line = 313, message = "Start", callback = "OnStart" },
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
