-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HARDROCKCAM.scr"
script.includes = {}
script.labels = {}


script.labels["dn"] = function(ctx)
    -- HARDROCKCAM.scr:8
    do return ctx:exit(1) end -- HARDROCKCAM.scr:10
end

script.labels["Play"] = function(ctx)
    -- HARDROCKCAM.scr:12
    ctx:state().hplayer = ctx:objectOrNil("dw") -- HARDROCKCAM.scr:14
    ctx:self():faceObject(ctx:player(), 90, "dn") -- HARDROCKCAM.scr:15
    do return ctx:exit(1) end -- HARDROCKCAM.scr:18
end

script.labels["Used"] = function(ctx)
    -- HARDROCKCAM.scr:21
    ctx:state().nX, ctx:state().nY, ctx:state().nZ = ctx:player():pos() -- HARDROCKCAM.scr:23
    ctx:self():moveToPos("nX", "nY", "nZ", 0, "dn") -- HARDROCKCAM.scr:24
    ctx:state().nX, ctx:state().nY, ctx:state().nZ = ctx:player():rotation() -- HARDROCKCAM.scr:25
    ctx:self():faceDir("nX", "nY", "nZ", 1000, "play") -- HARDROCKCAM.scr:26
    do return ctx:exit(1) end -- HARDROCKCAM.scr:28
end

script.labels["Main2"] = function(ctx)
    -- HARDROCKCAM.scr:31
    do return ctx:exit(1) end -- HARDROCKCAM.scr:34
end

script.labels["Main"] = function(ctx)
    -- HARDROCKCAM.scr:37
    ctx:state().hMyHandle = ctx:self() -- HARDROCKCAM.scr:38
    ctx:addTrigger("use", "Used") -- HARDROCKCAM.scr:39
    do return ctx:exit("") end -- HARDROCKCAM.scr:41
end

return script
