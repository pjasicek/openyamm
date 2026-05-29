-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GASRELEASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- GasRelease.scr
-- Karl Drown 10-11-01
-- Super simple "Send message" script.
script.labels["StopHere"] = function(ctx)
    -- GASRELEASE.scr:19
    do return ctx:exit("TRUE") end -- GASRELEASE.scr:22
end

script.labels["SendTrigger"] = function(ctx)
    -- GASRELEASE.scr:25
    ctx:state().nBool = ctx:object("PumpSwitch0"):getStat("IsOpen") -- GASRELEASE.scr:28-29
    -- if nBool==TRUE
    -- Trigger hMCMarkerA, MoveMe
    -- Trigger hMCMarkerB, MoveMe
    -- endif
    do return ctx:exit("TRUE") end -- GASRELEASE.scr:35
end

script.labels["Main2"] = function(ctx)
    -- GASRELEASE.scr:38
    -- GetObjectHandle PoolDamageBr0, hMCMarkerA
    -- GetObjectHandle PoolDamageBr1, hMCMarkerB
    do return ctx:exit("") end -- GASRELEASE.scr:45
end

script.labels["Main"] = function(ctx)
    -- GASRELEASE.scr:48
    ctx:addTrigger("On", "SendTrigger") -- GASRELEASE.scr:51
    do return ctx:exit("") end -- GASRELEASE.scr:53
end

return script
