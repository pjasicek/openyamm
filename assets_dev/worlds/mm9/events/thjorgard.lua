-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "thjorgard"
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
map.scripts["bellweight.scr"] = {
    source = "BELLWEIGHT.scr",
    registered_triggers = {
        { line = 16, message = "open", callback = "AdjustHeight" },
    },
    movement_commands = {
    },
}
map.scripts["boatjudge.scr"] = {
    source = "BOATJUDGE.scr",
    registered_triggers = {
        { line = 31, message = "use", callback = "OnUse" },
        { line = 60, message = "CPUArrival", callback = "AIWon" },
        { line = 61, message = "PlayerArrival", callback = "PlayerWon" },
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
map.scripts["npc7.scr"] = {
    source = "NPC7.scr",
    registered_triggers = {
        { line = 450, message = "Use", callback = "OnUse" },
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
map.scripts["racingboat.scr"] = {
    source = "RACINGBOAT.scr",
    registered_triggers = {
        { line = 48, message = "on", callback = "TurnOn" },
        { line = 50, message = "off", callback = "TurnOff" },
        { line = 51, message = "submerge", callback = "Submerge" },
    },
    movement_commands = {
        { line = 101, command = "SetPOS", arguments = "hMe, xMe,yMe,zMe" },
        { line = 120, command = "MoveDir", arguments = "dx,0,dz, nDist, nDist, Ready" },
        { line = 138, command = "MoveDir", arguments = "dx,0,dz, nDist, nSpeed, StartMoveLoop" },
        { line = 169, command = "MoveDir", arguments = "0,-1,0, 64, 64, ReturnToStart" },
        { line = 177, command = "SetPOS", arguments = "hMe, xMe,nTemp,zMe" },
        { line = 185, command = "MoveDir", arguments = "0,1,0, 64, 64, TurnOff" },
    },
}
map.scripts["scholarpromo.scr"] = {
    source = "SCHOLARPROMO.scr",
    registered_triggers = {
        { line = 69, message = "use", callback = "Init" },
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
map.scripts["thorgard_actor.scr"] = {
    source = "THORGARD_ACTOR.scr",
    registered_triggers = {
        { line = 178, message = "RobPlayer", callback = "OnRobPlayer" },
        { line = 336, message = "Attack", callback = "OnMagreebAttack" },
        { line = 399, message = "RunJimRun", callback = "RunJimRun" },
        { line = 438, message = "ComeGetMe", callback = "DeanGetHim" },
        { line = 454, message = "ComeGetMe", callback = "WalterGetHim" },
    },
    movement_commands = {
        { line = 279, command = "SetPos", arguments = "g_hMyObject,startX,startY,startZ" },
    },
}
map.scripts["trainingenter.scr"] = {
    source = "TRAININGENTER.scr",
    registered_triggers = {
        { line = 60, message = "Break", callback = "OnBreak" },
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
