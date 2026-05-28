-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RYANBUTTON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- Ryanbutton.scr
-- timmy
-- Handles ryan's deathmatch button thing
script.labels["OnUse"] = function(ctx)
    -- RYANBUTTON.scr:12
    if ctx:condition("counter==0") then -- RYANBUTTON.scr:15
        ctx:command("playanim", "OpenBook") -- RYANBUTTON.scr:17
        ctx:command("add", "counter, 1") -- RYANBUTTON.scr:18
        do return ctx:exit("") end -- RYANBUTTON.scr:19
    end -- RYANBUTTON.scr:20
    if ctx:condition("counter==1") then -- RYANBUTTON.scr:22
        ctx:command("playanim", "TurnPage") -- RYANBUTTON.scr:23
        ctx:command("add", "counter, 1") -- RYANBUTTON.scr:24
        do return ctx:exit("") end -- RYANBUTTON.scr:25
    end -- RYANBUTTON.scr:26
    if ctx:condition("counter==2") then -- RYANBUTTON.scr:28
        ctx:command("playanim", "TurnBack") -- RYANBUTTON.scr:29
        ctx:command("add", "counter, 1") -- RYANBUTTON.scr:30
        do return ctx:exit("") end -- RYANBUTTON.scr:31
    end -- RYANBUTTON.scr:32
    if ctx:condition("Counter>=3") then -- RYANBUTTON.scr:34
        ctx:command("playanim", "Closebook") -- RYANBUTTON.scr:35
        ctx:command("set", "counter, 0") -- RYANBUTTON.scr:36
        do return ctx:exit("") end -- RYANBUTTON.scr:37
    end -- RYANBUTTON.scr:38
end

script.labels["Main"] = function(ctx)
    -- RYANBUTTON.scr:44
    ctx:command("set", "counter, 0") -- RYANBUTTON.scr:49
    ctx:addTrigger("Use", "OnUse") -- RYANBUTTON.scr:50
    do return ctx:exit("") end -- RYANBUTTON.scr:51
end

return script
