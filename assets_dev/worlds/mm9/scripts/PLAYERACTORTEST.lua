-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PLAYERACTORTEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "aiglobals.inc" }

-- PlayerActorTest.scr
script.labels["OnArrival"] = function(ctx)
    -- PLAYERACTORTEST.scr:11
    ctx:state().g_hObject = ctx:objectOrNil("Scene0") -- PLAYERACTORTEST.scr:14
    if ctx:condition("g_hObject==NULL") then -- PLAYERACTORTEST.scr:16
        do return ctx:exit("") end -- PLAYERACTORTEST.scr:17
    end -- PLAYERACTORTEST.scr:18
    ctx:trigger("g_hObject", "off") -- PLAYERACTORTEST.scr:20
    do return ctx:exit("") end -- PLAYERACTORTEST.scr:22
end

script.labels["WalkTest"] = function(ctx)
    -- PLAYERACTORTEST.scr:25
    ctx:state().g_hTarget = ctx:objectOrNil("StairMarker") -- PLAYERACTORTEST.scr:29
    if ctx:condition("g_hTarget==NULL") then -- PLAYERACTORTEST.scr:31
        do return ctx:exit("FALSE") end -- PLAYERACTORTEST.scr:32
    end -- PLAYERACTORTEST.scr:33
    ctx:self():walkTo(ctx:object("g_hTarget"), 0, "OnArrival") -- PLAYERACTORTEST.scr:35
    do return ctx:exit("") end -- PLAYERACTORTEST.scr:37
end

script.labels["On"] = function(ctx)
    -- PLAYERACTORTEST.scr:40
    ctx:wait(2.0, 2.0, "WalkTest") -- PLAYERACTORTEST.scr:44
    do return ctx:exit("FALSE") end -- PLAYERACTORTEST.scr:48
end

script.labels["Stuck"] = function(ctx)
    -- PLAYERACTORTEST.scr:51
    ctx:self():walkTo(ctx:object("g_hTarget"), 0, "OnArrival") -- PLAYERACTORTEST.scr:53
    do return ctx:exit("TRUE") end -- PLAYERACTORTEST.scr:55
end

script.labels["Main"] = function(ctx)
    -- PLAYERACTORTEST.scr:58
    -- TraceON
    ctx:addTrigger("ON", "On") -- PLAYERACTORTEST.scr:62
    ctx:onEvent("OnStuck", "Stuck") -- PLAYERACTORTEST.scr:63
    do return ctx:exit("") end -- PLAYERACTORTEST.scr:66
end

return script
