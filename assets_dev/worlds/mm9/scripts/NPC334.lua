-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC334.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC334.scr
-- timmy
-- handles Hanndl and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC334.scr:19
    mm9.gosub(script, ctx, "Gungnir") -- NPC334.scr:22
    do return ctx:exit("") end -- NPC334.scr:25
end

script.labels["Gungnir"] = function(ctx)
    -- NPC334.scr:30
    -- Gungnir Quest
    if not ctx:hasKey(357) then -- NPC334.scr:36-37
        if ctx:hasKey(356) then -- NPC334.scr:38-39
            ctx:takeItem(189) -- NPC334.scr:40
            ctx:giveKey(357) -- NPC334.scr:41
            ctx:giveGold(40000) -- NPC334.scr:42
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC334.scr:43
            ctx:giveExp(5000) -- NPC334.scr:44
            do return ctx:exit("") end -- NPC334.scr:45
        end -- NPC334.scr:46
    end -- NPC334.scr:47
    -- End Gungir Quest
    do return ctx:exit("") end -- NPC334.scr:51
end

script.labels["OnUse"] = function(ctx)
    -- NPC334.scr:57
    if ctx:hasKey(353) then -- NPC334.scr:59-60
        if ctx:hasItem(189) then -- NPC334.scr:61-62
            ctx:giveKey(354) -- NPC334.scr:64
        end -- NPC334.scr:66
    end -- NPC334.scr:67
    ctx:playSound("voices\\NPC\\NPC_334.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC334.scr:68
    do return ctx:exit("") end -- NPC334.scr:70
end

script.labels["OnExit"] = function(ctx)
    -- NPC334.scr:73
    do return ctx:exit("") end -- NPC334.scr:76
end

script.labels["Main"] = function(ctx)
    -- NPC334.scr:79
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC334.scr:86
    ctx:addTrigger("Use", "OnUse") -- NPC334.scr:88
    do return ctx:exit("") end -- NPC334.scr:90
end

return script
