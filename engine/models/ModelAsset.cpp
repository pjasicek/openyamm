#include "engine/models/ModelAsset.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace OpenYAMM::Engine
{
std::optional<uint32_t> ModelAsset::findMaterialVariant(const std::string &name) const
{
    const auto iterator = std::find(materialVariants.begin(), materialVariants.end(), name);
    return iterator == materialVariants.end() ? std::nullopt
        : std::optional<uint32_t>(uint32_t(iterator - materialVariants.begin()) + 1);
}

std::optional<uint32_t> ModelAsset::findNode(const std::string &name) const
{
    const auto iterator = nodeIndicesByName.find(name);
    if (iterator == nodeIndicesByName.end())
    {
        return std::nullopt;
    }
    return iterator->second;
}

std::optional<uint32_t> ModelAsset::findClip(const std::string &name) const
{
    const auto iterator = clipIndicesByName.find(name);
    if (iterator == clipIndicesByName.end())
    {
        return std::nullopt;
    }
    return iterator->second;
}

ModelMatrix identityModelMatrix()
{
    return {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f,
    };
}

ModelMatrix composeModelTransform(const ModelTransform &transform)
{
    float x = transform.rotation[0];
    float y = transform.rotation[1];
    float z = transform.rotation[2];
    float w = transform.rotation[3];
    const float length = std::sqrt(x * x + y * y + z * z + w * w);
    if (length > 0.0f)
    {
        x /= length;
        y /= length;
        z /= length;
        w /= length;
    }
    else
    {
        x = 0.0f;
        y = 0.0f;
        z = 0.0f;
        w = 1.0f;
    }

    const float xx = x * x;
    const float yy = y * y;
    const float zz = z * z;
    const float xy = x * y;
    const float xz = x * z;
    const float yz = y * z;
    const float wx = w * x;
    const float wy = w * y;
    const float wz = w * z;

    ModelMatrix result = identityModelMatrix();
    result[0] = (1.0f - 2.0f * (yy + zz)) * transform.scale[0];
    result[1] = (2.0f * (xy + wz)) * transform.scale[0];
    result[2] = (2.0f * (xz - wy)) * transform.scale[0];
    result[4] = (2.0f * (xy - wz)) * transform.scale[1];
    result[5] = (1.0f - 2.0f * (xx + zz)) * transform.scale[1];
    result[6] = (2.0f * (yz + wx)) * transform.scale[1];
    result[8] = (2.0f * (xz + wy)) * transform.scale[2];
    result[9] = (2.0f * (yz - wx)) * transform.scale[2];
    result[10] = (1.0f - 2.0f * (xx + yy)) * transform.scale[2];
    result[12] = transform.translation[0];
    result[13] = transform.translation[1];
    result[14] = transform.translation[2];
    return result;
}

ModelMatrix multiplyModelMatrices(const ModelMatrix &left, const ModelMatrix &right)
{
    ModelMatrix result = {};
    for (size_t column = 0; column < 4; ++column)
    {
        for (size_t row = 0; row < 4; ++row)
        {
            for (size_t index = 0; index < 4; ++index)
            {
                result[column * 4 + row] += left[index * 4 + row] * right[column * 4 + index];
            }
        }
    }
    return result;
}

ModelTransform gltfModelPlacement(
    const std::array<float, 3> &openYammPosition,
    float yawRadians,
    float uniformScale)
{
    const float halfYaw = yawRadians * 0.5f;
    const float sineYaw = std::sin(halfYaw);
    const float cosineYaw = std::cos(halfYaw);
    constexpr float HalfSqrtTwo = 0.7071067811865475244f;
    return gltfModelPlacement(
        openYammPosition,
        {0.0f, 0.0f, sineYaw, cosineYaw},
        uniformScale);
}

ModelTransform gltfModelPlacement(
    const std::array<float, 3> &openYammPosition,
    const std::array<float, 4> &openYammRotation,
    float uniformScale)
{
    constexpr float HalfSqrtTwo = 0.7071067811865475244f;
    const float x = openYammRotation[0];
    const float y = openYammRotation[1];
    const float z = openYammRotation[2];
    const float w = openYammRotation[3];
    return {
        .translation = openYammPosition,
        .rotation = {
            (w + x) * HalfSqrtTwo,
            (y + z) * HalfSqrtTwo,
            (z - y) * HalfSqrtTwo,
            (w - x) * HalfSqrtTwo,
        },
        .scale = {uniformScale, uniformScale, -uniformScale},
    };
}
float determinant3x3(const ModelMatrix &matrix)
{
    return matrix[0] * (matrix[5] * matrix[10] - matrix[9] * matrix[6]) -
        matrix[4] * (matrix[1] * matrix[10] - matrix[9] * matrix[2]) +
        matrix[8] * (matrix[1] * matrix[6] - matrix[5] * matrix[2]);
}

ModelMatrix modelNormalMatrix(const ModelMatrix &matrix)
{
    const float determinant = determinant3x3(matrix);
    if (std::abs(determinant) <= std::numeric_limits<float>::epsilon())
    {
        return identityModelMatrix();
    }

    const float inverseDeterminant = 1.0f / determinant;
    ModelMatrix result = {};
    result[0] = (matrix[5] * matrix[10] - matrix[9] * matrix[6]) * inverseDeterminant;
    result[1] = (matrix[8] * matrix[6] - matrix[4] * matrix[10]) * inverseDeterminant;
    result[2] = (matrix[4] * matrix[9] - matrix[8] * matrix[5]) * inverseDeterminant;
    result[4] = (matrix[9] * matrix[2] - matrix[1] * matrix[10]) * inverseDeterminant;
    result[5] = (matrix[0] * matrix[10] - matrix[8] * matrix[2]) * inverseDeterminant;
    result[6] = (matrix[8] * matrix[1] - matrix[0] * matrix[9]) * inverseDeterminant;
    result[8] = (matrix[1] * matrix[6] - matrix[5] * matrix[2]) * inverseDeterminant;
    result[9] = (matrix[4] * matrix[2] - matrix[0] * matrix[6]) * inverseDeterminant;
    result[10] = (matrix[0] * matrix[5] - matrix[4] * matrix[1]) * inverseDeterminant;
    result[15] = 1.0f;
    return result;
}


bool modelMatrixVisible(const ModelMatrix &matrix)
{
    return std::abs(determinant3x3(matrix)) > std::numeric_limits<float>::epsilon();
}

}
