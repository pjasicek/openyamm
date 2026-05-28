-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "ruinedtemple"
map.scripts = {}

map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["colloidalgenie.scr"] = {
    source = "COLLOIDALGENIE.scr",
    registered_triggers = {
        { line = 55, message = "appear", callback = "AppearWait" },
        { line = 100, message = "use", callback = "BlockRUDE" },
    },
    movement_commands = {
        { line = 80, command = "SetPOS", arguments = "hMe, x,y,z" },
    },
}
map.scripts["geniecrystal.scr"] = {
    source = "GENIECRYSTAL.scr",
    registered_triggers = {
        { line = 19, message = "use", callback = "CallGenie" },
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
map.scripts["rt_cavein.scr"] = {
    source = "RT_CAVEIN.scr",
    registered_triggers = {
        { line = 60, message = "Fall", callback = "Delay" },
    },
    movement_commands = {
        { line = 45, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 220, StopHere" },
    },
}
map.scripts["rt_counterbalance.scr"] = {
    source = "RT_COUNTERBALANCE.scr",
    registered_triggers = {
        { line = 43, message = "Fall", callback = "MoveToMarker" },
    },
    movement_commands = {
        { line = 38, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 300, StopHere" },
    },
}
map.scripts["suntemplebuttons.scr"] = {
    source = "SUNTEMPLEBUTTONS.scr",
    registered_triggers = {
        { line = 127, message = "Star1", callback = "HandleStar1" },
        { line = 128, message = "Star2", callback = "HandleStar2" },
        { line = 129, message = "Diamond1", callback = "HandleDiamond1" },
        { line = 130, message = "Diamond2", callback = "HandleDiamond2" },
        { line = 131, message = "Moon1", callback = "HandleMoon1" },
        { line = 132, message = "Moon2", callback = "HandleMoon2" },
        { line = 133, message = "Use", callback = "HandleMainButton" },
    },
    movement_commands = {
    },
}
map.scripts["treeoflife.scr"] = {
    source = "TREEOFLIFE.scr",
    registered_triggers = {
        { line = 38, message = "Use", callback = "Onuse" },
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
