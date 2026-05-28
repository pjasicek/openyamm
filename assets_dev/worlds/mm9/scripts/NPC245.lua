-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC245.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basedoor.inc" }

-- NPC245.scr
-- timmy
-- handles Byri the Scarred voice and quest stuff
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC245.scr:18
    if ctx:hasKey(231) then -- NPC245.scr:21-22
        ctx:command("wait", "1 2 Run") -- NPC245.scr:23
    end -- NPC245.scr:24
    do return ctx:exit("") end -- NPC245.scr:25
end

script.labels["Run"] = function(ctx)
    -- NPC245.scr:28
    ctx:command("getobjecthandle", "RotatingDoor0 g_hobject") -- NPC245.scr:31
    ctx:trigger("g_hobject", "use") -- NPC245.scr:32
    ctx:command("getobjecthandle", "Marker6 g_hobject") -- NPC245.scr:33
    ctx:command("runto", "g_hobject 128 OnVanish") -- NPC245.scr:34
    do return ctx:exit("") end -- NPC245.scr:35
end

script.labels["OnVanish"] = function(ctx)
    -- NPC245.scr:38
    ctx:command("getmyhandle", "g_hmyobject") -- NPC245.scr:41
    ctx:command("removeobject", "g_hmyobject") -- NPC245.scr:42
    ctx:command("exitscript", "") -- NPC245.scr:43
    do return ctx:exit("") end -- NPC245.scr:44
end

script.labels["OnEnter"] = function(ctx)
    -- NPC245.scr:47
    mm9.gosub(script, ctx, "basedoorinit") -- NPC245.scr:49
    ctx:command("getmyhandle", "g_hobject") -- NPC245.scr:50
    ctx:command("setflag", "g_hobject, visible") -- NPC245.scr:51
    ctx:command("setflag", "g_hobject, solid") -- NPC245.scr:52
    ctx:command("setflag", "g_hobject, gravity") -- NPC245.scr:53
    ctx:command("getobjecthandle", "Marker2 g_hobject") -- NPC245.scr:54
    ctx:command("walkto", "g_hobject 16 DoNothing") -- NPC245.scr:55
    do return ctx:exit("") end -- NPC245.scr:56
end

script.labels["Init"] = function(ctx)
    -- NPC245.scr:59
    ctx:command("getmyhandle", "g_hobject") -- NPC245.scr:63
    ctx:command("clearflag", "g_hobject, visible") -- NPC245.scr:64
    ctx:command("clearflag", "g_hobject, solid") -- NPC245.scr:65
    ctx:command("clearflag", "g_hobject, gravity") -- NPC245.scr:66
    do return ctx:exit("") end -- NPC245.scr:67
end

script.labels["OnUse"] = function(ctx)
    -- NPC245.scr:71
    ctx:command("stop", "") -- NPC245.scr:74
    ctx:command("playsound", "voices\\NPC\\NPC_245.wav, DoNothing, 100, 240, FALSE, 100") -- NPC245.scr:75
    do return ctx:exit("") end -- NPC245.scr:76
end

script.labels["Main"] = function(ctx)
    -- NPC245.scr:80
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC245.scr:87
    ctx:addTrigger("Use", "OnUse") -- NPC245.scr:88
    ctx:addTrigger("Enter", "OnEnter") -- NPC245.scr:89
    mm9.gosub(script, ctx, "Init") -- NPC245.scr:90
    do return ctx:exit("") end -- NPC245.scr:92
end

return script
