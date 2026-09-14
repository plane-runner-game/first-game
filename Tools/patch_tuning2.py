import io, os

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def patch(path, pairs):
    s = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            raise SystemExit("PATCH MISMATCH in %s (%d hits): %s" % (path, n, old[:70]))
        s = s.replace(old, new)
    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    print("patched", path)

# --- FXManager: shake becomes an offset the camera rig reads
patch("Assets/_Game/Scripts/Runtime/FXManager.cs", [
 ("        public Transform cameraRig;        // shaken; the Camera is its child\n",
  "        public Vector3 ShakeOffset { get; private set; }\n"),
 ("        float shake;\n        Vector3 rigBase;\n", "        float shake;\n"),
 ("        void Awake() { I = this; if (cameraRig != null) rigBase = cameraRig.localPosition; }\n",
  "        void Awake() { I = this; }\n"),
 ("""            if (cameraRig != null)
            {
                shake = Mathf.Max(0f, shake - dt);
                float m = 0.35f * shake / 0.4f;
                cameraRig.localPosition = rigBase + (shake > 0f ? new Vector3(Random.Range(-m, m), Random.Range(-m, m), 0f) : Vector3.zero);
            }
""",
  """            shake = Mathf.Max(0f, shake - dt);
            float m = 0.35f * shake / 0.4f;
            ShakeOffset = shake > 0f ? new Vector3(Random.Range(-m, m), Random.Range(-m, m), 0f) : Vector3.zero;
"""),
])

# --- SceneBuilder: closer camera with follow, soft particle sprite, smaller planes, lane width
patch("Assets/_Game/Scripts/Editor/SceneBuilder.cs", [
 ('            var rig = new GameObject("CameraRig"); rig.transform.position = new Vector3(0f, 8f, -14f);',
  '            var rig = new GameObject("CameraRig"); rig.transform.position = new Vector3(0f, 6.2f, -9.5f);\n            var follow = rig.AddComponent<CameraFollow>(); follow.basePosition = rig.transform.position;'),
 ('            cam.fieldOfView = 66f; cam.nearClipPlane = 0.3f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;\n            camGo.transform.LookAt(new Vector3(0f, 3.5f, 16f));',
  '            cam.fieldOfView = 62f; cam.nearClipPlane = 0.3f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;\n            camGo.transform.LookAt(new Vector3(0f, 3.6f, 9f));'),
 ('            fx.explosionPrefab = P.explosion; fx.sparksPrefab = P.sparks; fx.floatTextPrefab = P.floatText; fx.ringPrefab = P.ring; fx.cameraRig = rig.transform;',
  '            fx.explosionPrefab = P.explosion; fx.sparksPrefab = P.sparks; fx.floatTextPrefab = P.floatText; fx.ringPrefab = P.ring;'),
 ('            var pilot = squadGo.AddComponent<AutoPilot>(); pilot.squad = squad;',
  '            var pilot = squadGo.AddComponent<AutoPilot>(); pilot.squad = squad;\n            follow.squad = squad;'),
 ('            M.particle = Particle("ParticleAdd", Color.white, true);\n            M.smoke = Particle("Smoke", new Color(0.35f, 0.35f, 0.4f, 0.6f), false);',
  '            var soft = SoftTexture();\n            M.particle = Particle("ParticleAdd", Color.white, true); M.particle.SetTexture("_BaseMap", soft);\n            M.smoke = Particle("Smoke", new Color(0.35f, 0.35f, 0.4f, 0.6f), false); M.smoke.SetTexture("_BaseMap", soft);'),
 ('        static Texture2D CloudTexture()\n',
  '''        static Texture2D SoftTexture()
        {
            int n = 64; var t = new Texture2D(n, n, TextureFormat.RGBA32, false);
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
                    float a = Mathf.Clamp01(1f - d); a = a * a * (3f - 2f * a);
                    t.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            t.Apply();
            var tex = SaveTex(t, "SoftParticle");
            var imp = AssetImporter.GetAtPath(Gen + "/Textures/SoftParticle.png") as TextureImporter;
            if (imp != null) { imp.wrapMode = TextureWrapMode.Clamp; imp.SaveAndReimport(); }
            return tex;
        }
        static Texture2D CloudTexture()
'''),
 ('            var root = new GameObject(name);\n            var pv = root.AddComponent<PlaneVisual>();\n            var bodyGo = MeshObj("Body", mesh, root.transform, body, accent, glass);',
  '            var root = new GameObject(name);\n            root.transform.localScale = Vector3.one * 0.8f;\n            var pv = root.AddComponent<PlaneVisual>();\n            var bodyGo = MeshObj("Body", mesh, root.transform, body, accent, glass);'),
 ('c.laneHalfWidth = 4.6f; c.sideX = 4.2f; });', 'c.laneHalfWidth = 4.2f; c.sideX = 3.8f; });'),
])

# --- squad formation a bit tighter (planes are 0.8 scale now)
patch("Assets/_Game/Scripts/Runtime/SquadController.cs", [
 ("                    slots.Add(new Vector3((j - k / 2f) * 1.1f, 0f, -k * 0.85f));",
  "                    slots.Add(new Vector3((j - k / 2f) * 0.92f, 0f, -k * 0.72f));"),
])
patch("Assets/_Game/Scripts/Runtime/GameConfig.cs", [
 ("public float laneHalfWidth = 4.6f;", "public float laneHalfWidth = 4.2f;"),
 ("public float sideX = 4.2f;          // where side gates sit", "public float sideX = 3.8f;          // where side gates sit"),
])

# --- bot: commit to a gate once it is close and we are lined up; prefer gates when small
patch("Assets/_Game/Scripts/Runtime/AutoPilot.cs", [
 ('''                float split = GameManager.I.config.altitudeSplit;
                if (h0 != null)
                {
                    bool urgent = h0.Z < 30f || h0.Units * h0.Kind.contactPower >= squad.Count;
                    float secondsToArrive = Mathf.Max(0f, h0.Z - 12f) / (GameManager.I.ScrollSpeed + h0.Kind.approachSpeed);
                    bool killableLater = h0.Units * h0.Kind.unitHp < squad.Dps * secondsToArrive * 0.8f;
                    if (p0 != null && !urgent && killableLater && p0.Z < h0.Z + 40f) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; }
                    else { tx = h0.X; ta = h0.Alt; }
                    have = true;
                }
                else if (p0 != null) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; have = true; }''',
  '''                float split = GameManager.I.config.altitudeSplit;
                bool committed = p0 != null && p0.Z < 22f && Mathf.Abs(p0.X - squad.X) < 2.5f && (squad.Alt >= split) == p0.High;
                if (committed) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; have = true; }
                else if (h0 != null)
                {
                    bool urgent = h0.Z < 26f || h0.Units * h0.Kind.contactPower >= squad.Count;
                    float secondsToArrive = Mathf.Max(0f, h0.Z - 12f) / (GameManager.I.ScrollSpeed + h0.Kind.approachSpeed);
                    bool killableLater = h0.Units * h0.Kind.unitHp < squad.Dps * secondsToArrive * 0.8f;
                    if (p0 != null && !urgent && killableLater && p0.Z < h0.Z + 40f) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; }
                    else { tx = h0.X; ta = h0.Alt; }
                    have = true;
                }
                else if (p0 != null) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; have = true; }'''),
])
print("ALL PATCHES OK")
