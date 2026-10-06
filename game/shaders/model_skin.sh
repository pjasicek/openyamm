// One RGBA32F row per world-space joint matrix, followed by its inverse-transpose normal matrix.
SAMPLER2D(s_modelJoints, 5);
uniform vec4 u_modelSkin;

mat4 modelJointMatrix(float joint)
{
    float y = (joint + 0.5) * u_modelSkin.y;
    return mtxFromCols(texture2DLod(s_modelJoints, vec2(0.125, y), 0.0),
        texture2DLod(s_modelJoints, vec2(0.375, y), 0.0),
        texture2DLod(s_modelJoints, vec2(0.625, y), 0.0),
        texture2DLod(s_modelJoints, vec2(0.875, y), 0.0));
}

vec3 modelSkinnedPosition(vec3 position)
{
    vec3 result = vec3(0.0, 0.0, 0.0);
    for (int index = 0; index < 4; ++index)
    {
        if (a_weight[index] > 0.0)
        {
            result += a_weight[index] * mul(modelJointMatrix(float(a_indices[index])), vec4(position, 1.0)).xyz;
        }
        if (a_texcoord3[index] > 0.0)
        {
            result += a_texcoord3[index] * mul(modelJointMatrix(float(a_texcoord5[index])), vec4(position, 1.0)).xyz;
        }
    }
    return result;
}

vec3 modelSkinnedNormal(vec3 normal)
{
    vec3 result = vec3(0.0, 0.0, 0.0);
    for (int index = 0; index < 4; ++index)
    {
        if (a_weight[index] > 0.0)
        {
            result += a_weight[index] * mul(modelJointMatrix(float(a_indices[index]) + u_modelSkin.z),
                vec4(normal, 0.0)).xyz;
        }
        if (a_texcoord3[index] > 0.0)
        {
            result += a_texcoord3[index] * mul(modelJointMatrix(float(a_texcoord5[index]) + u_modelSkin.z),
                vec4(normal, 0.0)).xyz;
        }
    }
    float magnitude = length(result);
    return magnitude > 0.0 ? result / magnitude : result;
}
