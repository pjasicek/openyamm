-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "bathhouse"
map.scripts = {}

map.scripts["bathfurnace.scr"] = {
    source = "BATHFURNACE.scr",
    registered_triggers = {
        { line = 112, message = "turnon", callback = "turnon" },
        { line = 113, message = "turnoff", callback = "turnoff" },
        { line = 114, message = "repeat0", callback = "repeat0" },
        { line = 115, message = "repeat1", callback = "repeat1" },
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
map.scripts["dp2steam.scr"] = {
    source = "DP2STEAM.scr",
    registered_triggers = {
        { line = 36, message = "FireOn", callback = "FireOn" },
        { line = 37, message = "FireOff", callback = "FireOff" },
    },
    movement_commands = {
    },
}
map.scripts["dp2waterdamage.scr"] = {
    source = "DP2WATERDAMAGE.scr",
    registered_triggers = {
        { line = 38, message = "DamageOn", callback = "DamageOn" },
        { line = 39, message = "DamageOff", callback = "DamageOff" },
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
map.scripts["eborabath.scr"] = {
    source = "EBORABATH.scr",
    registered_triggers = {
        { line = 209, message = "OnGossip", callback = "OnGossip" },
        { line = 210, message = "DeadConcubine", callback = "DeadConcubine" },
        { line = 211, message = "DeadPal", callback = "DeadPal" },
    },
    movement_commands = {
    },
}
map.scripts["eboracam1.scr"] = {
    source = "EBORACAM1.scr",
    registered_triggers = {
        { line = 25, message = "on", callback = "CameraOn" },
    },
    movement_commands = {
    },
}
map.scripts["eboraconcubine.scr"] = {
    source = "EBORACONCUBINE.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["effectsmgr.scr"] = {
    source = "EFFECTSMGR.scr",
    registered_triggers = {
        { line = 55, message = "StartScene", callback = "DoScene" },
        { line = 133, message = "QuakeOn", callback = "TurnQuakeOn" },
        { line = 134, message = "QuakeOff", callback = "TurnQuakeOff" },
        { line = 135, message = "TextOn", callback = "TurnTextOn" },
        { line = 136, message = "TextOff", callback = "TurnTextOff" },
        { line = 137, message = "BoxOn", callback = "TurnBoxOn" },
        { line = 138, message = "BoxOff", callback = "TurnBoxOff" },
        { line = 140, message = "DurationLong", callback = "SetDurationLong" },
        { line = 141, message = "DurationShort", callback = "SetDurationShort" },
        { line = 142, message = "DurationInstant", callback = "SetDurationInstant" },
        { line = 144, message = "QuakeStrong", callback = "SetQuakeHigh" },
        { line = 145, message = "QuakeWeak", callback = "SetQuakeMed" },
    },
    movement_commands = {
        { line = 126, command = "SetPOS", arguments = "hMe, x,y,z" },
    },
}
map.scripts["fatc.scr"] = {
    source = "FATC.scr",
    registered_triggers = {
        { line = 60, message = "Die", callback = "OnDie" },
        { line = 61, message = "MoveIt", callback = "OnMoveIt" },
        { line = 62, message = "EboraArrive", callback = "OnEboraArrive" },
    },
    movement_commands = {
        { line = 20, command = "MoveToPos", arguments = "1808, 44, g_posZ, g_velX, Arrived" },
    },
}
map.scripts["furnacewarning.scr"] = {
    source = "FURNACEWARNING.scr",
    registered_triggers = {
        { line = 32, message = "use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["imphenchman.scr"] = {
    source = "IMPHENCHMAN.scr",
    registered_triggers = {
        { line = 21, message = "Help", callback = "DefendImp" },
    },
    movement_commands = {
    },
}
map.scripts["spawnloc.scr"] = {
    source = "SPAWNLOC.scr",
    registered_triggers = {
        { line = 30, message = "On", callback = "TurnOn" },
        { line = 61, message = "spawn", callback = "RequestSpawn" },
        { line = 62, message = "focus", callback = "RequestFocus" },
        { line = 63, message = "off", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["spawnmgr.scr"] = {
    source = "SPAWNMGR.scr",
    registered_triggers = {
        { line = 73, message = "SetLocation", callback = "SetLocation" },
        { line = 74, message = "Respawn", callback = "OnCreatureDied" },
        { line = 75, message = "ForceSpawn", callback = "SpawnCreature" },
        { line = 76, message = "Off", callback = "TurnOff" },
        { line = 77, message = "On", callback = "TurnOn" },
        { line = 153, message = "Respawn", callback = "OnCreatureDied" },
        { line = 164, message = "Respawn", callback = "AdjustTotals" },
    },
    movement_commands = {
    },
}
map.scripts["steamvent.scr"] = {
    source = "STEAMVENT.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["steamventdb.scr"] = {
    source = "STEAMVENTDB.scr",
    registered_triggers = {
        { line = 66, message = "turnon", callback = "turnon" },
        { line = 67, message = "turnoff", callback = "turnoff" },
    },
    movement_commands = {
        { line = 37, command = "movetopos", arguments = "ax ay az 1000 dn" },
        { line = 45, command = "movetopos", arguments = "bx by bz 1000 dn" },
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
