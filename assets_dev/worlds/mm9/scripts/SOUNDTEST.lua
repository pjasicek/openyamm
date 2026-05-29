-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SOUNDTEST.scr"
script.includes = {}
script.labels = {}


script.labels["SoundDone"] = function(ctx)
    -- SOUNDTEST.scr:4
    ctx:cprint("sounddone") -- SOUNDTEST.scr:6
    do return ctx:exit("") end -- SOUNDTEST.scr:7
end

script.labels["go"] = function(ctx)
    -- SOUNDTEST.scr:9
    ctx:cprint("playing", "sound...") -- SOUNDTEST.scr:10
    ctx:playSound("filename", "SoundDone", 2000) -- SOUNDTEST.scr:11
    do return ctx:exit("") end -- SOUNDTEST.scr:13
end

script.labels["Main"] = function(ctx)
    -- SOUNDTEST.scr:16
    ctx:addTrigger("go", "go") -- SOUNDTEST.scr:18
    do return ctx:exit("") end -- SOUNDTEST.scr:19
end

return script
