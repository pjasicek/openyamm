-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOARDSPIKE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- BoardSpike.scr
-- By Karl
-- When spike is used it disappears.
script.labels["RemoveMe"] = function(ctx)
    -- BOARDSPIKE.scr:20
    ctx:object("hSpike"):remove() -- BOARDSPIKE.scr:23
    do return ctx:exit("TRUE") end -- BOARDSPIKE.scr:25
end

script.labels["OnUse"] = function(ctx)
    -- BOARDSPIKE.scr:28
    ctx:playSound("Sounds\\Events\\metalwood04.wav", "DoNothing", 100, 200, "FALSE", 100) -- BOARDSPIKE.scr:30
    ctx:trigger("hBoardDoor", "OnePulled") -- BOARDSPIKE.scr:33
    ctx:state().hSpike = ctx:self() -- BOARDSPIKE.scr:36
    ctx:wait(0, .1, "RemoveMe") -- BOARDSPIKE.scr:37
    do return ctx:exit(1) end -- BOARDSPIKE.scr:41
end

script.labels["main2"] = function(ctx)
    -- BOARDSPIKE.scr:44
    ctx:state().hBoardDoor = ctx:objectOrNil("sDoor") -- BOARDSPIKE.scr:47
    do return ctx:exit(1) end -- BOARDSPIKE.scr:49
end

script.labels["main"] = function(ctx)
    -- BOARDSPIKE.scr:53
    ctx:getParam(0, "sDoor") -- BOARDSPIKE.scr:55
    ctx:addTrigger("Use", "OnUse") -- BOARDSPIKE.scr:56
    ctx:wait(0, .1, "main2") -- BOARDSPIKE.scr:57
    do return ctx:exit("") end -- BOARDSPIKE.scr:59
end

return script
