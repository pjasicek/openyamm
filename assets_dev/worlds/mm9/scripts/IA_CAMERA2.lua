-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IA_CAMERA2.scr"
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
    -- IA_CAMERA2.scr:30
    ctx:command("getobjecthandle", "Camera3 g_hobject") -- IA_CAMERA2.scr:33
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- IA_CAMERA2.scr:34
    ctx:command("movetopos", "xpos Xpos Zpos 100 DoNothing") -- IA_CAMERA2.scr:35
    ctx:command("getobjecthandle", "Boat g_hobject") -- IA_CAMERA2.scr:36
    ctx:command("faceobject", "g_hobject 20 DoNothing") -- IA_CAMERA2.scr:37
    ctx:command("wait", "1 3.5 CraneShot") -- IA_CAMERA2.scr:38
    -- Target g_hobject
    do return ctx:exit("") end -- IA_CAMERA2.scr:40
end

script.labels["CraneShot"] = function(ctx)
    -- IA_CAMERA2.scr:43
    -- target g_hobject
    -- exit
    ctx:command("getobjecthandle", "Book g_hobject") -- IA_CAMERA2.scr:47
    ctx:trigger("g_hobject", "Crane") -- IA_CAMERA2.scr:48
    do return ctx:exit("") end -- IA_CAMERA2.scr:49
end

script.labels["Main"] = function(ctx)
    -- IA_CAMERA2.scr:52
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Pan", "OnPlay") -- IA_CAMERA2.scr:57
    do return ctx:exit("") end -- IA_CAMERA2.scr:61
end

return script
