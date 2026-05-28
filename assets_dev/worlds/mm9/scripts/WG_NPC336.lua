-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_NPC336.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- WG_NPC336.scr
-- timmy
-- handles Skraelos acting for cutscene
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["Loop"] = function(ctx)
    -- WG_NPC336.scr:25
    ctx:command("getmyhandle", "g_hobject") -- WG_NPC336.scr:29
    ctx:command("clearflag", "g_hobject, visible") -- WG_NPC336.scr:30
    ctx:command("clearflag", "g_hobject, solid") -- WG_NPC336.scr:31
    ctx:command("clearflag", "g_hobject, gravity") -- WG_NPC336.scr:32
    do return ctx:exit("") end -- WG_NPC336.scr:33
end

script.labels["OnStart"] = function(ctx)
    -- WG_NPC336.scr:36
    ctx:command("getmyhandle", "g_hobject") -- WG_NPC336.scr:39
    ctx:command("setflag", "g_hobject, visible") -- WG_NPC336.scr:40
    ctx:command("setflag", "g_hobject, solid") -- WG_NPC336.scr:41
    ctx:command("setflag", "g_hobject, gravity") -- WG_NPC336.scr:42
    ctx:command("loopanim", "stand 0 DoNothing") -- WG_NPC336.scr:43
    do return ctx:exit("") end -- WG_NPC336.scr:44
end

script.labels["Main"] = function(ctx)
    -- WG_NPC336.scr:47
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- WG_NPC336.scr:53
    mm9.gosub(script, ctx, "Loop") -- WG_NPC336.scr:54
    ctx:addTrigger("Stop", "Loop") -- WG_NPC336.scr:55
    do return ctx:exit("") end -- WG_NPC336.scr:56
end

return script
