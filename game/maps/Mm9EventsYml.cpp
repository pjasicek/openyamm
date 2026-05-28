#include "game/maps/Mm9EventsYml.h"

#include <yaml-cpp/yaml.h>

#include <exception>
#include <sstream>

namespace OpenYAMM::Game
{
namespace
{
template <typename ValueType>
bool readScalarNode(
    const YAML::Node &parentNode,
    const char *key,
    ValueType &value,
    std::string &errorMessage,
    bool required = true)
{
    const YAML::Node childNode = parentNode[key];
    if (!childNode)
    {
        if (required)
        {
            errorMessage = std::string("missing required field: ") + key;
            return false;
        }
        return true;
    }

    if (!childNode.IsScalar())
    {
        errorMessage = std::string("field must be a scalar: ") + key;
        return false;
    }

    try
    {
        value = childNode.as<ValueType>();
    }
    catch (const std::exception &exception)
    {
        errorMessage = std::string("could not parse field ") + key + ": " + exception.what();
        return false;
    }
    return true;
}

bool parseClassifications(
    const YAML::Node &objectNode,
    Mm9EventObject &eventObject,
    std::string &errorMessage)
{
    const YAML::Node classificationsNode = objectNode["classifications"];
    if (!classificationsNode)
    {
        return true;
    }
    if (!classificationsNode.IsSequence())
    {
        errorMessage = "object classifications must be a sequence";
        return false;
    }

    for (const YAML::Node &classificationNode : classificationsNode)
    {
        if (!classificationNode.IsScalar())
        {
            errorMessage = "object classification must be a scalar";
            return false;
        }
        eventObject.classifications.push_back(classificationNode.as<std::string>());
    }
    return true;
}

std::string yamlNodeToPreservedString(const YAML::Node &node)
{
    if (!node)
    {
        return {};
    }
    if (node.IsScalar())
    {
        return node.as<std::string>();
    }

    YAML::Emitter emitter;
    emitter << node;
    return std::string(emitter.c_str());
}

bool parseRawProperties(
    const YAML::Node &objectNode,
    Mm9EventObject &eventObject,
    std::string &errorMessage)
{
    const YAML::Node rawPropertiesNode = objectNode["raw_properties"];
    if (!rawPropertiesNode)
    {
        return true;
    }
    if (!rawPropertiesNode.IsSequence())
    {
        errorMessage = "object raw_properties must be a sequence";
        return false;
    }

    eventObject.rawProperties.reserve(rawPropertiesNode.size());
    for (const YAML::Node &propertyNode : rawPropertiesNode)
    {
        if (!propertyNode.IsMap())
        {
            errorMessage = "raw property entry must be a map";
            return false;
        }

        Mm9EventObject::RawPropertyRef property = {};
        if (!readScalarNode(propertyNode, "property_index", property.propertyIndex, errorMessage)
            || !readScalarNode(propertyNode, "name", property.name, errorMessage)
            || !readScalarNode(propertyNode, "decoded", property.decoded, errorMessage)
            || !readScalarNode(propertyNode, "code", property.code, errorMessage)
            || !readScalarNode(propertyNode, "flags", property.flags, errorMessage)
            || !readScalarNode(propertyNode, "raw_ref", property.rawRef, errorMessage))
        {
            return false;
        }

        eventObject.rawProperties.push_back(std::move(property));
    }
    return true;
}

bool parseNormalizedProperties(
    const YAML::Node &objectNode,
    Mm9EventObject &eventObject,
    std::string &errorMessage)
{
    const YAML::Node normalizedNode = objectNode["normalized_properties"];
    if (!normalizedNode)
    {
        return true;
    }
    if (!normalizedNode.IsMap())
    {
        errorMessage = "object normalized_properties must be a map";
        return false;
    }

    for (YAML::const_iterator propertyIterator = normalizedNode.begin();
         propertyIterator != normalizedNode.end();
         ++propertyIterator)
    {
        if (!propertyIterator->first.IsScalar())
        {
            errorMessage = "normalized property key must be a scalar";
            return false;
        }

        eventObject.normalizedProperties[propertyIterator->first.as<std::string>()] =
            yamlNodeToPreservedString(propertyIterator->second);
    }
    return true;
}

bool parseObjects(
    const YAML::Node &rootNode,
    Mm9EventsData &eventsData,
    std::string &errorMessage)
{
    const YAML::Node objectsNode = rootNode["objects"];
    if (!objectsNode || !objectsNode.IsSequence())
    {
        errorMessage = "objects must be a sequence";
        return false;
    }

    eventsData.objects.reserve(objectsNode.size());
    for (const YAML::Node &objectNode : objectsNode)
    {
        if (!objectNode.IsMap())
        {
            errorMessage = "object entry must be a map";
            return false;
        }

        Mm9EventObject eventObject = {};
        if (!readScalarNode(objectNode, "object_id", eventObject.objectId, errorMessage)
            || !readScalarNode(objectNode, "source_object_index", eventObject.sourceObjectIndex, errorMessage)
            || !readScalarNode(objectNode, "source_class", eventObject.sourceClass, errorMessage)
            || !readScalarNode(objectNode, "source_name", eventObject.sourceName, errorMessage)
            || !readScalarNode(objectNode, "raw_object_ref", eventObject.rawObjectRef, errorMessage, false)
            || !readScalarNode(objectNode, "raw_property_count", eventObject.rawPropertyCount, errorMessage)
            || !parseClassifications(objectNode, eventObject, errorMessage)
            || !parseRawProperties(objectNode, eventObject, errorMessage)
            || !parseNormalizedProperties(objectNode, eventObject, errorMessage))
        {
            return false;
        }
        eventsData.objects.push_back(eventObject);
    }
    return true;
}

bool readOptionalBoolNode(const YAML::Node &parentNode, const char *key, bool &value, bool &present)
{
    const YAML::Node childNode = parentNode[key];
    if (!childNode || !childNode.IsScalar())
    {
        return true;
    }

    try
    {
        value = childNode.as<bool>();
        present = true;
    }
    catch (const std::exception &)
    {
        present = false;
    }
    return true;
}

bool readOptionalFloatNode(const YAML::Node &parentNode, const char *key, float &value, bool &present)
{
    const YAML::Node childNode = parentNode[key];
    if (!childNode || !childNode.IsScalar())
    {
        return true;
    }

    try
    {
        value = childNode.as<float>();
        present = true;
    }
    catch (const std::exception &)
    {
        present = false;
    }
    return true;
}

bool readOptionalFloatVectorNode(
    const YAML::Node &parentNode,
    const char *key,
    std::vector<float> &values,
    bool &present,
    std::string &errorMessage)
{
    const YAML::Node childNode = parentNode[key];
    if (!childNode)
    {
        return true;
    }
    if (!childNode.IsSequence())
    {
        errorMessage = std::string("field must be a sequence: ") + key;
        return false;
    }

    values.clear();
    values.reserve(childNode.size());
    for (const YAML::Node &valueNode : childNode)
    {
        if (!valueNode.IsScalar())
        {
            errorMessage = std::string("field sequence item must be a scalar: ") + key;
            return false;
        }
        try
        {
            values.push_back(valueNode.as<float>());
        }
        catch (const std::exception &exception)
        {
            errorMessage = std::string("could not parse field ") + key + ": " + exception.what();
            return false;
        }
    }
    present = true;
    return true;
}

bool readFloatVectorNode(
    const YAML::Node &parentNode,
    const char *key,
    std::vector<float> &values,
    std::string &errorMessage)
{
    bool present = false;
    if (!readOptionalFloatVectorNode(parentNode, key, values, present, errorMessage))
    {
        return false;
    }
    if (!present)
    {
        errorMessage = std::string("missing required field: ") + key;
        return false;
    }
    return true;
}

bool parseExactBindingClaims(
    const YAML::Node &candidateNode,
    std::vector<Mm9EventBindingTarget::MovableWorldModelCandidate::ExactBindingClaim> &claims,
    std::string &errorMessage)
{
    const YAML::Node claimsNode = candidateNode["claimed_by_exact_bindings"];
    if (!claimsNode)
    {
        return true;
    }
    if (!claimsNode.IsSequence())
    {
        errorMessage = "binding target claimed_by_exact_bindings must be a sequence";
        return false;
    }

    claims.reserve(claimsNode.size());
    for (const YAML::Node &claimNode : claimsNode)
    {
        if (!claimNode.IsMap())
        {
            errorMessage = "binding target claimed_by_exact_bindings entry must be a map";
            return false;
        }

        Mm9EventBindingTarget::MovableWorldModelCandidate::ExactBindingClaim claim = {};
        if (!readScalarNode(claimNode, "source_object_index", claim.sourceObjectIndex, errorMessage)
            || !readScalarNode(claimNode, "source_name", claim.sourceName, errorMessage, false)
            || !readScalarNode(claimNode, "confidence", claim.confidence, errorMessage, false))
        {
            return false;
        }

        claims.push_back(std::move(claim));
    }

    return true;
}

bool parseMovableWorldModelCandidates(
    const YAML::Node &targetNode,
    const char *key,
    const char *distanceKey,
    std::vector<Mm9EventBindingTarget::MovableWorldModelCandidate> &candidates,
    std::string &errorMessage)
{
    const YAML::Node candidatesNode = targetNode[key];
    if (!candidatesNode)
    {
        return true;
    }
    if (!candidatesNode.IsSequence())
    {
        errorMessage = std::string("binding target ") + key + " must be a sequence";
        return false;
    }

    candidates.reserve(candidatesNode.size());
    for (const YAML::Node &candidateNode : candidatesNode)
    {
        if (!candidateNode.IsMap())
        {
            errorMessage = std::string("binding target ") + key + " entry must be a map";
            return false;
        }

        Mm9EventBindingTarget::MovableWorldModelCandidate candidate = {};
        bool hasDistance = false;
        if (!readScalarNode(candidateNode, "source_model_index", candidate.sourceModelIndex, errorMessage)
            || !readScalarNode(candidateNode, "source_name", candidate.sourceName, errorMessage, false)
            || !readScalarNode(candidateNode, "movable", candidate.movable, errorMessage, false)
            || !readFloatVectorNode(candidateNode, "world_translation_lt", candidate.worldTranslationLt, errorMessage)
            || !readOptionalFloatNode(candidateNode, distanceKey, candidate.distanceLt, hasDistance)
            || !parseExactBindingClaims(candidateNode, candidate.claimedByExactBindings, errorMessage))
        {
            return false;
        }
        if (!hasDistance)
        {
            errorMessage = std::string("missing required field: ") + distanceKey;
            return false;
        }

        candidates.push_back(std::move(candidate));
    }

    return true;
}

bool parseSourcePolygonGroup(
    const YAML::Node &targetNode,
    Mm9EventBindingTarget &target,
    std::string &errorMessage)
{
    const YAML::Node groupNode = targetNode["source_polygon_group"];
    if (!groupNode)
    {
        return true;
    }
    if (!groupNode.IsMap())
    {
        errorMessage = "binding target source_polygon_group must be a map";
        return false;
    }

    Mm9EventBindingTarget::SourcePolygonGroup group = {};
    bool hasBoundsMin = false;
    bool hasBoundsMax = false;
    if (!readScalarNode(groupNode, "source_model_index", group.sourceModelIndex, errorMessage)
        || !readScalarNode(groupNode, "source_model_name", group.sourceModelName, errorMessage, false)
        || !readScalarNode(groupNode, "source_poly_count", group.sourcePolyCount, errorMessage, false)
        || !readScalarNode(groupNode, "source_surface_count", group.sourceSurfaceCount, errorMessage, false)
        || !readOptionalFloatVectorNode(groupNode, "bounds_min_lt", group.boundsMinLt, hasBoundsMin, errorMessage)
        || !readOptionalFloatVectorNode(groupNode, "bounds_max_lt", group.boundsMaxLt, hasBoundsMax, errorMessage))
    {
        return false;
    }

    const YAML::Node rolesNode = groupNode["roles"];
    if (rolesNode)
    {
        if (!rolesNode.IsMap())
        {
            errorMessage = "binding target source_polygon_group roles must be a map";
            return false;
        }

        const YAML::Node movableNode = rolesNode["movable"];
        if (movableNode && movableNode.IsScalar())
        {
            try
            {
                group.movable = movableNode.as<bool>();
                group.hasMovable = true;
            }
            catch (const std::exception &exception)
            {
                errorMessage = std::string("could not parse source_polygon_group roles.movable: ")
                    + exception.what();
                return false;
            }
        }
    }

    target.sourcePolygonGroup = std::move(group);
    return true;
}

bool parseMechanismTriggerOutputs(
    const YAML::Node &mechanismNode,
    Mm9EventMechanism &mechanism,
    std::string &errorMessage)
{
    const YAML::Node outputsNode = mechanismNode["trigger_outputs"];
    if (!outputsNode)
    {
        return true;
    }
    if (!outputsNode.IsSequence())
    {
        errorMessage = "mechanism trigger_outputs must be a sequence";
        return false;
    }

    mechanism.triggerOutputs.reserve(outputsNode.size());
    for (const YAML::Node &outputNode : outputsNode)
    {
        if (!outputNode.IsMap())
        {
            errorMessage = "mechanism trigger_outputs entry must be a map";
            return false;
        }

        Mm9EventTriggerOutput output = {};
        if (!readScalarNode(outputNode, "phase", output.phase, errorMessage, false)
            || !readScalarNode(outputNode, "slot", output.slot, errorMessage, false)
            || !readScalarNode(outputNode, "target_name", output.targetName, errorMessage, false)
            || !readScalarNode(outputNode, "message_name", output.messageName, errorMessage, false)
            || !readScalarNode(outputNode, "resolution", output.resolution, errorMessage, false))
        {
            return false;
        }

        mechanism.triggerOutputs.push_back(std::move(output));
    }

    return true;
}

bool parseMechanisms(
    const YAML::Node &rootNode,
    Mm9EventsData &eventsData,
    std::string &errorMessage)
{
    const YAML::Node mechanismsNode = rootNode["mechanisms"];
    if (!mechanismsNode)
    {
        return true;
    }
    if (!mechanismsNode.IsSequence())
    {
        errorMessage = "mechanisms must be a sequence";
        return false;
    }

    eventsData.mechanisms.reserve(mechanismsNode.size());
    for (const YAML::Node &mechanismNode : mechanismsNode)
    {
        if (!mechanismNode.IsMap())
        {
            errorMessage = "mechanism entry must be a map";
            return false;
        }

        Mm9EventMechanism mechanism = {};
        if (!readScalarNode(mechanismNode, "mechanism_id", mechanism.mechanismId, errorMessage)
            || !readScalarNode(mechanismNode, "object_id", mechanism.objectId, errorMessage)
            || !readScalarNode(mechanismNode, "source_object_index", mechanism.sourceObjectIndex, errorMessage)
            || !readScalarNode(mechanismNode, "source_class", mechanism.sourceClass, errorMessage)
            || !readScalarNode(mechanismNode, "source_name", mechanism.sourceName, errorMessage))
        {
            return false;
        }

        const YAML::Node motionNode = mechanismNode["mechanism"];
        if (motionNode && motionNode.IsMap())
        {
            readScalarNode(motionNode, "kind", mechanism.kind, errorMessage, false);

            const YAML::Node linearNode = motionNode["linear"];
            if (linearNode && linearNode.IsMap())
            {
                if (!readOptionalFloatVectorNode(
                        linearNode,
                        "move_dir_lt",
                        mechanism.linear.moveDirLt,
                        mechanism.linear.hasMoveDir,
                        errorMessage))
                {
                    return false;
                }
                readOptionalFloatNode(
                    linearNode,
                    "move_dist_lt",
                    mechanism.linear.moveDistLt,
                    mechanism.linear.hasMoveDist);
                readOptionalFloatNode(
                    linearNode,
                    "open_speed_lt_per_sec",
                    mechanism.linear.openSpeedLtPerSecond,
                    mechanism.linear.hasOpenSpeed);
                readOptionalFloatNode(
                    linearNode,
                    "close_speed_lt_per_sec",
                    mechanism.linear.closeSpeedLtPerSecond,
                    mechanism.linear.hasCloseSpeed);
            }

            const YAML::Node rotationNode = motionNode["rotation"];
            if (rotationNode && rotationNode.IsMap())
            {
                if (!readOptionalFloatVectorNode(
                        rotationNode,
                        "rotation_point_lt",
                        mechanism.rotation.rotationPointLt,
                        mechanism.rotation.hasRotationPoint,
                        errorMessage)
                    || !readOptionalFloatVectorNode(
                        rotationNode,
                        "rotation_angles_deg",
                        mechanism.rotation.rotationAnglesDeg,
                        mechanism.rotation.hasRotationAngles,
                        errorMessage))
                {
                    return false;
                }
            }
        }

        const YAML::Node activationNode = mechanismNode["activation"];
        if (activationNode && activationNode.IsMap())
        {
            readOptionalBoolNode(
                activationNode,
                "start_open",
                mechanism.activation.startOpen,
                mechanism.activation.hasStartOpen);
            readOptionalBoolNode(activationNode, "locked", mechanism.activation.locked, mechanism.activation.hasLocked);
        }

        if (!parseMechanismTriggerOutputs(mechanismNode, mechanism, errorMessage))
        {
            return false;
        }

        eventsData.mechanisms.push_back(std::move(mechanism));
    }
    return true;
}

bool parseBindings(
    const YAML::Node &rootNode,
    Mm9EventsData &eventsData,
    std::string &errorMessage)
{
    const YAML::Node bindingsNode = rootNode["bindings"];
    if (!bindingsNode)
    {
        return true;
    }
    if (!bindingsNode.IsSequence())
    {
        errorMessage = "bindings must be a sequence";
        return false;
    }

    eventsData.bindings.reserve(bindingsNode.size());
    for (const YAML::Node &bindingNode : bindingsNode)
    {
        if (!bindingNode.IsMap())
        {
            errorMessage = "binding entry must be a map";
            return false;
        }

        Mm9EventBinding binding = {};
        if (!readScalarNode(bindingNode, "object_id", binding.objectId, errorMessage)
            || !readScalarNode(bindingNode, "source_object_index", binding.sourceObjectIndex, errorMessage))
        {
            return false;
        }

        const YAML::Node targetsNode = bindingNode["targets"];
        if (!targetsNode || !targetsNode.IsSequence())
        {
            errorMessage = "binding targets must be a sequence";
            return false;
        }

        for (const YAML::Node &targetNode : targetsNode)
        {
            if (!targetNode.IsMap())
            {
                errorMessage = "binding target entry must be a map";
                return false;
            }

            Mm9EventBindingTarget target = {};
            if (!readScalarNode(targetNode, "target_kind", target.targetKind, errorMessage)
                || !readScalarNode(targetNode, "target_id", target.targetId, errorMessage, false)
                || !readScalarNode(targetNode, "confidence", target.confidence, errorMessage, false)
                || !readScalarNode(targetNode, "bmodel_name", target.bmodelName, errorMessage, false)
                || !readScalarNode(targetNode, "source_model_name", target.sourceModelName, errorMessage, false)
                || !parseMovableWorldModelCandidates(
                    targetNode,
                    "nearest_movable_world_models_by_rotation_point",
                    "distance_from_rotation_point_lt",
                    target.nearestMovableWorldModelsByRotationPoint,
                    errorMessage)
                || !parseMovableWorldModelCandidates(
                    targetNode,
                    "nearest_movable_world_models_by_position",
                    "distance_from_position_lt",
                    target.nearestMovableWorldModelsByPosition,
                    errorMessage)
                || !parseSourcePolygonGroup(targetNode, target, errorMessage))
            {
                return false;
            }

            const YAML::Node bmodelIndexNode = targetNode["bmodel_index"];
            if (bmodelIndexNode && bmodelIndexNode.IsScalar())
            {
                try
                {
                    target.bmodelIndex = bmodelIndexNode.as<size_t>();
                }
                catch (const std::exception &exception)
                {
                    errorMessage = std::string("could not parse bmodel_index: ") + exception.what();
                    return false;
                }
            }

            binding.targets.push_back(std::move(target));
        }
        eventsData.bindings.push_back(std::move(binding));
    }
    return true;
}

bool parseScriptCommandList(
    const YAML::Node &scriptNode,
    const char *pKey,
    std::vector<Mm9EventScript::ScriptCommand> &commands,
    std::string &errorMessage)
{
    const YAML::Node commandsNode = scriptNode[pKey];
    if (!commandsNode)
    {
        return true;
    }
    if (!commandsNode.IsSequence())
    {
        errorMessage = std::string("script ") + pKey + " must be a sequence";
        return false;
    }

    commands.reserve(commandsNode.size());
    for (const YAML::Node &commandNode : commandsNode)
    {
        if (!commandNode.IsMap())
        {
            errorMessage = std::string("script ") + pKey + " entry must be a map";
            return false;
        }

        Mm9EventScript::ScriptCommand command = {};
        if (!readScalarNode(commandNode, "line", command.line, errorMessage, false)
            || !readScalarNode(commandNode, "command", command.command, errorMessage, false)
            || !readScalarNode(commandNode, "arguments_raw", command.argumentsRaw, errorMessage, false))
        {
            return false;
        }

        commands.push_back(std::move(command));
    }

    return true;
}

bool parseScripts(
    const YAML::Node &rootNode,
    Mm9EventsData &eventsData,
    std::string &errorMessage)
{
    const YAML::Node scriptsNode = rootNode["scripts"];
    if (!scriptsNode)
    {
        return true;
    }
    if (!scriptsNode.IsSequence())
    {
        errorMessage = "scripts must be a sequence";
        return false;
    }

    eventsData.scripts.reserve(scriptsNode.size());
    for (const YAML::Node &scriptNode : scriptsNode)
    {
        if (!scriptNode.IsMap())
        {
            errorMessage = "script entry must be a map";
            return false;
        }

        Mm9EventScript script = {};
        if (!readScalarNode(scriptNode, "script_id", script.scriptId, errorMessage)
            || !readScalarNode(scriptNode, "source_path", script.sourcePath, errorMessage)
            || !readScalarNode(scriptNode, "command_count", script.commandCount, errorMessage, false))
        {
            return false;
        }

        const YAML::Node registeredTriggersNode = scriptNode["registered_triggers"];
        if (registeredTriggersNode && registeredTriggersNode.IsSequence())
        {
            script.registeredTriggerCount = registeredTriggersNode.size();

            for (const YAML::Node &triggerNode : registeredTriggersNode)
            {
                if (!triggerNode.IsMap())
                {
                    errorMessage = "script registered_triggers entry must be a map";
                    return false;
                }

                Mm9EventScript::RegisteredTrigger trigger = {};
                if (!readScalarNode(triggerNode, "line", trigger.line, errorMessage, false)
                    || !readScalarNode(triggerNode, "message", trigger.message, errorMessage, false)
                    || !readScalarNode(triggerNode, "callback", trigger.callback, errorMessage, false)
                    || !readScalarNode(triggerNode, "arguments_raw", trigger.argumentsRaw, errorMessage, false))
                {
                    return false;
                }

                script.registeredTriggers.push_back(std::move(trigger));
            }
        }

        const YAML::Node triggerEdgesNode = scriptNode["trigger_edges"];
        if (triggerEdgesNode && triggerEdgesNode.IsSequence())
        {
            for (const YAML::Node &edgeNode : triggerEdgesNode)
            {
                if (!edgeNode.IsMap())
                {
                    errorMessage = "script trigger_edges entry must be a map";
                    return false;
                }

                Mm9EventScript::TriggerEdge edge = {};
                if (!readScalarNode(edgeNode, "line", edge.line, errorMessage, false)
                    || !readScalarNode(edgeNode, "target_expression", edge.targetExpression, errorMessage, false)
                    || !readScalarNode(edgeNode, "message_expression", edge.messageExpression, errorMessage, false)
                    || !readScalarNode(edgeNode, "arguments_raw", edge.argumentsRaw, errorMessage, false))
                {
                    return false;
                }

                script.triggerEdges.push_back(std::move(edge));
            }
        }

        const YAML::Node movementCommandsNode = scriptNode["movement_commands"];
        if (movementCommandsNode && movementCommandsNode.IsSequence())
        {
            script.movementCommandCount = movementCommandsNode.size();
        }
        if (!parseScriptCommandList(scriptNode, "movement_commands", script.movementCommands, errorMessage))
        {
            return false;
        }

        const YAML::Node unknownCommandsNode = scriptNode["unknown_commands"];
        if (unknownCommandsNode && unknownCommandsNode.IsSequence())
        {
            script.unknownCommandCount = unknownCommandsNode.size();
        }
        if (!parseScriptCommandList(scriptNode, "unknown_commands", script.unknownCommands, errorMessage))
        {
            return false;
        }

        eventsData.scripts.push_back(script);
    }
    return true;
}

bool parseUnresolvedEntries(
    const YAML::Node &rootNode,
    Mm9EventsData &eventsData,
    std::string &errorMessage)
{
    const YAML::Node unresolvedNode = rootNode["unresolved"];
    if (!unresolvedNode)
    {
        return true;
    }
    if (!unresolvedNode.IsSequence())
    {
        errorMessage = "unresolved must be a sequence";
        return false;
    }

    eventsData.unresolved.reserve(unresolvedNode.size());
    for (const YAML::Node &entryNode : unresolvedNode)
    {
        if (!entryNode.IsMap())
        {
            errorMessage = "unresolved entry must be a map";
            return false;
        }

        Mm9EventUnresolved entry = {};
        if (!readScalarNode(entryNode, "kind", entry.kind, errorMessage)
            || !readScalarNode(entryNode, "source_object_index", entry.sourceObjectIndex, errorMessage, false)
            || !readScalarNode(entryNode, "source_name", entry.sourceName, errorMessage, false)
            || !readScalarNode(entryNode, "source_class", entry.sourceClass, errorMessage, false)
            || !readScalarNode(entryNode, "severity", entry.severity, errorMessage, false))
        {
            return false;
        }

        const YAML::Node evidenceNode = entryNode["evidence"];
        if (evidenceNode)
        {
            if (!evidenceNode.IsMap())
            {
                errorMessage = "unresolved evidence must be a map";
                return false;
            }

            if (!parseMovableWorldModelCandidates(
                    evidenceNode,
                    "nearest_movable_world_models_by_rotation_point",
                    "distance_from_rotation_point_lt",
                    entry.nearestMovableWorldModelsByRotationPoint,
                    errorMessage)
                || !parseMovableWorldModelCandidates(
                    evidenceNode,
                    "nearest_movable_world_models_by_position",
                    "distance_from_position_lt",
                    entry.nearestMovableWorldModelsByPosition,
                    errorMessage))
            {
                return false;
            }
        }

        eventsData.unresolved.push_back(std::move(entry));
    }

    eventsData.unresolvedCount = eventsData.unresolved.size();
    return true;
}

void parseCounts(const YAML::Node &rootNode, Mm9EventsData &eventsData)
{
    const YAML::Node mechanismsNode = rootNode["mechanisms"];
    if (mechanismsNode && mechanismsNode.IsSequence())
    {
        eventsData.mechanismCount = mechanismsNode.size();
    }

    const YAML::Node triggersNode = rootNode["triggers"];
    if (triggersNode && triggersNode.IsSequence())
    {
        eventsData.triggerCount = triggersNode.size();
    }

    const YAML::Node interactionsNode = rootNode["interactions"];
    if (interactionsNode && interactionsNode.IsSequence())
    {
        eventsData.interactionCount = interactionsNode.size();
    }

    const YAML::Node unresolvedNode = rootNode["unresolved"];
    if (unresolvedNode && unresolvedNode.IsSequence())
    {
        eventsData.unresolvedCount = unresolvedNode.size();
    }
}
}

std::optional<Mm9EventsData> Mm9EventsYmlLoader::loadFromText(
    const std::string &yamlText,
    std::string &errorMessage) const
{
    YAML::Node rootNode;
    try
    {
        rootNode = YAML::Load(yamlText);
    }
    catch (const std::exception &exception)
    {
        errorMessage = exception.what();
        return std::nullopt;
    }

    if (!rootNode || !rootNode.IsMap())
    {
        errorMessage = "MM9 events YAML root must be a map";
        return std::nullopt;
    }

    Mm9EventsData eventsData = {};
    if (!readScalarNode(rootNode, "format_version", eventsData.formatVersion, errorMessage)
        || !readScalarNode(rootNode, "kind", eventsData.kind, errorMessage)
        || !readScalarNode(rootNode, "source_dat", eventsData.sourceDat, errorMessage, false)
        || !readScalarNode(rootNode, "source_raw_objects", eventsData.sourceRawObjects, errorMessage))
    {
        return std::nullopt;
    }

    if (eventsData.kind != "mm9_events")
    {
        errorMessage = "kind must be mm9_events";
        return std::nullopt;
    }

    const YAML::Node generatedNode = rootNode["generated"];
    if (generatedNode && generatedNode.IsMap())
    {
        if (!readScalarNode(generatedNode, "lua", eventsData.generatedLua, errorMessage, false)
            || !readScalarNode(generatedNode, "script_ir", eventsData.generatedScriptIr, errorMessage, false))
        {
            return std::nullopt;
        }
    }

    if (!parseObjects(rootNode, eventsData, errorMessage)
        || !parseMechanisms(rootNode, eventsData, errorMessage)
        || !parseBindings(rootNode, eventsData, errorMessage)
        || !parseScripts(rootNode, eventsData, errorMessage)
        || !parseUnresolvedEntries(rootNode, eventsData, errorMessage))
    {
        return std::nullopt;
    }

    parseCounts(rootNode, eventsData);
    return eventsData;
}
}
