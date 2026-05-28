-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC131.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "Basewander.inc" }

-- NPC131.scr
-- timmy
-- handles Nutty Nurtigan voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC131.scr:19
    mm9.gosub(script, ctx, "Healed") -- NPC131.scr:22
    do return ctx:exit("") end -- NPC131.scr:25
end

script.labels["Healed"] = function(ctx)
    -- NPC131.scr:29
    if ctx:hasKey(211) then -- NPC131.scr:31-32
        if ctx:hasItem(558) then -- NPC131.scr:33-34
            ctx:takeItem(558) -- NPC131.scr:35
            ctx:command("getobjecthandle", "Marker0 g_hobject") -- NPC131.scr:36
            ctx:command("walkto", "g_hobject 16 OnWander") -- NPC131.scr:37
            do return ctx:exit("") end -- NPC131.scr:38
        end -- NPC131.scr:39
    end -- NPC131.scr:40
    do return ctx:exit("") end -- NPC131.scr:41
end

script.labels["OnWander"] = function(ctx)
    -- NPC131.scr:45
    mm9.gosub(script, ctx, "BaseWanderInit") -- NPC131.scr:47
    do return ctx:exit("") end -- NPC131.scr:48
end

script.labels["OnUse"] = function(ctx)
    -- NPC131.scr:51
    ctx:command("playsound", "voices\\NPC\\NPC_131.wav, DoNothing, 100, 240, FALSE, 100") -- NPC131.scr:54
    do return ctx:exit("") end -- NPC131.scr:55
end

script.labels["Init"] = function(ctx)
    -- NPC131.scr:58
    if ctx:hasKey(211) then -- NPC131.scr:61-62
        ctx:command("getobjecthandle", "RotatingDoor3 g_hobject") -- NPC131.scr:63
        ctx:trigger("g_hobject", "Unlock") -- NPC131.scr:64
        ctx:trigger("g_hobject", "Open") -- NPC131.scr:65
        ctx:command("getobjecthandle", "Marker0 g_hobject") -- NPC131.scr:66
        ctx:command("walkto", "g_hobject 16 OnWander") -- NPC131.scr:67
        do return ctx:exit("") end -- NPC131.scr:68
    end -- NPC131.scr:69
    do return ctx:exit("") end -- NPC131.scr:71
end

script.labels["Main"] = function(ctx)
    -- NPC131.scr:74
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC131.scr:81
    ctx:addTrigger("Use", "OnUse") -- NPC131.scr:82
    mm9.gosub(script, ctx, "Init") -- NPC131.scr:83
    do return ctx:exit("") end -- NPC131.scr:84
end

return script
