-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "1000terrors"
map.scripts = {}

map.scripts["1000t_circleshooter.scr"] = {
    source = "1000T_CIRCLESHOOTER.scr",
    registered_triggers = {
        { line = 54, message = "go", callback = "StartShooting" },
    },
    movement_commands = {
        { line = 90, command = "MoveToPos", arguments = "xMe,yMe,zMe, 500, UpdatePOS" },
    },
}
map.scripts["1000t_flyingcreature_.scr"] = {
    source = "1000T_FLYINGCREATURE_.scr",
    registered_triggers = {
        { line = 39, message = "go", callback = "TraverseBegin" },
    },
    movement_commands = {
    },
}
map.scripts["1000t_lightningshooter.scr"] = {
    source = "1000T_LIGHTNINGSHOOTER.scr",
    registered_triggers = {
        { line = 39, message = "Go", callback = "StartShooting" },
        { line = 40, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["1000t_skeletonhead.scr"] = {
    source = "1000T_SKELETONHEAD.scr",
    registered_triggers = {
        { line = 52, message = "Go", callback = "Start" },
        { line = 53, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
        { line = 34, command = "Rotate", arguments = "0, 1, 0, 180, 180, TurnOff" },
    },
}
map.scripts["1000t_skheadshooter.scr"] = {
    source = "1000T_SKHEADSHOOTER.scr",
    registered_triggers = {
        { line = 52, message = "Go", callback = "StartShooting" },
    },
    movement_commands = {
    },
}
map.scripts["1000t_sorcstatues.scr"] = {
    source = "1000T_SORCSTATUES.scr",
    registered_triggers = {
        { line = 65, message = "Go", callback = "Start" },
        { line = 66, message = "Stop", callback = "TurnOff" },
    },
    movement_commands = {
    },
}
map.scripts["bootgive.scr"] = {
    source = "BOOTGIVE.scr",
    registered_triggers = {
        { line = 70, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["buttonpad.scr"] = {
    source = "BUTTONPAD.scr",
    registered_triggers = {
        { line = 548, message = "Button0", callback = "Button0" },
        { line = 549, message = "Button1", callback = "Button1" },
        { line = 550, message = "Button2", callback = "Button2" },
        { line = 551, message = "Button3", callback = "Button3" },
        { line = 552, message = "Button4", callback = "Button4" },
        { line = 553, message = "Button5", callback = "Button5" },
        { line = 554, message = "Button6", callback = "Button6" },
        { line = 555, message = "Button7", callback = "Button7" },
        { line = 556, message = "Button8", callback = "Button8" },
        { line = 557, message = "Button9", callback = "Button9" },
        { line = 558, message = "Button10", callback = "Button10" },
        { line = 559, message = "Button11", callback = "Button11" },
        { line = 560, message = "Button12", callback = "Button12" },
        { line = 561, message = "Button13", callback = "Button13" },
        { line = 562, message = "Button14", callback = "Button14" },
        { line = 563, message = "Button15", callback = "Button15" },
        { line = 564, message = "Reset", callback = "Reset" },
        { line = 565, message = "SetTrap", callback = "SetTrap" },
    },
    movement_commands = {
    },
}
map.scripts["buttonpuzzle.scr"] = {
    source = "BUTTONPUZZLE.scr",
    registered_triggers = {
        { line = 92, message = "Use", callback = "UseMe" },
        { line = 152, message = "TriggerMe", callback = "TriggerMe" },
        { line = 153, message = "MoveDoor", callback = "MoveDoor" },
        { line = 154, message = "TriggerTrap", callback = "TriggerTrap" },
        { line = 155, message = "UseStart", callback = "UseStart" },
    },
    movement_commands = {
        { line = 57, command = "MoveDir", arguments = "0, nMoveDir2, 0, nMoveDistA, 300, DoNothing" },
        { line = 117, command = "MoveDir", arguments = "0, nMoveDir, 0, nMoveDistB, nMoveSpeed, EndScript" },
        { line = 134, command = "MoveDir", arguments = "0, nMoveDir, 0, nMoveDistA, 0, DoNothing" },
    },
}
map.scripts["chessbishop.scr"] = {
    source = "CHESSBISHOP.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["chesscamera.scr"] = {
    source = "CHESSCAMERA.scr",
    registered_triggers = {
        { line = 23, message = "Look", callback = "ViewChessPiece" },
        { line = 24, message = "TurnOff", callback = "CameraOff" },
    },
    movement_commands = {
        { line = 45, command = "SetPos", arguments = "hPlayer,x,y,z" },
        { line = 74, command = "SetPOS", arguments = "hMe, x,y,z" },
    },
}
map.scripts["chessknight.scr"] = {
    source = "CHESSKNIGHT.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["chesspawn.scr"] = {
    source = "CHESSPAWN.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["chesssquare.scr"] = {
    source = "CHESSSQUARE.scr",
    registered_triggers = {
        { line = 33, message = "off", callback = "TurnOff" },
        { line = 34, message = "on", callback = "TurnOn" },
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
map.scripts["endcount.scr"] = {
    source = "ENDCOUNT.scr",
    registered_triggers = {
        { line = 64, message = "Spawned", callback = "OnSpawn" },
        { line = 65, message = "ForceSpawn", callback = "SpawnDemon" },
    },
    movement_commands = {
    },
}
map.scripts["endcounttrigger.scr"] = {
    source = "ENDCOUNTTRIGGER.scr",
    registered_triggers = {
        { line = 33, message = "default", callback = "OnSpawn" },
        { line = 34, message = "Count", callback = "OnSpawn" },
    },
    movement_commands = {
    },
}
map.scripts["flyrange.scr"] = {
    source = "FLYRANGE.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["giverandom.scr"] = {
    source = "GIVERANDOM.scr",
    registered_triggers = {
        { line = 52, message = "use", callback = "ProduceRandomEffect" },
    },
    movement_commands = {
    },
}
map.scripts["njamfreeze.scr"] = {
    source = "NJAMFREEZE.scr",
    registered_triggers = {
        { line = 229, message = "Chase", callback = "OnChase" },
        { line = 230, message = "Panic", callback = "OnPanic" },
        { line = 237, message = "Freeze", callback = "OnFreezeskin" },
    },
    movement_commands = {
    },
}
map.scripts["njamtaunt.scr"] = {
    source = "NJAMTAUNT.scr",
    registered_triggers = {
        { line = 111, message = "Start", callback = "OnStart" },
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
map.scripts["spawngeneric.scr"] = {
    source = "SPAWNGENERIC.scr",
    registered_triggers = {
        { line = 77, message = "Spawn", callback = "Onspawn" },
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
map.scripts["spawnnjam.scr"] = {
    source = "SPAWNNJAM.scr",
    registered_triggers = {
        { line = 180, message = "Spawn", callback = "Onspawn" },
        { line = 181, message = "KillNjam", callback = "Vanish2c" },
    },
    movement_commands = {
    },
}
map.scripts["tauntman.scr"] = {
    source = "TAUNTMAN.scr",
    registered_triggers = {
        { line = 112, message = "Start", callback = "OnStart" },
        { line = 113, message = "Arrive", callback = "OnCloseUp" },
        { line = 114, message = "VanishStart", callback = "OnFarCam" },
        { line = 115, message = "VanishDone", callback = "OnFadeOut" },
    },
    movement_commands = {
    },
}
map.scripts["wg_hand.scr"] = {
    source = "WG_HAND.scr",
    registered_triggers = {
        { line = 60, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
    },
}
map.scripts["wg_njamcam.scr"] = {
    source = "WG_NJAMCAM.scr",
    registered_triggers = {
        { line = 91, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 40, command = "MoveToPos", arguments = "xpos Ypos Zpos 100 OnArrive1" },
        { line = 52, command = "MoveToPos", arguments = "xpos Ypos Zpos 130 OnArrive2" },
    },
}
map.scripts["wg_shot2cam.scr"] = {
    source = "WG_SHOT2CAM.scr",
    registered_triggers = {
        { line = 48, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
    },
}
map.scripts["wg_shot5cam.scr"] = {
    source = "WG_SHOT5CAM.scr",
    registered_triggers = {
        { line = 70, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 45, command = "MoveToPos", arguments = "xpos Ypos Zpos 100 OnPanUp" },
    },
}
map.scripts["wg_shot7cam.scr"] = {
    source = "WG_SHOT7CAM.scr",
    registered_triggers = {
        { line = 99, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 53, command = "MoveToPos", arguments = "xpos Ypos Zpos 75 OnArrive1" },
        { line = 63, command = "MoveToPos", arguments = "xpos Ypos Zpos 75 OnArrive2" },
        { line = 72, command = "MoveToPos", arguments = "xpos Ypos Zpos 75 OnArrive3" },
        { line = 81, command = "MoveToPos", arguments = "xpos Ypos Zpos 75 CutTo" },
    },
}
map.scripts["winman.scr"] = {
    source = "WINMAN.scr",
    registered_triggers = {
        { line = 611, message = "Use", callback = "OnUse" },
        { line = 612, message = "NjamCamDone", callback = "OnNjamCamDone" },
        { line = 613, message = "HandDone", callback = "ONHandDone" },
        { line = 614, message = "BallStart", callback = "OnBallStart" },
        { line = 615, message = "CameraSwitch", callback = "OnCameraSwitch" },
        { line = 616, message = "CameraSwitch2", callback = "OnCameraSwitch2" },
        { line = 617, message = "Frozen", callback = "OnFrozen" },
        { line = 618, message = "Panup", callback = "OnPanUp" },
        { line = 619, message = "CutTo", callback = "OnCutTo" },
        { line = 620, message = "Krohn", callback = "OnKrohn" },
        { line = 622, message = "CutToKrohn", callback = "OnKrohnCut" },
        { line = 624, message = "krohn1", callback = "OnKrohn1" },
        { line = 625, message = "Krohn2", callback = "OnKrohn2" },
        { line = 626, message = "krohn3", callback = "OnKrohn3" },
        { line = 627, message = "Krohn4", callback = "OnKrohn4" },
        { line = 628, message = "krohn5", callback = "OnKrohn5" },
        { line = 629, message = "Krohn6", callback = "OnKrohn6" },
        { line = 630, message = "krohn7", callback = "OnKrohn7" },
        { line = 631, message = "krohnClose", callback = "OnKrohnClose" },
        { line = 632, message = "Ever", callback = "OnEver" },
        { line = 636, message = "Hanndl1", callback = "OnHanndl1" },
        { line = 637, message = "Hanndl2", callback = "OnHanndl2" },
        { line = 638, message = "Hanndl3", callback = "OnHanndl3" },
        { line = 639, message = "Hanndl4", callback = "OnHanndl4" },
        { line = 640, message = "Hanndl5", callback = "OnHanndl5" },
        { line = 641, message = "Hanndl6", callback = "OnHanndl6" },
        { line = 642, message = "HanndlClose", callback = "OnHanndlClose" },
        { line = 644, message = "switch", callback = "onSwitch" },
        { line = 646, message = "End", callback = "End" },
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
