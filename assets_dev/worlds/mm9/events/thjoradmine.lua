-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "thjoradmine"
map.scripts = {}

map.scripts["blowuptheboards.scr"] = {
    source = "BLOWUPTHEBOARDS.scr",
    registered_triggers = {
        { line = 37, message = "HitMe", callback = "DoTheDamage" },
    },
    movement_commands = {
    },
}
map.scripts["boardspike.scr"] = {
    source = "BOARDSPIKE.scr",
    registered_triggers = {
        { line = 56, message = "Use", callback = "OnUse" },
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
map.scripts["destructon.scr"] = {
    source = "DESTRUCTON.scr",
    registered_triggers = {
        { line = 37, message = "DamageOn", callback = "OnDamageOn" },
    },
    movement_commands = {
    },
}
map.scripts["dwarvenminer.scr"] = {
    source = "DWARVENMINER.scr",
    registered_triggers = {
        { line = 62, message = "use", callback = "OnRudeEnter" },
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
map.scripts["eboramines.scr"] = {
    source = "EBORAMINES.scr",
    registered_triggers = {
        { line = 98, message = "FreeAtLast", callback = "FreeAtLast" },
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
map.scripts["mine.scr"] = {
    source = "MINE.scr",
    registered_triggers = {
        { line = 45, message = "Use", callback = "Onuse" },
        { line = 46, message = "destroy", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["npc7.scr"] = {
    source = "NPC7.scr",
    registered_triggers = {
        { line = 450, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc8.scr"] = {
    source = "NPC8.scr",
    registered_triggers = {
        { line = 144, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc9.scr"] = {
    source = "NPC9.scr",
    registered_triggers = {
        { line = 126, message = "Use", callback = "OnUse" },
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
map.scripts["slagbase.scr"] = {
    source = "SLAGBASE.scr",
    registered_triggers = {
        { line = 39, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["slagextractor.scr"] = {
    source = "SLAGEXTRACTOR.scr",
    registered_triggers = {
        { line = 107, message = "Use", callback = "OnUse" },
        { line = 108, message = "Show", callback = "OnShow" },
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
map.scripts["spikedoora.scr"] = {
    source = "SPIKEDOORA.scr",
    registered_triggers = {
        { line = 38, message = "OnePulled", callback = "OnePulled" },
    },
    movement_commands = {
    },
}
map.scripts["spikedoorb.scr"] = {
    source = "SPIKEDOORB.scr",
    registered_triggers = {
        { line = 38, message = "OnePulled", callback = "OnePulled" },
    },
    movement_commands = {
    },
}
map.scripts["spikedooropen.scr"] = {
    source = "SPIKEDOOROPEN.scr",
    registered_triggers = {
        { line = 36, message = "OnePulled", callback = "OnePulled" },
    },
    movement_commands = {
    },
}
map.scripts["thjoradquake.scr"] = {
    source = "THJORADQUAKE.scr",
    registered_triggers = {
    },
    movement_commands = {
        { line = 66, command = "SetPOS", arguments = "hMe, xMe, yMe, zMe" },
    },
}
map.scripts["tm_fallingtorch.scr"] = {
    source = "TM_FALLINGTORCH.scr",
    registered_triggers = {
        { line = 45, message = "Hit", callback = "MoveToMarker" },
    },
    movement_commands = {
        { line = 31, command = "Rotate", arguments = "0, 0, 1, -90, 90, DoNothing" },
        { line = 32, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 180, StopHere" },
    },
}
map.scripts["tm_firstfallingflame.scr"] = {
    source = "TM_FIRSTFALLINGFLAME.scr",
    registered_triggers = {
        { line = 66, message = "Fall", callback = "MoveToMarker" },
    },
    movement_commands = {
        { line = 59, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 250, StopHere" },
    },
}
map.scripts["tm_firstfallingtorch.scr"] = {
    source = "TM_FIRSTFALLINGTORCH.scr",
    registered_triggers = {
        { line = 57, message = "KnockedLoose", callback = "ShortDelay" },
    },
    movement_commands = {
        { line = 43, command = "Rotate", arguments = "0, 0, 1, -90, 90, DoNothing" },
        { line = 44, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 180, StopHere" },
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
map.scripts["tm_minecara.scr"] = {
    source = "TM_MINECARA.scr",
    registered_triggers = {
    },
    movement_commands = {
        { line = 54, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 100, StopHere" },
    },
}
map.scripts["tm_steamwater.scr"] = {
    source = "TM_STEAMWATER.scr",
    registered_triggers = {
        { line = 43, message = "MoveWater", callback = "MoveToMarker" },
        { line = 44, message = "ReturnWater", callback = "MoveBack" },
    },
    movement_commands = {
        { line = 31, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 1500, StopHere" },
        { line = 38, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 2000, DoNothing" },
    },
}
map.scripts["tm_torchflame.scr"] = {
    source = "TM_TORCHFLAME.scr",
    registered_triggers = {
        { line = 170, message = "Fall", callback = "MoveToMarker" },
    },
    movement_commands = {
        { line = 163, command = "MoveToPos", arguments = "nVarX, nVarY, nVarZ, 250, StopHere" },
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
