-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "isleofashes"
map.scripts = {}

map.scripts["autoresurrect.scr"] = {
    source = "AUTORESURRECT.scr",
    registered_triggers = {
        { line = 83, message = "TMSG_RESURRECT", callback = "OnResurrect" },
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
map.scripts["forad.scr"] = {
    source = "FORAD.scr",
    registered_triggers = {
        { line = 176, message = "Use", callback = "OnUse" },
        { line = 177, message = "Appear", callback = "OnAppear" },
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
map.scripts["ia_camera2.scr"] = {
    source = "IA_CAMERA2.scr",
    registered_triggers = {
        { line = 57, message = "Pan", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 35, command = "MoveToPos", arguments = "xpos Xpos Zpos 100 DoNothing" },
    },
}
map.scripts["ia_island.scr"] = {
    source = "IA_ISLAND.scr",
    registered_triggers = {
        { line = 29, message = "SinkSpeed", callback = "OnSinkSpeed" },
    },
    movement_commands = {
    },
}
map.scripts["is_boat.scr"] = {
    source = "IS_BOAT.scr",
    registered_triggers = {
        { line = 62, message = "Move", callback = "OnMove" },
    },
    movement_commands = {
        { line = 42, command = "MoveToPos", arguments = "xpos MyY Zpos 100 DoNothing" },
    },
}
map.scripts["isle_islandexplosion.scr"] = {
    source = "ISLE_ISLANDEXPLOSION.scr",
    registered_triggers = {
        { line = 23, message = "explode", callback = "CreateExplosion" },
    },
    movement_commands = {
    },
}
map.scripts["isle_seamon.scr"] = {
    source = "ISLE_SEAMON.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["isle_skull.scr"] = {
    source = "ISLE_SKULL.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["isle_summoner.scr"] = {
    source = "ISLE_SUMMONER.scr",
    registered_triggers = {
        { line = 54, message = "spawn", callback = "SpawnCreature" },
    },
    movement_commands = {
    },
}
map.scripts["isleashesbook.scr"] = {
    source = "ISLEASHESBOOK.scr",
    registered_triggers = {
        { line = 252, message = "Crane", callback = "OnCrane2" },
        { line = 253, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["isleofashesactor.scr"] = {
    source = "ISLEOFASHESACTOR.scr",
    registered_triggers = {
        { line = 317, message = "RunNormalScript", callback = "RunNormalScript" },
        { line = 325, message = "MacRunAway", callback = "OnMacFoundPlayer" },
        { line = 326, message = "GoAfterPlayer", callback = "GoAfterPlayer" },
        { line = 331, message = "GoThrowBones", callback = "GoThrowBones" },
    },
    movement_commands = {
        { line = 73, command = "SetPos", arguments = "g_hObject,g_posX,g_posY,g_posZ" },
        { line = 166, command = "SetPos", arguments = "g_hMyObject,g_posX,g_posY,g_posZ" },
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
map.scripts["proptrigger.scr"] = {
    source = "PROPTRIGGER.scr",
    registered_triggers = {
        { line = 64, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["tm_hardrock.scr"] = {
    source = "TM_HARDROCK.scr",
    registered_triggers = {
        { line = 65, message = "OneDown", callback = "OneDown" },
    },
    movement_commands = {
    },
}
map.scripts["yrsa.scr"] = {
    source = "YRSA.scr",
    registered_triggers = {
        { line = 135, message = "Use", callback = "OnUse" },
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
