-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COFFIN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- coffin.scr
-- John Machin
-- Script to handle coffin opening and closing
script.labels["OnUse"] = function(ctx)
    -- COFFIN.scr:15
    if ctx:condition("bOpening == TRUE") then -- COFFIN.scr:17
        do return ctx:exit("") end -- COFFIN.scr:18
    end -- COFFIN.scr:19
    if ctx:condition("bOpened == TRUE") then -- COFFIN.scr:21
        do return ctx:exit("") end -- COFFIN.scr:22
    end -- COFFIN.scr:23
    ctx:command("set", "bOpening, TRUE") -- COFFIN.scr:25
    ctx:command("playanim", "Open, OnOpenDone") -- COFFIN.scr:26
    do return ctx:exit("") end -- COFFIN.scr:28
end

script.labels["OnOpenDone"] = function(ctx)
    -- COFFIN.scr:32
    ctx:command("set", "bOpening, FALSE") -- COFFIN.scr:34
    ctx:command("set", "bOpened, TRUE") -- COFFIN.scr:35
    do return ctx:exit("") end -- COFFIN.scr:37
end

script.labels["Main"] = function(ctx)
    -- COFFIN.scr:40
    -- Setup the following special triggers
    ctx:addTrigger("Use", "OnUse") -- COFFIN.scr:43
    do return ctx:exit("") end -- COFFIN.scr:45
end

return script
