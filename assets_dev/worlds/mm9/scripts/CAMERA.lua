-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAMERA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "followpath.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- camera.scr
-- jeffs fun test
script.labels["main"] = function(ctx)
    -- CAMERA.scr:11
    ctx:command("getmyhandle", "g_hThisObject") -- CAMERA.scr:14
    ctx:addTrigger("on", "OnCall") -- CAMERA.scr:15
    do return ctx:exit("") end -- CAMERA.scr:16
end

script.labels["OnCall"] = function(ctx)
    -- CAMERA.scr:20
    mm9.gosub(script, ctx, "FollowPathinit") -- CAMERA.scr:22
    ctx:command("set", "g_sFollowPathName, Marker") -- CAMERA.scr:23
    ctx:command("set", "g_nFollowPathSpeed, 120") -- CAMERA.scr:24
    -- Set g_nFollowPathCallback, < Callback # to use when we reach a marker>
    ctx:command("set", "g_nFollowPathDoneCallback, Pathdone") -- CAMERA.scr:26
    -- Set g_nFollowPathLoops, 1
    -- SetCallback g_nFollowPath
    mm9.gosub(script, ctx, "FollowPath") -- CAMERA.scr:29
    do return ctx:exit(0) end -- CAMERA.scr:30
end

script.labels["Pathdone"] = function(ctx)
    -- CAMERA.scr:32
    ctx:trigger("g_hThisObject", "off") -- CAMERA.scr:34
    do return ctx:exit("") end -- CAMERA.scr:36
end

return script
