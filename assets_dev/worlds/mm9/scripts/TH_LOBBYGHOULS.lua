-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TH_LOBBYGHOULS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "BaseMelee.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "Flags.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "range.inc" }
script.includes[#script.includes + 1] = { line = 15, path = "basedoor.inc" }

-- TH_LobbyGhouls.scr
-- Karl Drown 11-17-01
-- Ghouls in Lobby triggered to run to the sauna
-- room, then surprise party.
script.labels["DoNothing"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:33
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:36
end

script.labels["RunUpStairs"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:39
    ctx:state().hMarker = ctx:objectOrNil("sMarkerA") -- TH_LOBBYGHOULS.scr:41
    ctx:self():runTo(ctx:object("hMarker"), 10, "MarkerB") -- TH_LOBBYGHOULS.scr:42
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:43
end

script.labels["MarkerB"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:45
    ctx:state().hMarker = ctx:objectOrNil("sMarkerB") -- TH_LOBBYGHOULS.scr:46
    ctx:self():runTo(ctx:object("hMarker"), 10, "MarkerC") -- TH_LOBBYGHOULS.scr:47
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:48
end

script.labels["MarkerC"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:49
    ctx:state().hMarker = ctx:objectOrNil("sMarkerC") -- TH_LOBBYGHOULS.scr:50
    ctx:self():runTo(ctx:object("hMarker"), 10, "MarkerD") -- TH_LOBBYGHOULS.scr:51
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:52
end

script.labels["MarkerD"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:53
    ctx:self():stop() -- TH_LOBBYGHOULS.scr:54
    ctx:state().hMarker = ctx:objectOrNil("sMarkerD") -- TH_LOBBYGHOULS.scr:55
    ctx:state().nNumX, ctx:state().nNumY, ctx:state().nNumZ = ctx:object("hMarker"):pos() -- TH_LOBBYGHOULS.scr:56
    ctx:object("hMyObject"):setPos("nNumX", "nNumY", "nNumZ") -- TH_LOBBYGHOULS.scr:57
    mm9.gosub(script, ctx, "Pause") -- TH_LOBBYGHOULS.scr:58
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:59
end

script.labels["Pause"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:61
    ctx:state().HMarker = nil -- TH_LOBBYGHOULS.scr:63
    ctx:self():stop() -- TH_LOBBYGHOULS.scr:64
    ctx:wait(0, 1, "DoNothing") -- TH_LOBBYGHOULS.scr:65
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:66
end

script.labels["DropGhouls"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:68
    ctx:object("hObject"):setFlag("FLAG_SOLID", false) -- TH_LOBBYGHOULS.scr:71
    ctx:wait(0, 2, "SetSolid") -- TH_LOBBYGHOULS.scr:72
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:73
end

script.labels["SetSolid"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:75
    ctx:object("hObject"):setFlag("FLAG_SOLID", true) -- TH_LOBBYGHOULS.scr:77
    mm9.gosub(script, ctx, "BaseInit") -- TH_LOBBYGHOULS.scr:78
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:79
end

script.labels["Main2"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:82
    ctx:state().hObject = ctx:objectOrNil("WO_GhoulPlatform") -- TH_LOBBYGHOULS.scr:84
    ctx:state().hMyObject = ctx:self() -- TH_LOBBYGHOULS.scr:85
    ctx:addTrigger("Go", "RunUpStairs") -- TH_LOBBYGHOULS.scr:86
    ctx:addTrigger("Drop", "DropGhouls") -- TH_LOBBYGHOULS.scr:87
    ctx:onEvent("OnFoundTarget", "BaseInit") -- TH_LOBBYGHOULS.scr:88
    ctx:onEvent("OnDamage", "BaseInit") -- TH_LOBBYGHOULS.scr:89
    -- <-----------TL
    mm9.gosub(script, ctx, "RangeInit") -- TH_LOBBYGHOULS.scr:90
    -- <-----------TL
    mm9.gosub(script, ctx, "basedoorinit") -- TH_LOBBYGHOULS.scr:91
    do return ctx:exit("TRUE") end -- TH_LOBBYGHOULS.scr:92
end

script.labels["Main"] = function(ctx)
    -- TH_LOBBYGHOULS.scr:94
    ctx:getParam(0, "sMarkerA") -- TH_LOBBYGHOULS.scr:96
    ctx:getParam(1, "sMarkerB") -- TH_LOBBYGHOULS.scr:97
    ctx:getParam(2, "sMarkerC") -- TH_LOBBYGHOULS.scr:98
    ctx:getParam(3, "sMarkerD") -- TH_LOBBYGHOULS.scr:99
    ctx:wait(0, 0.5, "Main2") -- TH_LOBBYGHOULS.scr:100
    do return ctx:exit("") end -- TH_LOBBYGHOULS.scr:101
end

return script
