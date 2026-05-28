#include "game/mm9/Mm9DialogueUi.h"

#include <string>
#include <vector>

namespace OpenYAMM::Game
{
namespace
{
std::string titleForRuntime(const Mm9DialogueRuntime &runtime)
{
    if (!runtime.owner().objectName.empty())
    {
        return runtime.owner().objectName;
    }

    return "NPC " + std::to_string(runtime.currentRudeId());
}

std::string actionArgumentForTopic(const Mm9DialogueTopic &topic)
{
    return "choice=" + std::to_string(topic.choiceSlot) + ";next=" + std::to_string(topic.next);
}
}

EventDialogContent buildMm9DialogueContent(
    const Mm9DialogueRuntime &runtime,
    const std::string &responseText)
{
    EventDialogContent content = {};
    const bool closedWithoutResponse = runtime.closed() && responseText.empty();
    if (closedWithoutResponse || runtime.currentRudeId() <= 0)
    {
        return content;
    }

    content.isActive = true;
    content.sourceId = static_cast<uint32_t>(runtime.currentRudeId());
    content.title = titleForRuntime(runtime);
    if (!responseText.empty())
    {
        content.lines.push_back(responseText);
    }

    if (runtime.closed())
    {
        return content;
    }

    const std::vector<Mm9DialogueTopic> topics = runtime.visibleTopics();
    for (size_t topicIndex = 0; topicIndex < topics.size(); ++topicIndex)
    {
        const Mm9DialogueTopic &topic = topics[topicIndex];
        EventDialogAction action = {};
        action.kind = EventDialogActionKind::Mm9Topic;
        action.id = static_cast<uint32_t>(topicIndex);
        action.secondaryId = static_cast<uint32_t>(topic.sourceRow);
        action.label = topic.prompt;
        action.argument = actionArgumentForTopic(topic);
        content.actions.push_back(std::move(action));
    }

    return content;
}

Mm9DialogueUiActionResult executeMm9DialogueAction(
    Mm9DialogueRuntime &runtime,
    const EventDialogAction &action,
    Mm9DialogueServiceHandler *pServiceHandler)
{
    Mm9DialogueUiActionResult result = {};
    if (action.kind != EventDialogActionKind::Mm9Topic)
    {
        return result;
    }

    result.handled = true;
    result.selection = runtime.selectTopic(action.id);
    if (result.selection.kind == Mm9DialogueSelectionKind::Service && pServiceHandler != nullptr)
    {
        runtime.dispatchServiceSelection(result.selection, *pServiceHandler);
    }
    result.content = buildMm9DialogueContent(runtime, result.selection.response);
    return result;
}
}
