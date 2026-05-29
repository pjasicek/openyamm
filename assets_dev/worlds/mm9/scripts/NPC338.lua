-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC338.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC338.scr
-- timmy
-- handles Igrid voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC338.scr:19
    mm9.gosub(script, ctx, "darkpass") -- NPC338.scr:22
    do return ctx:exit("") end -- NPC338.scr:24
end

script.labels["darkpass"] = function(ctx)
    -- NPC338.scr:28
    -- darkpass Quest
    if ctx:hasKey(476) then -- NPC338.scr:34-35
        mm9.gosub(script, ctx, "activate") -- NPC338.scr:36
    end -- NPC338.scr:37
    if not ctx:hasKey(188) then -- NPC338.scr:40-41
        if ctx:hasItem(396) then -- NPC338.scr:42-43
            ctx:giveKey("", 188) -- NPC338.scr:44
            ctx:giveExp(146000) -- NPC338.scr:45
        end -- NPC338.scr:46
    end -- NPC338.scr:47
    if not ctx:hasKey(187) then -- NPC338.scr:51-52
        ctx:giveKey(476) -- NPC338.scr:53
        ctx:giveKey(187) -- NPC338.scr:54
        ctx:giveExp(92000) -- NPC338.scr:55
        mm9.gosub(script, ctx, "activate") -- NPC338.scr:56
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC338.scr:57
        do return ctx:exit("") end -- NPC338.scr:58
    end -- NPC338.scr:59
    do return ctx:exit("") end -- NPC338.scr:60
    -- End darkpass quest
    do return ctx:exit("") end -- NPC338.scr:65
end

script.labels["activate"] = function(ctx)
    -- NPC338.scr:70
    ctx:object("FlameCage"):trigger("open") -- NPC338.scr:73-74
    ctx:object("ExitPoint"):trigger("on") -- NPC338.scr:75-76
    -- this is where the exit it turned on!!
    do return ctx:exit("") end -- NPC338.scr:78
end

script.labels["OnUse"] = function(ctx)
    -- NPC338.scr:82
    do return ctx:exit("") end -- NPC338.scr:86
end

script.labels["OnExit"] = function(ctx)
    -- NPC338.scr:89
    do return ctx:exit("") end -- NPC338.scr:92
end

script.labels["Main"] = function(ctx)
    -- NPC338.scr:95
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC338.scr:102
    ctx:addTrigger("Use", "OnUse") -- NPC338.scr:104
    do return ctx:exit("") end -- NPC338.scr:106
end

return script
