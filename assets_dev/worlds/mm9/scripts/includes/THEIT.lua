-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THEIT.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "baseMelee.inc" }

-- TheIt.scr (stephen king's)
-- by SJR
-- 11-04-01
-- Purpose:turn into a weirdo lookin
-- spiky skeleton mutant
-- thing with big pointy teeth
script.labels["InitTheIt"] = function(ctx)
    -- THEIT.inc:23
    ctx:command("sattachment", "= \"..\\lobberpod.abc\"") -- THEIT.inc:25
    ctx:command("sskin", "= \"..\\skeleton1.dtx\"") -- THEIT.inc:26
    mm9.gosub(script, ctx, "InitStrings") -- THEIT.inc:28
    mm9.gosub(script, ctx, "BaseInit") -- THEIT.inc:29
    ctx:command("setmodelfilenames", "models\\skeleton.abc, skins\\skeleton1.dtx") -- THEIT.inc:31
    ctx:command("setidle", "") -- THEIT.inc:33
    ctx:command("getplayerhandle", "g_hTarget") -- THEIT.inc:35
    ctx:addTrigger("Mutate", "AttachThing") -- THEIT.inc:37
    ctx:command("ncounter", "= 0") -- THEIT.inc:38
    mm9.gosub(script, ctx, "BaseWanderStartup") -- THEIT.inc:40
    do return ctx:exit("TRUE") end -- THEIT.inc:42
end

script.labels["AttachThing"] = function(ctx)
    -- THEIT.inc:45
    ctx:command("playsound", "\"sounds\\animsounds\\pig\\wince1.wav\", DoNothing, 1, 500, FALSE, 100") -- THEIT.inc:47
    ctx:command("arrayget", "spSockets,\t\tnCounter, sSocket") -- THEIT.inc:49
    ctx:command("arrayget", "spAnimations,\tnCounter, sAnimation") -- THEIT.inc:50
    ctx:command("attachprop", "sAttachment, sSkin, sSocket, hAttachment") -- THEIT.inc:52
    ctx:trigger("hAttachment", "sAnimation") -- THEIT.inc:53
    if ctx:condition("nCounter>=7") then -- THEIT.inc:55
        mm9.gosub(script, ctx, "SetupTarget") -- THEIT.inc:56
        mm9.gosub(script, ctx, "AggressiveStart") -- THEIT.inc:57
        ctx:command("playsound", "\"sounds\\animsounds\\pig\\wince1.wav\", DoNothing, 1, 500, FALSE, 100") -- THEIT.inc:58
    end -- THEIT.inc:59
    ctx:command("ncounter", "= nCounter + 1") -- THEIT.inc:61
    mm9.gosub(script, ctx, "AttachThing") -- THEIT.inc:63
    do return ctx:exit("TRUE") end -- THEIT.inc:65
end

script.labels["InitStrings"] = function(ctx)
    -- THEIT.inc:69
    ctx:command("arrayput", "spAnimations, 0, \"hattack1\"") -- THEIT.inc:71
    ctx:command("arrayput", "spAnimations, 1, \"rattack1\"") -- THEIT.inc:72
    ctx:command("arrayput", "spAnimations, 2, \"wince1\"") -- THEIT.inc:73
    ctx:command("arrayput", "spAnimations, 3, \"wince2\"") -- THEIT.inc:74
    ctx:command("arrayput", "spAnimations, 4, \"land\"") -- THEIT.inc:75
    ctx:command("arrayput", "spAnimations, 5, \"hattack1\"") -- THEIT.inc:76
    ctx:command("arrayput", "spAnimations, 6, \"walk\"") -- THEIT.inc:77
    ctx:command("arrayput", "spAnimations, 7, \"fidget\"") -- THEIT.inc:78
    ctx:command("arrayput", "spSockets, 0, \"Head1\"") -- THEIT.inc:81
    ctx:command("arrayput", "spSockets, 1, \"SpineMiddle\"") -- THEIT.inc:82
    ctx:command("arrayput", "spSockets, 2, \"ThighR\"") -- THEIT.inc:83
    ctx:command("arrayput", "spSockets, 3, \"ThighL\"") -- THEIT.inc:84
    ctx:command("arrayput", "spSockets, 4, \"CalfR\"") -- THEIT.inc:85
    ctx:command("arrayput", "spSockets, 5, \"CalfL\"") -- THEIT.inc:86
    ctx:command("arrayput", "spSockets, 6, \"RHand1\"") -- THEIT.inc:87
    ctx:command("arrayput", "spSockets, 7, \"LHand1\"") -- THEIT.inc:88
    ctx:command("ncounter", "= 7") -- THEIT.inc:90
    while ctx:condition("nCounter>=0") do -- THEIT.inc:91
        ctx:command("arrayget", "spAnimations, nCounter, sAnimation") -- THEIT.inc:92
        ctx:command("sanimation", "= ANIMCOMMAND + sAnimation") -- THEIT.inc:93
        ctx:command("arrayput", "spAnimations, nCounter, sAnimation") -- THEIT.inc:94
        ctx:command("ncounter", "= nCounter - 1") -- THEIT.inc:95
    end -- THEIT.inc:96
    do return ctx:exit("TRUE") end -- THEIT.inc:98
end

return script
