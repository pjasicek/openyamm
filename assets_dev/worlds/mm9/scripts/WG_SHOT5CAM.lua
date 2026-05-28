-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SHOT5CAM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- WG_NjamCam.scr
-- timmy
-- tells a prop to run it's animation
-- Note: if the first parameter is the word
-- OnUse, the second parameter becomes
-- the animation name and the script will wait until being used
-- to play the animation.  Otherwise it will just
-- loop an anim for time specified
-- flag variables
script.labels["OnPlay"] = function(ctx)
    -- WG_SHOT5CAM.scr:30
    ctx:command("getobjecthandle", "Njam g_hobject") -- WG_SHOT5CAM.scr:34
    -- target g_hobject
    ctx:command("wait", "1 .5, OnBackUp") -- WG_SHOT5CAM.scr:36
    do return ctx:exit("") end -- WG_SHOT5CAM.scr:37
end

script.labels["OnBackUp"] = function(ctx)
    -- WG_SHOT5CAM.scr:40
    ctx:command("getobjecthandle", "Shot5Mk g_hobject") -- WG_SHOT5CAM.scr:43
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- WG_SHOT5CAM.scr:44
    ctx:command("movetopos", "xpos Ypos Zpos 100 OnPanUp") -- WG_SHOT5CAM.scr:45
    do return ctx:exit("") end -- WG_SHOT5CAM.scr:46
end

script.labels["OnArrive1"] = function(ctx)
    -- WG_SHOT5CAM.scr:49
    do return ctx:exit("") end -- WG_SHOT5CAM.scr:52
end

script.labels["OnPanUp"] = function(ctx)
    -- WG_SHOT5CAM.scr:55
    ctx:command("getobjecthandle", "winman g_hobject") -- WG_SHOT5CAM.scr:59
    ctx:trigger("g_hobject", "PanUp") -- WG_SHOT5CAM.scr:60
    do return ctx:exit("") end -- WG_SHOT5CAM.scr:62
end

script.labels["Main"] = function(ctx)
    -- WG_SHOT5CAM.scr:65
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_SHOT5CAM.scr:70
    do return ctx:exit("") end -- WG_SHOT5CAM.scr:74
end

return script
