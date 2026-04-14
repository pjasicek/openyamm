vec2 v_texcoord0    : TEXCOORD0 = vec2(0.0, 0.0);
vec4 v_texcoord1    : TEXCOORD1 = vec4(0.0, 0.0, 0.0, 0.0);
float v_screenspace : TEXCOORD2 = 0.0;
vec3 v_worldPosition: TEXCOORD3 = vec3(0.0, 0.0, 0.0);
vec4 v_color0       : COLOR0    = vec4(1.0, 1.0, 1.0, 1.0);
float v_depth       : FOG       = 0.0;

vec3 a_position     : POSITION;
vec4 a_color0       : COLOR0;
vec2 a_texcoord0    : TEXCOORD0;
vec4 a_texcoord1    : TEXCOORD1;
float a_texcoord2   : TEXCOORD2;
