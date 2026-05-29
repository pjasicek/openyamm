-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC335.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC335.scr
-- timmy
-- handles Krohn voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- NPC335.scr:25
    mm9.gosub(script, ctx, "StopNjam") -- NPC335.scr:28
    do return ctx:exit("") end -- NPC335.scr:31
end

script.labels["StopNjam"] = function(ctx)
    -- NPC335.scr:35
    -- Stop Njam Quest
    ctx:hasKey(191, "keycheck") -- NPC335.scr:42
    if ctx:condition("keycheck==0") then -- NPC335.scr:43
        -- checks to see if they already have got the reward.
        if ctx:hasKey(108) then -- NPC335.scr:45-46
            -- checks to see if they've spoken to Tamur
            ctx:giveItem(576) -- NPC335.scr:48
            ctx:giveKey(191) -- NPC335.scr:49
            ctx:giveExp(218000) -- NPC335.scr:50
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC335.scr:51
            -- gives reward
            do return ctx:exit("") end -- NPC335.scr:55
        end -- NPC335.scr:56
    end -- NPC335.scr:57
    do return ctx:exit("") end -- NPC335.scr:59
    -- End stop Njam quest
    do return ctx:exit("") end -- NPC335.scr:64
end

script.labels["Loop"] = function(ctx)
    -- NPC335.scr:67
    ctx:state().g_hobject = ctx:self() -- NPC335.scr:71
    ctx:self():setFlag("visible", false) -- NPC335.scr:72
    ctx:self():setFlag("solid", false) -- NPC335.scr:73
    ctx:self():setFlag("gravity", false) -- NPC335.scr:74
    do return ctx:exit("") end -- NPC335.scr:75
end

script.labels["OnStart"] = function(ctx)
    -- NPC335.scr:78
    ctx:state().g_hobject = ctx:self() -- NPC335.scr:81
    ctx:self():setFlag("visible", true) -- NPC335.scr:82
    ctx:self():setFlag("solid", true) -- NPC335.scr:83
    ctx:self():setFlag("gravity", true) -- NPC335.scr:84
    ctx:self():loopAnimation("stand", 0, "DoNothing") -- NPC335.scr:85
    do return ctx:exit("") end -- NPC335.scr:86
end

script.labels["OnExit"] = function(ctx)
    -- NPC335.scr:92
    do return ctx:exit("") end -- NPC335.scr:95
end

script.labels["Main"] = function(ctx)
    -- NPC335.scr:98
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC335.scr:105
    ctx:addTrigger("Start", "OnStart") -- NPC335.scr:106
    ctx:addTrigger("Stop", "Loop") -- NPC335.scr:107
    do return ctx:exit("") end -- NPC335.scr:109
end

return script
