-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SCENE7CAM3.scr"
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
    -- WG_SCENE7CAM3.scr:33
    ctx:command("getobjecthandle", "Krohn g_hobject") -- WG_SCENE7CAM3.scr:37
    ctx:command("target", "g_hobject") -- WG_SCENE7CAM3.scr:38
    -- wait 1 .2 OnPan
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:40
end

script.labels["OnPan"] = function(ctx)
    -- WG_SCENE7CAM3.scr:43
    ctx:command("getobjecthandle", "cam3marker g_hobject") -- WG_SCENE7CAM3.scr:46
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- WG_SCENE7CAM3.scr:47
    ctx:command("movetopos", "xpos Ypos Zpos 150 OnArrive") -- WG_SCENE7CAM3.scr:48
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:49
end

script.labels["OnArrive"] = function(ctx)
    -- WG_SCENE7CAM3.scr:54
    ctx:command("getobjecthandle", "Winman g_hobject") -- WG_SCENE7CAM3.scr:57
    -- Trigger g_hobject CutToKrohn
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:59
end

script.labels["Main"] = function(ctx)
    -- WG_SCENE7CAM3.scr:61
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_SCENE7CAM3.scr:67
    do return ctx:exit("") end -- WG_SCENE7CAM3.scr:71
end

return script
