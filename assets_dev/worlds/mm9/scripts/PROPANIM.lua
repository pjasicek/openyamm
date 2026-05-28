-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PROPANIM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- PropAnim.scr
-- timmy
-- tells a prop to run it's animation
-- Note: if the first parameter is the word
-- OnUse, the second parameter becomes
-- the animation name and the script will wait until being used
-- to play the animation.  Otherwise it will just
-- loop an anim for time specified
-- Parameters
-- P0 Name of Animation OR whether it should be used
-- P1  # of times animation runs OR Name of amination to play
-- P2 Whether or not to allow Anim to play multiple times ONUse
script.labels["PlayAnim"] = function(ctx)
    -- PROPANIM.scr:25
    ctx:command("loopanim", "Params 0 DoNothing") -- PROPANIM.scr:29
    -- exitScript
    do return ctx:exit("") end -- PROPANIM.scr:31
end

script.labels["Init"] = function(ctx)
    -- PROPANIM.scr:34
    if ctx:condition("bLoop=NULL") then -- PROPANIM.scr:37
        ctx:command("set", "bLoop, FALSE") -- PROPANIM.scr:38
    end -- PROPANIM.scr:39
    if ctx:condition("Params==OnUse") then -- PROPANIM.scr:41
        ctx:addTrigger("Use", "OnUse") -- PROPANIM.scr:42
        do return ctx:exit("") end -- PROPANIM.scr:43
    else -- PROPANIM.scr:44
        do return mm9.gotoLabel(script, ctx, "PlayAnim") end -- PROPANIM.scr:45
        do return ctx:exit("") end -- PROPANIM.scr:46
    end -- PROPANIM.scr:47
    do return ctx:exit("") end -- PROPANIM.scr:48
end

script.labels["OnUse"] = function(ctx)
    -- PROPANIM.scr:51
    if ctx:condition("g_nCounter==0") then -- PROPANIM.scr:54
        ctx:command("playanim", "sParameter2 DoNothing") -- PROPANIM.scr:55
        if ctx:condition("bLoop=FALSE") then -- PROPANIM.scr:56
            ctx:command("set", "g_nCounter, 1") -- PROPANIM.scr:57
        end -- PROPANIM.scr:58
    end -- PROPANIM.scr:59
    do return ctx:exit("") end -- PROPANIM.scr:60
end

script.labels["Main"] = function(ctx)
    -- PROPANIM.scr:65
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "Params") -- PROPANIM.scr:71
    ctx:getParam(1, "sParameter2") -- PROPANIM.scr:72
    ctx:getParam(2, "bLoop") -- PROPANIM.scr:73
    ctx:command("onpoststartworld", "Init") -- PROPANIM.scr:74
    -- OnPostMiniSaveLoad Init
    -- OnPostSaveLoad Init
    -- wait 1 .1 Init
    do return ctx:exit("") end -- PROPANIM.scr:80
end

return script
