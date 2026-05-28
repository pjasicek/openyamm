-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "lindisfarnemonastery"
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
map.scripts["lindisfarnebell.scr"] = {
    source = "LINDISFARNEBELL.scr",
    registered_triggers = {
        { line = 129, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["lindisfarnebellcontroller.scr"] = {
    source = "LINDISFARNEBELLCONTROLLER.scr",
    registered_triggers = {
        { line = 172, message = "Bell1", callback = "OnBell1" },
        { line = 173, message = "Bell2", callback = "OnBell2" },
        { line = 174, message = "Bell3", callback = "OnBell3" },
        { line = 175, message = "Bell4", callback = "OnBell4" },
        { line = 176, message = "Bell5", callback = "OnBell5" },
    },
    movement_commands = {
    },
}
map.scripts["monkguardbasic.scr"] = {
    source = "MONKGUARDBASIC.scr",
    registered_triggers = {
        { line = 46, message = "use", callback = "OnRudeEnter" },
        { line = 63, message = "gotopray", callback = "StartPrayer" },
    },
    movement_commands = {
    },
}
map.scripts["npc282.scr"] = {
    source = "NPC282.scr",
    registered_triggers = {
        { line = 148, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc283.scr"] = {
    source = "NPC283.scr",
    registered_triggers = {
        { line = 86, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc284.scr"] = {
    source = "NPC284.scr",
    registered_triggers = {
        { line = 94, message = "Use", callback = "OnUse" },
        { line = 95, message = "Appear", callback = "Appear" },
    },
    movement_commands = {
    },
}
map.scripts["npc420.scr"] = {
    source = "NPC420.scr",
    registered_triggers = {
        { line = 121, message = "Play", callback = "PlayAnim" },
        { line = 122, message = "Use", callback = "OnUse" },
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
map.scripts["thjorad.scr"] = {
    source = "THJORAD.scr",
    registered_triggers = {
        { line = 100, message = "Use", callback = "Onuse" },
        { line = 101, message = "TurnOn", callback = "OnTurnOn" },
    },
    movement_commands = {
    },
}
map.scripts["thjoradmonk.scr"] = {
    source = "THJORADMONK.scr",
    registered_triggers = {
        { line = 116, message = "GoToPray", callback = "OnGoToPray" },
        { line = 117, message = "Use", callback = "Onuse" },
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
