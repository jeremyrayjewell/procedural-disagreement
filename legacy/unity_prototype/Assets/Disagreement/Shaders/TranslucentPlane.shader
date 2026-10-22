// Double-sided unlit translucent sheet with a brighter border, used for the cutting planes.
// _Opacity may exceed 1 to flash the plane at the moment of its cut.
Shader "Disagreement/TranslucentPlane"
{
    Properties
    {
        _Color ("Color", Color) = (1, 1, 1, 0.35)
        _Opacity ("Opacity", Float) = 1
        _EdgeBoost ("Edge Boost", Range(0, 4)) = 1.6
    }
    SubShader
    {
        Tags { "Queue" = "Transparent+10" "RenderType" = "Transparent" "IgnoreProjector" = "True" }

        Pass
        {
            Cull Off
            ZWrite Off
            Blend SrcAlpha OneMinusSrcAlpha

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "UnityCG.cginc"

            fixed4 _Color;
            half _Opacity;
            half _EdgeBoost;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_FOG_COORDS(1)
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.texcoord.xy;
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float2 d = abs(i.uv - 0.5) * 2.0;
                float edge = smoothstep(0.92, 1.0, max(d.x, d.y));
                fixed4 col = _Color;
                col.rgb *= 1.0 + edge * 0.5;
                col.a = saturate(_Color.a * (1.0 + edge * _EdgeBoost) * _Opacity);
                UNITY_APPLY_FOG(i.fogCoord, col);
                return col;
            }
            ENDCG
        }
    }
}
