// SceneBuilder.EnemyPlanes.cs (Editor only)
// One enemy warplane per world (2026-10-10: "a different enemy plane for every level, military designs that suit the environment, beautiful"),
// instead of the one OH-1 helicopter recoloured for each world. Modelled from code in Blender (Tools/blender/enemy_planes.py ->
// Art/Enemies/Planes/Enemy_<id>.fbx): sea a carrier fighter (F-14 style), lava a forward-swept interceptor with glowing edges (Su-47), alien a
// saucer with a glowing dome, meadow a WWI biplane, autumn a twin-boom fighter (P-38), camping a night attack helicopter (Apache),
// christmas a silver swept jet (MiG-15), desert a ground-attack jet (A-10), city a stealth fighter (F-117), japan a carrier fighter (Zero),
// soccer a delta interceptor (Mirage), shuttle a spy jet (SR-71), treasure a flying boat (Catalina), west a dive bomber (Stuka). 2-4.5k
// triangles each. Each FBX holds "Body" plus its spinning parts ("Prop<n>" about the nose, "Rotor" about up, "TailRotor" about the wing axis);
// its material slots are "<id>_<Slot>" and carry their colour, the slot says how it is shaded. The OH-1 stays the fallback without the FBX.
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string EnemyPlaneDir = Root + "/Art/Enemies/Planes";

        /// <summary>A slot of an enemy plane FBX as a generated URP material: its colour from the file, glossy glass, metallic metal, HDR glows past the bloom threshold.</summary>
        static Material EnemyPlaneMaterial(Material src)
        {
            if (src == null) return null;
            string n = src.name; int us = n.LastIndexOf('_'); string slot = us >= 0 ? n.Substring(us + 1) : n;
            Color c = src.HasProperty("_BaseColor") ? src.GetColor("_BaseColor") : src.HasProperty("_Color") ? src.GetColor("_Color") : Color.white;
            c = c.linear; c.a = 1f;   // Blender writes the linear base colour, the importer reads it as sRGB: undo that or every plane comes out washed pale
            string name = "EnemyPlane_" + n;
            switch (slot)
            {
                case "Glass": return Lit(name, c, 0.92f);
                case "Metal": return Mat(name, "Universal Render Pipeline/Lit", c, m => { m.SetFloat("_Smoothness", 0.6f); m.SetFloat("_Metallic", 0.55f); });
                case "Glow":
                case "Lamp":
                    float k = slot == "Glow" ? 3.2f : 1.7f;
                    return Mat(name, "Universal Render Pipeline/Lit", c, m =>
                    {
                        m.SetFloat("_Smoothness", 0.5f); m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                        m.SetColor("_EmissionColor", new Color(c.r * k, c.g * k, c.b * k));
                    });
                case "Base": case "Belly": return Lit(name, c, 0.42f);
                default: return Lit(name, c, 0.5f);
            }
        }

        /// <summary>
        /// The enemy fighter of one world from Art/Enemies/Planes/Enemy_<id>.fbx, built like OH1EnemyPrefab: nose +Z inside the "Body" that
        /// Enemy turns toward the player, fitted 2.9 across / 3.3 long (EnemyKindDef.scale still applies), centred; the spinning parts sit on
        /// pivots whose Z is their axis (Enemy spins `propellers` about local Z) with the game's prop blur disc over each; toon outline on the
        /// body, the gun flash at the nose, the strike-run smoke at the tail, the HP label overhead. Null when the FBX is not there.
        /// </summary>
        static GameObject EnemyPlanePrefab(string id, string prefabName, Mats M, Meshes X, Color trailColor)
        {
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(EnemyPlaneDir + "/Enemy_" + id + ".fbx");
            if (model == null) { Debug.LogWarning("[SkySquad] no enemy plane model for " + id + ": the OH-1 stands in"); return null; }
            var root = new GameObject(prefabName);
            var en = root.AddComponent<Enemy>();
            var body = new GameObject("Body"); body.transform.SetParent(root.transform, false);
            en.model = body.transform;
            var plane = (GameObject)PrefabUtility.InstantiatePrefab(model);
            PrefabUtility.UnpackPrefabInstance(plane, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            plane.name = "Plane"; plane.transform.SetParent(body.transform, false);
            // the importer turns each Blender object 180 about Y: a one-object FBX (a jet) is that object, and zeroing it puts the nose on +Z;
            // with spinning parts the turned objects sit under a plain root with their positions mirrored, so the root turns them back
            plane.transform.localPosition = Vector3.zero; plane.transform.localRotation = plane.transform.childCount > 0 ? Quaternion.Euler(0f, 180f, 0f) : Quaternion.identity;
            var rends = plane.GetComponentsInChildren<Renderer>(true);
            foreach (var r in rends)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = EnemyPlaneMaterial(mats[i]);
                r.sharedMaterials = mats; r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true;
            }
            Bounds b = RootBounds(body.transform, rends);
            float k = Mathf.Min(2.9f / Mathf.Max(0.001f, b.size.x), 3.3f / Mathf.Max(0.001f, b.size.z));
            plane.transform.localScale = Vector3.one * k;
            b = RootBounds(body.transform, rends); plane.transform.localPosition = -b.center; b = RootBounds(body.transform, rends);

            Renderer hull = null; var spinners = new List<Transform>();
            float discSpan = Mathf.Max(0.001f, X.prop.bounds.size.x);
            foreach (var r in rends)
            {
                var t = r.transform;
                bool rotor = t.name == "Rotor", tail = t.name == "TailRotor";
                if (!rotor && !tail && !t.name.StartsWith("Prop"))
                {   // the body (a jet's FBX is that one object, imported as the root under the file's name)
                    hull = r;
                    var mf = r.GetComponent<MeshFilter>(); if (mf != null && mf.sharedMesh != null) Outline(r.gameObject, mf.sharedMesh, M.outline, 1.035f);
                    continue;
                }
                var pivot = new GameObject(t.name + "Pivot").transform; pivot.SetParent(t.parent, false);
                pivot.position = t.position;
                pivot.rotation = body.transform.rotation * (rotor ? Quaternion.Euler(-90f, 0f, 0f) : tail ? Quaternion.Euler(0f, 90f, 0f) : Quaternion.identity);   // pivot Z = the spin axis: the nose, up, or across
                t.SetParent(pivot, true);
                var sz = r.bounds.size; float span = Mathf.Max(sz.x, Mathf.Max(sz.y, sz.z));
                var disc = MeshObj("Blur", X.prop, pivot, M.propDisc, M.propDisc);
                disc.transform.localRotation = Quaternion.identity; disc.transform.localPosition = Vector3.zero;
                disc.transform.localScale = Vector3.one * (span / discSpan / Mathf.Max(0.0001f, pivot.lossyScale.x));
                disc.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
                spinners.Add(pivot);
            }
            en.bodyRenderer = hull != null ? hull : rends[0];
            en.propellers = spinners.ToArray();

            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            flash.transform.localPosition = new Vector3(0f, -0.05f, b.max.z + 0.05f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.6f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            var trailGo = new GameObject("Trail"); trailGo.transform.SetParent(body.transform, false); trailGo.transform.localPosition = new Vector3(0f, 0.05f, b.min.z + 0.3f);
            var tr = trailGo.AddComponent<TrailRenderer>();
            tr.sharedMaterial = M.tracer; tr.time = 0.5f; tr.startWidth = 0.34f; tr.endWidth = 0.03f; tr.minVertexDistance = 0.06f; tr.emitting = false; tr.shadowCastingMode = ShadowCastingMode.Off;
            tr.startColor = trailColor; tr.endColor = new Color(trailColor.r * 0.4f, trailColor.g * 0.2f, trailColor.b * 0.1f, 0f);
            en.trail = tr;
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 1.4f, 0f), 6f, Color.white, fontOutline);
            return SavePrefab(root, prefabName);
        }
    }
}
