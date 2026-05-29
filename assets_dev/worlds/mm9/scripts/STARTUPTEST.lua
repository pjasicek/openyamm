-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "STARTUPTEST.scr"
script.includes = {}
script.labels = {}


-- startuptest.scr
-- Set's up console variables for startup..
script.labels["Main"] = function(ctx)
    -- STARTUPTEST.scr:7
    -- ConsoleCommand ShowFrameRate 1
    ctx:consoleCommand("NumConsoleLines", 1) -- STARTUPTEST.scr:9
    ctx:exitScript() -- STARTUPTEST.scr:10
    do return ctx:exit("") end -- STARTUPTEST.scr:12
end

return script
