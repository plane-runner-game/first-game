
Shader "Custom/PlaneBodyShader"
{
    Properties
    {
        _MainTex("Albedo (RGB)", 2D) = "white" {}
        _PanelTex("Panel (RGB)", 2D) = "white" {}
        _CanopyTex("Canopy (RGB)", 2D) = "white" {}

        _Glossiness ("Smoothness", Range(0,1)) = 0.5
        _Metallic ("Metallic", Range(0,1)) = 0.0

        _TopColor("TopColor", Color) = (1,1,1,1)
        _BottomColor("BottomColor", Color) = (1,1,1,1)

        _CanopyRatio("CanopyRatio", Range(0,1)) = 0.0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        CGPROGRAM
        // Physically based Standard lighting model, and enable shadows on all light types
        #pragma surface surf Standard fullforwardshadows nolightmap vertex:vert

        // Use shader model 3.0 target, to get nicer looking lighting
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _PanelTex;
        sampler2D _CanopyTex;

        struct Input
        {
            float2 uv_MainTex;
            float3 worldNormal;
            float3 objectNormal;
            float3 objectPosition;
        };

        half _Glossiness;
        half _Metallic;
        fixed4 _TopColor;
        fixed4 _BottomColor;
        half _CanopyRatio;
        fixed3 _Dimensions;
        fixed3 _TintRatios;
        fixed3 _NoseTint;
        fixed3 _WingTint;

        // Add instancing support for this shader. You need to check 'Enable Instancing' on materials that use the shader.
        // See https://docs.unity3d.com/Manual/GPUInstancing.html for more information about instancing.
        // #pragma instancing_options assumeuniformscaling
        UNITY_INSTANCING_BUFFER_START(Props)
            // put more per-instance properties here
        UNITY_INSTANCING_BUFFER_END(Props)

        void vert(inout appdata_base v, out Input data)
        {
            UNITY_INITIALIZE_OUTPUT(Input, data);
            data.objectNormal = v.normal;
            data.objectPosition.xyz = v.vertex.xyz;
        }

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            float3 pos = IN.objectPosition;

            float zPerc = clamp((pos.z + (_Dimensions.z * 0.5)) / _Dimensions.z, 0, 1);

            float xPerc = clamp(abs(pos.x) / _Dimensions.x, 0, 1);

            float y = pos.y;

            fixed4 cc = tex2D(_MainTex, float2((pos.x - y - 8) * 0.07, (pos.z + y + 5) * 0.1));

            float side = y * 0.5;

            fixed4 panel = tex2D(_PanelTex, float2((pos.x + side) * 0.3, (pos.z + side) * 0.3));

            fixed4 canopy = tex2D(_CanopyTex, IN.uv_MainTex);


            // bottom to top based on vert normal.
            float d = dot(IN.objectNormal, float3(0, 1, 0));
            d += 1;
            d *= 0.5f;

            fixed4 c = cc;

            
            // middle fade
            //c *= lerp(fixed4(1, 1, 1, 1), fixed4(0.2, 0.2, 0.2, 1), step(_TintRatios.y, 1 - distPerc)); // 0.6

            // bottom fade
            c = lerp(_BottomColor, c, d);

            // nose coloring
            c.rgb = lerp(c.rgb, _NoseTint, step(_TintRatios.z, zPerc));

            // wing tip coloring
            c.rgb = lerp(c.rgb, _WingTint, step(_TintRatios.x, xPerc));

            // panelling
            c *= panel;

            // canopy
            c *= lerp(fixed4(1,1,1,1), canopy, _CanopyRatio);


            o.Albedo = c.rgb;
            // Metallic and smoothness come from slider variables
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
            o.Alpha = c.a;
        }
        ENDCG
    }
    FallBack "Diffuse"
}
