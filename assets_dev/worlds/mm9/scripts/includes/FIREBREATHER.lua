-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FIREBREATHER.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- FireBreather.inc
-- by SJR
-- Purpose:fire eater at a
-- carnival.
script.labels["InitFireBreather"] = function(ctx)
    -- FIREBREATHER.inc:22
    ctx:state().fire_hMe = ctx:self() -- FIREBREATHER.inc:24
    do return ctx:exit("TRUE") end -- FIREBREATHER.inc:26
end

script.labels["BreatheFire"] = function(ctx)
    -- FIREBREATHER.inc:29
    if ctx:condition("fire_hShooter==0") then -- FIREBREATHER.inc:31
        ctx:state().fire_hShooter = ctx:objectOrNil("fire_sShooterName") -- FIREBREATHER.inc:32
        if ctx:condition("fire_hShooter==0") then -- FIREBREATHER.inc:33
            ctx:cprint("FireBreather.inc", "retrieved", "NULL", "shooter!") -- FIREBREATHER.inc:34
            do return ctx:exit("TRUE") end -- FIREBREATHER.inc:35
        end -- FIREBREATHER.inc:36
    end -- FIREBREATHER.inc:37
    -- cprint fire_sShooterName
    -- cprint fire_hShooter
    mm9.gosub(script, ctx, "OrientShooter") -- FIREBREATHER.inc:40
    mm9.gosub(script, ctx, "StartFire") -- FIREBREATHER.inc:41
    ctx:wait(0, 3, "EndFire") -- FIREBREATHER.inc:42
    do return ctx:exit("TRUE") end -- FIREBREATHER.inc:44
end

script.labels["OrientShooter"] = function(ctx)
    -- FIREBREATHER.inc:47
    ctx:state().fire_xDir, ctx:state().fire_yDir, ctx:state().fire_zDir = ctx:object("fire_hMe"):rotation() -- FIREBREATHER.inc:49
    ctx:state().fire_xMe, ctx:state().fire_yMe, ctx:state().fire_zMe = ctx:object("fire_hMe"):pos() -- FIREBREATHER.inc:50
    ctx:object("fire_hShooter"):setPos("fire_xMe", "fire_yMe", "fire_zMe") -- FIREBREATHER.inc:52
    ctx:setRotation("fire_hShooter", "fire_xDir", "fire_yDir", "fire_zDir") -- FIREBREATHER.inc:53
    do return ctx:exit("TRUE") end -- FIREBREATHER.inc:55
end

script.labels["StartFire"] = function(ctx)
    -- FIREBREATHER.inc:58
    ctx:trigger("fire_hShooter", "on") -- FIREBREATHER.inc:60
    do return ctx:exit("TRUE") end -- FIREBREATHER.inc:62
end

script.labels["EndFire"] = function(ctx)
    -- FIREBREATHER.inc:65
    ctx:trigger("fire_hShooter", "off") -- FIREBREATHER.inc:67
    do return ctx:exit("TRUE") end -- FIREBREATHER.inc:69
end

return script
