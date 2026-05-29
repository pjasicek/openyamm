-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FURNACESWITCH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- FurnaceSwitch.scr
-- Karl Drown 10-11-01
-- Super simple "Move My World Object" script.
script.labels["StopHere"] = function(ctx)
    -- FURNACESWITCH.scr:22
    do return ctx:exit("TRUE") end -- FURNACESWITCH.scr:25
end

script.labels["SendTrigger"] = function(ctx)
    -- FURNACESWITCH.scr:28
    -- GetObjectHandle GasRelease0, hMessageA
    -- GetStat hMessage, IsOpen, bVarA
    -- GetObjectHandle PoolDamageBr0, hMCMarkerA
    -- GetObjectHandle PoolDamageBr1, hMCMarkerB
    ctx:state().bVarB = ctx:object("hMessageB"):getStat("IsOpen") -- FURNACESWITCH.scr:37
    if ctx:condition("bVarB==TRUE") then -- FURNACESWITCH.scr:39
        ctx:trigger("hMCMarkerA", "MoveMe") -- FURNACESWITCH.scr:40
        ctx:trigger("hMCMarkerB", "MoveMe") -- FURNACESWITCH.scr:41
    end -- FURNACESWITCH.scr:43
    do return ctx:exit("") end -- FURNACESWITCH.scr:45
end

script.labels["Initiate"] = function(ctx)
    -- FURNACESWITCH.scr:48
    ctx:state().hMessageB = ctx:self() -- FURNACESWITCH.scr:50
    ctx:state().hMessageA = ctx:objectOrNil("GasRelease0") -- FURNACESWITCH.scr:51
    -- GetStat hMessageB, IsOpen, bVarB
    -- GetStat hMessageA, IsOpen, bVarA
    ctx:state().hMCMarkerA = ctx:objectOrNil("PoolDamageBr0") -- FURNACESWITCH.scr:56
    ctx:state().hMCMarkerB = ctx:objectOrNil("PoolDamageBr1") -- FURNACESWITCH.scr:57
    -- GoSub SendTrigger
    do return ctx:exit("") end -- FURNACESWITCH.scr:61
end

script.labels["Main"] = function(ctx)
    -- FURNACESWITCH.scr:64
    ctx:addTrigger("Use", "") -- FURNACESWITCH.scr:67
    do return ctx:exit("") end -- FURNACESWITCH.scr:68
end

return script
