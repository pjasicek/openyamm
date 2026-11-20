#pragma once

#include <functional>
#include <string>
#include <utility>
#include <vector>

namespace OpenYAMM::Game
{
// What one stage did to a hit, for the damage breakdown and the combat log.
struct DamageStageRecord
{
    std::string stage;
    int before = 0;
    int after = 0;
};

// Damage as named stages run in order (devdocs/maw/HANDOFF.md §3.6). A stage changes Hit::amount and may set
// Hit::stop to end the hit there. Each ruleset builds its own list, reusing the Standard stages it agrees with.
template <typename Hit>
class DamagePipeline
{
public:
    using Stage = std::function<void(Hit &)>;

    void add(std::string name, Stage stage)
    {
        m_stages.emplace_back(std::move(name), std::move(stage));
    }

    // The final amount; with pRecord, one record per stage that ran.
    int run(Hit &hit, std::vector<DamageStageRecord> *pRecord = nullptr) const
    {
        for (const auto &[name, stage] : m_stages)
        {
            const int before = hit.amount;
            stage(hit);

            if (pRecord != nullptr)
            {
                pRecord->push_back({name, before, hit.amount});
            }

            if (hit.stop)
            {
                break;
            }
        }

        return hit.amount;
    }

    std::vector<std::string> stageNames() const
    {
        std::vector<std::string> names;

        for (const auto &stage : m_stages)
        {
            names.push_back(stage.first);
        }

        return names;
    }

private:
    std::vector<std::pair<std::string, Stage>> m_stages;
};
}
