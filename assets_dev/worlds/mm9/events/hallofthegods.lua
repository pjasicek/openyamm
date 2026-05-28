-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "hallofthegods"
map.scripts = {}

map.scripts["bookletter.scr"] = {
    source = "BOOKLETTER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc335.scr"] = {
    source = "NPC335.scr",
    registered_triggers = {
        { line = 106, message = "Start", callback = "OnStart" },
        { line = 107, message = "Stop", callback = "Loop" },
    },
    movement_commands = {
    },
}
map.scripts["npc336.scr"] = {
    source = "NPC336.scr",
    registered_triggers = {
        { line = 321, message = "use", callback = "OnUse" },
        { line = 326, message = "Reborn", callback = "OnReborn" },
        { line = 327, message = "Done", callback = "OnDone" },
    },
    movement_commands = {
    },
}
map.scripts["npc337.scr"] = {
    source = "NPC337.scr",
    registered_triggers = {
        { line = 72, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc377.scr"] = {
    source = "NPC377.scr",
    registered_triggers = {
        { line = 31, message = "Use", callback = "OnUse" },
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
map.scripts["wg_npc334.scr"] = {
    source = "WG_NPC334.scr",
    registered_triggers = {
        { line = 267, message = "Start", callback = "OnStart" },
        { line = 268, message = "Stop", callback = "Loop" },
        { line = 269, message = "Action", callback = "OnAction" },
        { line = 270, message = "Hanndl1", callback = "OnHanndl1" },
        { line = 271, message = "Hanndl2", callback = "OnHanndl2" },
        { line = 272, message = "Hanndl3", callback = "OnHanndl3" },
        { line = 273, message = "Hanndl4", callback = "OnHanndl4" },
        { line = 274, message = "Hanndl5", callback = "OnHanndl5" },
        { line = 275, message = "Hanndl6", callback = "OnHanndl6" },
    },
    movement_commands = {
    },
}
map.scripts["wg_npc335.scr"] = {
    source = "WG_NPC335.scr",
    registered_triggers = {
        { line = 272, message = "Arrive", callback = "OnArrive" },
        { line = 273, message = "Start", callback = "OnStart" },
        { line = 274, message = "Stop", callback = "Loop" },
        { line = 275, message = "krohn1", callback = "OnKrohn1" },
        { line = 276, message = "Krohn2", callback = "OnKrohn2" },
        { line = 277, message = "krohn3", callback = "OnKrohn3" },
        { line = 278, message = "Krohn4", callback = "OnKrohn4" },
        { line = 279, message = "krohn5", callback = "OnKrohn5" },
        { line = 280, message = "Krohn6", callback = "OnKrohn6" },
        { line = 281, message = "krohn7", callback = "OnKrohn7" },
    },
    movement_commands = {
    },
}
map.scripts["wg_npc336.scr"] = {
    source = "WG_NPC336.scr",
    registered_triggers = {
        { line = 53, message = "Start", callback = "OnStart" },
        { line = 55, message = "Stop", callback = "Loop" },
    },
    movement_commands = {
    },
}
map.scripts["wg_scene7cam1.scr"] = {
    source = "WG_SCENE7CAM1.scr",
    registered_triggers = {
        { line = 70, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 50, command = "MoveToPos", arguments = "xpos Ypos Zpos 150 OnArrive" },
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
