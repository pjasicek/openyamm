-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RELIC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- Relic.scr
-- By Timmy
-- gives the player Saint's Relic
-- item 368
script.labels["Onuse"] = function(ctx)
    -- RELIC.scr:11
    if ctx:hasKey(338) then -- RELIC.scr:14-15
        if not ctx:hasKey(340) then -- RELIC.scr:16-17
            ctx:giveItem(368) -- RELIC.scr:18
            ctx:giveKey(340) -- RELIC.scr:19
            ctx:self():remove() -- RELIC.scr:21
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 50000, "FALSE", 100) -- RELIC.scr:22
            do return ctx:exit("") end -- RELIC.scr:23
        end -- RELIC.scr:24
    else -- RELIC.scr:25
        if not ctx:hasKey(339) then -- RELIC.scr:26-27
            ctx:giveItem(368) -- RELIC.scr:28
            ctx:giveKey(339) -- RELIC.scr:29
            ctx:self():remove() -- RELIC.scr:31
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 50000, "FALSE", 100) -- RELIC.scr:32
            do return ctx:exit("") end -- RELIC.scr:33
        end -- RELIC.scr:34
    end -- RELIC.scr:35
    do return ctx:exit("") end -- RELIC.scr:37
end

script.labels["DeleteCheck"] = function(ctx)
    -- RELIC.scr:40
    if ctx:hasKey(340) then -- RELIC.scr:43-44
        ctx:self():remove() -- RELIC.scr:46
        do return ctx:exit("") end -- RELIC.scr:47
    end -- RELIC.scr:48
    if ctx:hasKey(339) then -- RELIC.scr:50-51
        ctx:self():remove() -- RELIC.scr:53
        do return ctx:exit("") end -- RELIC.scr:54
    end -- RELIC.scr:55
    do return ctx:exit("") end -- RELIC.scr:56
end

script.labels["Main"] = function(ctx)
    -- RELIC.scr:60
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- RELIC.scr:64
    mm9.gosub(script, ctx, "DeleteCheck") -- RELIC.scr:65
    do return ctx:exit("") end -- RELIC.scr:66
end

return script
