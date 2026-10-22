// Translucent tinted shell for alternate realities.
// _Opacity is set per material (the whole reality fades together);
// _Glow is set per renderer to show energy in conduits and cells.
Shader "Disagreement/GhostShell"
{
    Properties
    {
        _Color ("Tint", Color) = (1, 0.6, 0.2, 1)
        _Opacity ("Opacity", Float) = 0.5
        _Glow ("Glow", Float) = 0
        _RimPower ("Rim Power", Range(0.5, 6)) = 2
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }

        Pass
        {
            Cull Back
            ZWrite Off
            Blend SrcAlpha OneMinusSrcAlpha

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "UnityCG.cginc"

            fixed4 _Color;
            half _Opacity;
            half _Glow;
            half _RimPower;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 normal : TEXCOORD0;
                float3 viewDir : TEXCOORD1;
                UNITY_FOG_COORDS(2)
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.viewDir = WorldSpaceViewDir(v.vertex);
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float3 n = normalize(i.normal);
                float3 v = normalize(i.viewDir);
                float rim = pow(1.0 - saturate(dot(n, v)), _RimPower);
                float shade = 0.65 + 0.35 * saturate(dot(n, normalize(float3(0.25, 0.85, -0.45))));
                fixed4 col;
                col.rgb = _Color.rgb * shade * (1.0 + _Glow * 0.9);
                col.a = saturate(_Opacity * (0.45 + 0.55 * rim + _Glow * 0.25));
                UNITY_APPLY_FOG(i.fogCoord, col);
                return col;
            }
            ENDCG
        }
    }
}
