-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "verhoffinruins"
map.scripts = {}

map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["capstone.scr"] = {
    source = "CAPSTONE.scr",
    registered_triggers = {
        { line = 135, message = "place", callback = "OnPlace" },
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
map.scripts["drainwater.scr"] = {
    source = "DRAINWATER.scr",
    registered_triggers = {
        { line = 50, message = "drain", callback = "DrainWater" },
        { line = 51, message = "fill", callback = "FillWater" },
        { line = 66, message = "drain", callback = "DrainWater" },
        { line = 78, message = "fill", callback = "FillWater" },
    },
    movement_commands = {
        { line = 70, command = "MoveToPOS", arguments = "xMe,yMe,zMe, 10, OnFillWater" },
        { line = 82, command = "MoveToPOS", arguments = "xMe,yMe,zMe, 10, OnDrainWater" },
    },
}
map.scripts["fakebook.scr"] = {
    source = "FAKEBOOK.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "Onuse" },
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
map.scripts["kingkong.scr"] = {
    source = "KINGKONG.scr",
    registered_triggers = {
        { line = 41, message = "ForceBreak", callback = "RushCage" },
        { line = 42, message = "ForceFall", callback = "FallThrough" },
        { line = 43, message = "ForceAttack", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["pentagrampuzzle.scr"] = {
    source = "PENTAGRAMPUZZLE.scr",
    registered_triggers = {
        { line = 49, message = "start", callback = "StartPuzzle" },
        { line = 72, message = "first", callback = "FirstStep" },
        { line = 73, message = "second", callback = "SecondStep" },
        { line = 74, message = "third", callback = "ThirdStep" },
        { line = 75, message = "fourth", callback = "FourthStep" },
        { line = 76, message = "fifth", callback = "FifthStep" },
    },
    movement_commands = {
    },
}
map.scripts["placecapstone.scr"] = {
    source = "PLACECAPSTONE.scr",
    registered_triggers = {
        { line = 48, message = "Use", callback = "Onuse" },
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
map.scripts["writ.scr"] = {
    source = "WRIT.scr",
    registered_triggers = {
        { line = 71, message = "Use", callback = "Onuse" },
        { line = 81, message = "init", callback = "OnInit" },
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
