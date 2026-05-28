-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTGLOBALS.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "aiglobals.inc" }

-- BotGlobals.Inc
-- Globals that are shared by the various Bot include files..
-- Our wait callback ids...
script.labels["DoNothing"] = function(ctx)
    -- BOTGLOBALS.inc:37
    -- Used to kill callbacks...
    do return ctx:exit("") end -- BOTGLOBALS.inc:42
end

return script
