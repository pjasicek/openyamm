-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "followpath.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "camera.scr" }

-- test.scr
-- jeffs fun test
script.labels["main"] = function(ctx)
    -- TEST.scr:12
    ctx:command("ontouchnotify", "run") -- TEST.scr:14
    do return ctx:exit("") end -- TEST.scr:16
end

script.labels["run"] = function(ctx)
    -- TEST.scr:20
    ctx:command("runscript", "camera.scr") -- TEST.scr:22
end

-- :Goto
-- Goto OnCall
-- exit
return script
