-- generated from MM9 event sidecars; do not edit by hand
local map = {}
map.map_id = "thronheimcity"
map.scripts = {}

map.scripts["ake.scr"] = {
    source = "AKE.scr",
    registered_triggers = {
        { line = 208, message = "blabber", callback = "Onblabber" },
        { line = 209, message = "Use", callback = "OnUse" },
        { line = 210, message = "shutup", callback = "onexit" },
        { line = 227, message = "GoPosition1", callback = "GoPosition1" },
        { line = 228, message = "GoPosition2", callback = "GoPosition2" },
        { line = 229, message = "GoPosition3", callback = "GoPosition3" },
        { line = 230, message = "GoPosition4", callback = "GoPosition4" },
    },
    movement_commands = {
        { line = 134, command = "SetPos", arguments = "g_hMyObject,3328.0,1344.0,-480.0" },
        { line = 142, command = "SetPos", arguments = "g_hMyObject,3557,1254,3331" },
        { line = 151, command = "SetPos", arguments = "g_hMyObject,-720,1246,2166" },
        { line = 160, command = "SetPos", arguments = "g_hMyObject,-2176,1246,4711" },
    },
}
map.scripts["arg_bjarni.scr"] = {
    source = "ARG_BJARNI.scr",
    registered_triggers = {
        { line = 183, message = "Shot1A", callback = "On1A" },
        { line = 190, message = "Speak2", callback = "OnSpeak2" },
        { line = 193, message = "Speak9", callback = "OnSpeak9" },
        { line = 195, message = "Speak16", callback = "OnSpeak16" },
        { line = 198, message = "Shake", callback = "OnShake" },
        { line = 199, message = "Clap", callback = "OnApplause" },
        { line = 201, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_forad.scr"] = {
    source = "ARG_FORAD.scr",
    registered_triggers = {
        { line = 129, message = "Speak6", callback = "OnSpeak6" },
        { line = 131, message = "Speak20", callback = "OnSpeak20" },
        { line = 134, message = "Clap", callback = "OnApplause" },
        { line = 136, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_kira.scr"] = {
    source = "ARG_KIRA.scr",
    registered_triggers = {
        { line = 307, message = "Clap", callback = "OnApplause" },
        { line = 308, message = "Speak5", callback = "OnSpeak5" },
        { line = 310, message = "Speak7", callback = "OnSpeak7" },
        { line = 312, message = "Speak10", callback = "OnSpeak10" },
        { line = 314, message = "Speak12", callback = "OnSpeak12" },
        { line = 316, message = "Speak14", callback = "OnSpeak14" },
        { line = 321, message = "Stand", callback = "OnStand" },
        { line = 323, message = "Speak18", callback = "OnSpeak18" },
        { line = 324, message = "Speak19", callback = "OnSpeak19" },
        { line = 330, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_markel.scr"] = {
    source = "ARG_MARKEL.scr",
    registered_triggers = {
        { line = 237, message = "Scene2", callback = "OnScene2" },
        { line = 239, message = "Speak4", callback = "OnSpeak4" },
        { line = 241, message = "Speak8", callback = "OnSpeak8" },
        { line = 243, message = "Speak11", callback = "OnSpeak11" },
        { line = 245, message = "Speak13", callback = "OnSpeak13" },
        { line = 247, message = "Speak15", callback = "OnSpeak15" },
        { line = 249, message = "Move", callback = "OnMove" },
        { line = 251, message = "Kill", callback = "OnKill" },
        { line = 253, message = "Clap", callback = "OnApplause" },
        { line = 255, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_sigmund.scr"] = {
    source = "ARG_SIGMUND.scr",
    registered_triggers = {
        { line = 135, message = "Shot1A", callback = "OnShot1A" },
        { line = 141, message = "Speak3", callback = "ONSpeak3" },
        { line = 143, message = "Shake", callback = "OnShake" },
        { line = 144, message = "Clap", callback = "OnApplause" },
        { line = 146, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_sven.scr"] = {
    source = "ARG_SVEN.scr",
    registered_triggers = {
        { line = 81, message = "Clap", callback = "OnApplause" },
        { line = 83, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_tryygva.scr"] = {
    source = "ARG_TRYYGVA.scr",
    registered_triggers = {
        { line = 81, message = "Clap", callback = "ONApplause" },
        { line = 83, message = "Agree", callback = "OnAgree" },
    },
    movement_commands = {
    },
}
map.scripts["arg_unhide.scr"] = {
    source = "ARG_UNHIDE.scr",
    registered_triggers = {
    },
    movement_commands = {
    },
}
map.scripts["arg_yrsa.scr"] = {
    source = "ARG_YRSA.scr",
    registered_triggers = {
        { line = 119, message = "Appear", callback = "OnAppear" },
    },
    movement_commands = {
    },
}
map.scripts["arguecam1.scr"] = {
    source = "ARGUECAM1.scr",
    registered_triggers = {
        { line = 55, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 35, command = "MoveToPos", arguments = "xpos Ypos Zpos nSpeed OnArrive" },
    },
}
map.scripts["arguetreaty.scr"] = {
    source = "ARGUETREATY.scr",
    registered_triggers = {
        { line = 48, message = "Play", callback = "OnPlay" },
    },
    movement_commands = {
        { line = 34, command = "MoveToPos", arguments = "xpos Ypos Zpos nSpeed DoNothing" },
    },
}
map.scripts["argument.scr"] = {
    source = "ARGUMENT.scr",
    registered_triggers = {
        { line = 759, message = "Done", callback = "OnDone" },
        { line = 760, message = "ForceStart", callback = "ForceStart" },
        { line = 761, message = "Start", callback = "Init" },
    },
    movement_commands = {
    },
}
map.scripts["bankorb.scr"] = {
    source = "BANKORB.scr",
    registered_triggers = {
        { line = 179, message = "Use", callback = "ONUse" },
    },
    movement_commands = {
    },
}
map.scripts["book.scr"] = {
    source = "BOOK.scr",
    registered_triggers = {
        { line = 50, message = "Use", callback = "OnUse" },
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
map.scripts["dorude.scr"] = {
    source = "DORUDE.scr",
    registered_triggers = {
        { line = 71, message = "Use", callback = "Onuse" },
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
map.scripts["honkies.scr"] = {
    source = "HONKIES.scr",
    registered_triggers = {
        { line = 145, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["kirashield.scr"] = {
    source = "KIRASHIELD.scr",
    registered_triggers = {
        { line = 49, message = "Use", callback = "Onuse" },
    },
    movement_commands = {
    },
}
map.scripts["knutspeech.scr"] = {
    source = "KNUTSPEECH.scr",
    registered_triggers = {
        { line = 172, message = "blabber", callback = "Onblabber" },
        { line = 173, message = "Use", callback = "OnUse" },
        { line = 186, message = "GoPosition1", callback = "GoPosition1" },
        { line = 187, message = "GoPosition2", callback = "GoPosition2" },
        { line = 188, message = "GoPosition3", callback = "GoPosition3" },
        { line = 189, message = "GoPosition4", callback = "GoPosition4" },
    },
    movement_commands = {
        { line = 99, command = "SetPos", arguments = "g_hMyObject,3424.0 1344.0 -672.0" },
        { line = 107, command = "SetPos", arguments = "g_hMyObject,3494,1254,3166" },
        { line = 116, command = "SetPos", arguments = "g_hMyObject,-933,1254,2036" },
        { line = 125, command = "SetPos", arguments = "g_hMyObject,-2324,1254,4559" },
    },
}
map.scripts["npc239.scr"] = {
    source = "NPC239.scr",
    registered_triggers = {
        { line = 239, message = "Use", callback = "OnUse" },
        { line = 240, message = "KillMarkel", callback = "OnKillMarkel" },
    },
    movement_commands = {
    },
}
map.scripts["npc240.scr"] = {
    source = "NPC240.scr",
    registered_triggers = {
        { line = 53, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc241.scr"] = {
    source = "NPC241.scr",
    registered_triggers = {
        { line = 69, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc242.scr"] = {
    source = "NPC242.scr",
    registered_triggers = {
        { line = 95, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc246.scr"] = {
    source = "NPC246.scr",
    registered_triggers = {
        { line = 78, message = "Use", callback = "OnUse" },
    },
    movement_commands = {
    },
}
map.scripts["npc378.scr"] = {
    source = "NPC378.scr",
    registered_triggers = {
        { line = 281, message = "Use", callback = "OnUse" },
        { line = 282, message = "Appear", callback = "OnAppear" },
        { line = 283, message = "Appear2", callback = "OnAppear2" },
    },
    movement_commands = {
        { line = 108, command = "setpos", arguments = "g_hobject -2806 1240 5040" },
        { line = 144, command = "setpos", arguments = "g_hmyobject MyX MyY MyZ" },
        { line = 165, command = "setpos", arguments = "g_hmyobject XPos YPos ZPos" },
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
map.scripts["retainer.scr"] = {
    source = "RETAINER.scr",
    registered_triggers = {
        { line = 74, message = "Use", callback = "OnUse" },
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
map.scripts["thronheimcity_actor.scr"] = {
    source = "THRONHEIMCITY_ACTOR.scr",
    registered_triggers = {
        { line = 64, message = "HereComesBadAss", callback = "OnHereComesBadAssShmoe" },
        { line = 153, message = "RunAwayFromMe", callback = "RunAwayFromBadAss" },
        { line = 154, message = "HereComesBadAss", callback = "OnHereComesBadAssBen" },
    },
    movement_commands = {
    },
}
map.scripts["thronheimcity_badass.scr"] = {
    source = "THRONHEIMCITY_BADASS.scr",
    registered_triggers = {
        { line = 304, message = "BreakOut", callback = "OnBreakOut" },
        { line = 305, message = "test", callback = "OnTest" },
    },
    movement_commands = {
    },
}
map.scripts["thronheimcity_guard.scr"] = {
    source = "THRONHEIMCITY_GUARD.scr",
    registered_triggers = {
        { line = 78, message = "ComeGetMe", callback = "GetBadAss" },
        { line = 79, message = "OpenEyes", callback = "OpenEyes" },
    },
    movement_commands = {
    },
}
map.scripts["townportal.scr"] = {
    source = "TOWNPORTAL.scr",
    registered_triggers = {
        { line = 103, message = "Use", callback = "OnUse" },
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
