import io, os, sys

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

# 1) camera, sky, water
patch("Assets/_Game/Scripts/Editor/SceneBuilder.cs", [
 ('            var rig = new GameObject("CameraRig"); rig.transform.position = new Vector3(0f, 8.5f, -13f);',
  '            var rig = new GameObject("CameraRig"); rig.transform.position = new Vector3(0f, 8f, -14f);'),
 ('            cam.fieldOfView = 68f; cam.nearClipPlane = 0.3f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;\n            camGo.transform.LookAt(new Vector3(0f, 3.2f, 14f));',
  '            cam.fieldOfView = 66f; cam.nearClipPlane = 0.3f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;\n            camGo.transform.LookAt(new Vector3(0f, 3.5f, 16f));'),
 ('            sky.SetColor("_SkyTint", new Color(0.45f, 0.72f, 1f)); sky.SetColor("_GroundColor", new Color(0.2f, 0.55f, 0.8f)); sky.SetFloat("_Exposure", 1.35f); sky.SetFloat("_SunSize", 0.06f); sky.SetFloat("_AtmosphereThickness", 0.85f);',
  '            sky.SetColor("_SkyTint", new Color(0.5f, 0.75f, 1f)); sky.SetColor("_GroundColor", new Color(0.12f, 0.45f, 0.72f)); sky.SetFloat("_Exposure", 1.15f); sky.SetFloat("_SunSize", 0.05f); sky.SetFloat("_AtmosphereThickness", 0.55f);'),
 ('            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 60f; RenderSettings.fogEndDistance = 220f; RenderSettings.fogColor = new Color(0.72f, 0.86f, 1f);',
  '            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 70f; RenderSettings.fogEndDistance = 240f; RenderSettings.fogColor = new Color(0.62f, 0.8f, 0.98f);'),
 ('            M.water = Lit("Water", new Color(0.1f, 0.55f, 0.8f), 0.85f);\n            M.water.SetTexture("_BaseMap", WaterTexture()); M.water.SetTextureScale("_BaseMap", new Vector2(60f, 60f));',
  '            M.water = Lit("Water", new Color(0.08f, 0.5f, 0.78f), 0.8f);\n            M.water.SetTexture("_BaseMap", WaterTexture()); M.water.SetTextureScale("_BaseMap", new Vector2(150f, 150f));'),
 ('                    float v = 0.86f + 0.14f * Mathf.Sin(x / (float)n * Mathf.PI * 2f * 3f + Mathf.Sin(y / (float)n * Mathf.PI * 2f) * 1.2f) * Mathf.Sin(y / (float)n * Mathf.PI * 2f * 2f);\n                    float crest = Mathf.Max(0f, Mathf.Sin(y / (float)n * Mathf.PI * 2f * 2f + x / (float)n * 4f) - 0.92f) * 6f;\n                    float c = Mathf.Clamp01(v + crest);',
  '                    float u = x / (float)n * Mathf.PI * 2f, w = y / (float)n * Mathf.PI * 2f;\n                    float v = 0.9f + 0.05f * Mathf.Sin(u * 2f + Mathf.Sin(w) * 1.3f) * Mathf.Sin(w * 3f + Mathf.Sin(u * 2f)) + 0.03f * Mathf.Sin(u * 5f + w * 3f);\n                    float crest = Mathf.Max(0f, Mathf.Sin(w * 3f + Mathf.Sin(u * 2f) * 1.5f) - 0.94f) * 1.6f;\n                    float c = Mathf.Clamp01(v + crest);'),
 ('            D.config = Asset<GameConfig>("GameConfig", c => { c.weapons = new[] { D.gatling, D.rockets, D.laser }; c.hordeKinds = new[] { D.fighter, D.drone, D.bomber }; });',
  '            D.config = Asset<GameConfig>("GameConfig", c => { c.weapons = new[] { D.gatling, D.rockets, D.laser }; c.hordeKinds = new[] { D.fighter, D.drone, D.bomber }; c.laneHalfWidth = 4.6f; c.sideX = 4.2f; });'),
 ('                b.transform.position = new Vector3(side * (D.config.laneHalfWidth + 2.4f), 0.15f, -20f + i / 2 * 27.5f);',
  '                b.transform.position = new Vector3(side * (D.config.laneHalfWidth + 2.0f), 0.15f, -20f + i / 2 * 27.5f);'),
])

# 2) config defaults
patch("Assets/_Game/Scripts/Runtime/GameConfig.cs", [
 ("public float laneHalfWidth = 6f;", "public float laneHalfWidth = 4.6f;"),
 ("public float sideX = 5.4f;          // where side gates sit", "public float sideX = 4.2f;          // where side gates sit"),
])

# 3) horde spread follows the lane width
patch("Assets/_Game/Scripts/Runtime/HordeSpawner.cs", [
 ('                float x = n == 1 ? (float)(rng.NextDouble() - 0.5) * 6f : (i == 0 ? -1f : 1f) * (2.2f + (float)rng.NextDouble() * 2f);',
  '                float spread = cfg.laneHalfWidth * 0.75f;\n                float x = n == 1 ? (float)(rng.NextDouble() - 0.5) * spread * 1.6f : (i == 0 ? -1f : 1f) * (spread * 0.5f + (float)rng.NextDouble() * spread * 0.5f);'),
])

# 4) smarter bot: take gates when the nearest horde is not urgent
patch("Assets/_Game/Scripts/Runtime/AutoPilot.cs", [
 ('''                Pickup p0 = null;
                foreach (var p in PickupSpawner.I.Active)
                {
                    if (p.Dead || p.Z <= 10f) continue;
                    if (p.Kind == PickupKind.Weapon) continue;
                    if (h0 != null && p.Z > h0.Z - 8f) continue;
                    if (p0 == null || p.Z < p0.Z) p0 = p;
                }
                if (h0 != null)
                {
                    if (p0 != null && h0.Z > 45f && h0.Units < squad.Count * 1.5f) { tx = p0.X; ta = p0.High ? 6.6f : 2.2f; }
                    else { tx = h0.X; ta = h0.Alt; }
                    have = true;
                }
                else if (p0 != null) { tx = p0.X; ta = p0.High ? 6.6f : 2.2f; have = true; }''',
  '''                Pickup p0 = null;
                foreach (var p in PickupSpawner.I.Active)
                {
                    if (p.Dead || p.Z <= 6f) continue;
                    if (p.Kind == PickupKind.Weapon) continue;
                    if (p0 == null || p.Z < p0.Z) p0 = p;
                }
                float split = GameManager.I.config.altitudeSplit;
                if (h0 != null)
                {
                    bool urgent = h0.Z < 30f || h0.Units * h0.Kind.contactPower >= squad.Count;
                    float secondsToArrive = Mathf.Max(0f, h0.Z - 12f) / (GameManager.I.ScrollSpeed + h0.Kind.approachSpeed);
                    bool killableLater = h0.Units * h0.Kind.unitHp < squad.Dps * secondsToArrive * 0.8f;
                    if (p0 != null && !urgent && killableLater && p0.Z < h0.Z + 40f) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; }
                    else { tx = h0.X; ta = h0.Alt; }
                    have = true;
                }
                else if (p0 != null) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; have = true; }'''),
])
print("ALL PATCHES OK")
