-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "templeofhonk"
map.scripts = {}

map.scripts["dumbgoose.scr"] = {
    source = "DUMBGOOSE.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["dumbgoose2.scr"] = {
    source = "DUMBGOOSE2.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["honk.scr"] = {
    source = "HONK.scr",
    registered_triggers = {
        { line = 94, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["honkaccountant.scr"] = {
    source = "HONKACCOUNTANT.scr",
    registered_triggers = {
        { line = 55, message = "stolen", callback = "KeyWasStolen" },
    },
    movement_commands = {
    },
}
map.scripts["honkfollower.scr"] = {
    source = "HONKFOLLOWER.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["honkfollowgoose.scr"] = {
    source = "HONKFOLLOWGOOSE.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["honkfollowgoose2.scr"] = {
    source = "HONKFOLLOWGOOSE2.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["honkkey.scr"] = {
    source = "HONKKEY.scr",
    registered_triggers = {
        { line = 54, message = "use", callback = "GivePlayerKey" },
        { line = 55, message = "getkey", callback = "RemoveKey" },
        { line = 56, message = "putkey", callback = "ReplaceKey" },
        { line = 97, message = "use", callback = "GivePlayerKey" },
    },
    movement_commands = {
    },
}
map.scripts["honkleader.scr"] = {
    source = "HONKLEADER.scr",
    registered_triggers = {
        { line = 52, message = "FollowerReady", callback = "StartCeremony" },
    },
    movement_commands = {
    },
}
map.scripts["honksecretdoor.scr"] = {
    source = "HONKSECRETDOOR.scr",
    registered_triggers = {
        { line = 170, message = "reset", callback = "resetButtons" },
        { line = 172, message = "UnlockButtons", callback = "UnlockButtons" },
        { line = 173, message = "hPressed", callback = "hPressed" },
        { line = 174, message = "oPressed", callback = "oPressed" },
        { line = 175, message = "nPressed", callback = "nPressed" },
        { line = 176, message = "kPressed", callback = "kPressed" },
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

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
