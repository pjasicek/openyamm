-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WORKINGMONKMOD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "MonkHostility.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }
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
    -- WORKINGMONKMOD.scr:37
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:40
end

script.labels["OnUse"] = function(ctx)
    -- WORKINGMONKMOD.scr:43
    if ctx:condition("NPC_ID!=0") then -- WORKINGMONKMOD.scr:46
        ctx:state().Talking = true -- WORKINGMONKMOD.scr:47
        ctx:self():stop() -- WORKINGMONKMOD.scr:48
        mm9.gosub(script, ctx, "BasewanderStop") -- WORKINGMONKMOD.scr:49
        ctx:self():getCurrentAnimation("g_ntemp") -- WORKINGMONKMOD.scr:51
        ctx:self():getAnimationName("g_ntemp", "g_stemp") -- WORKINGMONKMOD.scr:52
        -- cprint g_stemp
        -- if (g_stemp==Monk_Anim)
        ctx:self():playAnimation("Fidget_Name", "FidgetStand") -- WORKINGMONKMOD.scr:55
        -- endif
        ctx:getParam(0, "g_hobject") -- WORKINGMONKMOD.scr:57
        ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- WORKINGMONKMOD.scr:58
        ctx:self():pauseWait(-1) -- WORKINGMONKMOD.scr:59
        ctx:doRude("NPC_ID") -- WORKINGMONKMOD.scr:60
        do return ctx:exit("TRUE") end -- WORKINGMONKMOD.scr:61
    end -- WORKINGMONKMOD.scr:62
    do return ctx:exit("TRUE") end -- WORKINGMONKMOD.scr:64
end

script.labels["FidgetStand"] = function(ctx)
    -- WORKINGMONKMOD.scr:68
    ctx:self():loopAnimation("Fidget_Stand", 0, "Donothing") -- WORKINGMONKMOD.scr:72
    do return ctx:exit("TRUE") end -- WORKINGMONKMOD.scr:74
end

script.labels["OnRude"] = function(ctx)
    -- WORKINGMONKMOD.scr:77
    ctx:self():resumeWait(-1) -- WORKINGMONKMOD.scr:81
    ctx:state().talking = false -- WORKINGMONKMOD.scr:82
    ctx:state().g_hobject2 = ctx:objectOrNil("Face_Object") -- WORKINGMONKMOD.scr:83
    if ctx:condition("g_hobject2!=0") then -- WORKINGMONKMOD.scr:85
        ctx:self():faceObject(ctx:object("g_hobject2"), 200, "DoNothing") -- WORKINGMONKMOD.scr:86
    end -- WORKINGMONKMOD.scr:87
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- WORKINGMONKMOD.scr:89
    if ctx:condition("bWanderEnabled==TRUE") then -- WORKINGMONKMOD.scr:91
        mm9.gosub(script, ctx, "Basewanderstart") -- WORKINGMONKMOD.scr:92
        do return ctx:exit("") end -- WORKINGMONKMOD.scr:93
    end -- WORKINGMONKMOD.scr:94
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:96
end

script.labels["OnTurnedHostile"] = function(ctx)
    -- WORKINGMONKMOD.scr:100
    ctx:self():detachProp(ctx:object("g_hobject2"), "false") -- WORKINGMONKMOD.scr:104
    ctx:object("g_hobject2"):remove() -- WORKINGMONKMOD.scr:105
    ctx:state().Attacked = true -- WORKINGMONKMOD.scr:106
    mm9.gosub(script, ctx, "BaseInit") -- WORKINGMONKMOD.scr:107
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:109
end

script.labels["SetupWork"] = function(ctx)
    -- WORKINGMONKMOD.scr:112
    ctx:self():attachProp("Prop_Name", "Skin_Name", "Socket_Name", ctx:object("g_hobject2")) -- WORKINGMONKMOD.scr:114
    ctx:state().Working = true -- WORKINGMONKMOD.scr:115
    ctx:self():loopAnimation("Fidget_Stand", 0, "Donothing") -- WORKINGMONKMOD.scr:117
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:119
end

script.labels["StartWork"] = function(ctx)
    -- WORKINGMONKMOD.scr:122
    ctx:randomInt(1, 10, "g_ntemp") -- WORKINGMONKMOD.scr:125
    ctx:wait(1, "g_ntemp", "OnWorkStart") -- WORKINGMONKMOD.scr:126
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:127
end

script.labels["OnWorkStart"] = function(ctx)
    -- WORKINGMONKMOD.scr:130
    ctx:state().Working = true -- WORKINGMONKMOD.scr:133
    ctx:wait(1, 500, "Rest") -- WORKINGMONKMOD.scr:134
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- WORKINGMONKMOD.scr:135
    mm9.gosub(script, ctx, "BaseWanderInit") -- WORKINGMONKMOD.scr:137
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:139
end

script.labels["Rest"] = function(ctx)
    -- WORKINGMONKMOD.scr:142
    ctx:self():playAnimation("Fidget_Name", "StartWork") -- WORKINGMONKMOD.scr:145
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:146
end

script.labels["BaseWanderGo"] = function(ctx)
    -- WORKINGMONKMOD.scr:149
    ctx:self():playAnimation("Fidget_Name", "WanderGo") -- WORKINGMONKMOD.scr:152
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:153
end

script.labels["WanderGo"] = function(ctx)
    -- WORKINGMONKMOD.scr:156
    ctx:self():loopAnimation("Fidget_Stand", 0, "Donothing") -- WORKINGMONKMOD.scr:159
    if ctx:condition("Talking==FALSE") then -- WORKINGMONKMOD.scr:160
        mm9.gosub(script, ctx, "BaseWanderGo") -- WORKINGMONKMOD.scr:161
        do return ctx:exit("") end -- WORKINGMONKMOD.scr:162
    end -- WORKINGMONKMOD.scr:163
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:164
end

script.labels["BaseWanderStopTick"] = function(ctx)
    -- WORKINGMONKMOD.scr:167
    ctx:wait("WANDER_LEASH_WAIT", 0, "DoNothing") -- WORKINGMONKMOD.scr:170
    ctx:self():stop() -- WORKINGMONKMOD.scr:171
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- WORKINGMONKMOD.scr:172
    mm9.gosub(script, ctx, "BaseWanderStart") -- WORKINGMONKMOD.scr:173
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:175
end

script.labels["BaseWanderObstacle"] = function(ctx)
    -- WORKINGMONKMOD.scr:178
    if ctx:condition("hCurrentMarker!=0") then -- WORKINGMONKMOD.scr:180
        do return ctx:exit("FALSE") end -- WORKINGMONKMOD.scr:181
    end -- WORKINGMONKMOD.scr:182
    ctx:randomInt(0, 100, "g_nRandom") -- WORKINGMONKMOD.scr:184
    ctx:getParam(0, "g_hObject") -- WORKINGMONKMOD.scr:186
    ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("Actor") -- WORKINGMONKMOD.scr:187
    if ctx:condition("g_bTemp==TRUE") then -- WORKINGMONKMOD.scr:189
        if ctx:condition("g_nRandom < 90") then -- WORKINGMONKMOD.scr:190
            do return ctx:exit("FALSE") end -- WORKINGMONKMOD.scr:191
        end -- WORKINGMONKMOD.scr:192
    else -- WORKINGMONKMOD.scr:193
        if ctx:condition("g_nRandom < 70") then -- WORKINGMONKMOD.scr:194
            do return ctx:exit("FALSE") end -- WORKINGMONKMOD.scr:195
        end -- WORKINGMONKMOD.scr:196
    end -- WORKINGMONKMOD.scr:197
    ctx:getParam(1, "normalX") -- WORKINGMONKMOD.scr:199
    ctx:getParam(2, "normalY") -- WORKINGMONKMOD.scr:200
    ctx:getParam(3, "normalZ") -- WORKINGMONKMOD.scr:201
    mm9.gosub(script, ctx, "BaseWanderPause") -- WORKINGMONKMOD.scr:203
    ctx:self():stop() -- WORKINGMONKMOD.scr:204
    ctx:self():loopAnimation("Monk_Anim", 0, "Donothing") -- WORKINGMONKMOD.scr:205
    ctx:wait("WANDER_LEASH_WAIT", 0, "DoNothing") -- WORKINGMONKMOD.scr:206
    ctx:state().bObstacle = true -- WORKINGMONKMOD.scr:207
    mm9.gosub(script, ctx, "BaseWanderResume") -- WORKINGMONKMOD.scr:208
    ctx:getParam(0, "g_hObject") -- WORKINGMONKMOD.scr:210
    ctx:state().g_bTemp = ctx:object("g_hObject"):isClass("Actor") -- WORKINGMONKMOD.scr:211
    if ctx:condition("g_bTemp==FALSE") then -- WORKINGMONKMOD.scr:212
        ctx:self():faceDir("normalX", 0, "normalZ", 360) -- WORKINGMONKMOD.scr:213
    end -- WORKINGMONKMOD.scr:214
    do return ctx:exit("TRUE") end -- WORKINGMONKMOD.scr:217
end

script.labels["WorkInit"] = function(ctx)
    -- WORKINGMONKMOD.scr:220
    if ctx:condition("Monk_Anim==Hoe") then -- WORKINGMONKMOD.scr:223
        ctx:set("Prop_Name", "MonkHoe.ABC") -- WORKINGMONKMOD.scr:224
        ctx:set("Skin_Name", "MonkHoe.dtx") -- WORKINGMONKMOD.scr:225
        ctx:set("Socket_Name", "Hoe") -- WORKINGMONKMOD.scr:226
        ctx:set("Fidget_Name", "HoeFidget") -- WORKINGMONKMOD.scr:227
        ctx:set("Fidget_Stand", "Hoewait") -- WORKINGMONKMOD.scr:228
        do return ctx:exit("") end -- WORKINGMONKMOD.scr:229
    end -- WORKINGMONKMOD.scr:230
    if ctx:condition("Monk_Anim==Sweep") then -- WORKINGMONKMOD.scr:232
        ctx:set("Prop_Name", "MonkBroom.ABC") -- WORKINGMONKMOD.scr:233
        ctx:set("Skin_Name", "MonkBroom.dtx") -- WORKINGMONKMOD.scr:234
        ctx:set("Socket_Name", "Broom") -- WORKINGMONKMOD.scr:235
        ctx:set("Fidget_Name", "sweepfidget") -- WORKINGMONKMOD.scr:236
        ctx:set("Fidget_Stand", "Sweepwait") -- WORKINGMONKMOD.scr:237
        do return ctx:exit("") end -- WORKINGMONKMOD.scr:238
    end -- WORKINGMONKMOD.scr:239
    if ctx:condition("Monk_Anim==Hammer") then -- WORKINGMONKMOD.scr:241
        ctx:set("Prop_Name", "MonkHammer.ABC") -- WORKINGMONKMOD.scr:242
        ctx:set("Skin_Name", "MonkHammer.dtx") -- WORKINGMONKMOD.scr:243
        ctx:set("Socket_Name", "Hammer") -- WORKINGMONKMOD.scr:244
        ctx:set("Fidget_Name", "HammerFidget") -- WORKINGMONKMOD.scr:245
        ctx:set("Fidget_Stand", "Hammerwait") -- WORKINGMONKMOD.scr:246
        do return ctx:exit("") end -- WORKINGMONKMOD.scr:247
    end -- WORKINGMONKMOD.scr:248
    if ctx:condition("Monk_Anim==Wash") then -- WORKINGMONKMOD.scr:250
        ctx:set("Prop_Name", "MonkCloth.ABC") -- WORKINGMONKMOD.scr:251
        ctx:set("Skin_Name", "MonkCloth.dtx") -- WORKINGMONKMOD.scr:252
        ctx:set("Socket_Name", "Cloth") -- WORKINGMONKMOD.scr:253
        ctx:set("Fidget_Name", "WashFidget") -- WORKINGMONKMOD.scr:254
        ctx:set("Fidget_Stand", "WashWait") -- WORKINGMONKMOD.scr:255
        do return ctx:exit("") end -- WORKINGMONKMOD.scr:256
    end -- WORKINGMONKMOD.scr:257
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:259
end

script.labels["Init"] = function(ctx)
    -- WORKINGMONKMOD.scr:263
    mm9.gosub(script, ctx, "WorkInit") -- WORKINGMONKMOD.scr:266
    mm9.gosub(script, ctx, "SetupWork") -- WORKINGMONKMOD.scr:267
    mm9.gosub(script, ctx, "StartWork") -- WORKINGMONKMOD.scr:268
    mm9.gosub(script, ctx, "MS_Init") -- WORKINGMONKMOD.scr:269
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:271
end

script.labels["Main"] = function(ctx)
    -- WORKINGMONKMOD.scr:274
    -- TraceON
    ctx:getParam(0, "Monk_Anim") -- WORKINGMONKMOD.scr:279
    ctx:getParam(1, "NPC_ID") -- WORKINGMONKMOD.scr:280
    ctx:getParam(2, "Face_Object") -- WORKINGMONKMOD.scr:281
    ctx:getParam(3, "bSoundOn") -- WORKINGMONKMOD.scr:282
    ctx:addTrigger("Use", "Onuse") -- WORKINGMONKMOD.scr:283
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- WORKINGMONKMOD.scr:284
    ctx:onEvent("OnPostStartWorld", "Init") -- WORKINGMONKMOD.scr:285
    -- jsl-->OnPostMiniSaveLoad Init
    -- jsl-->OnPostSaveLoad Init
    ctx:wait(1, .1, "Init") -- WORKINGMONKMOD.scr:288
    ctx:wait(0, 5, "InitMonkHostility") -- WORKINGMONKMOD.scr:289
    do return ctx:exit("") end -- WORKINGMONKMOD.scr:290
end

return script
