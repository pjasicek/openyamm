-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDWALK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- GuardWalk.scr
-- timmy
-- 9/19
-- make a guard walk back and forth.!
script.labels["OnUse"] = function(ctx)
    -- GUARDWALK.scr:14
    if ctx:condition("counter==0") then -- GUARDWALK.scr:20
        ctx:command("set", "L_marker g_marker1") -- GUARDWALK.scr:21
        ctx:command("set", "counter 1") -- GUARDWALK.scr:22
        do return mm9.gotoLabel(script, ctx, "WalkStart") end -- GUARDWALK.scr:23
        do return ctx:exit("") end -- GUARDWALK.scr:24
    end -- GUARDWALK.scr:25
    if ctx:condition("counter==1") then -- GUARDWALK.scr:27
        ctx:command("set", "L_marker g_marker2") -- GUARDWALK.scr:28
        ctx:command("set", "counter 0") -- GUARDWALK.scr:29
        do return mm9.gotoLabel(script, ctx, "WalkStart") end -- GUARDWALK.scr:30
        do return ctx:exit("") end -- GUARDWALK.scr:31
    end -- GUARDWALK.scr:32
    do return ctx:exit("") end -- GUARDWALK.scr:34
end

script.labels["WalkStart"] = function(ctx)
    -- GUARDWALK.scr:37
    ctx:command("getobjecthandle", "L_marker g_hobject") -- GUARDWALK.scr:40
    ctx:command("runto", "g_hobject 32 Arrive") -- GUARDWALK.scr:41
    do return ctx:exit("") end -- GUARDWALK.scr:42
end

script.labels["Arrive"] = function(ctx)
    -- GUARDWALK.scr:46
    ctx:command("wait", "0 .01 OnUse") -- GUARDWALK.scr:49
    -- gosub OnUse
    do return ctx:exit("") end -- GUARDWALK.scr:51
end

script.labels["OnExit"] = function(ctx)
    -- GUARDWALK.scr:56
    do return ctx:exit("") end -- GUARDWALK.scr:59
end

script.labels["Main"] = function(ctx)
    -- GUARDWALK.scr:62
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("onstuck", "WalkStart") -- GUARDWALK.scr:68
    ctx:addTrigger("use", "OnUse") -- GUARDWALK.scr:69
    do return ctx:exit("") end -- GUARDWALK.scr:70
end

return script
