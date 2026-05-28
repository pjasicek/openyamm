-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC209.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC209.scr
-- timmy
-- handles boat dude voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
script.labels["OnRude"] = function(ctx)
    -- NPC209.scr:19
    mm9.gosub(script, ctx, "book") -- NPC209.scr:22
    do return ctx:exit("") end -- NPC209.scr:25
end

script.labels["Book"] = function(ctx)
    -- NPC209.scr:29
    if ctx:hasKey(378) then -- NPC209.scr:32-33
        do return ctx:exit("") end -- NPC209.scr:34
    end -- NPC209.scr:35
    if ctx:hasKey(72) then -- NPC209.scr:37-38
        ctx:giveItem(562) -- NPC209.scr:39
        ctx:giveKey(378) -- NPC209.scr:40
        do return ctx:exit("") end -- NPC209.scr:41
    end -- NPC209.scr:42
    do return ctx:exit("") end -- NPC209.scr:44
end

script.labels["Main"] = function(ctx)
    -- NPC209.scr:47
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC209.scr:54
    do return ctx:exit("") end -- NPC209.scr:57
end

return script
