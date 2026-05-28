-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "guberland"
map.scripts = {}

map.scripts["armwrestle.scr"] = {
    source = "ARMWRESTLE.scr",
    registered_triggers = {
        { line = 19, message = "use", callback = "OnUse" },
        { line = 97, message = "use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["atlipromo.scr"] = {
    source = "ATLIPROMO.scr",
    registered_triggers = {
        { line = 81, message = "Return", callback = "OnReturn" },
    },
    movement_commands = {
    },
}
map.scripts["atliwagon.scr"] = {
    source = "ATLIWAGON.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["bellweight.scr"] = {
    source = "BELLWEIGHT.scr",
    registered_triggers = {
        { line = 16, message = "open", callback = "AdjustHeight" },
    },
    movement_commands = {
    },
}
map.scripts["dingthebell.scr"] = {
    source = "DINGTHEBELL.scr",
    registered_triggers = {
        { line = 17, message = "use", callback = "HitBell" },
        { line = 18, message = "ring", callback = "CheckWin" },
        { line = 35, message = "use", callback = "BlockUse" },
        { line = 70, message = "use", callback = "HitBell" },
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
map.scripts["givetake.scr"] = {
    source = "GIVETAKE.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["huckstermod.scr"] = {
    source = "HUCKSTERMOD.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["mastermind.scr"] = {
    source = "MASTERMIND.scr",
    registered_triggers = {
        { line = 65, message = "check", callback = "CompareColors" },
        { line = 66, message = "reset", callback = "GenerateColors" },
        { line = 67, message = "update", callback = "ColorChosen" },
        { line = 172, message = "check", callback = "CompareColors" },
    },
    movement_commands = {
    },
}
map.scripts["mastermindcolor.scr"] = {
    source = "MASTERMINDCOLOR.scr",
    registered_triggers = {
        { line = 20, message = "use", callback = "ChangeColor" },
    },
    movement_commands = {
    },
}
map.scripts["mastermindspace.scr"] = {
    source = "MASTERMINDSPACE.scr",
    registered_triggers = {
        { line = 36, message = "use", callback = "UpdateColor" },
    },
    movement_commands = {
    },
}
map.scripts["npc130.scr"] = {
    source = "NPC130.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["npc132.scr"] = {
    source = "NPC132.scr",
    registered_triggers = {
        { line = 89, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc133.scr"] = {
    source = "NPC133.scr",
    registered_triggers = {
        { line = 163, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc150.scr"] = {
    source = "NPC150.scr",
    registered_triggers = {
        { line = 188, message = "Start", callback = "OnStart" },
        { line = 189, message = "Speak3", callback = "OnSpeak3" },
        { line = 190, message = "Speak5", callback = "OnSpeak5" },
        { line = 191, message = "Speak7", callback = "OnSpeak7" },
        { line = 192, message = "Speak9", callback = "OnSpeak9" },
        { line = 193, message = "Speak11", callback = "OnSpeak11" },
    },
    movement_commands = {
    },
}
map.scripts["npc151.scr"] = {
    source = "NPC151.scr",
    registered_triggers = {
        { line = 160, message = "Speak2", callback = "OnSpeak2" },
        { line = 161, message = "Speak4", callback = "OnSpeak4" },
        { line = 162, message = "Speak6", callback = "OnSpeak6" },
        { line = 163, message = "Speak8", callback = "OnSpeak8" },
        { line = 164, message = "Speak10", callback = "OnSpeak10" },
        { line = 165, message = "Speak12", callback = "OnWalkAway" },
        { line = 166, message = "Target", callback = "OnTarget" },
    },
    movement_commands = {
    },
}
map.scripts["npc186.scr"] = {
    source = "NPC186.scr",
    registered_triggers = {
        { line = 191, message = "Summon", callback = "OnSummon" },
        { line = 192, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc187.scr"] = {
    source = "NPC187.scr",
    registered_triggers = {
        { line = 97, message = "Use", callback = "OnUse" },
        { line = 98, message = "Return", callback = "OnReturn" },
    },
    movement_commands = {
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
map.scripts["npcshopkeeper.scr"] = {
    source = "NPCSHOPKEEPER.scr",
    registered_triggers = {
        { line = 47, message = "Use", callback = "OnUse" },
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
map.scripts["proptrigger.scr"] = {
    source = "PROPTRIGGER.scr",
    registered_triggers = {
        { line = 64, message = "Use", callback = "OnUse" },
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
map.scripts["stonesgame.scr"] = {
    source = "STONESGAME.scr",
    registered_triggers = {
        { line = 54, message = "move", callback = "CheckMove" },
        { line = 110, message = "move", callback = "CheckMove" },
    },
    movement_commands = {
    },
}
map.scripts["stonespiece.scr"] = {
    source = "STONESPIECE.scr",
    registered_triggers = {
        { line = 11, message = "white", callback = "TurnWhite" },
        { line = 12, message = "black", callback = "TurnBlack" },
    },
    movement_commands = {
    },
}
map.scripts["stonesplayer.scr"] = {
    source = "STONESPLAYER.scr",
    registered_triggers = {
        { line = 28, message = "play", callback = "PlacePiece" },
        { line = 30, message = "use", callback = "OnRudeEnter" },
    },
    movement_commands = {
    },
}
map.scripts["stonessquare.scr"] = {
    source = "STONESSQUARE.scr",
    registered_triggers = {
        { line = 37, message = "use", callback = "RequestMove" },
        { line = 38, message = "white", callback = "TurnPieceWhite" },
        { line = 39, message = "black", callback = "TurnPieceBlack" },
        { line = 40, message = "clear", callback = "TurnPieceClear" },
    },
    movement_commands = {
    },
}
map.scripts["thjorgardspectator.scr"] = {
    source = "THJORGARDSPECTATOR.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["whack-a-honky.scr"] = {
    source = "WHACK-A-HONKY.scr",
    registered_triggers = {
        { line = 34, message = "start", callback = "StartGame" },
        { line = 35, message = "popup", callback = "ReceivePopup" },
        { line = 36, message = "reset", callback = "ResetPOS" },
        { line = 104, message = "use", callback = "OnDamage" },
        { line = 182, message = "start", callback = "StartGame" },
    },
    movement_commands = {
        { line = 108, command = "MoveDir", arguments = "0,1,0, 20, 100, OnFinishedRaise" },
        { line = 142, command = "MoveToPOS", arguments = "xMe,yMe,zMe, 100, OnFinishedLower" },
        { line = 189, command = "SetPOS", arguments = "hMe, xMe,yMe,zMe" },
    },
}

function map.register(ctx)
    if ctx == nil or ctx.registerMm9MapEvents == nil then
        return
    end
    ctx:registerMm9MapEvents(map)
end

return map
