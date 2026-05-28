-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "1000T_SKELETONHEAD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }

-- 1000T_SkeletonHead.scr
-- Karl Drown 11-27-01
-- Very Large Skull that targets the party.
script.labels["DoNothing"] = function(ctx)
    -- 1000T_SKELETONHEAD.scr:22
    do return ctx:exit("TRUE") end -- 1000T_SKELETONHEAD.scr:25
end

script.labels["Start"] = function(ctx)
    -- 1000T_SKELETONHEAD.scr:27
    -- Cprint Start
    if ctx:condition("bIsAnimating==FALSE") then -- 1000T_SKELETONHEAD.scr:30
        do return ctx:exit("") end -- 1000T_SKELETONHEAD.scr:31
    end -- 1000T_SKELETONHEAD.scr:32
    ctx:command("bisanimating", "= FALSE") -- 1000T_SKELETONHEAD.scr:33
    ctx:command("rotate", "0, 1, 0, 180, 180, TurnOff") -- 1000T_SKELETONHEAD.scr:34
    do return ctx:exit("TRUE") end -- 1000T_SKELETONHEAD.scr:36
end

script.labels["TurnOff"] = function(ctx)
    -- 1000T_SKELETONHEAD.scr:38
    -- Cprint TurnOff
    ctx:command("bisanimating", "= TRUE") -- 1000T_SKELETONHEAD.scr:41
    ctx:trigger("hShooterA", "Go") -- 1000T_SKELETONHEAD.scr:42
    ctx:trigger("hShooterB", "Go") -- 1000T_SKELETONHEAD.scr:43
    do return ctx:exit("TRUE") end -- 1000T_SKELETONHEAD.scr:45
end

script.labels["Main2"] = function(ctx)
    -- 1000T_SKELETONHEAD.scr:47
    ctx:command("bisanimating", "= TRUE") -- 1000T_SKELETONHEAD.scr:49
    ctx:command("getobjecthandle", "sShooterA, hShooterA") -- 1000T_SKELETONHEAD.scr:50
    ctx:command("getobjecthandle", "sShooterB, hShooterB") -- 1000T_SKELETONHEAD.scr:51
    ctx:addTrigger("Go", "Start") -- 1000T_SKELETONHEAD.scr:52
    ctx:addTrigger("Stop", "TurnOff") -- 1000T_SKELETONHEAD.scr:53
    ctx:trigger("hShooterA", "Go") -- 1000T_SKELETONHEAD.scr:54
    ctx:trigger("hShooterB", "Go") -- 1000T_SKELETONHEAD.scr:55
    do return ctx:exit("True") end -- 1000T_SKELETONHEAD.scr:57
end

script.labels["Main"] = function(ctx)
    -- 1000T_SKELETONHEAD.scr:59
    ctx:getParam(0, "sShooterA") -- 1000T_SKELETONHEAD.scr:61
    ctx:getParam(1, "sShooterB") -- 1000T_SKELETONHEAD.scr:62
    ctx:command("wait", "0, 0.5, Main2") -- 1000T_SKELETONHEAD.scr:63
    do return ctx:exit("") end -- 1000T_SKELETONHEAD.scr:64
end

return script
