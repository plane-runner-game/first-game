// Sea.shader - the ocean under the lane (URP, hand-written HLSL). Two scrolling ripple-normal layers
// (SceneBuilder.SeaNormalTexture, scrolled by WorldScroller through _BaseMap's offset so the sea moves
// with the world and stops when the game pauses), a fresnel blend from the shallow colour to the deep
// colour and to the sky reflection (the skybox reflection probe), and the sun's highlight from the
// main light. No vertex waves: the sea plane is a 10 x 10 primitive.
Shader "SkySquad/Sea"
{
    Properties
    {
        _ShallowColor ("Shallow colour", Color) = (0.12, 0.64, 0.88, 1)
        _DeepColor ("Deep colour", Color) = (0.03, 0.28, 0.6, 1)
        _BaseMap ("Ripple normals", 2D) = "bump" {}
        _Tiling ("Ripple tiles per unit", Float) = 0.15
        _NormalStrength ("Ripple strength", Range(0, 2)) = 0.55
        _Fresnel ("Fresnel power", Range(0.5, 8)) = 3
        _Reflect ("Sky reflection", Range(0, 1)) = 0.75
        _SpecPower ("Sun highlight size", Range(4, 512)) = 120
        _SpecIntensity ("Sun highlight", Range(0, 4)) = 1.4
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
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _ShallowColor, _DeepColor;
            float _Tiling, _NormalStrength, _Fresnel, _Reflect, _SpecPower, _SpecIntensity;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; float fog : TEXCOORD1; };

            Varyings vert(Attributes a)
            {
                Varyings o;
                o.positionWS = TransformObjectToWorld(a.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.fog = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 uv = i.positionWS.xz * _Tiling;
                float2 off = -_BaseMap_ST.zw;                                  // scrolled by WorldScroller with the world (it sets (0, -distance); the ripples come toward the player)
                float3 n1 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv + off).xyz * 2.0 - 1.0;
                float3 n2 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv * 0.47 + off * 0.6 + float2(0.13, -0.07) * _Time.y).xyz * 2.0 - 1.0;   // a bigger, slower swell across the ripples
                float2 nxy = (n1.xy + n2.xy * 0.8) * _NormalStrength;
                float3 N = normalize(float3(nxy.x, 1.0, nxy.y));
                float3 V = normalize(_WorldSpaceCameraPos - i.positionWS);
                float fres = pow(1.0 - saturate(dot(N, V)), _Fresnel);
                float3 R = reflect(-V, N);
                half4 env = SAMPLE_TEXTURECUBE_LOD(unity_SpecCube0, samplerunity_SpecCube0, R, 2.5);
                half3 sky = DecodeHDREnvironment(env, unity_SpecCube0_HDR);
                sky = sky / (1.0 + sky * 0.45);                                  // soft-clamp the HDR sky so the far sea does not bloom white
                Light sun = GetMainLight();
                float3 H = normalize(sun.direction + V);
                half spec = pow(saturate(dot(N, H)), _SpecPower) * _SpecIntensity;
                half3 base = lerp(_ShallowColor.rgb, _DeepColor.rgb, fres);
                base *= 0.82 + 0.18 * saturate(dot(N, sun.direction));         // the ripples catch a little sun
                half3 col = lerp(base, sky, fres * _Reflect) + spec * sun.color;
                col = MixFog(col, i.fog);
                return half4(col, 1.0);
            }
            ENDHLSL
        }
    }
    FallBack "Universal Render Pipeline/Unlit"
}
