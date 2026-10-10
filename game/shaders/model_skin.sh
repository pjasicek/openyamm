// Frame joint palette shared by every skinned model: world-space joint matrices, four RGBA32F texels each,
// 128 joints per texture row (512 texels wide). A skin starts at its own row (`row`); larger skins continue on the
// following rows. u_modelSkin: x = skinned, y = 1 / palette height, z = the skin's first row (non-instanced draws).
SAMPLER2D(s_modelJoints, 5);
uniform vec4 u_modelSkin;

mat4 modelJointMatrix(float row, float joint)
{
    float jointRow = floor(joint / 128.0);
    float x = (joint - jointRow * 128.0) * (4.0 / 512.0) + 0.5 / 512.0;
    float y = (row + jointRow + 0.5) * u_modelSkin.y;
    return mtxFromCols(texture2DLod(s_modelJoints, vec2(x, y), 0.0),
        texture2DLod(s_modelJoints, vec2(x + 1.0 / 512.0, y), 0.0),
        texture2DLod(s_modelJoints, vec2(x + 2.0 / 512.0, y), 0.0),
        texture2DLod(s_modelJoints, vec2(x + 3.0 / 512.0, y), 0.0));
}

// Linear-blend skin matrix of up to eight influences, fetched once and shared by position and normal. Joints carry
// rotation, translation and uniform scale, so the blended matrix also transforms normals (renormalized after).
mat4 modelSkinMatrix(float row)
{
    mat4 skin = a_weight[0] * modelJointMatrix(row, float(a_indices[0]));
    for (int index = 1; index < 4; ++index)
    {
        if (a_weight[index] > 0.0)
        {
            skin += a_weight[index] * modelJointMatrix(row, float(a_indices[index]));
        }
    }
    for (int index = 0; index < 4; ++index)
    {
        if (a_texcoord3[index] > 0.0)
        {
            skin += a_texcoord3[index] * modelJointMatrix(row, float(a_texcoord5[index]));
        }
    }
    return skin;
}
