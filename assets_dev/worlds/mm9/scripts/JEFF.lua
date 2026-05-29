-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "JEFF.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Monksounds.inc" }

-- WorkingMonk.scr
-- timmy
-- Makes Monks play working animations
-- 10/23
-- parameters:
-- p0 the name of the animation to play
-- p1 number of NPC to do
-- p2 the name of the object to face after completing dialog
script.labels["DoRUDEAnim"] = function(ctx)
    -- JEFF.scr:37
    do return ctx:exit("") end -- JEFF.scr:40
end

script.labels["OnUse"] = function(ctx)
    -- JEFF.scr:43
    if ctx:condition("NPC_ID!=NULL") then -- JEFF.scr:46
        ctx:state().Talking = true -- JEFF.scr:47
        ctx:self():stop() -- JEFF.scr:48
        mm9.gosub(script, ctx, "BasewanderStop") -- JEFF.scr:49
        ctx:self():getCurrentAnimation("g_ntemp") -- JEFF.scr:51
        ctx:self():getAnimationName("g_ntemp", "g_stemp") -- JEFF.scr:52
        -- cprint g_stemp
        -- if (g_stemp==Monk_Anim)
        ctx:self():playAnimation("Fidget_Name", "FidgetStand") -- JEFF.scr:55
        -- endif
        ctx:getParam(0, "g_hobject") -- JEFF.scr:57
        ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- JEFF.scr:58
        ctx:self():pauseWait(-1) -- JEFF.scr:59
        ctx:doRude("NPC_ID") -- JEFF.scr:60
        do return ctx:exit("TRUE") end -- JEFF.scr:61
    end -- JEFF.scr:62
    do return ctx:exit("TRUE") end -- JEFF.scr:64
end

script.labels["FidgetStand"] = function(ctx)
    -- JEFF.scr:68
    ctx:self():loopAnimation("Fidget_Stand", 0, "Donothing") -- JEFF.scr:72
    do return ctx:exit("") end -- JEFF.scr:74
end

script.labels["OnRude"] = function(ctx)
    -- JEFF.scr:77
    ctx:self():resumeWait(-1) -- JEFF.scr:81
    ctx:state().talking = false -- JEFF.scr:82
    ctx:state().g_hobject2 = ctx:objectOrNil("Face_Object") -- JEFF.scr:83
    if ctx:condition("g_hobject2!=NULL") then -- JEFF.scr:85
        ctx:self():faceObject(ctx:object("g_hobject2"), 200, "DoNothing") -- JEFF.scr:86
    end -- JEFF.scr:87
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- JEFF.scr:89
    if ctx:condition("bWanderEnabled==TRUE") then -- JEFF.scr:91
        mm9.gosub(script, ctx, "Basewanderstart") -- JEFF.scr:92
        do return ctx:exit("") end -- JEFF.scr:93
    end -- JEFF.scr:94
    do return ctx:exit("") end -- JEFF.scr:96
end

script.labels["OnDamage"] = function(ctx)
    -- JEFF.scr:100
    ctx:self():detachProp(ctx:object("g_hobject2"), "false") -- JEFF.scr:104
    ctx:object("g_hobject2"):remove() -- JEFF.scr:105
    ctx:state().Attacked = true -- JEFF.scr:106
    mm9.gosub(script, ctx, "BaseInit") -- JEFF.scr:107
    do return ctx:exit("") end -- JEFF.scr:109
end

script.labels["SetupWork"] = function(ctx)
    -- JEFF.scr:112
    ctx:self():attachProp("Prop_Name", "Skin_Name", "Socket_Name", ctx:object("g_hobject2")) -- JEFF.scr:114
    ctx:state().Working = true -- JEFF.scr:115
    ctx:self():loopAnimation("Fidget_Stand", 0, "Donothing") -- JEFF.scr:117
    do return ctx:exit("") end -- JEFF.scr:119
end

script.labels["StartWork"] = function(ctx)
    -- JEFF.scr:122
    ctx:randomInt(1, 10, "g_ntemp") -- JEFF.scr:125
    ctx:wait(1, "g_ntemp", "OnWorkStart") -- JEFF.scr:126
    do return ctx:exit("") end -- JEFF.scr:127
end

script.labels["OnWorkStart"] = function(ctx)
    -- JEFF.scr:130
    ctx:state().Working = true -- JEFF.scr:133
    ctx:wait(1, 500, "Rest") -- JEFF.scr:134
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- JEFF.scr:135
    mm9.gosub(script, ctx, "BaseWanderInit") -- JEFF.scr:137
    do return ctx:exit("") end -- JEFF.scr:139
end

script.labels["Rest"] = function(ctx)
    -- JEFF.scr:142
    ctx:self():playAnimation("Fidget_Name", "StartWork") -- JEFF.scr:145
    do return ctx:exit("") end -- JEFF.scr:146
end

script.labels["BaseWanderGo"] = function(ctx)
    -- JEFF.scr:149
    ctx:self():playAnimation("Fidget_Name", "WanderGo") -- JEFF.scr:152
    do return ctx:exit("") end -- JEFF.scr:153
end

script.labels["WanderGo"] = function(ctx)
    -- JEFF.scr:156
    ctx:self():loopAnimation("Fidget_Stand", 0, "Donothing") -- JEFF.scr:159
    if ctx:condition("Talking==FALSE") then -- JEFF.scr:160
        mm9.gosub(script, ctx, "BaseWanderGo") -- JEFF.scr:161
        do return ctx:exit("") end -- JEFF.scr:162
    end -- JEFF.scr:163
    do return ctx:exit("") end -- JEFF.scr:164
end

script.labels["BaseWanderStopTick"] = function(ctx)
    -- JEFF.scr:167
    mm9.gosub(script, ctx, "BaseWanderStopTick") -- JEFF.scr:170
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- JEFF.scr:172
    do return ctx:exit("") end -- JEFF.scr:174
end

script.labels["WorkInit"] = function(ctx)
    -- JEFF.scr:177
    if ctx:condition("Monk_Anim==Hoe") then -- JEFF.scr:180
        ctx:set("Prop_Name", "MonkHoe.ABC") -- JEFF.scr:181
        ctx:set("Skin_Name", "MonkHoe.dtx") -- JEFF.scr:182
        ctx:set("Socket_Name", "Hoe") -- JEFF.scr:183
        ctx:set("Fidget_Name", "HoeFidget") -- JEFF.scr:184
        ctx:set("Fidget_Stand", "Hoewait") -- JEFF.scr:185
        do return ctx:exit("") end -- JEFF.scr:186
    end -- JEFF.scr:187
    if ctx:condition("Monk_Anim==Sweep") then -- JEFF.scr:189
        ctx:set("Prop_Name", "MonkBroom.ABC") -- JEFF.scr:190
        ctx:set("Skin_Name", "MonkBroom.dtx") -- JEFF.scr:191
        ctx:set("Socket_Name", "Broom") -- JEFF.scr:192
        ctx:set("Fidget_Name", "sweepfidget") -- JEFF.scr:193
        ctx:set("Fidget_Stand", "Sweepwait") -- JEFF.scr:194
        do return ctx:exit("") end -- JEFF.scr:195
    end -- JEFF.scr:196
    if ctx:condition("Monk_Anim==Hammer") then -- JEFF.scr:198
        ctx:set("Prop_Name", "MonkHammer.ABC") -- JEFF.scr:199
        ctx:set("Skin_Name", "MonkHammer.dtx") -- JEFF.scr:200
        ctx:set("Socket_Name", "Hammer") -- JEFF.scr:201
        ctx:set("Fidget_Name", "HammerFidget") -- JEFF.scr:202
        ctx:set("Fidget_Stand", "Hammerwait") -- JEFF.scr:203
        do return ctx:exit("") end -- JEFF.scr:204
    end -- JEFF.scr:205
    if ctx:condition("Monk_Anim==Wash") then -- JEFF.scr:207
        ctx:set("Prop_Name", "MonkCloth.ABC") -- JEFF.scr:208
        ctx:set("Skin_Name", "MonkCloth.dtx") -- JEFF.scr:209
        ctx:set("Socket_Name", "Cloth") -- JEFF.scr:210
        ctx:set("Fidget_Name", "WashFidget") -- JEFF.scr:211
        ctx:set("Fidget_Stand", "WashWait") -- JEFF.scr:212
        do return ctx:exit("") end -- JEFF.scr:213
    end -- JEFF.scr:214
    do return ctx:exit("") end -- JEFF.scr:216
end

script.labels["Init"] = function(ctx)
    -- JEFF.scr:220
    mm9.gosub(script, ctx, "WorkInit") -- JEFF.scr:223
    mm9.gosub(script, ctx, "SetupWork") -- JEFF.scr:224
    mm9.gosub(script, ctx, "StartWork") -- JEFF.scr:225
    mm9.gosub(script, ctx, "MS_Init") -- JEFF.scr:226
    do return ctx:exit("") end -- JEFF.scr:228
end

script.labels["Main"] = function(ctx)
    -- JEFF.scr:231
    -- TraceON
    ctx:getParam(0, "Monk_Anim") -- JEFF.scr:236
    ctx:getParam(1, "NPC_ID") -- JEFF.scr:237
    ctx:getParam(2, "Face_Object") -- JEFF.scr:238
    ctx:getParam(3, "bSoundOn") -- JEFF.scr:239
    ctx:addTrigger("Use", "Onuse") -- JEFF.scr:240
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- JEFF.scr:241
    ctx:onEvent("OnDamage", "OnDamage") -- JEFF.scr:242
    ctx:onEvent("OnPostStartWorld", "Init") -- JEFF.scr:243
    -- jsl-->OnPostMiniSaveLoad Init
    -- jsl-->OnPostSaveLoad Init
    ctx:wait(1, .1, "Init") -- JEFF.scr:246
    do return ctx:exit("") end -- JEFF.scr:247
end

return script
