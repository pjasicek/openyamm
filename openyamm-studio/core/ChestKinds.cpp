#include "core/ChestKinds.h"

#include <algorithm>
#include <cctype>
#include <tuple>

namespace OpenYAMM::Studio
{
std::optional<ChestKind> chestKindOf(const std::string &name)
{
    ChestKind kind;

    if (name == "ch1" || name == "ch2" || name == "ch3" || name == "ch4" || name == "ch5")
    {
        kind.frontLeft = name + "frle";
        kind.frontMiddle = name + (name == "ch5" ? "frnt" : "frntb");
        kind.frontRight = name + "frre";
        kind.side = name + "side";
        kind.topLeft = name + (name == "ch5" ? "toplb" : "tople");
        kind.topMiddle = name + (name == "ch4" ? "top" : "topb");
        kind.topRight = name + (name == "ch5" ? "toprb" : "topre");
        return kind;
    }

    const bool gt = name == "7gt002" || name == "gt002";
    const bool numbered = name.size() == 5 && name.starts_with("ch00") && name[4] >= '1' && name[4] <= '6';

    if (!gt && !numbered)
    {
        return std::nullopt;
    }

    // 7gt002 and gt002 by the letters a (middle), b (ends), c (short ends), e (front slope), g (short ends' upper
    // strip); the ch001 to ch006 families each one letter on (b, c, d, f, h).
    const auto letter = [&name, gt](char gtLetter)
    {
        return name + std::string(1, static_cast<char>(gt ? gtLetter : gtLetter + 1));
    };

    kind.frontLeft = letter('b');
    kind.frontMiddle = letter('a');
    kind.frontRight = kind.frontLeft;
    kind.side = letter('c');
    kind.topLeft = kind.frontLeft;
    kind.topMiddle = kind.frontMiddle;
    kind.topRight = kind.frontLeft;
    kind.sloped = true;
    kind.slopeMiddle = letter('e');
    kind.sideTop = letter('g');
    kind.size = {96.0, 64.0, 80.0};
    return kind;
}

std::string chestKindList()
{
    return "the kinds are ch1, ch2, ch3, ch4 and ch5 (MM6's flat-lidded chests), 7gt002 (MM7's), gt002 (MM8's) and "
        "ch001 to ch006 (chests with a sloping lid)";
}

std::string chestFamilyOfMiddle(const std::string &texture)
{
    std::string lower = texture;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c)
    {
        return static_cast<char>(std::tolower(c));
    });

    for (const char *pName : {"ch1", "ch2", "ch3", "ch4", "ch5", "7gt002", "gt002", "ch001", "ch002", "ch003",
             "ch004", "ch005", "ch006"})
    {
        const std::optional<ChestKind> kind = chestKindOf(pName);

        if (kind && (lower == kind->frontMiddle || (!kind->sloped && lower == std::string(pName) + "frnt")))
        {
            return pName;
        }
    }

    return {};
}

bool isChestTexture(const std::string &texture)
{
    std::string lower = texture;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c)
    {
        return static_cast<char>(std::tolower(c));
    });

    // The kinds' own pictures (chestKindOf), and MM6's lid and back variants (ch3tpbv, ch1bkre).
    for (const char *pName : {"ch1", "ch2", "ch3", "ch4", "ch5", "7gt002", "gt002", "ch001", "ch002", "ch003",
             "ch004", "ch005", "ch006"})
    {
        const std::optional<ChestKind> kind = chestKindOf(pName);

        for (const std::string &picture : {kind->frontLeft, kind->frontMiddle, kind->frontRight, kind->side,
                 kind->topLeft, kind->topMiddle, kind->topRight, kind->slopeMiddle, kind->sideTop})
        {
            if (!picture.empty() && lower == picture)
            {
                return true;
            }
        }

        const std::string family = pName;

        const std::string rest = lower.size() > 3 ? lower.substr(3) : std::string();

        if (family.size() == 3 && lower.starts_with(family)
            && (rest.starts_with("fr") || rest.starts_with("tp") || rest.starts_with("top") || rest.starts_with("bk")
                || rest.starts_with("side")))
        {
            return true;
        }
    }

    return false;
}

std::string defaultChestKind(const std::string &styleWorld)
{
    return styleWorld == "mm8" ? "gt002" : styleWorld == "mm7" || styleWorld == "xeen" ? "7gt002" : "ch1";
}

std::vector<ChestFace> chestKindFaces(const ChestKind &kind, const std::array<double, 3> &size, double bottom,
    double top)
{
    using Corner = std::array<double, 3>;
    std::vector<ChestFace> faces;
    const double halfWidth = size[0] / 2.0;
    const double halfDepth = size[1] / 2.0;
    const double body = kind.sloped ? top - 16.0 : top;
    // MM6's ends are textures 16 wide of their own; MM7's and MM8's the first and last 16 columns of one 64 wide.
    const int endWidth = kind.sloped ? 64 : 16;
    const auto add = [&faces](ChestPart part, double sign, const std::string &texture, int width,
                         std::vector<Corner> corners, std::vector<std::array<double, 2>> texels, const Corner &normal)
    {
        ChestFace face;
        face.part = part;
        face.sign = sign;
        face.texture = texture;
        face.width = width;
        face.corners = std::move(corners);
        face.texels = std::move(texels);
        face.normal = normal;
        faces.push_back(std::move(face));
    };
    // A strip across the chest's width: left end, middle and right end, from `leftAcross` (where the viewer of this
    // face has the left end) to the other side. `corner(across, 0)` is on the strip's edge where the picture's rows
    // are `vFrom`, `corner(across, 1)` on the other edge (`vTo`).
    const auto addStrip = [&](ChestPart part, double sign, const auto &corner, double leftAcross, const Corner &normal,
                              const std::string &left, const std::string &middle, const std::string &right,
                              double vFrom, double vTo)
    {
        const double direction = leftAcross > 0.0 ? -1.0 : 1.0;
        const double full = size[0];
        const std::array<std::tuple<double, double, std::string, double, int>, 3> pieces = {{
            {0.0, 16.0, left, 0.0, endWidth},
            {16.0, full - 16.0, middle, 0.0, 64},
            {full - 16.0, full, right, kind.sloped ? 48.0 : 0.0, endWidth}}};

        for (const std::tuple<double, double, std::string, double, int> &piece : pieces)
        {
            const double from = leftAcross + direction * std::get<0>(piece);
            const double to = leftAcross + direction * std::get<1>(piece);
            const double uFrom = std::get<3>(piece);
            const double uTo = uFrom + std::get<1>(piece) - std::get<0>(piece);
            add(part, sign, std::get<2>(piece), std::get<4>(piece),
                {corner(from, 0), corner(to, 0), corner(to, 1), corner(from, 1)},
                {{uFrom, vFrom}, {uTo, vFrom}, {uTo, vTo}, {uFrom, vTo}}, normal);
        }
    };

    // The front (+depth) and the back.
    for (const double sign : {1.0, -1.0})
    {
        addStrip(ChestPart::Side, sign, [sign, halfDepth, body, bottom](double across, int edge)
            {
                return Corner{across, sign * halfDepth, edge == 0 ? body : bottom};
            }, sign * halfWidth, {0.0, sign, 0.0}, kind.frontLeft, kind.frontMiddle, kind.frontRight, 0.0,
            body - bottom);
    }

    // The short ends (+width and -width), and under a sloping lid the strip above each.
    for (const double sign : {1.0, -1.0})
    {
        // Seen from outside this end, its left is toward -depth at the +width end.
        const double across = sign * halfWidth;
        add(ChestPart::End, sign, kind.side, 64,
            {{across, -sign * halfDepth, body}, {across, sign * halfDepth, body}, {across, sign * halfDepth, bottom},
                {across, -sign * halfDepth, bottom}},
            {{0.0, 0.0}, {size[1], 0.0}, {size[1], body - bottom}, {0.0, body - bottom}}, {sign, 0.0, 0.0});

        if (kind.sloped)
        {
            add(ChestPart::EndTop, sign, kind.sideTop, 64,
                {{across, -sign * halfDepth, body}, {across, sign * halfDepth, body},
                    {across, sign * (halfDepth - 16.0), top}, {across, -sign * (halfDepth - 16.0), top}},
                {{0.0, 64.0}, {size[1], 64.0}, {size[1] - 16.0, 48.0}, {16.0, 48.0}}, {sign, 0.0, 0.0});
        }
    }

    // The lid.
    const double topDepth = kind.sloped ? halfDepth - 16.0 : halfDepth;

    if (kind.sloped)
    {
        for (const double sign : {1.0, -1.0})
        {
            addStrip(ChestPart::Slope, sign, [sign, halfDepth, body, top](double across, int edge)
                {
                    return edge == 0 ? Corner{across, sign * (halfDepth - 16.0), top}
                                     : Corner{across, sign * halfDepth, body};
                }, sign * halfWidth, {0.0, sign, 1.0}, kind.frontLeft,
                sign > 0.0 ? kind.slopeMiddle : kind.frontMiddle, kind.frontRight, 48.0, 64.0);
        }
    }

    if (kind.lidAcross)
    {
        // From the +width end: left end, middle, right end; u from the front (+depth) to the back, v along.
        const std::array<std::tuple<double, double, std::string>, 3> pieces = {{
            {halfWidth, halfWidth - 16.0, kind.topLeft},
            {halfWidth - 16.0, 16.0 - halfWidth, kind.topMiddle},
            {16.0 - halfWidth, -halfWidth, kind.topRight}}};

        for (const std::tuple<double, double, std::string> &piece : pieces)
        {
            const double from = std::get<0>(piece);
            const double to = std::get<1>(piece);
            const double along = from - to;
            add(ChestPart::Top, 0.0, std::get<2>(piece), 64,
                {{from, topDepth, top}, {from, -topDepth, top}, {to, -topDepth, top}, {to, topDepth, top}},
                {{0.0, 0.0}, {2.0 * topDepth, 0.0}, {2.0 * topDepth, along}, {0.0, along}}, {0.0, 0.0, 1.0});
        }
    }
    else
    {
        addStrip(ChestPart::Top, 0.0, [topDepth, top](double across, int edge)
            {
                return Corner{across, edge == 0 ? topDepth : -topDepth, top};
            }, -halfWidth, {0.0, 0.0, 1.0}, kind.topLeft, kind.topMiddle, kind.topRight,
            kind.sloped ? 64.0 - 2.0 * topDepth : 0.0, kind.sloped ? 64.0 : 2.0 * topDepth);
    }

    return faces;
}
}
