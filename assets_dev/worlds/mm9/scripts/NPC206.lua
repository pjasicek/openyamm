-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC206.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "bankorb.inc" }

-- NPC206.scr
-- timmy
-- handles Fiachna A'Lanth voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC206.scr:19
    ctx:command("getobjecthandle", "bankdoor g_hobject") -- NPC206.scr:24
    ctx:trigger("g_hobject", "toggle") -- NPC206.scr:25
    mm9.gosub(script, ctx, "OnRude") -- NPC206.scr:26
    do return ctx:exit("") end -- NPC206.scr:27
end

script.labels["OnBank"] = function(ctx)
    -- NPC206.scr:35
    if ctx:hasKey(322) then -- NPC206.scr:39-40
        if ctx:hasItem(252) then -- NPC206.scr:41-42
            ctx:giveKey(330) -- NPC206.scr:43
        end -- NPC206.scr:44
    end -- NPC206.scr:45
    ctx:doRude(206) -- NPC206.scr:48
    ctx:command("playsound", "voices\\NPC\\NPC_206.wav, Onexit, 100, 240, FALSE, 100") -- NPC206.scr:49
    do return ctx:exit("") end -- NPC206.scr:52
end

script.labels["OnExit"] = function(ctx)
    -- NPC206.scr:55
    do return ctx:exit("") end -- NPC206.scr:58
end

script.labels["Main"] = function(ctx)
    -- NPC206.scr:61
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC206.scr:68
    ctx:addTrigger("bank", "OnBank") -- NPC206.scr:69
    ctx:command("set", "sLocation, Frosgard") -- NPC206.scr:70
    ctx:command("onpoststartworld", "Init") -- NPC206.scr:71
    ctx:command("onpostminisaveload", "Init") -- NPC206.scr:72
    ctx:command("onpostsaveload", "Init") -- NPC206.scr:73
    ctx:command("onpostsaveload", "Init") -- NPC206.scr:74
    ctx:command("wait", "1 .1 Init") -- NPC206.scr:75
    do return ctx:exit("") end -- NPC206.scr:76
end

return script
