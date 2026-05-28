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
    ctx:command("nindex", "= nChildIndex * 2 + 1") -- BONELIMB.scr:40
    ctx:command("nchildindex", "= nChildIndex + 1") -- BONELIMB.scr:41
    ctx:command("wait", "0, 1, InitBoneLimb") -- BONELIMB.scr:43
    do return ctx:exit("TRUE") end -- BONELIMB.scr:44
end

script.labels["InitBoneLimb"] = function(ctx)
    -- BONELIMB.scr:47
    ctx:addTrigger("sCommand", "UpdateLimb") -- BONELIMB.scr:49
    ctx:command("schildname", "= sChildName + nChildIndex") -- BONELIMB.scr:51
    ctx:command("schildsocketname", "= sChildSocketName + nIndex") -- BONELIMB.scr:52
    ctx:command("getmyhandle", "hMe") -- BONELIMB.scr:54
    ctx:command("getobjecthandle", "sChildSocketName, hChildSocket") -- BONELIMB.scr:55
    ctx:command("getobjecthandle", "sChildName, hChildLimb") -- BONELIMB.scr:56
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
    ctx:command("getdims", "hMe, nDummy, nHeight, nDummy") -- BONELIMB.scr:89
    ctx:command("nheight", "= nHeight / 2") -- BONELIMB.scr:90
    mm9.gosub(script, ctx, "GetUpDir") -- BONELIMB.scr:91
    ctx:command("vecscale", "dx,dy,dz, nHeight") -- BONELIMB.scr:92
    ctx:command("getpos", "hParentSocket, xMe,yMe,zMe") -- BONELIMB.scr:93
    ctx:command("xme", "= xMe + dx") -- BONELIMB.scr:94
    ctx:command("xme", "= yMe + dy") -- BONELIMB.scr:95
    ctx:command("xme", "= zMe + dz") -- BONELIMB.scr:96
    ctx:command("setpos", "hMe, xMe,yMe,zMe") -- BONELIMB.scr:97
    do return ctx:exit("TRUE") end -- BONELIMB.scr:98
end

script.labels["LimbUpdateChild"] = function(ctx)
    -- BONELIMB.scr:101
    -- scales head direction by half-length
    -- and moves child socket
    ctx:command("getdims", "hMe, nDummy, nHeight, nDummy") -- BONELIMB.scr:105
    ctx:command("nheight", "= nHeight / 2") -- BONELIMB.scr:106
    mm9.gosub(script, ctx, "GetUpDir") -- BONELIMB.scr:107
    ctx:command("cprint", "nHeight") -- BONELIMB.scr:108
    ctx:command("vecscale", "dx,dy,dz, nHeight") -- BONELIMB.scr:109
    ctx:command("getpos", "hMe, xMe,yMe,zMe") -- BONELIMB.scr:110
    ctx:command("xme", "= xMe + dx") -- BONELIMB.scr:111
    ctx:command("xme", "= yMe + dy") -- BONELIMB.scr:112
    ctx:command("xme", "= zMe + dz") -- BONELIMB.scr:113
    ctx:command("setpos", "hChildSocket, xMe,yMe,zMe") -- BONELIMB.scr:114
    ctx:trigger("hChildLimb", "sCommand") -- BONELIMB.scr:115
    do return ctx:exit("TRUE") end -- BONELIMB.scr:116
end

script.labels["GetUpDir"] = function(ctx)
    -- BONELIMB.scr:119
    -- GetForwardDir hMe, dx2,dy2,dz2
    -- GetRightDir hMe, dx1,dy1,dz1
    ctx:command("dx1", "= 1") -- BONELIMB.scr:123
    ctx:command("dz2", "= 1") -- BONELIMB.scr:124
    ctx:command("vecscale", "dy2,dy1,dz1,0") -- BONELIMB.scr:125
    ctx:command("vecscale", "dy2,dx2,dz1,0") -- BONELIMB.scr:126
    ctx:command("veccross", "dx1,dy1,dz1, dx2,dy2,dz2, dx,dy,dz") -- BONELIMB.scr:127
    -- VecCross 0,0,1, 1,0,0, dx,dy,dz
    ctx:command("cprint", "dx") -- BONELIMB.scr:129
    ctx:command("cprint", "dy") -- BONELIMB.scr:130
    ctx:command("cprint", "dz") -- BONELIMB.scr:131
    ctx:command("vecnorm", "dx,dy,dz") -- BONELIMB.scr:132
    do return ctx:exit("TRUE") end -- BONELIMB.scr:133
end

script.labels["GetDownDir"] = function(ctx)
    -- BONELIMB.scr:136
    -- save computation, always call GetUpDir first
    -- gosub GetUpDir
    ctx:command("vecscale", "dx,dy,dz, -1") -- BONELIMB.scr:140
    do return ctx:exit("TRUE") end -- BONELIMB.scr:141
end

return script
