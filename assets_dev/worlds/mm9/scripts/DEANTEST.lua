-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DEANTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- deantest.scr
-- By Timmy
-- handles forad's stuff
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
script.labels["Onblabber"] = function(ctx)
    -- DEANTEST.scr:19
    -- erccs blabber
    ctx:doRude(400) -- DEANTEST.scr:25
    do return ctx:exit("") end -- DEANTEST.scr:29
end

script.labels["Onexit"] = function(ctx)
    -- DEANTEST.scr:35
    do return ctx:exit("") end -- DEANTEST.scr:38
end

script.labels["Main"] = function(ctx)
    -- DEANTEST.scr:41
    -- TraceOn ;delete me!!
    ctx:command("@m", "00:15 Onblabber") -- DEANTEST.scr:45
    do return ctx:exit("") end -- DEANTEST.scr:48
end

return script
