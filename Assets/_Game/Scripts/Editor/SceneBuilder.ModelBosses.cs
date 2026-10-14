// SceneBuilder.ModelBosses.cs (Editor only)
// A boss from a Blender FBX made from code (Tools/blender/alien_bosses.py, sea_bosses.py): the alien world's five (2026-10-10) and the
// sea world's five (the same day). The FBX object names say how each part moves.
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        /// <summary>
        /// One boss from <dir>/Boss_<id>.fbx, built like the pack bosses (HP bar, number, flash) with the enemy planes' materials
        /// (EnemyPlaneMaterial: the colour from the file, the slot name says how it is shaded), fitted 'width' across, no taller than maxHeight
        /// and no longer than maxLength (model units; EnemyKindDef.scale then multiplies). The moving parts get pivots whose Z is their axis:
        /// "Prop*" spin fast about the nose, "Rotor*" about up, "TailRotor" and "Wheel*" about the wing axis (Enemy.propellers, with the blur disc when X is
        /// given); "Cloth" stays still without the outline; "Spin*" turn slowly about up and "Roll*" about the nose axis (Enemy.slowSpinners); "Flap*" rock about the nose axis, "Sway*" about the wing axis and "Wag*" about up
        /// (BossWiggle, wiggleSpeed radians a second); the shots and the flash leave from "Muzzle". Null without the file.
        /// </summary>
        /// <summary>A boss whose surfaces were baked in Blender (Tools/blender/boss_bake.py, 2026-10-14: "more realistic, keep the cartoonish look,
        /// they still look plasticky") wears one textured material - Boss_&lt;id&gt;_Albedo (colour, the occlusion of every crease in it), _Normal
        /// (the feathers, weave, grain, pores), _Mask (R metal, A smoothness) and _Emission (.jpg or .png) beside its FBX - instead of the flat slot colours.
        /// Null when the boss has no Albedo texture: it keeps the slots.</summary>
        static Material BakedBossMaterial(string dir, string id)
        {
            string p = dir + "/Boss_" + id + "_";
            var albedo = BakedBossTexture(p + "Albedo", true, false);
            if (albedo == null) return null;
            var normal = BakedBossTexture(p + "Normal", false, true);
            var mask = BakedBossTexture(p + "Mask", false, false);
            var emission = BakedBossTexture(p + "Emission", true, false);
            return Mat("BossBaked_" + id, "Universal Render Pipeline/Lit", Color.white, m =>
            {
                m.SetTexture("_BaseMap", albedo);
                if (normal != null) { m.SetTexture("_BumpMap", normal); m.SetFloat("_BumpScale", 1f); m.EnableKeyword("_NORMALMAP"); }
                if (mask != null)
                {   // URP Lit reads metal from R and smoothness from A (times _Smoothness)
                    m.SetTexture("_MetallicGlossMap", mask); m.SetFloat("_Smoothness", 1f); m.SetFloat("_SmoothnessTextureChannel", 0f);
                    m.EnableKeyword("_METALLICSPECGLOSSMAP");
                }
                if (emission != null)
                {   // the glows as bright as the slot materials': Glow 3.2, Lamp 1.7 (baked at 0.53 of Glow)
                    m.SetTexture("_EmissionMap", emission); m.SetColor("_EmissionColor", new Color(3.2f, 3.2f, 3.2f));
                    m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                }
            });
        }

        static Texture2D BakedBossTexture(string pathNoExt, bool srgb, bool normalMap)
        {
            string path = pathNoExt + ".png";   // the colour and the normals come as .jpg (smaller in the repo), the mask as .png
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp == null) { path = pathNoExt + ".jpg"; imp = AssetImporter.GetAtPath(path) as TextureImporter; }
            if (imp == null) return null;
            bool dirty = false;
            if (normalMap && imp.textureType != TextureImporterType.NormalMap) { imp.textureType = TextureImporterType.NormalMap; dirty = true; }
            if (!normalMap && imp.sRGBTexture != srgb) { imp.sRGBTexture = srgb; dirty = true; }
            if (imp.maxTextureSize != 2048) { imp.maxTextureSize = 2048; dirty = true; }
            if (imp.alphaIsTransparency) { imp.alphaIsTransparency = false; dirty = true; }
            if (dirty) imp.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        static GameObject ModelBossPrefab(string dir, string id, string prefabName, Mats M, Meshes X, float width, float maxHeight, float maxLength, float wiggleSpeed)
        {
            var fbx = AssetDatabase.LoadAssetAtPath<GameObject>(dir + "/Boss_" + id + ".fbx");
            if (fbx == null) return null;
            var root = new GameObject(prefabName);
            var en = root.AddComponent<Enemy>();
            var body = new GameObject("Body"); body.transform.SetParent(root.transform, false);
            en.model = body.transform;
            var model = (GameObject)PrefabUtility.InstantiatePrefab(fbx);
            PrefabUtility.UnpackPrefabInstance(model, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            model.name = "Model"; model.transform.SetParent(body.transform, false);
            model.transform.localPosition = Vector3.zero; model.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // the importer turns each object 180 about Y; the root turns them back, nose +Z
            var rends = model.GetComponentsInChildren<Renderer>(true);
            var baked = BakedBossMaterial(dir, id);
            foreach (var r in rends)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = baked != null ? baked : EnemyPlaneMaterial(mats[i]);
                r.sharedMaterials = mats; r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true;
            }
            var b = RootBounds(body.transform, rends);
            float k = Mathf.Min(width / Mathf.Max(0.001f, b.size.x), Mathf.Min(maxHeight / Mathf.Max(0.001f, b.size.y), maxLength / Mathf.Max(0.001f, b.size.z)));
            model.transform.localScale = Vector3.one * k;
            b = RootBounds(body.transform, rends); model.transform.localPosition = -b.center; b = RootBounds(body.transform, rends);

            var fast = new List<Transform>(); var spin = new List<Transform>(); var wiggle = new List<Transform>(); var amp = new List<float>(); var phase = new List<float>();
            Transform muzzle = null; Renderer hull = null;
            float discSpan = X != null && X.prop != null ? Mathf.Max(0.001f, X.prop.bounds.size.x) : 1f;
            foreach (var r in rends)
            {
                var t = r.transform; string n = t.name;
                if (n == "Muzzle") { muzzle = t; continue; }
                if (n.StartsWith("Cloth")) continue;   // sails, fins, frills: thin sheets the outline would cover in black from one side
                bool isProp = n.StartsWith("Prop"), isRotor = n.StartsWith("Rotor"), isTail = n == "TailRotor", isWheel = n.StartsWith("Wheel");
                bool isSpin = n.StartsWith("Spin"), isRoll = n.StartsWith("Roll"), isFlap = n.StartsWith("Flap"), isSway = n.StartsWith("Sway"), isWag = n.StartsWith("Wag");
                if (!isProp && !isRotor && !isTail && !isWheel && !isSpin && !isRoll && !isFlap && !isSway && !isWag)
                {
                    hull = r;
                    var mf = r.GetComponent<MeshFilter>(); if (mf != null && mf.sharedMesh != null) Outline(r.gameObject, mf.sharedMesh, M.outline, 1.03f);
                    continue;
                }
                var pivot = new GameObject(n + "Pivot").transform; pivot.SetParent(t.parent, false);
                pivot.position = t.position;
                Quaternion axis = isSpin || isRotor || isWag ? Quaternion.Euler(-90f, 0f, 0f) : isSway || isTail || isWheel ? Quaternion.Euler(0f, 90f, 0f) : Quaternion.identity;
                pivot.rotation = body.transform.rotation * axis;
                t.SetParent(pivot, true);
                if (isWheel) { fast.Add(pivot); continue; }   // a train's wheels: they turn as fast as a prop, with no blur disc
                if (isProp || isRotor || isTail)
                {
                    fast.Add(pivot);
                    if (X != null && X.prop != null)
                    {
                        var sz = r.bounds.size; float span = Mathf.Max(sz.x, Mathf.Max(sz.y, sz.z));
                        var disc = MeshObj("Blur", X.prop, pivot, M.propDisc, M.propDisc);
                        disc.transform.localRotation = Quaternion.identity; disc.transform.localPosition = Vector3.zero;
                        disc.transform.localScale = Vector3.one * (span / discSpan / Mathf.Max(0.0001f, pivot.lossyScale.x));
                        disc.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
                    }
                    continue;
                }
                if (isSpin || isRoll) { spin.Add(pivot); continue; }   // a Roll pivot keeps Z on the nose axis: it turns face-on to the player (the frost crystal)
                float side = body.transform.InverseTransformPoint(pivot.position).x >= 0f ? 1f : -1f;
                float reach = body.transform.InverseTransformPoint(r.bounds.center).x - body.transform.InverseTransformPoint(pivot.position).x;
                if (isFlap && Mathf.Abs(reach) > 0.05f * Mathf.Max(0.001f, r.bounds.size.x)) side = reach > 0f ? 1f : -1f;   // the side the wing reaches out to: both wings of a crow off to one side still beat mirrored
                wiggle.Add(pivot);
                if (isFlap) { amp.Add(26f * side); phase.Add(0f); }             // both wings (fins) beat together
                else if (isWag) { amp.Add(20f); phase.Add(0f); }                // a fish's tail wagging side to side, about up (2026-10-14)
                else if (n.StartsWith("SwayLeg"))                                // a galloping leg (SwayLeg0..3: fore R, fore L, hind R, hind L): a big stride, the
                {                                                                // two forelegs half a beat apart and the hind pair a quarter beat behind them
                    int leg = n.Length > 7 && char.IsDigit(n[7]) ? n[7] - '0' : 0;
                    amp.Add(24f); phase.Add((leg % 2) * Mathf.PI + (leg / 2) * Mathf.PI * 0.5f);
                }
                else { amp.Add(11f); phase.Add(wiggle.Count * 0.9f); }          // tentacles one after another
            }
            en.bodyRenderers = rends;
            en.bodyRenderer = hull;
            if (fast.Count > 0) en.propellers = fast.ToArray();
            if (spin.Count > 0) { en.slowSpinners = spin.ToArray(); en.slowSpinDeg = 70f; }
            if (wiggle.Count > 0)
            {
                var w = root.AddComponent<BossWiggle>();
                w.parts = wiggle.ToArray(); w.amplitude = amp.ToArray(); w.phase = phase.ToArray(); w.speed = wiggleSpeed;
            }
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            Vector3 mp = muzzle != null ? body.transform.InverseTransformPoint(muzzle.GetComponent<Renderer>().bounds.center) : new Vector3(0f, b.center.y, b.max.z);
            flash.transform.localPosition = mp + new Vector3(0f, 0f, 0.15f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.9f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.bossFlash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            float barY = b.max.y * BossModelScale + 0.6f;   // the bar and the label hang off the root, which never takes the model's scale
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, barY + 0.82f, 0f), 10f, Color.white, fontOutline);
            BossHpBar(en, root, M, barY, 3.6f);
            return SavePrefab(root, prefabName);
        }

        /// <summary>Boss n wears the ((n-1) % count)-th model; from the second stage on his name carries the stage's numeral ("VOID DRAGON III").</summary>
        static string[] StageCycleNames(string[] titles)
        {
            string[] roman = { "", " II", " III", " IV", " V", " VI", " VII", " VIII" };
            var names = new string[BossCount];
            for (int i = 0; i < BossCount; i++) names[i] = titles[i % titles.Length] + roman[Mathf.Min(i / titles.Length, roman.Length - 1)];
            return names;
        }

        static GameObject[] StageCycle(GameObject[] models)
        {
            var res = new GameObject[BossCount];
            for (int n = 0; n < BossCount; n++) res[n] = models[n % models.Length];
            return res;
        }
    }
}
