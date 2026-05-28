-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THETHINGERIZER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }

-- TheThing.scr (john carpenter's)
-- by SJR
-- 11-04-01
-- Purpose:turn into a weirdo lookin
-- rastafied evil terror eye
-- thing with big pointy teeth
script.labels["Main"] = function(ctx)
    -- THETHINGERIZER.scr:23
    mm9.gosub(script, ctx, "InitStrings") -- THETHINGERIZER.scr:25
    ctx:command("wait", "0, 3, InitTheThingerizer") -- THETHINGERIZER.scr:27
    do return ctx:exit("TRUE") end -- THETHINGERIZER.scr:29
end

script.labels["InitTheThingerizer"] = function(ctx)
    -- THETHINGERIZER.scr:32
    ctx:command("setmodelfilenames", "models\\socketskeleton.abc, skins\\skeleton1.dtx") -- THETHINGERIZER.scr:34
    ctx:command("ncounter", "= 0") -- THETHINGERIZER.scr:36
    ctx:addTrigger("Mutate", "AttachThing") -- THETHINGERIZER.scr:37
    ctx:command("getplayerhandle", "g_hPlayer") -- THETHINGERIZER.scr:39
    mm9.gosub(script, ctx, "BaseInit") -- THETHINGERIZER.scr:40
    do return ctx:exit("TRUE") end -- THETHINGERIZER.scr:42
end

script.labels["AttachThing"] = function(ctx)
    -- THETHINGERIZER.scr:45
    mm9.gosub(script, ctx, "SetupTarget") -- THETHINGERIZER.scr:47
    mm9.gosub(script, ctx, "AggressiveStart") -- THETHINGERIZER.scr:48
    ctx:command("playsound", "\"sounds\\animsounds\\pig\\wince01.wav\", DoNothing, 1, 500, FALSE, 100") -- THETHINGERIZER.scr:50
    ctx:command("arrayget", "spSockets,\t\tnCounter, sSocket") -- THETHINGERIZER.scr:52
    ctx:command("arrayget", "spAnimations,\tnCounter, sAnimation") -- THETHINGERIZER.scr:53
    ctx:command("attachprop", "sAttachment, sSkin, sSocket, hAttachment") -- THETHINGERIZER.scr:55
    ctx:trigger("hAttachment", "sAnimation") -- THETHINGERIZER.scr:56
    if ctx:condition("nCounter>=7") then -- THETHINGERIZER.scr:58
        ctx:command("runscript", "baseMelee.scr") -- THETHINGERIZER.scr:59
    else -- THETHINGERIZER.scr:60
        ctx:command("ncounter", "= nCounter + 1") -- THETHINGERIZER.scr:61
    end -- THETHINGERIZER.scr:62
    do return ctx:exit("TRUE") end -- THETHINGERIZER.scr:64
end

script.labels["InitStrings"] = function(ctx)
    -- THETHINGERIZER.scr:68
    ctx:command("arrayput", "spAnimations, 0, \"hattack1\"") -- THETHINGERIZER.scr:70
    ctx:command("arrayput", "spAnimations, 1, \"rattack1\"") -- THETHINGERIZER.scr:71
    ctx:command("arrayput", "spAnimations, 2, \"wince1\"") -- THETHINGERIZER.scr:72
    ctx:command("arrayput", "spAnimations, 3, \"wince2\"") -- THETHINGERIZER.scr:73
    ctx:command("arrayput", "spAnimations, 4, \"land\"") -- THETHINGERIZER.scr:74
    ctx:command("arrayput", "spAnimations, 5, \"hattack1\"") -- THETHINGERIZER.scr:75
    ctx:command("arrayput", "spAnimations, 6, \"walk\"") -- THETHINGERIZER.scr:76
    ctx:command("arrayput", "spAnimations, 7, \"fidget\"") -- THETHINGERIZER.scr:77
    ctx:command("ncounter", "= 7") -- THETHINGERIZER.scr:79
    while ctx:condition("nCounter>=0") do -- THETHINGERIZER.scr:80
        ctx:command("arrayget", "spAnimations, nCounter, sAnimation") -- THETHINGERIZER.scr:81
        ctx:command("sanimation", "= ANIMCOMMAND + sAnimation") -- THETHINGERIZER.scr:82
        ctx:command("arrayput", "spAnimations, nCounter, sAnimation") -- THETHINGERIZER.scr:83
        ctx:command("ncounter", "= nCounter - 1") -- THETHINGERIZER.scr:84
    end -- THETHINGERIZER.scr:85
    ctx:command("sattachment", "= \"..\\lobberpod.abc\"") -- THETHINGERIZER.scr:87
    ctx:command("sskin", "= \"..\\skeleton1.dtx\"") -- THETHINGERIZER.scr:88
    ctx:command("arrayput", "spSockets, 0, Head1") -- THETHINGERIZER.scr:90
    ctx:command("arrayput", "spSockets, 1, SpineMiddle") -- THETHINGERIZER.scr:91
    ctx:command("arrayput", "spSockets, 2, ThighR") -- THETHINGERIZER.scr:92
    ctx:command("arrayput", "spSockets, 3, ThighL") -- THETHINGERIZER.scr:93
    ctx:command("arrayput", "spSockets, 4, CalfR") -- THETHINGERIZER.scr:94
    ctx:command("arrayput", "spSockets, 5, CalfL") -- THETHINGERIZER.scr:95
    ctx:command("arrayput", "spSockets, 6, RHand1") -- THETHINGERIZER.scr:96
    ctx:command("arrayput", "spSockets, 7, LHand1") -- THETHINGERIZER.scr:97
    do return ctx:exit("TRUE") end -- THETHINGERIZER.scr:99
end

return script
