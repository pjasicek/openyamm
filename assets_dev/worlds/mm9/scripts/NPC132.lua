-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC132.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC132.scr
-- timmy
-- handles Hjordisa the Hag voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["GiveHair"] = function(ctx)
    -- NPC132.scr:22
    -- Nurtigan Quest
    if ctx:hasItem(240) then -- NPC132.scr:27-28
        do return ctx:exit("") end -- NPC132.scr:29
    end -- NPC132.scr:30
    ctx:giveItem(240) -- NPC132.scr:32
    do return ctx:exit("") end -- NPC132.scr:33
    if not ctx:hasKey(207) then -- NPC132.scr:35-36
        if ctx:hasKey(206) then -- NPC132.scr:37-38
            ctx:giveKey(207) -- NPC132.scr:39
            ctx:giveItem(240) -- NPC132.scr:40
            do return ctx:exit("") end -- NPC132.scr:41
        end -- NPC132.scr:42
    end -- NPC132.scr:43
    -- End Nurtigan quest
    do return ctx:exit("") end -- NPC132.scr:47
end

script.labels["OnDamage"] = function(ctx)
    -- NPC132.scr:51
    ctx:self():die() -- NPC132.scr:54
    ctx:state().nUnconscious = true -- NPC132.scr:55
    mm9.gosub(script, ctx, "givehair") -- NPC132.scr:56
    do return ctx:exit("") end -- NPC132.scr:57
end

script.labels["OnStop"] = function(ctx)
    -- NPC132.scr:60
    ctx:self():stop() -- NPC132.scr:63
    do return ctx:exit("") end -- NPC132.scr:64
end

script.labels["OnUse"] = function(ctx)
    -- NPC132.scr:68
    if ctx:condition("nUnConscious==TRUE") then -- NPC132.scr:71
        mm9.gosub(script, ctx, "Givehair") -- NPC132.scr:72
        do return ctx:exit("") end -- NPC132.scr:73
    end -- NPC132.scr:74
    ctx:doRude(132) -- NPC132.scr:76
    ctx:playSound("voices\\NPC\\NPC_132.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC132.scr:77
    do return ctx:exit("") end -- NPC132.scr:78
end

script.labels["Main"] = function(ctx)
    -- NPC132.scr:81
    -- traceon
    -- Don't Forget to Delete this!
    -- OnDamage OnDamage
    ctx:addTrigger("Use", "OnUse") -- NPC132.scr:89
    do return ctx:exit("") end -- NPC132.scr:91
end

return script
