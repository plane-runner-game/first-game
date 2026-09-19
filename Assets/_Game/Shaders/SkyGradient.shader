// SkyGradient.shader - the bright-day sky (2026-09-19, "bright day, match the colours with the new UI"): a clean two-colour gradient
// from a pale horizon to a saturated blue overhead, the flat cartoon sky of the reference game, plus a small sun disc and glow where
// the main light comes from. No texture, no haze band from a photograph: the horizon colour is a number the fog and the sea reuse.
Shader "SkySquad/SkyGradient"
{
    Properties
    {
        _TopColor ("Sky overhead", Color) = (0.20, 0.55, 0.92, 1)
        _HorizonColor ("Sky at the horizon", Color) = (0.62, 0.85, 0.98, 1)
        _GroundColor ("Below the horizon", Color) = (0.45, 0.70, 0.90, 1)
        _Curve ("Gradient curve", Range(0.2, 4)) = 1.1
        _SunColor ("Sun", Color) = (1, 0.98, 0.9, 1)
        _SunSize ("Sun size (cos)", Range(0.9, 1)) = 0.9975
        _SunGlow ("Sun glow", Range(0, 2)) = 0.6
    }
    SubShader
    {
        Tags { "Queue" = "Background" "RenderType" = "Background" "PreviewType" = "Skybox" "RenderPipeline" = "UniversalPipeline" }
        Cull Off ZWrite Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
            half4 _TopColor, _HorizonColor, _GroundColor, _SunColor;
            float _Curve, _SunSize, _SunGlow;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 dir : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.dir = v.positionOS.xyz;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float3 d = normalize(i.dir);
                float up = saturate(d.y);
                half3 col = lerp(_HorizonColor.rgb, _TopColor.rgb, pow(up, _Curve));
                col = lerp(_GroundColor.rgb, col, saturate(d.y * 40.0 + 0.5));   // a soft line at the horizon (the sea covers it anyway)
                float3 sun = normalize(_MainLightPosition.xyz);
                float cosA = dot(d, sun);
                float disc = smoothstep(_SunSize - 0.0015, _SunSize + 0.0005, cosA);
                float glow = pow(saturate(cosA), 32.0) * _SunGlow;
                col += _SunColor.rgb * (disc * 3.0 + glow);
                return half4(col, 1.0);
            }
            ENDHLSL
        }
    }
}
