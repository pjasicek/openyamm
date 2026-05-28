-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SCENE7CAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- Wg_Shot7Cam.scr
-- timmy
-- tells a prop to run it's animation
-- Note: if the first parameter is the word
-- OnUse, the second parameter becomes
-- the animation name and the script will wait until being used
-- to play the animation.  Otherwise it will just
-- loop an anim for time specified
-- flag variables
script.labels["OnPlay"] = function(ctx)
    -- WG_SCENE7CAM1.scr:33
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WG_SCENE7CAM1.scr:37
    ctx:command("target", "g_hobject") -- WG_SCENE7CAM1.scr:38
    if ctx:condition("g_stemp!=cam2") then -- WG_SCENE7CAM1.scr:39
        ctx:command("wait", "1 1 OnPan") -- WG_SCENE7CAM1.scr:40
    end -- WG_SCENE7CAM1.scr:41
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:42
end

script.labels["OnPan"] = function(ctx)
    -- WG_SCENE7CAM1.scr:45
    ctx:command("getobjecthandle", "sMarker g_hobject") -- WG_SCENE7CAM1.scr:48
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- WG_SCENE7CAM1.scr:49
    ctx:command("movetopos", "xpos Ypos Zpos 150 OnArrive") -- WG_SCENE7CAM1.scr:50
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:51
end

script.labels["OnArrive"] = function(ctx)
    -- WG_SCENE7CAM1.scr:56
    ctx:command("getobjecthandle", "Winman g_hobject") -- WG_SCENE7CAM1.scr:59
    ctx:trigger("g_hobject", "CutToKrohn") -- WG_SCENE7CAM1.scr:60
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:61
end

script.labels["Main"] = function(ctx)
    -- WG_SCENE7CAM1.scr:63
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "G_stemp") -- WG_SCENE7CAM1.scr:68
    ctx:getParam(1, "sMarker") -- WG_SCENE7CAM1.scr:69
    ctx:addTrigger("Play", "OnPlay") -- WG_SCENE7CAM1.scr:70
    do return ctx:exit("") end -- WG_SCENE7CAM1.scr:74
end

return script
