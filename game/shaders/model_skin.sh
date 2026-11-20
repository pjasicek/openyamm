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
// Attributes are parameters: HLSL and Metal pass vertex inputs to main, not as globals.
mat4 modelSkinMatrix(float row, vec4 weights, uvec4 indices, vec4 weights2, uvec4 indices2)
{
    mat4 skin = weights[0] * modelJointMatrix(row, float(indices[0]));
    for (int index = 1; index < 4; ++index)
    {
        if (weights[index] > 0.0)
        {
            skin += weights[index] * modelJointMatrix(row, float(indices[index]));
        }
    }
    for (int index = 0; index < 4; ++index)
    {
        if (weights2[index] > 0.0)
        {
            skin += weights2[index] * modelJointMatrix(row, float(indices2[index]));
        }
    }
    return skin;
}

// Creature contour shell (outline flag 3): the vertex pushed out along its screen-space normal by pixelsPer1080 pixels
// per 1080 view rows (at least one) at its own depth. Only its back faces are drawn, after the body, so it shows as a
// dark rim past the silhouette and along limbs that cross the body; the rest fails the depth test.
vec4 modelContourPosition(vec3 worldPosition, vec3 worldNormal, float pixelsPer1080)
{
    vec4 clip = mul(u_viewProj, vec4(worldPosition, 1.0));
    vec2 screenNormal = mul(u_viewProj, vec4(worldNormal, 0.0)).xy * u_viewRect.zw;
    float pixels = max(1.0, pixelsPer1080 * u_viewRect.w / 1080.0);
    clip.xy += screenNormal / max(length(screenNormal), 0.0001) * (pixels * 2.0) / u_viewRect.zw * clip.w;
    return clip;
}
