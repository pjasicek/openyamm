-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BATHHOUSE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- bathhouse.scr
-- By Timmy
-- checks to see if the player has killed everything in anskram keep
script.labels["Onuse"] = function(ctx)
    -- BATHHOUSE.scr:15
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    if ctx:hasKey(348) then -- BATHHOUSE.scr:20-21
        if not ctx:hasKey(349) then -- BATHHOUSE.scr:22-23
            ctx:giveKey(349) -- BATHHOUSE.scr:24
            do return ctx:exit("") end -- BATHHOUSE.scr:25
        end -- BATHHOUSE.scr:26
    else -- BATHHOUSE.scr:27
        if not ctx:hasKey(350) then -- BATHHOUSE.scr:28-29
            ctx:giveKey(350) -- BATHHOUSE.scr:30
            do return ctx:exit("") end -- BATHHOUSE.scr:31
        end -- BATHHOUSE.scr:32
    end -- BATHHOUSE.scr:33
    do return ctx:exit("") end -- BATHHOUSE.scr:34
end

script.labels["Main"] = function(ctx)
    -- BATHHOUSE.scr:38
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onuse") -- BATHHOUSE.scr:42
    ctx:addTrigger("kill", "Onuse") -- BATHHOUSE.scr:43
    do return ctx:exit("") end -- BATHHOUSE.scr:44
end

return script
