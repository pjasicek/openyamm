-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC190.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- NPC190.scr
-- timmy
-- handles Soxolf Tryygvassen voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC190.scr:14
    mm9.gosub(script, ctx, "maypole") -- NPC190.scr:17
    mm9.gosub(script, ctx, "pledge") -- NPC190.scr:18
    do return ctx:exit("") end -- NPC190.scr:20
end

script.labels["Maypole"] = function(ctx)
    -- NPC190.scr:24
    -- maypole Quest
    if not ctx:hasKey(268) then -- NPC190.scr:29-30
        if ctx:hasKey(267) then -- NPC190.scr:31-32
            ctx:command("hasgold", "500 g_ntemp") -- NPC190.scr:33
            if ctx:condition("g_ntemp==1") then -- NPC190.scr:34
                ctx:command("takegold", "500") -- NPC190.scr:35
                ctx:giveKey(268) -- NPC190.scr:36
                do return ctx:exit("") end -- NPC190.scr:37
            else -- NPC190.scr:38
                ctx:takeKey(267) -- NPC190.scr:39
                -- playsound "you don't have enough"
                do return ctx:exit("") end -- NPC190.scr:41
            end -- NPC190.scr:42
        end -- NPC190.scr:43
    end -- NPC190.scr:44
    do return ctx:exit("") end -- NPC190.scr:45
    -- End maypole quest
    do return ctx:exit("") end -- NPC190.scr:53
end

script.labels["OnUse"] = function(ctx)
    -- NPC190.scr:58
    ctx:command("playsound", "voices\\NPC\\NPC_190.wav, DoNothing, 100, 240, FALSE, 100") -- NPC190.scr:61
    do return ctx:exit("") end -- NPC190.scr:62
end

script.labels["Init"] = function(ctx)
    -- NPC190.scr:65
    if not ctx:hasKey(268) then -- NPC190.scr:68-69
        do return ctx:exit("") end -- NPC190.scr:70
    end -- NPC190.scr:71
    ctx:command("getobjecthandle", "Prop0 g_hobject") -- NPC190.scr:73
    ctx:command("setmodelfilenames", "model_name Model_skin") -- NPC190.scr:74
    do return ctx:exit("") end -- NPC190.scr:76
end

script.labels["Main"] = function(ctx)
    -- NPC190.scr:79
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC190.scr:86
    ctx:addTrigger("Use", "OnUse") -- NPC190.scr:88
    ctx:command("wait", "1 1 Init") -- NPC190.scr:89
    do return ctx:exit("") end -- NPC190.scr:90
end

return script
