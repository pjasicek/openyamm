-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SCHOLARPROMO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basewander.inc" }

-- Scholarpromo.scr
-- timmy
-- handles scholar promo stuff
-- flag variables
script.labels["RunAway"] = function(ctx)
    -- SCHOLARPROMO.scr:17
    ctx:self():stop() -- SCHOLARPROMO.scr:19
    mm9.gosub(script, ctx, "basewanderstop") -- SCHOLARPROMO.scr:20
    ctx:state().g_hobject = ctx:objectOrNil("MagreebMarker1") -- SCHOLARPROMO.scr:21
    ctx:self():runTo(ctx:object("g_hobject"), 16, "OnVanish") -- SCHOLARPROMO.scr:22
    if ctx:hasKey(201) then -- SCHOLARPROMO.scr:23-24
        if not ctx:hasKey(202) then -- SCHOLARPROMO.scr:26-27
            ctx:giveKey(202) -- SCHOLARPROMO.scr:28
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SCHOLARPROMO.scr:29
        end -- SCHOLARPROMO.scr:30
    end -- SCHOLARPROMO.scr:32
    do return ctx:exit("") end -- SCHOLARPROMO.scr:34
end

script.labels["OnVanish"] = function(ctx)
    -- SCHOLARPROMO.scr:37
    ctx:self():remove() -- SCHOLARPROMO.scr:41
    do return ctx:exit("") end -- SCHOLARPROMO.scr:43
end

script.labels["Init"] = function(ctx)
    -- SCHOLARPROMO.scr:46
    ctx:onEvent("OnFoundPlayer", "RunAway") -- SCHOLARPROMO.scr:51
    ctx:onEvent("OnDamage", "RunAway") -- SCHOLARPROMO.scr:52
    ctx:onEvent("OnLostTarget", "OnLost") -- SCHOLARPROMO.scr:53
    do return ctx:exit("") end -- SCHOLARPROMO.scr:54
end

script.labels["OnLost"] = function(ctx)
    -- SCHOLARPROMO.scr:57
    do return ctx:exit("TRUE") end -- SCHOLARPROMO.scr:60
end

script.labels["Main"] = function(ctx)
    -- SCHOLARPROMO.scr:64
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("use", "Init") -- SCHOLARPROMO.scr:69
    ctx:onEvent("OnPostStartWorld", "Init") -- SCHOLARPROMO.scr:70
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- SCHOLARPROMO.scr:71
    ctx:onEvent("OnPostSaveLoad", "Init") -- SCHOLARPROMO.scr:72
    ctx:wait(1, .1, "Init") -- SCHOLARPROMO.scr:73
    do return ctx:exit("") end -- SCHOLARPROMO.scr:76
end

return script
