-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSNAGASH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "base.inc" }

-- ILSnagash.scr
-- Timmy
-- This script makes Nagash do stuff
-- Parameters:
script.labels["OnAware"] = function(ctx)
    -- ILSNAGASH.scr:23
    ctx:state().Aware = true -- ILSNAGASH.scr:27
    if ctx:condition("Lever==true") then -- ILSNAGASH.scr:28
        do return mm9.gotoLabel(script, ctx, "InitBase") end -- ILSNAGASH.scr:29
        do return ctx:exit("") end -- ILSNAGASH.scr:30
    end -- ILSNAGASH.scr:31
    ctx:wait(2, 2, "Awarestart") -- ILSNAGASH.scr:33
end

script.labels["AwareStart"] = function(ctx)
    -- ILSNAGASH.scr:36
    ctx:object("RotatingDoor68"):trigger("use") -- ILSNAGASH.scr:40-41
    ctx:object("RotatingDoor69"):trigger("use") -- ILSNAGASH.scr:42-43
    ctx:state().g_hobject = ctx:objectOrNil("Switch0") -- ILSNAGASH.scr:44
    ctx:self():runTo(ctx:object("g_hobject"), 32, "Alert") -- ILSNAGASH.scr:45
    do return ctx:exit("") end -- ILSNAGASH.scr:46
end

script.labels["Alert"] = function(ctx)
    -- ILSNAGASH.scr:49
    ctx:object("Switch0"):trigger("use") -- ILSNAGASH.scr:52-53
    ctx:wait(3, 3, "Startfight") -- ILSNAGASH.scr:54
end

script.labels["Startfight"] = function(ctx)
    -- ILSNAGASH.scr:57
    ctx:state().Lever = true -- ILSNAGASH.scr:61
    do return mm9.gotoLabel(script, ctx, "InitBase") end -- ILSNAGASH.scr:62
    do return ctx:exit("") end -- ILSNAGASH.scr:63
end

script.labels["OnTurn"] = function(ctx)
    -- ILSNAGASH.scr:67
    ctx:self():loopAnimation("walk", 0) -- ILSNAGASH.scr:70
    ctx:self():rotate(0, 1, 0, 180, 40) -- ILSNAGASH.scr:71
    do return ctx:exit("") end -- ILSNAGASH.scr:73
end

script.labels["Nav1"] = function(ctx)
    -- ILSNAGASH.scr:76
    if ctx:condition("Aware==True") then -- ILSNAGASH.scr:79
        do return mm9.gotoLabel(script, ctx, "OnAware") end -- ILSNAGASH.scr:80
        do return ctx:exit("") end -- ILSNAGASH.scr:81
    end -- ILSNAGASH.scr:82
    ctx:state().g_hobject = ctx:objectOrNil("nav1") -- ILSNAGASH.scr:85
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget1") -- ILSNAGASH.scr:86
    do return ctx:exit("") end -- ILSNAGASH.scr:87
end

script.labels["Fidget1"] = function(ctx)
    -- ILSNAGASH.scr:91
    -- Playanim fidget2
    ctx:wait(3, 3, "nav2") -- ILSNAGASH.scr:96
    do return ctx:exit("") end -- ILSNAGASH.scr:98
end

script.labels["Nav2"] = function(ctx)
    -- ILSNAGASH.scr:102
    ctx:state().g_hobject = ctx:objectOrNil("nav2") -- ILSNAGASH.scr:105
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget2") -- ILSNAGASH.scr:107
    do return ctx:exit("") end -- ILSNAGASH.scr:108
end

script.labels["Fidget2"] = function(ctx)
    -- ILSNAGASH.scr:111
    ctx:self():playAnimation("Threat") -- ILSNAGASH.scr:115
    ctx:wait(3, 3, "nav3") -- ILSNAGASH.scr:116
    do return ctx:exit("") end -- ILSNAGASH.scr:118
end

script.labels["Nav3"] = function(ctx)
    -- ILSNAGASH.scr:121
    ctx:state().g_hobject = ctx:objectOrNil("nav3") -- ILSNAGASH.scr:124
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget3") -- ILSNAGASH.scr:126
    do return ctx:exit("") end -- ILSNAGASH.scr:127
end

script.labels["Fidget3"] = function(ctx)
    -- ILSNAGASH.scr:131
    ctx:state().g_hobject = ctx:objectOrNil("RotatingDoor69") -- ILSNAGASH.scr:136
    ctx:self():faceObject(ctx:object("g_hobject"), 30, "OpenDoor1") -- ILSNAGASH.scr:137
    do return ctx:exit("") end -- ILSNAGASH.scr:139
end

script.labels["OpenDoor1"] = function(ctx)
    -- ILSNAGASH.scr:143
    ctx:self():playAnimation("HAttack1") -- ILSNAGASH.scr:146
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:147
    ctx:wait(3, 3, "nav4") -- ILSNAGASH.scr:148
    do return ctx:exit("") end -- ILSNAGASH.scr:150
end

script.labels["Nav4"] = function(ctx)
    -- ILSNAGASH.scr:154
    ctx:state().g_hobject = ctx:objectOrNil("nav4") -- ILSNAGASH.scr:157
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget4") -- ILSNAGASH.scr:159
    do return ctx:exit("") end -- ILSNAGASH.scr:160
end

script.labels["Fidget4"] = function(ctx)
    -- ILSNAGASH.scr:164
    ctx:self():playAnimation("Threat") -- ILSNAGASH.scr:168
    ctx:wait(3, 3, "nav5") -- ILSNAGASH.scr:169
    do return ctx:exit("") end -- ILSNAGASH.scr:171
end

script.labels["Nav5"] = function(ctx)
    -- ILSNAGASH.scr:174
    ctx:state().g_hobject = ctx:objectOrNil("nav5") -- ILSNAGASH.scr:177
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget5") -- ILSNAGASH.scr:179
    do return ctx:exit("") end -- ILSNAGASH.scr:180
end

script.labels["Fidget5"] = function(ctx)
    -- ILSNAGASH.scr:183
    ctx:state().g_hobject = ctx:objectOrNil("RotatingDoor68") -- ILSNAGASH.scr:188
    ctx:self():faceObject(ctx:object("g_hobject"), 60, "OpenDoor2") -- ILSNAGASH.scr:189
    do return ctx:exit("") end -- ILSNAGASH.scr:191
end

script.labels["OpenDoor2"] = function(ctx)
    -- ILSNAGASH.scr:195
    ctx:self():playAnimation("HAttack1") -- ILSNAGASH.scr:198
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:199
    ctx:wait(3, 3, "nav6") -- ILSNAGASH.scr:200
    do return ctx:exit("") end -- ILSNAGASH.scr:202
end

script.labels["Nav6"] = function(ctx)
    -- ILSNAGASH.scr:207
    ctx:state().g_hobject = ctx:objectOrNil("nav6") -- ILSNAGASH.scr:210
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget6") -- ILSNAGASH.scr:212
    do return ctx:exit("") end -- ILSNAGASH.scr:213
end

script.labels["Fidget6"] = function(ctx)
    -- ILSNAGASH.scr:217
    ctx:self():playAnimation("Threat") -- ILSNAGASH.scr:221
    ctx:wait(3, 3, "nav7") -- ILSNAGASH.scr:222
    do return ctx:exit("") end -- ILSNAGASH.scr:224
end

script.labels["Nav7"] = function(ctx)
    -- ILSNAGASH.scr:228
    ctx:state().g_hobject = ctx:objectOrNil("nav7") -- ILSNAGASH.scr:231
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "Fidget7") -- ILSNAGASH.scr:233
    do return ctx:exit("") end -- ILSNAGASH.scr:234
end

script.labels["Fidget7"] = function(ctx)
    -- ILSNAGASH.scr:238
    ctx:wait(3, 3, "nav1") -- ILSNAGASH.scr:243
    do return ctx:exit("") end -- ILSNAGASH.scr:245
end

script.labels["Stuck"] = function(ctx)
    -- ILSNAGASH.scr:249
    ctx:object("RotatingDoor68"):trigger("use") -- ILSNAGASH.scr:252-253
    ctx:object("RotatingDoor69"):trigger("use") -- ILSNAGASH.scr:254-255
    ctx:wait(3, 3, "stucknav") -- ILSNAGASH.scr:256
end

script.labels["Stucknav"] = function(ctx)
    -- ILSNAGASH.scr:259
    ctx:state().g_hobject = ctx:objectOrNil("stucknav") -- ILSNAGASH.scr:264
    ctx:self():walkTo(ctx:object("g_hobject"), 32, "nav1") -- ILSNAGASH.scr:266
    do return ctx:exit("") end -- ILSNAGASH.scr:267
end

script.labels["Main"] = function(ctx)
    -- ILSNAGASH.scr:270
    -- TRACEON
    ctx:state().Aware = false -- ILSNAGASH.scr:275
    ctx:onEvent("OnStuck", "Stuck") -- ILSNAGASH.scr:276
    ctx:addTrigger("Aware", "OnAware") -- ILSNAGASH.scr:277
    ctx:onEvent("OnDamage", "") -- ILSNAGASH.scr:278
    ctx:wait(2, 2, "nav1") -- ILSNAGASH.scr:279
    do return ctx:exit("") end -- ILSNAGASH.scr:281
end

return script
