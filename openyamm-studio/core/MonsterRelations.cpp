#include "core/MonsterRelations.h"

#include "core/Json.h"
#include "core/SketchRead.h"
#include "core/TableNames.h"

#include <algorithm>
#include <cctype>
#include <charconv>
#include <map>

namespace OpenYAMM::Studio
{
namespace
{
std::string lowerText(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char character)
    {
        return static_cast<char>(std::tolower(character));
    });
    return text;
}

int integerOf(const YAML::Node &node)
{
    const std::string &text = node.Scalar();
    double parsed = 0.0;
    const char *pBegin = text.data() + ((!text.empty() && text[0] == '+') ? 1 : 0);
    std::from_chars(pBegin, text.data() + text.size(), parsed);
    return static_cast<int>(parsed);
}

std::string luaSide(const MonsterRelationSide &side)
{
    if (side.group != 0)
    {
        return "{group = " + std::to_string(side.group) + "}";
    }

    return std::to_string(side.monster);
}

// A list of words: "a", "a and b", "a, b and c".
std::string listed(const std::vector<std::string> &words)
{
    std::string text;

    for (size_t index = 0; index < words.size(); ++index)
    {
        text += (index == 0 ? "" : index + 1 == words.size() ? " and " : ", ") + words[index];
    }

    return text;
}

std::string numberList(const std::set<int> &numbers)
{
    std::string text;

    for (const int number : numbers)
    {
        text += (text.empty() ? "" : ", ") + std::to_string(number);
    }

    return text;
}

int relationClass(int monster)
{
    return monster > 0 ? (monster - 1) / 3 + 1 : 0;
}
}

std::vector<MonsterRelationRow> readMonsterRelations(
    const YAML::Node &relations,
    const std::string &file,
    const MonsterNumberLookup &monsterNumber,
    std::vector<ProjectIssue> &issues)
{
    std::vector<MonsterRelationRow> rows;

    if (!relations || !relations.IsSequence())
    {
        return rows;
    }

    // One side: a monster kind's number, {group: n} or the party.
    const auto side = [&](const YAML::Node &value, const std::string &path, bool partyAllowed)
        -> std::optional<MonsterRelationSide>
    {
        noteRead(value);

        if (partyAllowed && value.IsScalar() && value.Scalar() == "party")
        {
            return MonsterRelationSide{};
        }

        if (value.IsMap() && value.size() == 1 && value["group"]
            && classifyScalar(value["group"]) == ScalarKind::Integer)
        {
            const int group = integerOf(value["group"]);

            if (group < 1 || group > 32767)
            {
                issues.push_back({file, path + ".group", "a group is 1 to 32767", "schema"});
                return std::nullopt;
            }

            return MonsterRelationSide{0, group};
        }

        const std::optional<int> monster = value.IsScalar() ? monsterNumber(value, path) : std::nullopt;

        if (!monster)
        {
            if (!value.IsScalar())
            {
                issues.push_back({file, path, std::string("a side of a relation is a monster (its number or name in "
                    "monster_data.txt), {group: <n>}") + (partyAllowed ? " or party" : ""), "schema"});
            }

            return std::nullopt;
        }

        return MonsterRelationSide{*monster, 0};
    };

    size_t index = 0;

    for (const YAML::Node &relation : relations)
    {
        const std::string path = "relations[" + std::to_string(index++) + "]";
        static const std::map<std::string, int> named = {{"friendly", 0}, {"hostile", 4}};
        const YAML::Node level = relation.IsMap() ? relation["relation"] : YAML::Node();
        int number = -1;

        if (level && level.IsScalar() && named.contains(level.Scalar()))
        {
            number = named.at(level.Scalar());
        }
        else if (level && classifyScalar(level) == ScalarKind::Integer)
        {
            number = integerOf(level);
        }

        if (level)
        {
            noteRead(level);
        }

        const bool known = relation.IsMap() && std::all_of(relation.begin(), relation.end(), [](const auto &entry)
        {
            const std::string name = entry.first.Scalar();
            return name == "of" || name == "toward" || name == "relation" || name == "both_ways";
        });

        if (!known || !relation["of"] || !relation["toward"] || number < 0 || number > 4)
        {
            issues.push_back({file, path, "a relation is {of: <monsters>, toward: <party or monsters>, relation: "
                "<friendly, hostile, or 0 (friendly) to 4 (hostile at any distance), as hostile.txt>, both_ways: "
                "<true: the other side's too>}; monsters are a kind (its number or name in monster_data.txt), a "
                "list of kinds or {group: <n>}", "schema"});
            continue;
        }

        std::vector<MonsterRelationSide> left;
        const YAML::Node of = relation["of"];

        for (size_t at = 0; at < (of.IsSequence() ? of.size() : 1); ++at)
        {
            const std::optional<MonsterRelationSide> one = side(of.IsSequence() ? of[at] : of,
                path + ".of" + (of.IsSequence() ? "[" + std::to_string(at) + "]" : std::string()), false);

            if (one)
            {
                left.push_back(*one);
            }
        }

        const std::optional<MonsterRelationSide> right = side(relation["toward"], path + ".toward", true);
        const YAML::Node bothWaysNode = relation["both_ways"];
        const bool bothWays = bothWaysNode && bothWaysNode.IsScalar() && bothWaysNode.Scalar() == "true";

        if (bothWaysNode)
        {
            noteRead(bothWaysNode);
        }

        if (!right || left.size() != (of.IsSequence() ? of.size() : 1))
        {
            continue;
        }

        if (bothWays && right->party())
        {
            issues.push_back({file, path + ".both_ways", "the party has no relation of its own: drop `both_ways`",
                "schema"});
            continue;
        }

        for (const MonsterRelationSide &one : left)
        {
            rows.push_back({one, *right, number, path});

            if (bothWays)
            {
                rows.push_back({*right, one, number, path});
            }
        }
    }

    return rows;
}

std::vector<std::string> monsterRelationLines(const std::vector<MonsterRelationRow> &rows)
{
    std::vector<std::string> lines;

    for (const MonsterRelationRow &row : rows)
    {
        lines.push_back("evt.SetMonsterRelation(" + luaSide(row.of) + ", " + luaSide(row.toward) + ", "
            + std::to_string(row.relation) + ")");
    }

    return lines;
}

void readMapSlots(
    const YAML::Node &card,
    const std::vector<std::vector<std::string>> &mapStatsRows,
    MapMonsters &monsters)
{
    const YAML::Node stats = card.IsMap() ? card["map_stats"] : YAML::Node();

    if (!stats || !stats.IsMap())
    {
        return;
    }

    // The reference row: encounter slot n's picture in column 16 + 4 (n - 1), its name in the next (the game takes
    // the picture, or the name when there is none); "0" is none.
    const YAML::Node reference = stats["reference"];

    if (reference && reference.IsScalar())
    {
        const std::string wanted = lowerText(reference.Scalar());

        for (const std::vector<std::string> &row : mapStatsRows)
        {
            if (row.size() <= 2 || lowerText(row[2]) != wanted)
            {
                continue;
            }

            for (size_t slot = 0; slot < 3; ++slot)
            {
                const size_t column = 16 + slot * 4;
                std::string family = column < row.size() ? row[column] : std::string();
                family = family.empty() && column + 1 < row.size() ? row[column + 1] : family;

                if (!family.empty() && family != "0")
                {
                    monsters.slots[slot] = family;
                    monsters.shippedSlots.push_back(family);
                }
            }

            break;
        }
    }

    const YAML::Node slots = stats["slots"];

    for (size_t slot = 0; slots && slots.IsSequence() && slot < slots.size() && slot < 3; ++slot)
    {
        const YAML::Node monster = slots[slot].IsMap() ? slots[slot]["monster"] : YAML::Node();

        if (monster && monster.IsScalar())
        {
            monsters.slots[slot] = monster.Scalar();
        }
    }
}

std::vector<std::string> monsterHostilityWarnings(
    const MapMonsters &monsters,
    const std::vector<std::vector<std::string>> &monsterRows,
    const std::vector<std::vector<std::string>> &relationRows,
    const std::string &file)
{
    std::vector<std::string> warnings;

    if (monsterRows.empty() || relationRows.size() < 2)
    {
        return warnings;
    }

    // The monster table's names and pictures by number.
    std::map<int, const std::vector<std::string> *> rowOf;
    std::map<std::string, int> numberOfPicture;

    for (const std::vector<std::string> &row : monsterRows)
    {
        const int number = cellNumber(row, 0).value_or(0);

        if (number > 0 && row.size() > 2)
        {
            rowOf.emplace(number, &row);
            numberOfPicture.emplace(lowerText(row[2]), number);
        }
    }

    const auto nameOf = [&rowOf](int monster)
    {
        const auto found = rowOf.find(monster);
        return found != rowOf.end() ? (*found->second)[1] : std::to_string(monster);
    };

    // hostile.txt: a header, then a row per relation class (0 the party) toward which the columns' classes have
    // that relation: the game's m_relations[toward][of].
    const auto tableRelation = [&relationRows](int ofClass, int towardClass)
    {
        const size_t row = static_cast<size_t>(towardClass) + 1;
        const size_t column = static_cast<size_t>(ofClass) + 1;
        return row < relationRows.size() && column < relationRows[row].size()
            ? cellNumber(relationRows[row], column).value_or(0) : 0;
    };

    // The relation rows the game finds for an actor of `monster` (group `group`) toward another (or the party):
    // the map's script sets them in order, a later row over an earlier one.
    const auto overrideOf = [&monsters](const MonsterRelationSide &of, const MonsterRelationSide &toward)
    {
        std::optional<int> found;

        for (const MonsterRelationRow &row : monsters.relations)
        {
            if (row.of.monster == of.monster && row.of.group == of.group && row.toward.monster == toward.monster
                && row.toward.group == toward.group)
            {
                found = row.relation;
            }
        }

        return found;
    };

    // Every kind that may stand in the map, once per group and source.
    struct Member
    {
        int monster = 0;
        int group = 0;
        // "slot 2" or the placed monster's id.
        std::string source;
        int slot = 0;
        bool placed = false;
        bool hostile = false;
        bool said = false;
        bool shipped = false;
    };

    std::vector<Member> members;
    const auto addMember = [&members](const Member &member)
    {
        const bool known = std::any_of(members.begin(), members.end(), [&member](const Member &other)
        {
            return other.monster == member.monster && other.group == member.group && other.slot == member.slot
                && other.placed == member.placed && other.hostile == member.hostile && other.said == member.said;
        });

        if (!known)
        {
            members.push_back(member);
        }
    };

    for (const MapMonsters::Spawn &spawn : monsters.spawns)
    {
        if (spawn.slot < 1 || spawn.slot > 3 || monsters.slots[static_cast<size_t>(spawn.slot - 1)].empty())
        {
            continue;
        }

        const std::string family = monsters.slots[static_cast<size_t>(spawn.slot - 1)];
        const bool shipped = std::any_of(monsters.shippedSlots.begin(), monsters.shippedSlots.end(),
            [&family](const std::string &other) { return lowerText(other) == lowerText(family); });

        for (const char tier : std::string("ABC"))
        {
            const auto found = numberOfPicture.find(lowerText(family + " " + tier));

            if ((spawn.tier == '\0' || spawn.tier == tier) && found != numberOfPicture.end())
            {
                Member member;
                member.monster = found->second;
                member.group = spawn.group;
                member.source = "slot " + std::to_string(spawn.slot);
                member.slot = spawn.slot;
                member.shipped = shipped;
                addMember(member);
            }
        }
    }

    for (const MapMonsters::Placed &placed : monsters.placed)
    {
        Member member;
        member.monster = placed.monster;
        member.group = placed.group;
        member.source = !placed.id.empty() ? placed.id : "a placed " + nameOf(placed.monster);
        member.placed = true;
        member.hostile = placed.hostile.value_or(false);
        member.said = placed.hostile.has_value();
        addMember(member);
    }

    // Each one's relation to the party: its kind's row toward the party, else a peaceful group, else `hostile`,
    // else the table.
    for (Member &member : members)
    {
        if (const std::optional<int> relation = overrideOf({member.monster, 0}, {}))
        {
            member.hostile = *relation > 0;
            member.said = true;
        }
        else if (member.group > 0 && monsters.peacefulGroups.contains(member.group))
        {
            member.hostile = false;
            member.said = true;
        }
        else if (!member.said)
        {
            member.hostile = tableRelation(relationClass(member.monster), 0) > 0;
        }
    }

    // "monster:guard (Archer)", "slot 2 (Bowman)", "a placed Archer".
    const auto described = [&nameOf](const Member &member)
    {
        return member.source.rfind("a placed ", 0) == 0 ? member.source
            : member.source + " (" + nameOf(member.monster) + ")";
    };
    std::set<int> shippedClasses;

    for (const Member &member : members)
    {
        if (member.shipped)
        {
            shippedClasses.insert(relationClass(member.monster));
        }
    }

    // Slots whose monsters leave the party alone, unsaid.
    for (int slot = 1; slot <= 3; ++slot)
    {
        std::set<int> kinds;
        std::vector<std::string> names;

        for (const Member &member : members)
        {
            if (member.slot == slot && !member.placed && !member.hostile && !member.said && !member.shipped
                && kinds.insert(member.monster).second)
            {
                names.push_back(nameOf(member.monster));
            }
        }

        if (kinds.empty())
        {
            continue;
        }

        const std::string family = monsters.slots[static_cast<size_t>(slot - 1)];
        warnings.push_back("slot " + std::to_string(slot) + " (" + family + ") spawns " + listed(names) + " ("
            + numberList(kinds) + "), which engine/data_tables/hostile.txt has friendly to the party: they leave the "
            "party alone until it strikes them. To have them fight the party, add to " + file + " `relations` {of: ["
            + numberList(kinds) + "], toward: party, relation: hostile}; if they are to be peaceful, say so there "
            "with relation: friendly");
    }

    // Placed monsters left peaceful by the table beside hostile ones of their kind.
    std::map<int, std::vector<const Member *>> byClass;

    for (const Member &member : members)
    {
        byClass[relationClass(member.monster)].push_back(&member);
    }

    for (const std::pair<const int, std::vector<const Member *>> &kind : byClass)
    {
        std::vector<std::string> peaceful;
        std::vector<std::string> hostile;
        std::set<int> kinds;

        for (const Member *pMember : kind.second)
        {
            if (pMember->placed && !pMember->hostile && !pMember->said)
            {
                peaceful.push_back(described(*pMember));
                kinds.insert(pMember->monster);
            }
            else if (pMember->hostile && hostile.size() < 3)
            {
                hostile.push_back(described(*pMember));
            }
        }

        if (peaceful.empty() || hostile.empty() || shippedClasses.contains(kind.first))
        {
            continue;
        }

        warnings.push_back(listed(peaceful) + (peaceful.size() == 1 ? " is" : " are") + " of a kind that "
            "engine/data_tables/hostile.txt has friendly to the party (" + numberList(kinds) + "), so "
            + (peaceful.size() == 1 ? "it leaves" : "they leave") + " the party alone, while " + listed(hostile)
            + " of that kind " + (hostile.size() == 1 ? "is" : "are") + " hostile: say which is meant with "
            "`hostile: true`, or `hostile: false` and a `group` of their own");
    }

    // Kinds both hostile to the party that the table sets on each other.
    struct Fight
    {
        std::set<int> first;
        std::set<int> second;
        std::vector<std::string> firstSources;
        std::vector<std::string> secondSources;
        int firstToward = 0;
        int secondToward = 0;
    };

    std::map<std::pair<int, int>, Fight> fights;
    // An actor's relation toward a target as the game takes it: a row of the map's script (the actor's group toward
    // the target's kind, its kind toward the target's group, kind toward kind), else none between one group, else
    // the table. Nothing when a row of the project says it.
    const auto unsaidRelation = [&](const Member &actor, const Member &target) -> int
    {
        if ((actor.group != 0 && overrideOf({0, actor.group}, {target.monster, 0}))
            || (target.group != 0 && overrideOf({actor.monster, 0}, {0, target.group}))
            || overrideOf({actor.monster, 0}, {target.monster, 0}))
        {
            return 0;
        }

        if (actor.group != 0 && actor.group == target.group)
        {
            return 0;
        }

        return tableRelation(relationClass(actor.monster), relationClass(target.monster));
    };

    for (size_t first = 0; first < members.size(); ++first)
    {
        for (size_t second = first + 1; second < members.size(); ++second)
        {
            const Member *pFirst = &members[first];
            const Member *pSecond = &members[second];
            int firstClass = relationClass(pFirst->monster);
            int secondClass = relationClass(pSecond->monster);

            if (firstClass == secondClass || !pFirst->hostile || !pSecond->hostile
                || shippedClasses.contains(firstClass) || shippedClasses.contains(secondClass))
            {
                continue;
            }

            if (firstClass > secondClass)
            {
                std::swap(pFirst, pSecond);
                std::swap(firstClass, secondClass);
            }

            const int firstToward = unsaidRelation(*pFirst, *pSecond);
            const int secondToward = unsaidRelation(*pSecond, *pFirst);

            if (firstToward <= 0 && secondToward <= 0)
            {
                continue;
            }

            Fight &fight = fights[{firstClass, secondClass}];
            fight.first.insert(pFirst->monster);
            fight.second.insert(pSecond->monster);
            fight.firstToward = std::max(fight.firstToward, firstToward);
            fight.secondToward = std::max(fight.secondToward, secondToward);

            if (std::find(fight.firstSources.begin(), fight.firstSources.end(), pFirst->source)
                == fight.firstSources.end() && fight.firstSources.size() < 3)
            {
                fight.firstSources.push_back(pFirst->source);
            }

            if (std::find(fight.secondSources.begin(), fight.secondSources.end(), pSecond->source)
                == fight.secondSources.end() && fight.secondSources.size() < 3)
            {
                fight.secondSources.push_back(pSecond->source);
            }
        }
    }

    for (const std::pair<const std::pair<int, int>, Fight> &entry : fights)
    {
        const Fight &fight = entry.second;
        std::vector<std::string> firstNames;
        std::vector<std::string> secondNames;
        std::vector<std::string> others;

        for (const int monster : fight.first)
        {
            firstNames.push_back(nameOf(monster));
        }

        for (const int monster : fight.second)
        {
            secondNames.push_back(nameOf(monster));
            others.push_back(std::to_string(monster));
        }

        const std::string rowText = "{of: [" + numberList(fight.first) + "], toward: " + others.front()
            + ", relation: friendly, both_ways: true}";
        warnings.push_back(listed(firstNames) + " (" + listed(fight.firstSources) + ") and " + listed(secondNames)
            + " (" + listed(fight.secondSources) + ") are both hostile to the party, and "
            "engine/data_tables/hostile.txt sets them on each other (" + std::to_string(fight.firstToward) + " and "
            + std::to_string(fight.secondToward) + "): they fight wherever they meet. To keep them from it, add to "
            + file + " `relations` " + rowText
            + (others.size() > 1 ? " and the same toward " + listed(std::vector<std::string>(others.begin() + 1,
                others.end())) : std::string())
            + "; if they are to fight, say so there with relation: hostile");
    }

    // A group's relation toward the party: the game takes the party's foes by kind only.
    for (const MonsterRelationRow &row : monsters.relations)
    {
        if (row.of.group != 0 && row.toward.party())
        {
            warnings.push_back(file + " " + row.path + ": a group's relation toward the party does nothing: the game "
                "sets a monster's relation to the party by its kind (evt.SetMonsterRelation(<kind>, 0, ...)). Name "
                "the kinds in `of`, or give the placed monsters `hostile`");
        }
    }

    return warnings;
}
}
