-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "THETHING.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseFile.inc" }

-- TheThing.inc (john carpenter's)
-- by SJR
-- 11-04-01
-- Purpose:turn into a weirdo lookin
-- rastafied evil terror eye
-- thing with big pointy teeth
script.labels["InitTheThing"] = function(ctx)
    -- THETHING.inc:25
    ctx:command("cachesound", "sounds\\animsounds\\dragon\\wince2.wav") -- THETHING.inc:27
    ctx:command("setmodelfilenames", "\"models\\evileyeterror.abc\", \"skins\\evileyeterror.dtx\"") -- THETHING.inc:29
    mm9.gosub(script, ctx, "InitStrings") -- THETHING.inc:30
    ctx:command("onfoundtarget", "BeginBaseScript") -- THETHING.inc:31
    ctx:command("sheadname", "= PARENT + lobberpod + ABC") -- THETHING.inc:33
    ctx:command("sheadskin", "= PARENT + lobberpod + DTX") -- THETHING.inc:34
    ctx:command("slimbname", "= PARENT + lobberpod + ABC") -- THETHING.inc:36
    ctx:command("slimbskin", "= PARENT + lobberpod + DTX") -- THETHING.inc:37
    ctx:command("attachprop", "sHeadName, sHeadSkin, rhand1, hAttach") -- THETHING.inc:39
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:40
    ctx:command("attachprop", "sHeadName, sHeadSkin, lhand1, hAttach") -- THETHING.inc:41
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:42
    ctx:command("attachprop", "sHeadName, sHeadSkin, rangeattack5, hAttach") -- THETHING.inc:43
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:44
    ctx:command("attachprop", "sLimbName, sLimbSkin, rangeattack2, hAttach") -- THETHING.inc:45
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:46
    ctx:command("attachprop", "sLimbName, sLimbSkin, rangeattack3, hAttach") -- THETHING.inc:47
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:48
    ctx:command("attachprop", "sLimbName, sLimbSkin, rangeattack6, hAttach") -- THETHING.inc:49
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:50
    ctx:command("attachprop", "sHeadName, sHeadSkin, rangeattack4, hAttach") -- THETHING.inc:51
    mm9.gosub(script, ctx, "SetAnim") -- THETHING.inc:52
    do return ctx:exit("") end -- THETHING.inc:54
end

script.labels["SetAnim"] = function(ctx)
    -- THETHING.inc:57
    -- set the socket anims
    ctx:command("arrayget", "spAnims, nCounter, sAnim") -- THETHING.inc:60
    ctx:trigger("hAttach", "sAnim") -- THETHING.inc:61
    ctx:command("ncounter", "= nCounter + 1") -- THETHING.inc:62
    ctx:command("mod", "nCounter, 7") -- THETHING.inc:63
    do return ctx:exit("") end -- THETHING.inc:65
end

script.labels["InitStrings"] = function(ctx)
    -- THETHING.inc:68
    -- init the socket names
    ctx:command("arrayput", "spAnims, 0, hattack1") -- THETHING.inc:71
    ctx:command("arrayput", "spAnims, 1, rattack1") -- THETHING.inc:72
    ctx:command("arrayput", "spAnims, 2, wince1") -- THETHING.inc:73
    ctx:command("arrayput", "spAnims, 3, wince2") -- THETHING.inc:74
    ctx:command("arrayput", "spAnims, 4, land") -- THETHING.inc:75
    ctx:command("arrayput", "spAnims, 5, hattack1") -- THETHING.inc:76
    ctx:command("arrayput", "spAnims, 6, walk") -- THETHING.inc:77
    ctx:command("ncounter", "= 6") -- THETHING.inc:79
    while ctx:condition("nCounter>=0") do -- THETHING.inc:80
        ctx:command("arrayget", "spAnims, nCounter, sAnim") -- THETHING.inc:81
        ctx:command("sanim", "= ANIMCOMMAND + sAnim") -- THETHING.inc:82
        ctx:command("arrayput", "spAnims, nCounter, sAnim") -- THETHING.inc:83
        ctx:command("ncounter", "= nCounter - 1") -- THETHING.inc:84
    end -- THETHING.inc:85
    ctx:command("ncounter", "= 0") -- THETHING.inc:86
    do return ctx:exit("") end -- THETHING.inc:88
end

script.labels["BeginBaseScript"] = function(ctx)
    -- THETHING.inc:91
    -- play a freaky sound, launch base.scr
    ctx:command("playsound", "sounds\\animsounds\\dragon\\wince2.wav, DoNothing, 1, 500, 0, 100") -- THETHING.inc:94
    ctx:command("runscript", "baseRange.scr") -- THETHING.inc:96
    do return ctx:exit("") end -- THETHING.inc:98
end

script.labels["DoNothing"] = function(ctx)
    -- THETHING.inc:101
    do return ctx:exit(1) end -- THETHING.inc:103
end

return script
