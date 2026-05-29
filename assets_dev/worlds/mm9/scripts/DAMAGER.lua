-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DAMAGER.scr"
script.includes = {}
script.labels = {}


script.labels["d"] = function(ctx)
    -- DAMAGER.scr:8
    ctx:rolloverText(1, 1, 3000, 3500) -- DAMAGER.scr:10
    if ctx:condition("c == 0") then -- DAMAGER.scr:13
        ctx:state().t = ctx:objectOrNil("db0") -- DAMAGER.scr:14
        ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:15
    else -- DAMAGER.scr:16
        if ctx:condition("c == 1") then -- DAMAGER.scr:17
            ctx:state().t = ctx:objectOrNil("db1") -- DAMAGER.scr:18
            ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:19
        else -- DAMAGER.scr:20
            if ctx:condition("c == 2") then -- DAMAGER.scr:21
                ctx:state().t = ctx:objectOrNil("db2") -- DAMAGER.scr:22
                ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:23
            else -- DAMAGER.scr:24
                if ctx:condition("c == 3") then -- DAMAGER.scr:25
                    ctx:state().t = ctx:objectOrNil("db3") -- DAMAGER.scr:26
                    ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:27
                else -- DAMAGER.scr:28
                    if ctx:condition("c == 4") then -- DAMAGER.scr:29
                        ctx:state().t = ctx:objectOrNil("db4") -- DAMAGER.scr:30
                        ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:31
                    else -- DAMAGER.scr:32
                        if ctx:condition("c == 5") then -- DAMAGER.scr:33
                            ctx:state().t = ctx:objectOrNil("db5") -- DAMAGER.scr:34
                            ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:35
                        else -- DAMAGER.scr:36
                            if ctx:condition("c == 6") then -- DAMAGER.scr:37
                                ctx:state().t = ctx:objectOrNil("db6") -- DAMAGER.scr:38
                                ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:39
                            else -- DAMAGER.scr:40
                                if ctx:condition("c == 7") then -- DAMAGER.scr:41
                                    ctx:state().t = ctx:objectOrNil("db7") -- DAMAGER.scr:42
                                    ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:43
                                else -- DAMAGER.scr:44
                                    if ctx:condition("c == 8") then -- DAMAGER.scr:45
                                        ctx:state().t = ctx:objectOrNil("db8") -- DAMAGER.scr:46
                                        ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:47
                                    else -- DAMAGER.scr:48
                                        if ctx:condition("c == 9") then -- DAMAGER.scr:49
                                            ctx:state().t = ctx:objectOrNil("db9") -- DAMAGER.scr:50
                                            ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:51
                                        else -- DAMAGER.scr:52
                                            if ctx:condition("c == 10") then -- DAMAGER.scr:53
                                                ctx:state().t = ctx:objectOrNil("db10") -- DAMAGER.scr:54
                                                ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:55
                                            else -- DAMAGER.scr:56
                                                if ctx:condition("c == 11") then -- DAMAGER.scr:57
                                                    ctx:state().t = ctx:objectOrNil("db11") -- DAMAGER.scr:58
                                                    ctx:object("t"):damage(2, 4, 0) -- DAMAGER.scr:59
                                                else -- DAMAGER.scr:60
                                                    ctx:self():die() -- DAMAGER.scr:61
                                                end -- DAMAGER.scr:63
                                            end -- DAMAGER.scr:64
                                        end -- DAMAGER.scr:65
                                    end -- DAMAGER.scr:66
                                end -- DAMAGER.scr:67
                            end -- DAMAGER.scr:68
                        end -- DAMAGER.scr:69
                    end -- DAMAGER.scr:70
                end -- DAMAGER.scr:71
            end -- DAMAGER.scr:72
        end -- DAMAGER.scr:73
    end -- DAMAGER.scr:74
    ctx:set("c", "c + 1") -- DAMAGER.scr:75
    do return ctx:exit(1) end -- DAMAGER.scr:77
end

script.labels["main2"] = function(ctx)
    -- DAMAGER.scr:79
    ctx:onEvent("OnDamage", "d") -- DAMAGER.scr:80
    do return ctx:exit(1) end -- DAMAGER.scr:84
end

script.labels["main"] = function(ctx)
    -- DAMAGER.scr:88
    ctx:wait(0, .1, "main2") -- DAMAGER.scr:90
    do return ctx:exit("") end -- DAMAGER.scr:93
end

return script
