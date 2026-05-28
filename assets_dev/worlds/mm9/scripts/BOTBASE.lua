-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOTBASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "botbase.inc" }

-- BotBase.scr
-- Jeff Leggett
script.labels["Main"] = function(ctx)
    -- BOTBASE.scr:11
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "BotBaseInit") -- BOTBASE.scr:16
    do return ctx:exit("") end -- BOTBASE.scr:18
end

return script
