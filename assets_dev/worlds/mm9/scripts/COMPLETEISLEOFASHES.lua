-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COMPLETEISLEOFASHES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "TestingStuff.inc" }

script.labels["Main"] = function(ctx)
    -- COMPLETEISLEOFASHES.scr:3
    ctx:addTrigger("win", "CompleteIsleOfAshes") -- COMPLETEISLEOFASHES.scr:4
    ctx:addTrigger("max", "MaxOutAll") -- COMPLETEISLEOFASHES.scr:5
    ctx:addTrigger("min", "ZeroOutAll") -- COMPLETEISLEOFASHES.scr:6
    do return ctx:exit(1) end -- COMPLETEISLEOFASHES.scr:7
end

return script
