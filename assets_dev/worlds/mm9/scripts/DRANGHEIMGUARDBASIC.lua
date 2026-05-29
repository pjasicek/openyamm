-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMGUARDBASIC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "DrangheimHostility.inc" }

-- DrangheimGuardBasic.scr
-- by SJR
-- Purpose:standard guard, but with
-- checking for visitor pass
script.labels["Main"] = function(ctx)
    -- DRANGHEIMGUARDBASIC.scr:10
    ctx:onEvent("OnPostStartWorld", "InitDrangheimGuardBasic") -- DRANGHEIMGUARDBASIC.scr:12
    ctx:onEvent("OnPostMiniSaveLoad", "InitDrangheimGuardBasic") -- DRANGHEIMGUARDBASIC.scr:13
    do return ctx:exit("TRUE") end -- DRANGHEIMGUARDBASIC.scr:15
end

script.labels["InitDrangheimGuardBasic"] = function(ctx)
    -- DRANGHEIMGUARDBASIC.scr:18
    mm9.gosub(script, ctx, "InitDrangheimHostility") -- DRANGHEIMGUARDBASIC.scr:20
    do return ctx:exit("TRUE") end -- DRANGHEIMGUARDBASIC.scr:22
end

return script
