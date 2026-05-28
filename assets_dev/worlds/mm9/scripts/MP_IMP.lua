-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MP_IMP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "basemelee.scr" }

-- MP_Imp.scr
-- By Timmy
-- Imp walks to target until it finds player.
-- then it runs to its friends before attacking
-- 11/1/01
script.labels["OnStart"] = function(ctx)
    -- MP_IMP.scr:15
    -- start the walking
    ctx:command("onfoundtarget", "TargetFound") -- MP_IMP.scr:19
    ctx:command("getobjecthandle", "ImpMarker1 g_hobject") -- MP_IMP.scr:20
    ctx:command("walkto", "g_hobject 8 DoNothing") -- MP_IMP.scr:21
    do return ctx:exit("") end -- MP_IMP.scr:22
end

script.labels["TargetFound"] = function(ctx)
    -- MP_IMP.scr:25
    -- play wince anim and run for friends
    ctx:getParam(0, "g_hTarget") -- MP_IMP.scr:30
    ctx:command("playanim", "wince1 DoNothing") -- MP_IMP.scr:31
    ctx:command("getobjecthandle", "ImpMarker2 g_hobject") -- MP_IMP.scr:32
    ctx:command("runto", "g_hobject 32 StartAttack") -- MP_IMP.scr:33
    do return ctx:exit("") end -- MP_IMP.scr:34
end

script.labels["StartAttack"] = function(ctx)
    -- MP_IMP.scr:37
    -- shout for help and start attacking
    ctx:command("help", "g_htarget") -- MP_IMP.scr:41
    mm9.gosub(script, ctx, "BaseInit") -- MP_IMP.scr:42
    do return ctx:exit("") end -- MP_IMP.scr:43
end

script.labels["Main"] = function(ctx)
    -- MP_IMP.scr:46
    -- TraceOn ;delete me!!
    ctx:command("wait", "1 1 OnStart") -- MP_IMP.scr:52
    do return ctx:exit("") end -- MP_IMP.scr:54
end

return script
