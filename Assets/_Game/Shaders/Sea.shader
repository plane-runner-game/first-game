// Sea.shader - the ocean under the lane (URP, hand-written HLSL; no compute, runs on WebGL / phones).
// Four Gerstner waves displace a dense grid (MeshFactory.SeaGrid) in the vertex shader and give an analytic
// normal; two scrolling ripple-normal layers (SceneBuilder.SeaNormalTexture) add the chop. The world slides
// toward the camera: WorldScroller sets the global _SeaScroll (units travelled) and every wave / ripple is
// evaluated at (x, z + _SeaScroll), so the sea moves with the buoys and stops when the game pauses.
// Shading: deep -> shallow colour by wave height, a sunlit turquoise glow through the crests, the main
// light's diffuse and shadows (the squad's shadows land on the water), a stylised sky gradient reflection
// through a fresnel term (not the HDRI: its grey side made the 2026-09-16 sea "ugly"), sun glitter, foam
// on the crests from a tileable noise (SceneBuilder.SeaFoamTexture), fog. Requested 2026-09-18 after Crest
// turned out to be Built-in-only and never WebGL: "a better sea that works on the web".
Shader "SkySquad/Sea"
{
    Properties
    {
        _ShallowColor ("Shallow colour", Color) = (0.10, 0.66, 0.86, 1)
        _DeepColor ("Deep colour", Color) = (0.02, 0.26, 0.58, 1)
        _SSSColor ("Crest glow", Color) = (0.20, 0.85, 0.75, 1)
        _SkyHorizon ("Sky at the horizon", Color) = (0.80, 0.87, 0.95, 1)
        _SkyZenith ("Sky overhead", Color) = (0.34, 0.58, 0.92, 1)
        _FoamColor ("Foam", Color) = (0.95, 0.98, 1.0, 1)
        _BaseMap ("Ripple normals", 2D) = "bump" {}
        _FoamMap ("Foam noise", 2D) = "white" {}
        _Tiling ("Ripple tiles per unit", Float) = 0.12
        _NormalStrength ("Ripple strength", Range(0, 2)) = 0.45
        _WaveA ("Wave 1 (dir x, dir z, steepness, length)", Vector) = (0.15, -1, 0.10, 16)
        _WaveB ("Wave 2", Vector) = (0.6, -0.8, 0.09, 9)
        _WaveC ("Wave 3", Vector) = (-0.7, -0.7, 0.07, 5.5)
        _WaveD ("Wave 4", Vector) = (0.3, -0.95, 0.05, 3.5)
        _WaveSpeed ("Wave speed", Float) = 1.0
        _Reflect ("Sky reflection", Range(0, 1)) = 0.6
        _Fresnel ("Fresnel power", Range(0.5, 8)) = 4
        _SpecPower ("Sun glitter size", Range(4, 1024)) = 260
        _SpecIntensity ("Sun glitter", Range(0, 4)) = 1.6
        _Foam ("Foam amount", Range(0, 2)) = 0.9
        _FoamStart ("Foam starts at crest height", Range(0, 1)) = 0.45
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Back
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_FoamMap); SAMPLER(sampler_FoamMap);
            CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST, _FoamMap_ST;
            half4 _ShallowColor, _DeepColor, _SSSColor, _SkyHorizon, _SkyZenith, _FoamColor;
            float4 _WaveA, _WaveB, _WaveC, _WaveD;
            float _Tiling, _NormalStrength, _WaveSpeed, _Reflect, _Fresnel, _SpecPower, _SpecIntensity, _Foam, _FoamStart;
            CBUFFER_END
            float _SeaScroll;   // global: units the world has slid toward the camera (WorldScroller)

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;   // displaced
                float3 normalWS   : TEXCOORD1;   // the Gerstner normal
                float2 seaPos     : TEXCOORD2;   // (x, z + scroll): the sea-space position the ripples and foam tile on
                float  height     : TEXCOORD3;   // wave height / max height: -1 trough .. 1 crest
                float  fog        : TEXCOORD4;
            };

            // one Gerstner wave (Catlike Coding's form): wave = (dir x, dir z, steepness, wavelength); accumulates the position offset,
            // the tangent and the binormal so the normal is analytic. Returns the vertical part of the offset.
            float Gerstner(float4 wave, float2 p, float t, inout float3 offset, inout float3 tangent, inout float3 binormal)
            {
                float k = 2.0 * PI / wave.w;
                float c = sqrt(9.8 / k) * _WaveSpeed;
                float2 d = normalize(wave.xy);
                float f = k * (dot(d, p) - c * t);
                float a = wave.z / k;
                float s = sin(f), co = cos(f);
                tangent += float3(-d.x * d.x * (wave.z * s), d.x * (wave.z * co), -d.x * d.y * (wave.z * s));
                binormal += float3(-d.x * d.y * (wave.z * s), d.y * (wave.z * co), -d.y * d.y * (wave.z * s));
                offset += float3(d.x * (a * co), a * s, d.y * (a * co));
                return a;
            }

            Varyings vert(Attributes a)
            {
                Varyings o;
                float3 pWS = TransformObjectToWorld(a.positionOS.xyz);
                float2 p = float2(pWS.x, pWS.z + _SeaScroll);
                float t = _Time.y;
                float3 offset = 0, tangent = float3(1, 0, 0), binormal = float3(0, 0, 1);
                float maxH = 0;
                maxH += Gerstner(_WaveA, p, t, offset, tangent, binormal);
                maxH += Gerstner(_WaveB, p, t, offset, tangent, binormal);
                maxH += Gerstner(_WaveC, p, t, offset, tangent, binormal);
                maxH += Gerstner(_WaveD, p, t, offset, tangent, binormal);
                pWS += offset;
                o.positionWS = pWS;
                o.positionCS = TransformWorldToHClip(pWS);
                o.normalWS = normalize(cross(binormal, tangent));
                o.seaPos = p + offset.xz;
                o.height = offset.y / max(maxH, 0.001);
                o.fog = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                // chop: two ripple layers (the second bigger, slower and drifting sideways) over the Gerstner normal
                float2 uv = i.seaPos * _Tiling;
                float3 n1 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv + float2(0.02, 0.0) * _Time.y).xyz * 2.0 - 1.0;
                float3 n2 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv * 0.41 + float2(-0.015, 0.01) * _Time.y).xyz * 2.0 - 1.0;
                float2 nxy = (n1.xy + n2.xy * 0.7) * _NormalStrength;
                float3 N = normalize(i.normalWS + float3(nxy.x, 0.0, nxy.y));
                float3 V = normalize(_WorldSpaceCameraPos - i.positionWS);
                float4 shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                Light sun = GetMainLight(shadowCoord);
                float3 L = normalize(sun.direction);
                half shadow = lerp(0.6, 1.0, sun.shadowAttenuation);

                // colour: deep in the troughs, shallow on the crests, a sunlit glow through the crests facing away from the sun
                float h = saturate(i.height * 0.5 + 0.5);
                half3 base = lerp(_DeepColor.rgb, _ShallowColor.rgb, smoothstep(0.15, 0.9, h));
                float sss = pow(saturate(dot(V, -L)), 3.0) * pow(h, 2.0) * 0.6 + pow(h, 4.0) * 0.15;
                base += _SSSColor.rgb * sss;
                float ndl = saturate(dot(N, L));
                half3 col = base * (0.62 + 0.38 * ndl) * shadow;

                // the sky: a clean two-tone gradient through a fresnel term
                float fres = pow(1.0 - saturate(dot(N, V)), _Fresnel);
                float3 R = reflect(-V, N);
                half3 sky = lerp(_SkyHorizon.rgb, _SkyZenith.rgb, pow(saturate(R.y), 0.6));
                col = lerp(col, sky, fres * _Reflect);

                // sun glitter: a tight lobe on the chop plus a soft broad sheen
                float3 H = normalize(L + V);
                float ndh = saturate(dot(N, H));
                half spec = (pow(ndh, _SpecPower) * _SpecIntensity + pow(ndh, 28.0) * 0.10) * shadow;
                col += spec * sun.color;

                // foam on the crests, streaked by the noise, thinning to nothing in the troughs
                float2 fuv = i.seaPos * _FoamMap_ST.xy + float2(0.0, 0.03) * _Time.y;
                half noise = SAMPLE_TEXTURE2D(_FoamMap, sampler_FoamMap, fuv).r;
                half noise2 = SAMPLE_TEXTURE2D(_FoamMap, sampler_FoamMap, fuv * 2.3 + float2(0.05, -0.02) * _Time.y).r;
                float crest = smoothstep(_FoamStart, 1.0, h);
                half foam = saturate((crest * (noise * 0.7 + noise2 * 0.5) - 0.18) * 2.2) * _Foam;
                col = lerp(col, _FoamColor.rgb * (0.85 + 0.15 * ndl) * shadow, saturate(foam));

                col = MixFog(col, i.fog);
                return half4(col, 1.0);
            }
            ENDHLSL
        }
    }
    FallBack "Universal Render Pipeline/Unlit"
}
