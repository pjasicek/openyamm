-- generated MM9 script runtime support; do not edit by hand
local runtime = {}

function runtime.findLabel(script, name)
    local direct = script.labels[name]
    if direct ~= nil then
        return direct
    end
    local lowered = string.lower(name)
    for labelName, labelFunc in pairs(script.labels) do
        if string.lower(labelName) == lowered then
            return labelFunc
        end
    end
    return nil
end

function runtime.gosub(script, ctx, name)
    ctx:command("gosub", name)
    local labelFunc = runtime.findLabel(script, name)
    if labelFunc ~= nil then
        return labelFunc(ctx)
    end
    return nil
end

function runtime.gotoLabel(script, ctx, name)
    ctx:command("goto", name)
    local labelFunc = runtime.findLabel(script, name)
    if labelFunc ~= nil then
        return labelFunc(ctx)
    end
    return nil
end

return runtime
