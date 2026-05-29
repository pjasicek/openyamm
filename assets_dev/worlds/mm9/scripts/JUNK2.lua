-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JUNK2.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "aiglobals.inc" }

-- junk2.scr
-- Jeff Leggett
-- Parameters:
-- none
script.labels["AttackDone"] = function(ctx)
    -- JUNK2.scr:12
end

script.labels["AttackReady"] = function(ctx)
    -- JUNK2.scr:13
    ctx:self():attack("AttackDone") -- JUNK2.scr:15
    do return ctx:exit("") end -- JUNK2.scr:16
end

script.labels["FoundPlayer"] = function(ctx)
    -- JUNK2.scr:19
    ctx:getParam(0, "g_hTarget") -- JUNK2.scr:20
    ctx:self():faceObject(ctx:object("g_hTarget")) -- JUNK2.scr:21
    ctx:onEvent("OnFoundPlayer") -- JUNK2.scr:22
    ctx:self():attack("AttackDone") -- JUNK2.scr:24
    do return ctx:exit("") end -- JUNK2.scr:25
end

script.labels["Main"] = function(ctx)
    -- JUNK2.scr:27
    ctx:onEvent("OnFoundPlayer", "FoundPlayer") -- JUNK2.scr:28
    ctx:onEvent("OnAttackReady", "AttackReady") -- JUNK2.scr:29
    do return ctx:exit("") end -- JUNK2.scr:31
end

return script
