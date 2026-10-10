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
        /// "Prop*" spin fast about the nose, "Rotor*" about up and "TailRotor" about the wing axis (Enemy.propellers, with the blur disc when X is
        /// given); "Cloth" stays still without the outline; "Spin*" turn slowly about up and "Roll*" about the nose axis (Enemy.slowSpinners); "Flap*" rock about the nose axis and "Sway*" about the wing axis
        /// (BossWiggle, wiggleSpeed radians a second); the shots and the flash leave from "Muzzle". Null without the file.
        /// </summary>
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
            foreach (var r in rends)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = EnemyPlaneMaterial(mats[i]);
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
                bool isProp = n.StartsWith("Prop"), isRotor = n.StartsWith("Rotor"), isTail = n == "TailRotor";
                bool isSpin = n.StartsWith("Spin"), isRoll = n.StartsWith("Roll"), isFlap = n.StartsWith("Flap"), isSway = n.StartsWith("Sway");
                if (!isProp && !isRotor && !isTail && !isSpin && !isRoll && !isFlap && !isSway)
                {
                    hull = r;
                    var mf = r.GetComponent<MeshFilter>(); if (mf != null && mf.sharedMesh != null) Outline(r.gameObject, mf.sharedMesh, M.outline, 1.03f);
                    continue;
                }
                var pivot = new GameObject(n + "Pivot").transform; pivot.SetParent(t.parent, false);
                pivot.position = t.position;
                Quaternion axis = isSpin || isRotor ? Quaternion.Euler(-90f, 0f, 0f) : isSway || isTail ? Quaternion.Euler(0f, 90f, 0f) : Quaternion.identity;
                pivot.rotation = body.transform.rotation * axis;
                t.SetParent(pivot, true);
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
                wiggle.Add(pivot);
                if (isFlap) { amp.Add(26f * side); phase.Add(0f); }             // both wings (fins) beat together
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
