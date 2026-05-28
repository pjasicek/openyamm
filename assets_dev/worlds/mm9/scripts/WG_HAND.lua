-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WG_HAND.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- WG_Hand.scr
-- timmy
-- tells a prop to run it's animation
-- Note: if the first parameter is the word
-- OnUse, the second parameter becomes
-- the animation name and the script will wait until being used
-- to play the animation.  Otherwise it will just
-- loop an anim for time specified
-- flag variables
script.labels["Init"] = function(ctx)
    -- WG_HAND.scr:25
    ctx:command("getmyhandle", "g_hmyobject") -- WG_HAND.scr:28
    ctx:command("clearflag", "g_hmyobject Visible") -- WG_HAND.scr:29
    ctx:command("clearflag", "g_hmyobject Gravity") -- WG_HAND.scr:30
    ctx:command("clearflag", "g_hmyobject Solid") -- WG_HAND.scr:31
    do return ctx:exit("") end -- WG_HAND.scr:32
end

script.labels["OnPlay"] = function(ctx)
    -- WG_HAND.scr:35
    ctx:command("getmyhandle", "g_hmyobject") -- WG_HAND.scr:38
    -- SetFlag g_hmyobject Visible
    ctx:command("playanim", "SC07_Shot1 DoNothing") -- WG_HAND.scr:40
    ctx:command("wait", "1 1 OnDone") -- WG_HAND.scr:41
    do return ctx:exit("") end -- WG_HAND.scr:42
end

script.labels["OnDone"] = function(ctx)
    -- WG_HAND.scr:45
    ctx:command("getobjecthandle", "WinMan g_hobject") -- WG_HAND.scr:48
    ctx:trigger("g_hobject", "HandDone") -- WG_HAND.scr:49
    ctx:command("getmyhandle", "g_hmyobject") -- WG_HAND.scr:50
    ctx:command("clearflag", "g_hmyobject Visible") -- WG_HAND.scr:51
    do return ctx:exit("") end -- WG_HAND.scr:52
end

script.labels["Main"] = function(ctx)
    -- WG_HAND.scr:55
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- WG_HAND.scr:60
    mm9.gosub(script, ctx, "Init") -- WG_HAND.scr:61
    do return ctx:exit("") end -- WG_HAND.scr:64
end

return script
