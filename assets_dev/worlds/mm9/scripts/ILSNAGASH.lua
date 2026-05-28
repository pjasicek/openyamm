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
    ctx:command("set", "Aware, True") -- ILSNAGASH.scr:27
    if ctx:condition("Lever==true") then -- ILSNAGASH.scr:28
        do return mm9.gotoLabel(script, ctx, "InitBase") end -- ILSNAGASH.scr:29
        do return ctx:exit("") end -- ILSNAGASH.scr:30
    end -- ILSNAGASH.scr:31
    ctx:command("wait", "2, Awarestart") -- ILSNAGASH.scr:33
end

script.labels["AwareStart"] = function(ctx)
    -- ILSNAGASH.scr:36
    ctx:command("getobjecthandle", "RotatingDoor68, g_hobject") -- ILSNAGASH.scr:40
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:41
    ctx:command("getobjecthandle", "RotatingDoor69, g_hobject") -- ILSNAGASH.scr:42
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:43
    ctx:command("getobjecthandle", "Switch0, g_hobject") -- ILSNAGASH.scr:44
    ctx:command("runto", "g_hobject 32 Alert") -- ILSNAGASH.scr:45
    do return ctx:exit("") end -- ILSNAGASH.scr:46
end

script.labels["Alert"] = function(ctx)
    -- ILSNAGASH.scr:49
    ctx:command("getobjecthandle", "Switch0, g_hobject") -- ILSNAGASH.scr:52
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:53
    ctx:command("wait", "3, Startfight") -- ILSNAGASH.scr:54
end

script.labels["Startfight"] = function(ctx)
    -- ILSNAGASH.scr:57
    ctx:command("set", "Lever, True") -- ILSNAGASH.scr:61
    do return mm9.gotoLabel(script, ctx, "InitBase") end -- ILSNAGASH.scr:62
    do return ctx:exit("") end -- ILSNAGASH.scr:63
end

script.labels["OnTurn"] = function(ctx)
    -- ILSNAGASH.scr:67
    ctx:command("loopanim", "walk 0") -- ILSNAGASH.scr:70
    ctx:command("rotate", "0, 1, 0, 180, 40") -- ILSNAGASH.scr:71
    do return ctx:exit("") end -- ILSNAGASH.scr:73
end

script.labels["Nav1"] = function(ctx)
    -- ILSNAGASH.scr:76
    if ctx:condition("Aware==True") then -- ILSNAGASH.scr:79
        do return mm9.gotoLabel(script, ctx, "OnAware") end -- ILSNAGASH.scr:80
        do return ctx:exit("") end -- ILSNAGASH.scr:81
    end -- ILSNAGASH.scr:82
    ctx:command("getobjecthandle", "nav1, g_hobject") -- ILSNAGASH.scr:85
    ctx:command("walkto", "g_hobject 32 Fidget1") -- ILSNAGASH.scr:86
    do return ctx:exit("") end -- ILSNAGASH.scr:87
end

script.labels["Fidget1"] = function(ctx)
    -- ILSNAGASH.scr:91
    -- Playanim fidget2
    ctx:command("wait", "3, nav2") -- ILSNAGASH.scr:96
    do return ctx:exit("") end -- ILSNAGASH.scr:98
end

script.labels["Nav2"] = function(ctx)
    -- ILSNAGASH.scr:102
    ctx:command("getobjecthandle", "nav2, g_hobject") -- ILSNAGASH.scr:105
    ctx:command("walkto", "g_hobject 32 Fidget2") -- ILSNAGASH.scr:107
    do return ctx:exit("") end -- ILSNAGASH.scr:108
end

script.labels["Fidget2"] = function(ctx)
    -- ILSNAGASH.scr:111
    ctx:command("playanim", "Threat") -- ILSNAGASH.scr:115
    ctx:command("wait", "3, nav3") -- ILSNAGASH.scr:116
    do return ctx:exit("") end -- ILSNAGASH.scr:118
end

script.labels["Nav3"] = function(ctx)
    -- ILSNAGASH.scr:121
    ctx:command("getobjecthandle", "nav3, g_hobject") -- ILSNAGASH.scr:124
    ctx:command("walkto", "g_hobject 32 Fidget3") -- ILSNAGASH.scr:126
    do return ctx:exit("") end -- ILSNAGASH.scr:127
end

script.labels["Fidget3"] = function(ctx)
    -- ILSNAGASH.scr:131
    ctx:command("getobjecthandle", "RotatingDoor69, g_hobject") -- ILSNAGASH.scr:136
    ctx:command("faceobject", "g_hobject, 30, OpenDoor1") -- ILSNAGASH.scr:137
    do return ctx:exit("") end -- ILSNAGASH.scr:139
end

script.labels["OpenDoor1"] = function(ctx)
    -- ILSNAGASH.scr:143
    ctx:command("playanim", "HAttack1") -- ILSNAGASH.scr:146
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:147
    ctx:command("wait", "3, nav4") -- ILSNAGASH.scr:148
    do return ctx:exit("") end -- ILSNAGASH.scr:150
end

script.labels["Nav4"] = function(ctx)
    -- ILSNAGASH.scr:154
    ctx:command("getobjecthandle", "nav4, g_hobject") -- ILSNAGASH.scr:157
    ctx:command("walkto", "g_hobject 32 Fidget4") -- ILSNAGASH.scr:159
    do return ctx:exit("") end -- ILSNAGASH.scr:160
end

script.labels["Fidget4"] = function(ctx)
    -- ILSNAGASH.scr:164
    ctx:command("playanim", "Threat") -- ILSNAGASH.scr:168
    ctx:command("wait", "3, nav5") -- ILSNAGASH.scr:169
    do return ctx:exit("") end -- ILSNAGASH.scr:171
end

script.labels["Nav5"] = function(ctx)
    -- ILSNAGASH.scr:174
    ctx:command("getobjecthandle", "nav5, g_hobject") -- ILSNAGASH.scr:177
    ctx:command("walkto", "g_hobject 32 Fidget5") -- ILSNAGASH.scr:179
    do return ctx:exit("") end -- ILSNAGASH.scr:180
end

script.labels["Fidget5"] = function(ctx)
    -- ILSNAGASH.scr:183
    ctx:command("getobjecthandle", "RotatingDoor68, g_hobject") -- ILSNAGASH.scr:188
    ctx:command("faceobject", "g_hobject, 60, OpenDoor2") -- ILSNAGASH.scr:189
    do return ctx:exit("") end -- ILSNAGASH.scr:191
end

script.labels["OpenDoor2"] = function(ctx)
    -- ILSNAGASH.scr:195
    ctx:command("playanim", "HAttack1") -- ILSNAGASH.scr:198
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:199
    ctx:command("wait", "3, nav6") -- ILSNAGASH.scr:200
    do return ctx:exit("") end -- ILSNAGASH.scr:202
end

script.labels["Nav6"] = function(ctx)
    -- ILSNAGASH.scr:207
    ctx:command("getobjecthandle", "nav6, g_hobject") -- ILSNAGASH.scr:210
    ctx:command("walkto", "g_hobject 32 Fidget6") -- ILSNAGASH.scr:212
    do return ctx:exit("") end -- ILSNAGASH.scr:213
end

script.labels["Fidget6"] = function(ctx)
    -- ILSNAGASH.scr:217
    ctx:command("playanim", "Threat") -- ILSNAGASH.scr:221
    ctx:command("wait", "3, nav7") -- ILSNAGASH.scr:222
    do return ctx:exit("") end -- ILSNAGASH.scr:224
end

script.labels["Nav7"] = function(ctx)
    -- ILSNAGASH.scr:228
    ctx:command("getobjecthandle", "nav7, g_hobject") -- ILSNAGASH.scr:231
    ctx:command("walkto", "g_hobject 32 Fidget7") -- ILSNAGASH.scr:233
    do return ctx:exit("") end -- ILSNAGASH.scr:234
end

script.labels["Fidget7"] = function(ctx)
    -- ILSNAGASH.scr:238
    ctx:command("wait", "3, nav1") -- ILSNAGASH.scr:243
    do return ctx:exit("") end -- ILSNAGASH.scr:245
end

script.labels["Stuck"] = function(ctx)
    -- ILSNAGASH.scr:249
    ctx:command("getobjecthandle", "RotatingDoor68, g_hobject") -- ILSNAGASH.scr:252
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:253
    ctx:command("getobjecthandle", "RotatingDoor69, g_hobject") -- ILSNAGASH.scr:254
    ctx:trigger("g_hobject", "use") -- ILSNAGASH.scr:255
    ctx:command("wait", "3, stucknav") -- ILSNAGASH.scr:256
end

script.labels["Stucknav"] = function(ctx)
    -- ILSNAGASH.scr:259
    ctx:command("getobjecthandle", "stucknav, g_hobject") -- ILSNAGASH.scr:264
    ctx:command("walkto", "g_hobject 32 nav1") -- ILSNAGASH.scr:266
    do return ctx:exit("") end -- ILSNAGASH.scr:267
end

script.labels["Main"] = function(ctx)
    -- ILSNAGASH.scr:270
    -- TRACEON
    ctx:command("set", "Aware, False") -- ILSNAGASH.scr:275
    ctx:command("onstuck", "Stuck") -- ILSNAGASH.scr:276
    ctx:addTrigger("Aware", "OnAware") -- ILSNAGASH.scr:277
    ctx:command("ondamage", ", OnAware") -- ILSNAGASH.scr:278
    ctx:command("wait", "2, nav1") -- ILSNAGASH.scr:279
    do return ctx:exit("") end -- ILSNAGASH.scr:281
end

return script
