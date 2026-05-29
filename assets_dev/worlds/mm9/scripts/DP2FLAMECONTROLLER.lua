-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP2FLAMECONTROLLER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "globals.inc" }

-- DP2flamecontroller.scr
-- timmy
script.labels["OnFlameOn"] = function(ctx)
    -- DP2FLAMECONTROLLER.scr:17
    ctx:getParam(1, "TorchId") -- DP2FLAMECONTROLLER.scr:20
    ctx:arrayPut("FlameArray", "TorchId", "True") -- DP2FLAMECONTROLLER.scr:21
    mm9.gosub(script, ctx, "CheckAllFlamers") -- DP2FLAMECONTROLLER.scr:22
    do return ctx:exit("") end -- DP2FLAMECONTROLLER.scr:23
end

script.labels["CheckAllFlamers"] = function(ctx)
    -- DP2FLAMECONTROLLER.scr:27
    if ctx:condition("BeenDone==true") then -- DP2FLAMECONTROLLER.scr:31
        do return ctx:exit("") end -- DP2FLAMECONTROLLER.scr:32
    end -- DP2FLAMECONTROLLER.scr:33
    ctx:state().counter = 0 -- DP2FLAMECONTROLLER.scr:35
end

script.labels["CheckAllFlamersloop"] = function(ctx)
    -- DP2FLAMECONTROLLER.scr:39
    ctx:arrayGet("FlameArray", "counter", "FlameOn") -- DP2FLAMECONTROLLER.scr:45
    if ctx:condition("Flameon==false") then -- DP2FLAMECONTROLLER.scr:46
        do return ctx:exit("") end -- DP2FLAMECONTROLLER.scr:47
    end -- DP2FLAMECONTROLLER.scr:48
    ctx:state().Counter = (tonumber(ctx:state().Counter) or 0) + 1 -- DP2FLAMECONTROLLER.scr:50
    if ctx:condition("counter<6") then -- DP2FLAMECONTROLLER.scr:52
        do return mm9.gotoLabel(script, ctx, "CheckAllFlamersloop") end -- DP2FLAMECONTROLLER.scr:53
    end -- DP2FLAMECONTROLLER.scr:54
    ctx:object("Door6"):trigger("Unlock") -- DP2FLAMECONTROLLER.scr:56-57
    -- Trigger Door7, Unlock
    ctx:trigger("g_hobject", "Use") -- DP2FLAMECONTROLLER.scr:60
    ctx:state().BeenDone = true -- DP2FLAMECONTROLLER.scr:61
    ctx:wait(0.2, 0.2, "killme") -- DP2FLAMECONTROLLER.scr:62
    do return ctx:exit("") end -- DP2FLAMECONTROLLER.scr:63
end

script.labels["killme"] = function(ctx)
    -- DP2FLAMECONTROLLER.scr:66
    ctx:exitScript() -- DP2FLAMECONTROLLER.scr:69
end

script.labels["Main"] = function(ctx)
    -- DP2FLAMECONTROLLER.scr:73
    ctx:addTrigger("FlameOn", "OnFlameOn") -- DP2FLAMECONTROLLER.scr:76
    do return ctx:exit("") end -- DP2FLAMECONTROLLER.scr:78
end

return script
