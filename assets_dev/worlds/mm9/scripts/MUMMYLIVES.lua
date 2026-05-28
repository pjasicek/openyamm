-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MUMMYLIVES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- MummyLives.scr
-- timmy
-- 12/6
-- makes mummys alive in OnFoundTarget
-- flag variables
script.labels["OnFoundTarget"] = function(ctx)
    -- MUMMYLIVES.scr:21
    ctx:command("runscript", "basemelee.scr") -- MUMMYLIVES.scr:24
    ctx:command("exitscript", "") -- MUMMYLIVES.scr:25
    do return ctx:exit("") end -- MUMMYLIVES.scr:26
end

script.labels["Init"] = function(ctx)
    -- MUMMYLIVES.scr:29
    ctx:command("loopanim", "coffin 0 DoNothing") -- MUMMYLIVES.scr:32
    ctx:command("onfoundtarget", "OnFoundTarget") -- MUMMYLIVES.scr:33
    do return ctx:exit("") end -- MUMMYLIVES.scr:34
end

script.labels["Main"] = function(ctx)
    -- MUMMYLIVES.scr:37
    -- traceon ;Delete
    ctx:getParam(0, "nRange") -- MUMMYLIVES.scr:42
    if ctx:condition("nRange==NULL") then -- MUMMYLIVES.scr:43
        ctx:command("set", "nRange, 1024") -- MUMMYLIVES.scr:44
    end -- MUMMYLIVES.scr:46
    -- wait 1 1 Init
    do return ctx:exit("") end -- MUMMYLIVES.scr:48
end

return script
