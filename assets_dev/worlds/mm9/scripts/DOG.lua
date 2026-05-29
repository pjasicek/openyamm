-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOG.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 17, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 18, path = "baseWander.inc" }

-- Dog.Scr
-- Jeff Leggett
-- 08/03/2001
-- Behavior:
-- - go from actor to actor and hang out with them
-- - Search for cats.  If a cat appears, then we'll
-- go chase him until we are "tired".
-- - Follow the player for a while perhaps....
script.labels["DoNothing"] = function(ctx)
    -- DOG.scr:36
    do return ctx:exit("") end -- DOG.scr:39
end

script.labels["OnHangoutObstacle"] = function(ctx)
    -- DOG.scr:42
    mm9.gosub(script, ctx, "DoneHangingOut") -- DOG.scr:45
    do return ctx:exit("TRUE") end -- DOG.scr:47
end

script.labels["OnHangoutStuckDone"] = function(ctx)
    -- DOG.scr:50
    mm9.gosub(script, ctx, "DoneHangingOut") -- DOG.scr:53
    do return ctx:exit("TRUE") end -- DOG.scr:55
end

script.labels["DisableWandering"] = function(ctx)
    -- DOG.scr:59
    -- Do all things necessary to disable
    -- Wandering...
    mm9.gosub(script, ctx, "BaseWanderStop") -- DOG.scr:66
    ctx:onEvent("OnObstacle", "OnHangoutObstacle") -- DOG.scr:68
    ctx:onEvent("OnStuckDone", "OnHangoutStuckDone") -- DOG.scr:69
    ctx:onEvent("OnStuck") -- DOG.scr:70
    do return ctx:exit("") end -- DOG.scr:72
end

script.labels["LookForPerson"] = function(ctx)
    -- DOG.scr:75
    -- Just turn on the OnFoundPlayer again..
    ctx:onEvent("OnFoundTarget", "FoundTarget") -- DOG.scr:81
    do return ctx:exit("") end -- DOG.scr:83
end

script.labels["DoneHangingOut"] = function(ctx)
    -- DOG.scr:86
    -- Time to move on from this guy... (ie: stop following)
    -- Cancel out some timers...
    ctx:wait("HANGOUT_WAIT", 0, "DoNothing") -- DOG.scr:92
    ctx:wait("SITTING_WAIT", 0, "DoNothing") -- DOG.scr:93
    ctx:onEvent("OnTargetBeyondDist", 0, "DoNothing") -- DOG.scr:94
    ctx:state().g_hTarget = nil -- DOG.scr:96
    ctx:self():setTarget(nil) -- DOG.scr:97
    ctx:self():stop() -- DOG.scr:98
    mm9.gosub(script, ctx, "BaseWanderStart") -- DOG.scr:100
    ctx:onEvent("OnFoundTarget", "DoNothing") -- DOG.scr:102
    ctx:randomInt(10, 20, "g_nRandom") -- DOG.scr:104
    ctx:wait("HANGOUT_WAIT", "g_nRandom", "LookForPerson") -- DOG.scr:106
    do return ctx:exit("") end -- DOG.scr:108
end

script.labels["FoundTarget"] = function(ctx)
    -- DOG.scr:111
    -- Note: Target for cat is all NPCs and player.
    ctx:getParam(0, "g_hTarget") -- DOG.scr:117
    ctx:self():setTarget(ctx:object("g_hTarget")) -- DOG.scr:118
    mm9.gosub(script, ctx, "DisableWandering") -- DOG.scr:120
    ctx:self():walkTo(ctx:object("g_hTarget"), 0, "OnArrival") -- DOG.scr:122
    do return ctx:exit("") end -- DOG.scr:123
end

script.labels["OnArrival"] = function(ctx)
    -- DOG.scr:127
    ctx:randomFloat(8, 15, "g_nRandom") -- DOG.scr:130
    ctx:wait("HANGOUT_WAIT", "g_nRandom", "DoneHangingOut") -- DOG.scr:132
    ctx:self():stop() -- DOG.scr:133
    ctx:onEvent("OnTargetBeyondDist", 120, "GoAfterHim") -- DOG.scr:135
    ctx:self():loopAnimation("Sitting", 0) -- DOG.scr:137
    ctx:trigger("g_hTarget", "LookAtMe") -- DOG.scr:139
    do return ctx:exit("TRUE") end -- DOG.scr:141
end

script.labels["GoAfterHim"] = function(ctx)
    -- DOG.scr:144
    ctx:onEvent("OnTargetBeyondDist", 0) -- DOG.scr:147
    ctx:wait("SITTING_WAIT", 0, "DoNothing") -- DOG.scr:148
    ctx:self():stop() -- DOG.scr:150
    ctx:self():setIdle() -- DOG.scr:151
    ctx:self():walkTo(ctx:object("g_hTarget"), 0, "OnArrival") -- DOG.scr:153
    do return ctx:exit("") end -- DOG.scr:155
end

script.labels["CatArrival"] = function(ctx)
    -- DOG.scr:159
    ctx:self():playAnimation("Bark", "ChaseCat") -- DOG.scr:162
    do return ctx:exit("") end -- DOG.scr:164
end

script.labels["WarnCat"] = function(ctx)
    -- DOG.scr:167
    ctx:onEvent("OnTargetWithinDist", "", "0") -- DOG.scr:170
    ctx:trigger("g_hTarget", "DogChase") -- DOG.scr:171
    do return ctx:exit("") end -- DOG.scr:172
end

script.labels["OnChaseStuckDone"] = function(ctx)
    -- DOG.scr:175
    mm9.gosub(script, ctx, "ChaseCat") -- DOG.scr:178
    do return ctx:exit("TRUE") end -- DOG.scr:180
end

script.labels["ChaseCat"] = function(ctx)
    -- DOG.scr:183
    -- Cat is in g_hTarget
    ctx:onEvent("OnTargetWithinDist", 120, "WarnCat") -- DOG.scr:188
    ctx:self():stop() -- DOG.scr:190
    ctx:self():setIdle() -- DOG.scr:191
    ctx:onEvent("OnObstacle") -- DOG.scr:192
    ctx:onEvent("OnStuckDone", "OnChaseStuckDone") -- DOG.scr:193
    ctx:self():setTarget(ctx:object("g_hTarget")) -- DOG.scr:195
    ctx:self():runTo(ctx:object("g_hTarget"), 0, "CatArrival") -- DOG.scr:196
    do return ctx:exit("") end -- DOG.scr:198
end

script.labels["ChaseCatEnd"] = function(ctx)
    -- DOG.scr:201
    -- Stop chasing the poor cat...
    ctx:randomInt(15, 30, "g_nRandom") -- DOG.scr:206
    ctx:wait("CAT_SEARCH_WAIT", "g_nRandom", "LookForCats") -- DOG.scr:207
    ctx:trigger("g_hTarget", "DogGiveUp") -- DOG.scr:208
    ctx:self():playAnimation("Bark", "DoneHangingOut") -- DOG.scr:210
    -- gosub DoneHangingOut
    do return ctx:exit("") end -- DOG.scr:213
end

script.labels["LookForCats"] = function(ctx)
    -- DOG.scr:216
    -- See if any cats are near by....
    ctx:getObjects("sAnimal", 500, 5, "g_hCatArray", "g_nNumCats") -- DOG.scr:222
    if ctx:condition("nNumCats==0") then -- DOG.scr:224
        ctx:wait("CAT_SEARCH_WAIT", 1, "LookForCats") -- DOG.scr:225
        do return ctx:exit("") end -- DOG.scr:226
    end -- DOG.scr:227
    ctx:state().g_nTemp = 0 -- DOG.scr:229
    while ctx:condition("g_nTemp < g_nNumCats") do -- DOG.scr:231
        ctx:arrayGet("g_hCatArray", "g_nTemp", "g_hObject") -- DOG.scr:232
        ctx:state().g_bTemp = ctx:self():isFacing(ctx:object("g_hObject")) -- DOG.scr:234
        if ctx:condition("g_bTemp==FALSE") then -- DOG.scr:236
            do return mm9.gotoLabel(script, ctx, "LookForCatsNext") end -- DOG.scr:237
        end -- DOG.scr:238
        ctx:state().g_bTemp = ctx:object("g_hObject"):isVisible() -- DOG.scr:240
        if ctx:condition("g_bTemp==TRUE") then -- DOG.scr:242
            do return mm9.gotoLabel(script, ctx, "FoundCat") end -- DOG.scr:243
        end -- DOG.scr:244
    end -- implicit close before DOG.scr:246
end

script.labels["LookForCatsNext"] = function(ctx)
    -- DOG.scr:246
    ctx:set("g_nTemp", "g_nTemp + 1") -- DOG.scr:248
    -- unmatched endwhile at DOG.scr:250
end

script.labels["LookForCatsDone"] = function(ctx)
    -- DOG.scr:252
    ctx:wait("CAT_SEARCH_WAIT", 1, "LookForCats") -- DOG.scr:253
    do return ctx:exit("") end -- DOG.scr:254
end

script.labels["FoundCat"] = function(ctx)
    -- DOG.scr:256
    ctx:set("g_hTarget", "g_hObject") -- DOG.scr:258
    ctx:randomInt(15, 25, "g_nRandom") -- DOG.scr:260
    ctx:wait("CAT_SEARCH_WAIT", "g_nRandom", "ChaseCatEnd") -- DOG.scr:262
    mm9.gosub(script, ctx, "DisableWandering") -- DOG.scr:263
    mm9.gosub(script, ctx, "ChaseCat") -- DOG.scr:264
    do return ctx:exit("") end -- DOG.scr:266
end

script.labels["StartUp"] = function(ctx)
    -- DOG.scr:270
    -- g_bUseHidingPlaces = FALSE
    mm9.gosub(script, ctx, "BaseWanderForceStartUp") -- DOG.scr:275
    mm9.gosub(script, ctx, "LookForCats") -- DOG.scr:276
    do return ctx:exit("") end -- DOG.scr:278
end

script.labels["OnTargetDead"] = function(ctx)
    -- DOG.scr:281
    mm9.gosub(script, ctx, "DoneHangingOut") -- DOG.scr:283
    do return ctx:exit("FALSE") end -- DOG.scr:285
end

script.labels["Main"] = function(ctx)
    -- DOG.scr:288
    ctx:getParam(0, "nTemp") -- DOG.scr:295
    if ctx:condition("nTemp!=0") then -- DOG.scr:297
        -- <----------TL
        ctx:getParam(0, "sAnimal") -- DOG.scr:299
    end -- DOG.scr:300
    ctx:onEvent("OnFoundTarget", "FoundTarget") -- DOG.scr:303
    ctx:onEvent("OnTargetDead", "OnTargetDead") -- DOG.scr:304
    mm9.gosub(script, ctx, "BaseWanderInit") -- DOG.scr:306
    ctx:wait(0, 1.0, "StartUp") -- DOG.scr:307
    do return ctx:exit("") end -- DOG.scr:309
end

return script
