-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BONELIMB.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }

-- BoneLimb.scr
-- by SJR
-- 11-06-01
-- Purpose:act as a limb in
-- BoneDragon.scr
script.labels["Main"] = function(ctx)
    -- BONELIMB.scr:37
    ctx:getParam(0, "nChildIndex") -- BONELIMB.scr:39
    ctx:set("nIndex", "nChildIndex * 2 + 1") -- BONELIMB.scr:40
    ctx:set("nChildIndex", "nChildIndex + 1") -- BONELIMB.scr:41
    ctx:wait(0, 1, "InitBoneLimb") -- BONELIMB.scr:43
    do return ctx:exit("TRUE") end -- BONELIMB.scr:44
end

script.labels["InitBoneLimb"] = function(ctx)
    -- BONELIMB.scr:47
    ctx:addTrigger("sCommand", "UpdateLimb") -- BONELIMB.scr:49
    ctx:set("sChildName", "sChildName + nChildIndex") -- BONELIMB.scr:51
    ctx:set("sChildSocketName", "sChildSocketName + nIndex") -- BONELIMB.scr:52
    ctx:state().hChildSocket = ctx:objectOrNil("sChildSocketName") -- BONELIMB.scr:55
    ctx:state().hChildLimb = ctx:objectOrNil("sChildName") -- BONELIMB.scr:56
    -- Trigger hMe, sCommand
    mm9.gosub(script, ctx, "UpdateLimb") -- BONELIMB.scr:59
    -- gosub GetUpDir
    do return ctx:exit("TRUE") end -- BONELIMB.scr:62
end

-- private
script.labels["UpdateLimb"] = function(ctx)
    -- BONELIMB.scr:75
    -- GetParam 0, hParentSocket
    -- gosub ParentUpdateLimb
    mm9.gosub(script, ctx, "LimbUpdateChild") -- BONELIMB.scr:80
    -- GetDistance hParentSocket, hChildSocket, nDummy
    -- cprint nDummy
    do return ctx:exit("TRUE") end -- BONELIMB.scr:83
end

-- static direction
script.labels["ParentUpdateLimb"] = function(ctx)
    -- BONELIMB.scr:87
    ctx:state().nDummy, ctx:state().nHeight, ctx:state().nDummy = ctx:self():dims() -- BONELIMB.scr:89
    ctx:set("nHeight", "nHeight / 2") -- BONELIMB.scr:90
    mm9.gosub(script, ctx, "GetUpDir") -- BONELIMB.scr:91
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecScale("dx", "dy", "dz", "nHeight") -- BONELIMB.scr:92
    ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:object("hParentSocket"):pos() -- BONELIMB.scr:93
    ctx:set("xMe", "xMe + dx") -- BONELIMB.scr:94
    ctx:set("xMe", "yMe + dy") -- BONELIMB.scr:95
    ctx:set("xMe", "zMe + dz") -- BONELIMB.scr:96
    ctx:self():setPos("xMe", "yMe", "zMe") -- BONELIMB.scr:97
    do return ctx:exit("TRUE") end -- BONELIMB.scr:98
end

script.labels["LimbUpdateChild"] = function(ctx)
    -- BONELIMB.scr:101
    -- scales head direction by half-length
    -- and moves child socket
    ctx:state().nDummy, ctx:state().nHeight, ctx:state().nDummy = ctx:self():dims() -- BONELIMB.scr:105
    ctx:set("nHeight", "nHeight / 2") -- BONELIMB.scr:106
    mm9.gosub(script, ctx, "GetUpDir") -- BONELIMB.scr:107
    ctx:cprint("nHeight") -- BONELIMB.scr:108
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecScale("dx", "dy", "dz", "nHeight") -- BONELIMB.scr:109
    ctx:state().xMe, ctx:state().yMe, ctx:state().zMe = ctx:self():pos() -- BONELIMB.scr:110
    ctx:set("xMe", "xMe + dx") -- BONELIMB.scr:111
    ctx:set("xMe", "yMe + dy") -- BONELIMB.scr:112
    ctx:set("xMe", "zMe + dz") -- BONELIMB.scr:113
    ctx:object("hChildSocket"):setPos("xMe", "yMe", "zMe") -- BONELIMB.scr:114
    ctx:trigger("hChildLimb", "sCommand") -- BONELIMB.scr:115
    do return ctx:exit("TRUE") end -- BONELIMB.scr:116
end

script.labels["GetUpDir"] = function(ctx)
    -- BONELIMB.scr:119
    -- GetForwardDir hMe, dx2,dy2,dz2
    -- GetRightDir hMe, dx1,dy1,dz1
    ctx:state().dx1 = 1 -- BONELIMB.scr:123
    ctx:state().dz2 = 1 -- BONELIMB.scr:124
    ctx:state().dy2, ctx:state().dy1, ctx:state().dz1 = ctx:vecScale("dy2", "dy1", "dz1", 0) -- BONELIMB.scr:125
    ctx:state().dy2, ctx:state().dx2, ctx:state().dz1 = ctx:vecScale("dy2", "dx2", "dz1", 0) -- BONELIMB.scr:126
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecCross("dx1", "dy1", "dz1", "dx2", "dy2", "dz2") -- BONELIMB.scr:127
    -- VecCross 0,0,1, 1,0,0, dx,dy,dz
    ctx:cprint("dx") -- BONELIMB.scr:129
    ctx:cprint("dy") -- BONELIMB.scr:130
    ctx:cprint("dz") -- BONELIMB.scr:131
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecNorm("dx", "dy", "dz") -- BONELIMB.scr:132
    do return ctx:exit("TRUE") end -- BONELIMB.scr:133
end

script.labels["GetDownDir"] = function(ctx)
    -- BONELIMB.scr:136
    -- save computation, always call GetUpDir first
    -- gosub GetUpDir
    ctx:state().dx, ctx:state().dy, ctx:state().dz = ctx:vecScale("dx", "dy", "dz", -1) -- BONELIMB.scr:140
    do return ctx:exit("TRUE") end -- BONELIMB.scr:141
end

return script
