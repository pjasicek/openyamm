-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DPGUARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "baseMelee.inc" }

-- NPC419.scr
-- timmy
-- handles Aymril Banito voice and quest stuff
script.labels["OnHelp"] = function(ctx)
    -- DPGUARD.scr:12
    -- traceon
    ctx:command("getobjecthandle", "CommonerHumanMaleB0 g_hobject") -- DPGUARD.scr:17
    ctx:command("runto", "g_hobject 16 DoNothing") -- DPGUARD.scr:18
    ctx:getParam(0, "g_htarget") -- DPGUARD.scr:19
    -- help g_htarget
    ctx:command("removeenemy", "Commoner") -- DPGUARD.scr:21
    ctx:command("traceoff", "") -- DPGUARD.scr:22
    do return ctx:exit("") end -- DPGUARD.scr:23
end

script.labels["OnExit"] = function(ctx)
    -- DPGUARD.scr:28
    do return ctx:exit("") end -- DPGUARD.scr:31
end

script.labels["Main"] = function(ctx)
    -- DPGUARD.scr:34
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Help", "OnHelp") -- DPGUARD.scr:39
    mm9.gosub(script, ctx, "BaseInit") -- DPGUARD.scr:41
    do return ctx:exit("") end -- DPGUARD.scr:43
end

return script
