-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BLADETRAP.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- BladeTrap.scr
-- For use with the spinning blad trap....
script.labels["TrapDone"] = function(ctx)
    -- BLADETRAP.scr:13
    ctx:trigger("hMyHandle", "OFF") -- BLADETRAP.scr:15
    do return ctx:exit("") end -- BLADETRAP.scr:16
end

script.labels["MoveDownDone"] = function(ctx)
    -- BLADETRAP.scr:19
    ctx:self():moveDir(-1, 0, 0, 500, 48, "TrapDone") -- BLADETRAP.scr:22
    do return ctx:exit("") end -- BLADETRAP.scr:24
end

script.labels["MoveLeftDone"] = function(ctx)
    -- BLADETRAP.scr:27
    ctx:self():moveDir(0, -1, 0, 10, 48, "MoveDownDone") -- BLADETRAP.scr:29
    do return ctx:exit("") end -- BLADETRAP.scr:31
end

script.labels["MoveUpDone"] = function(ctx)
    -- BLADETRAP.scr:34
    ctx:self():moveDir(1, 0, 0, 500, 48, "MoveLeftDone") -- BLADETRAP.scr:37
    do return ctx:exit("") end -- BLADETRAP.scr:38
end

script.labels["TurnOn"] = function(ctx)
    -- BLADETRAP.scr:41
    ctx:self():moveDir(0, 1, 0, 10, 48, "MoveUpDone") -- BLADETRAP.scr:44
    do return ctx:exit("FALSE") end -- BLADETRAP.scr:46
end

script.labels["OnTest"] = function(ctx)
    -- BLADETRAP.scr:49
    ctx:trigger("hMyHandle", "ON") -- BLADETRAP.scr:51
    do return ctx:exit("") end -- BLADETRAP.scr:54
end

script.labels["Main"] = function(ctx)
    -- BLADETRAP.scr:57
    ctx:state().hMyHandle = ctx:self() -- BLADETRAP.scr:60
    ctx:addTrigger("Test", "OnTest") -- BLADETRAP.scr:62
    ctx:addTrigger("ON", "TurnOn") -- BLADETRAP.scr:63
    -- TraceOn
    do return ctx:exit("") end -- BLADETRAP.scr:67
end

return script
