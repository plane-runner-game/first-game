// CloudWall.shader - the bank of cloud that stands where the world ends (2026-09-20: "after the last buoys I want no sea,
// nothing - something foggy that covers... not a straight line at the bottom, cloudy, and at the top too, and darker").
// A plain unlit transparent quad: the texture (SceneBuilder.CloudWallTexture) carries the ragged top and bottom edges in
// its alpha and the darker rims / lighter core in its colour; the shader only drifts it slowly sideways. No fog on
// purpose: the distance fog would grey it toward the sky and flatten the tones the user asked for.
Shader "SkySquad/CloudWall"
{
    Properties
    {
        _MainTex ("Cloud (rgb tone, a cover)", 2D) = "white" {}
        _Color ("Tint", Color) = (1, 1, 1, 1)
        _Drift ("Drift (u per second)", Float) = 0.004
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
            float4 _MainTex_ST;
            half4 _Color;
            float _Drift;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex) + float2(_Time.y * _Drift, 0);   // the bank drifts, the edges crawl
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half4 c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv) * _Color;
                return c;
            }
            ENDHLSL
        }
    }
}
