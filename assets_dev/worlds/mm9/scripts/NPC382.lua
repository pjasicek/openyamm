-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC382.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "Basewander.inc" }

-- NPC382.scr
-- timmy
-- handles Pilgrim Jann and the Fizbin of Misfortune voice and quest stuff
script.labels["OnRude"] = function(ctx)
    -- NPC382.scr:12
    ctx:takeKey(393) -- NPC382.scr:14
    if ctx:hasKey(394) then -- NPC382.scr:16-17
        ctx:takeItem(216) -- NPC382.scr:18
        ctx:giveGold(40000) -- NPC382.scr:19
        ctx:takeKey(394) -- NPC382.scr:20
        do return ctx:exit("") end -- NPC382.scr:21
    end -- NPC382.scr:22
    do return ctx:exit("") end -- NPC382.scr:23
end

script.labels["OnUse"] = function(ctx)
    -- NPC382.scr:26
    if ctx:hasItem(216) then -- NPC382.scr:31-32
        ctx:giveKey(393) -- NPC382.scr:33
        do return ctx:exit("") end -- NPC382.scr:34
    end -- NPC382.scr:35
    do return ctx:exit("") end -- NPC382.scr:38
end

script.labels["Main"] = function(ctx)
    -- NPC382.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC382.scr:49
    ctx:addTrigger("Use", "OnUse") -- NPC382.scr:50
    mm9.gosub(script, ctx, "basewanderinit") -- NPC382.scr:51
    do return ctx:exit("") end -- NPC382.scr:52
end

return script
