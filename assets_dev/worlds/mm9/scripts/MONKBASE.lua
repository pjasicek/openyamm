-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MONKBASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "Basemelee.scr" }
script.includes[#script.includes + 1] = { line = 10, path = "monksounds.inc" }

-- MonkBase.scr
-- timmy
-- 10/30
-- randomizes guard idle sounds.
script.labels["Main"] = function(ctx)
    -- MONKBASE.scr:15
    ctx:getParam(0, "bHostile") -- MONKBASE.scr:19
    mm9.gosub(script, ctx, "MS_Init") -- MONKBASE.scr:21
    if ctx:condition("bHotstile==True") then -- MONKBASE.scr:22
        mm9.gosub(script, ctx, "BaseInit") -- MONKBASE.scr:23
    end -- MONKBASE.scr:24
    do return ctx:exit("") end -- MONKBASE.scr:26
end

return script
