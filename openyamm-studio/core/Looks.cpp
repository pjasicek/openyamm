#include "core/Looks.h"

#include <algorithm>
#include <cctype>
#include <cmath>

namespace OpenYAMM::Studio
{
std::optional<std::array<double, 2>> texelRates(
    const std::vector<std::array<double, 3>> &points, const std::vector<std::array<double, 2>> &texels)
{
    if (points.size() < 3 || texels.size() != points.size())
    {
        return std::nullopt;
    }

    const auto subtract = [](const std::array<double, 3> &left, const std::array<double, 3> &right)
    {
        return std::array<double, 3>{left[0] - right[0], left[1] - right[1], left[2] - right[2]};
    };
    const auto dot = [](const std::array<double, 3> &left, const std::array<double, 3> &right)
    {
        return left[0] * right[0] + left[1] * right[1] + left[2] * right[2];
    };
    size_t second = 1;
    size_t third = 2;
    double area = -1.0;

    for (size_t one = 1; one + 1 < points.size(); ++one)
    {
        for (size_t two = one + 1; two < points.size(); ++two)
        {
            const std::array<double, 3> a = subtract(points[one], points[0]);
            const std::array<double, 3> b = subtract(points[two], points[0]);
            const std::array<double, 3> across = {
                a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};

            if (dot(across, across) > area)
            {
                area = dot(across, across);
                second = one;
                third = two;
            }
        }
    }

    // The gradient g of each coordinate in the face's plane: g . (corner - first corner) = its change there.
    const std::array<double, 3> one = subtract(points[second], points[0]);
    const std::array<double, 3> two = subtract(points[third], points[0]);
    const double oneOne = dot(one, one);
    const double oneTwo = dot(one, two);
    const double twoTwo = dot(two, two);
    const double determinant = oneOne * twoTwo - oneTwo * oneTwo;

    if (determinant < 1.0)
    {
        return std::nullopt;
    }

    std::array<double, 2> rates = {};

    for (size_t component = 0; component < 2; ++component)
    {
        const double alongOne = texels[second][component] - texels[0][component];
        const double alongTwo = texels[third][component] - texels[0][component];
        const double a = (alongOne * twoTwo - alongTwo * oneTwo) / determinant;
        const double b = (alongTwo * oneOne - alongOne * oneTwo) / determinant;
        const std::array<double, 3> gradient = {
            a * one[0] + b * two[0], a * one[1] + b * two[1], a * one[2] + b * two[2]};
        rates[component] = std::sqrt(dot(gradient, gradient));
    }

    if (rates[0] < 1.0e-6 || rates[1] < 1.0e-6)
    {
        return std::nullopt;
    }

    return rates;
}

bool decorationHangs(const std::string &hint)
{
    std::string lower = hint;
    std::transform(lower.begin(), lower.end(), lower.begin(),
        [](unsigned char character) { return static_cast<char>(std::tolower(character)); });

    for (const char *pWord : {"chandelier", "lantern", "sconce", "torch", "flambeaux", "cage", "flag", "noose",
             "stalagtite", "stalactite", "buoy", "lily", "seaweed", "banner", "hang"})
    {
        if (lower.find(pWord) != std::string::npos)
        {
            return true;
        }
    }

    return false;
}
}
