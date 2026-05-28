-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "wizardslab"
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
map.scripts["givetake.scr"] = {
    source = "GIVETAKE.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc55.scr"] = {
    source = "NPC55.scr",
    registered_triggers = {
        { line = 81, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["relic.scr"] = {
    source = "RELIC.scr",
    registered_triggers = {
        { line = 64, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["teleportermulti.scr"] = {
    source = "TELEPORTERMULTI.scr",
    registered_triggers = {
        { line = 19, message = "update", callback = "UpdateDestination" },
    },
    movement_commands = {
    },
}
map.scripts["teleporterswitch.scr"] = {
    source = "TELEPORTERSWITCH.scr",
    registered_triggers = {
        { line = 31, message = "use", callback = "SetDestination" },
        { line = 84, message = "use", callback = "SetDestination" },
    },
    movement_commands = {
    },
}
map.scripts["wizardeffect.scr"] = {
    source = "WIZARDEFFECT.scr",
    registered_triggers = {
        { line = 35, message = "play", callback = "PlayConjureEffect" },
        { line = 36, message = "shoot", callback = "PlayShootEffect" },
    },
    movement_commands = {
    },
}
map.scripts["wizardlabcamera.scr"] = {
    source = "WIZARDLABCAMERA.scr",
    registered_triggers = {
        { line = 19, message = "next", callback = "SoftExit" },
        { line = 29, message = "next", callback = "StartNextScene" },
    },
    movement_commands = {
    },
}
map.scripts["wizardmaster.scr"] = {
    source = "WIZARDMASTER.scr",
    registered_triggers = {
        { line = 47, message = "start", callback = "ConjureSpell" },
        { line = 48, message = "finish", callback = "BanishDemon" },
    },
    movement_commands = {
    },
}
map.scripts["wizardsummoner.scr"] = {
    source = "WIZARDSUMMONER.scr",
    registered_triggers = {
        { line = 43, message = "start", callback = "ConjureSpell" },
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
