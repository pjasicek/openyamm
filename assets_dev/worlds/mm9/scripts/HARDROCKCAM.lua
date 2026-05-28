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
    ctx:command("getobjecthandle", "dw hplayer") -- HARDROCKCAM.scr:14
    ctx:command("faceobject", "hplayer 90 dn") -- HARDROCKCAM.scr:15
    do return ctx:exit(1) end -- HARDROCKCAM.scr:18
end

script.labels["Used"] = function(ctx)
    -- HARDROCKCAM.scr:21
    ctx:command("getplayerhandle", "hPlayer 1000") -- HARDROCKCAM.scr:22
    ctx:command("getpos", "hPlayer nX nY nZ") -- HARDROCKCAM.scr:23
    ctx:command("movetopos", "nX nY nZ 0 dn") -- HARDROCKCAM.scr:24
    ctx:command("getfacedir", "hPlayer nX nY nZ") -- HARDROCKCAM.scr:25
    ctx:command("facedir", "nX nY nZ 1000 play") -- HARDROCKCAM.scr:26
    do return ctx:exit(1) end -- HARDROCKCAM.scr:28
end

script.labels["Main2"] = function(ctx)
    -- HARDROCKCAM.scr:31
    do return ctx:exit(1) end -- HARDROCKCAM.scr:34
end

script.labels["Main"] = function(ctx)
    -- HARDROCKCAM.scr:37
    ctx:command("getmyhandle", "hMyHandle") -- HARDROCKCAM.scr:38
    ctx:addTrigger("use", "Used") -- HARDROCKCAM.scr:39
    do return ctx:exit("") end -- HARDROCKCAM.scr:41
end

return script
