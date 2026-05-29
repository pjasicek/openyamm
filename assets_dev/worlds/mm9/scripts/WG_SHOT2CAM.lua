-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_SHOT2CAM.scr"
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
    -- WG_SHOT2CAM.scr:30
    ctx:state().g_hobject = ctx:objectOrNil("WinMan") -- WG_SHOT2CAM.scr:34
    ctx:self():setTarget(ctx:object("g_hobject")) -- WG_SHOT2CAM.scr:35
    -- facedir 3476.0 1172.0 -3596.0 0 DoNothing
    ctx:screenFadeIn(1) -- WG_SHOT2CAM.scr:37
    ctx:trigger("g_hobject", "switch") -- WG_SHOT2CAM.scr:38
    do return ctx:exit("") end -- WG_SHOT2CAM.scr:40
end

script.labels["Main"] = function(ctx)
    -- WG_SHOT2CAM.scr:43
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_SHOT2CAM.scr:48
    do return ctx:exit("") end -- WG_SHOT2CAM.scr:52
end

return script
