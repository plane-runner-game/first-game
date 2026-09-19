# Sky Squad — Handoff

_Last updated: 2026-09-15 (second session: lanes, strike runs, reticles, gates), on `main` of https://github.com/plane-runner-game/first-game — see `git log` for the commit._

This document is the complete state of the project for whoever picks it up next (a person or an AI
session). It covers what the game is, every rule as it currently works, every number, every script,
how the whole thing is generated from code, how it is built and bot-tested, what was tried and
rejected, and what is left to do. It is long on purpose. Read section 1 for the summary, section 3
for the rules, section 9 for the daily workflow, and section 12 before changing any mechanic.

---

## 1. TL;DR

- **What**: a portrait mobile plane-squadron runner/shooter cloning the mechanics of the mobile game
  *"Real War: not fake"* (a bridge-runner: you push a crowd forward, break loot on one side to grow,
  fight a red enemy crowd on the other, bank coins, buy upgrades, retry). Ours is turned vertical:
  **enemies in the HIGH altitude band, loot crates in the LOW band**.
- **Engine**: Unity 6 (`6000.6.0f1`), URP, TextMeshPro, new Input System. Portrait, test window 540×960.
- **Everything is generated from code.** Materials, meshes, prefabs, ScriptableObject data, the
  scene, the HUD and lobby, post-processing, URP settings: all created by
  `Assets/_Game/Scripts/Editor/SceneBuilder.cs` through the menu **Sky Squad → 2. Build Everything**.
  Do not hand-edit the scene or the generated assets; edit the builder and rebuild.
- **Current mechanic**: a scattered **kamikaze swarm** streams in from the far end of the high band,
  flies straight down one of 6 fixed lanes at its own speed and dives at you when close. Each one that reaches you blows up and costs one
  plane. You shoot them with straight-flying bullets, but only the ones in your own lane. Every 100×k
  fighters a **boss** flies in, parks on a red dashed line and shoots you (one plane per hit). The next
  horde loiters behind him and floods in when he dies.
- **Meta loop**: the round is identical every attempt (seeded). Coins persist. Between attempts a
  lobby sells three upgrades (fire rate, damage, coin revenue). Bot-tuned so that attempt 1 reaches
  boss 1 and dies, attempts 2–3 chip him, attempt 4 kills him, and boss 2 ends the run after that.
- **Testing**: a built-in bot (`AutoPilot.cs`) plays the Windows build, writes screenshots and a
  `status.jsonl`; `Tools/build_and_test.sh` runs it and `Tools/summarize_run.py` summarizes.
- **Live project folder**: `D:\Unity\first-game` on the current machine (earlier sessions used
  `C:\Users\test2\first-game`; opened from Unity Hub, git remote above).
  `C:\Users\test2\Dev\SkySquad` is a **stale duplicate — do not use it**.

---

## 2. Project facts

| Item | Value |
|---|---|
| Unity | 6000.6.0f1, URP (Universal Render Pipeline), TextMeshPro, Input System package |
| Repo | `C:\Users\test2\first-game` → `https://github.com/plane-runner-game/first-game.git`, branch `main` |
| GitHub user used to push | `nbo6y` (collaborator on the private repo) |
| Last commits | `fa6a092` Vertical bands, kamikaze swarm, bosses and the upgrade loop · `b0d2cf6` General Improvements & New Ideas · `c188391` test-commit |
| Scene | `Assets/_Game/Scenes/Main.unity` (generated, the only scene) |
| Scripts | `Assets/_Game/Scripts/Runtime/*.cs` (24 files) and `Assets/_Game/Scripts/Editor/*.cs` (3 files) |
| Generated assets | `Assets/_Game/Generated/{Data,Fonts,Materials,Meshes,Prefabs,Textures}` |
| Data assets | `Assets/_Game/Generated/Data/`: `GameConfig.asset`, `Weapon_Gatling/Rockets/Laser.asset`, `Enemy_Fighter.asset`, `Enemy_MiniBoss.asset`, `PostFX.asset` |
| Builds | `Builds/Windows/SkySquad.exe` (test player), `Builds/Android/SkySquad.apk` (menu exists, never run here). `Builds/` is git-ignored |
| Bot output | `Builds/Shots/<run>/` (`status.jsonl`, `shot_000.png`…, `player.log`) |
| App id | `com.mtjrcloud.skysquad`, company `mtjrcloud` (set by `SceneBuilder.ApplyPlayerSettings`) |
| Claude memory | `C:\Users\test2\.claude\projects\C--Users-test2-Dev-SkySquad\memory\` (`MEMORY.md`, `skysquad-repo-and-test-loop.md`, `skysquad-band-design.md`) |

**Important**: the last Windows player build on disk was made *before* the final change of boss 1
from 300 to 280 HP. The committed scene/config has 280. Run **Sky Squad → Build Windows (test
player)** before trusting the exe.

---

## 3. The game as it stands — every rule

### 3.1 Space, camera, controls

- The world scrolls toward the player at `scrollSpeed` = 9 units/s (water, buoys, clouds move; the
  squad stays at z = 0). `SquadController.Z` = (1 − Alt/`altitudeMax`) × `diveForward` can push the diving squad ahead; **`diveForward` is 0** (2026-09-18: 8.5 kept the diving squad at ~41% of the screen instead of 19% but was reverted within the hour, "do not bring the plane closer, just go down" — the dive is a straight drop). Everything measured "from the squad" uses `sq.Z`: the strike line is `diveZ` + `sq.Z` (`Enemy`), a gate passes at `sq.Z` + 0.4 and is dropped past `sq.Z` − 6 (`UpgradeGate`), guns engage `e.Z > sq.Z + 1` (`AutoFire`); with 8.5 the planes looked ~40% smaller at altitude 0 and a parked boss sat only 3.5 ahead of a dived squad. One unit ≈ 20 px of the original HTML prototype.
- The squad has an **X** (−4.2 … +4.2, `laneHalfWidth`) and an **altitude** (0 … 5.0,
  `altitudeMax`). World y = 1 + altitude.
- **Two bands** split at altitude 3.6 (`altitudeSplit`; 4.4 until 2026-09-18): below = LOW band (crates), at or above =
  HIGH band (enemies). `SquadController.IsHigh` = `Alt >= altitudeSplit`.
- **The ceiling equals the swarm's altitude** (5.0 = 3.6 + 1.4; was 5.85 = 4.4 + 1.4 with the crates at 1.5 until 2026-09-18 — **the bands were pulled together**: crates 2.2, split 3.6, swarm 5.0, so the climb from the crates to the swarm is 1.4 instead of 2.9: "when I go up the distance is long, I can stop where I hit neither the crates nor the planes — shorten it"). You can fly *at* the enemies' height
  but never over them. This was an explicit request ("you shouldn't allow me to go higher than the
  altitude of the coming enemies").
- Controls (`SquadInput.cs`): touch or mouse drag moves the squad (`DragDelta` as a fraction of screen
  height × `dragUnitsPerScreen` 20 (18 until 2026-09-17: on a phone a short thumb move must cross the whole lane; 30 until 2026-09-18, when the slider range was cut and the default became its top) — **the player can change it**: the SETTINGS panel (a "SETTINGS" pill next to the pause button during play, `HUD.OnSettingsButton`: pauses the game and opens the panel; "PLANE SPEED" slider 1–20 (10–60 until 2026-09-18: "speed 60 is far too high, I want the most 20 and the least 1"; a value saved under the old range is clamped on load), DONE returns to the pause screen) stores it as PlayerPrefs `sq_drag` (`Settings.cs`; `Settings.DragUnits(config)` is what `SquadController` reads, 0 = the config default, and the keyboard steer/climb speeds are scaled by the same ratio so "speed" means every direction). While the panel is up `GameManager.OnTap` ignores taps, so DONE does not resume the game (requested 2026-09-18: "a settings button with control of the plane's movement speed", then "at the top, not every time I die", "the speed must apply up, down, left and right"); arrows/WASD steer at
  `steerSpeed` 8 and climb at `climbSpeed` 7.5 units/s; a tap (press+release without moving) is `Tapped`.
- Camera (`CameraFollow.cs`): rig base position (0, 4.55, −11), pitch 13.5° (2026-09-17, third pass: "the plane I move still disappears under my thumb, I want 40% of the screen height for the thumb", then "lower it a bit, 35%" — the squad sat at 42% of the screen height at altitude 0 and 57% at the ceiling with that rig; see the anchored camera below for the current numbers (ceiling 58%, altitude 0 19%). History: (0, 6.2, −9.5) pitch 8° put the squad at 11–28%; pitch 17° put it at 29–45% with the horizon at 82%, "too little sky"; (0, 5, −9.5) pitch 11° kept 29–46% with the horizon at 70%, still under the thumb; y 3.95 gave 47–63%, "a bit too high"), FOV 52. **The camera is anchored on the swarm, not the squad** (2026-09-18, "when I go down for the crates the camera goes down so far with me that the planes above no longer show… the camera stays up on the enemy planes like before the dive"): `followAlt` is **0.2** (was 0.7) and the rig base is (0, 7.48, −11) so the ceiling pose — where every attempt starts — is the (0, 8.65, −11) / pitch 13.5° view above (squad 58%, swarm 66–75%, horizon 75%). On a full dive to altitude 0 the camera drops only 1.2 units: the swarm stays at 71–74%, the horizon at 75%, and **the squad moves down the screen to 19%** (under the thumb, accepted: the dive is short). `CameraFollow` also has `pitchLow` / `dollyLow` (blend by altitude: a flatter pitch and a rig further back at altitude 0); both are neutral now (13.5 / 0) — the "zoom out on the dive" (pitch 8.9, dolly 4, squad kept at 42%, swarm 69–75%) was tried and dropped the same day. The rig
  slides `followX` 0.55 × squad X sideways (trailing the target by at most `maxLagX` 0.5 even on a fast swipe) and 0.2 × squad altitude upward (`followAlt`), smoothed. **The squad is stopped before a plane leaves the screen** (`SquadController.XLimit`, 2026-09-18: "when I turn, no plane may leave the screen… stop me at 15 of 20"): the visible half-width at the squad's depth (≈ 3.05) minus the formation's outer slot plus `planeHalfWidth` 0.55, divided by (1 − followX), clamped between `laneReachMin` 3.2 (always enough to cover the outer lane at 3.8) and `laneHalfWidth` 4.2 — so one plane reaches 4.2, three planes 3.4, five or more stop at 3.2 (a wide formation still spills a little; centring the camera on the squad, `followX` 1, was tried the same day and rejected: "the camera as it was, it must not move with me"). The vertical FOV is derived from a fixed **horizontal FOV 30.7°** (`CameraFollow.horizontalFov`: 52° vertical at 9:16, ~61° on a 9:19.5 phone), so the visible width at the squad is the same on every phone; **never below 52°** (2026-09-18: a 1920×1080 landscape Game view derived ~18° and zoomed onto the squad — "the game is very close, in my face, it looks bad"; the Game view now has a "Phone 9:16" 1080×1920 entry, keep it selected). Screen shake
  offset comes from `FXManager.ShakeOffset`.
- Visual stack: FXAA + MSAA 4×, soft shadows (distance 70), post-processing volume `PostFX.asset`
  (Bloom threshold 1.15, Vignette, Color Adjustments, Tonemapping Neutral) — **the scene Volume had no
  profile until 2026-09-16** (`vol.profile` made a runtime clone; now `vol.sharedProfile`), so every
  earlier screenshot/tuning was without post FX. Black inverted-hull toon outlines on planes and
  crates, spinning propellers, white hit-flash via MaterialPropertyBlock.
- **Sea** (2026-09-18, `Assets/_Game/Shaders/Sea.shader`, "a better sea that works on the web" — Crest was asked for first, but the GitHub zip is the Built-in-pipeline version and Crest never runs on WebGL, so it was not installed): `MeshFactory.SeaGrid` (24k vertices, power-law spacing dense near the camera, x ±100, z −30..250) displaced by four Gerstner waves in the vertex shader (`_WaveA..D` = dir, steepness, length: a 16-unit swell toward the player plus 9 / 5.5 / 3.5 crossing waves, ≈0.4 at the highest crest; the boats sit at 0.65), two scrolling ripple-normal layers (`SeaNormalTexture`), deep→shallow colour by crest height with a turquoise glow through the crests, main-light diffuse **and shadows** (the squad still shadows the water), a two-tone sky **gradient** through fresnel (`_Reflect` 0.35, `_Fresnel` 5 — 0.6 / 4 washed the far sea white; not the HDRI), sun glitter, crest foam from `SeaFoamTexture` noise (`_Foam` 0.5, `_FoamStart` 0.62 — 0.9 / 0.45 was foam everywhere), fog. `WorldScroller` sets the global `_SeaScroll` (units travelled) so the wave field slides with the buoys and stops on pause. The old 1200 × 1200 flat plane stays as `WaterFar` half a unit lower for the horizon, same material. **The waterline is `SceneBuilder.SeaLevel` = −2.5** (0 until later on 2026-09-18: "the sea is close to me, I want it farther") — the water meshes, the buoys and, through `supplyAlt` = 0.65 + SeaLevel = −1.85, the boats / crates / gates all sit on it; the squad's altitude 0 (world y 1) is unchanged, so the box face (top at 1.68) is still in front of the guns. Before: the flat blue Lit plane with the scrolling grey tile texture (1200 × 1200, tiling 300). A reflective
  ripple shader (fresnel to the sky, sun highlight) was tried on 2026-09-16 and rejected ("ugly, put it back").
- **Bright morning again, a simple green sea** (2026-09-19, "the sunset does not fit the new UI; light, simple green colours; a simpler sea"): the Kloofendal sky is back (`SkyRotation` 120), a white sun from 52 degrees, pale haze fog (0.82, 0.91, 0.94), grading +14 saturation / +8 contrast, vignette 0.22; the sea is two flat greens (shallow (0.42, 0.86, 0.72), deep (0.12, 0.60, 0.62)) with faint ripples (`_NormalStrength` 0.12), a gentle swell (steepness 0.05 / 0.04 / 0.03 / 0.02), no sun glitter, hardly any foam (0.15 from 0.8). The war dusk below served for a day.
- **No cloud rails** (2026-09-19, "the clouds in a straight line left and right, I don't want them"): the 20 small puffs that ran along both lane edges at the split altitude are gone; the nine drifting clusters stay.
- **The sea is Stylized Water 3** (2026-09-19, Staggart Creations v3.2.6, `Assets/Stylized Water 3`; "this sea I want" - the ArcadeOcean preset, picked from six presets shot in the game): `SceneBuilder.StylizedWater` copies `StylizedWater3_ArcadeOcean.mat` to `Generated/Materials/Water.mat` (waves 0.35 instead of 0.62, the surface panning toward the player) on the same SeaGrid + far plane; without the pack the game's own `SkySquad/Sea` shader stands in. It needs the URP depth + opaque textures (on). WebGL renders it (its compute height queries are unused). The pack's demo, models and prefabs are git-ignored.
- **Casual RPG VFX** (2026-09-19, Lana Studio, `Assets/Lana Studio/Casual RPG VFX`; "pick the best effects for the planes and the enemies"): `SceneBuilder.UpgradeVfxMaterials` moves the pack's Built-in Mobile/Particles materials to URP Particles/Unlit (its own URP upgrade is a nested .unitypackage), and `FXManager` takes seven prefabs (`airExplosionPrefab` Fire_explosion_air for every shot-down plane, `hitPrefab` Hit_fire where bullets land - throttled to 12/s -, `poofPrefab` Poof_generic on a crate break (`CrateBreak`), `coinPoofPrefab` Poof_coins under a coin burst of 10+, `ringsPrefab` Burst_rings through a gate (`GateBurst`), `fireTrailPrefab` Fire_trail on a wreck, `bossFirePrefab` Fire_medium on a boss under 30% hp - `Enemy.burning`); each null falls back to the generated effect. Only the used prefab folders are tracked.
- **War dusk** (later on 2026-09-18, "I don't want a morning, I want something that says war"): the sky is Poly Haven *Belfast sunset* pure sky (CC0, `Assets/_Game/Art/Sky/belfast_sunset_puresky_4k.hdr`, licence beside it; the Kloofendal morning file is kept): `SkyRotation` **90** (0 = grey mass ahead; 105–180 face the bare sun and wash out), exposure 0.9; the sun is (1, 0.72, 0.5) × 1.35 from 18° up, yaw −12; fog (0.74, 0.60, 0.56) dusty rose; post FX saturation −4 / contrast 22 / exposure 0 / colour filter (1, 0.93, 0.85), vignette 0.38; the sea shallow (0.16, 0.34, 0.42), deep (0.03, 0.09, 0.18), crest glow (0.30, 0.50, 0.42), water-sky horizon (0.95, 0.58, 0.32) / zenith (0.22, 0.24, 0.33), foam grey (0.82, 0.78, 0.74); the near cloud puffs grey-mauve (0.62, 0.56, 0.58). `WaterFar` sits a full unit under the waterline (0.5 let its flat polygons show through the troughs). Before, the morning:
- **Sky** (2026-09-16, "the background is ugly, I want a professional sky"): a photographed pure-sky
  HDRI, Poly Haven *Kloofendal 48d partly cloudy* 4k (CC0, `Assets/_Game/Art/Sky/`, LICENSE.txt beside
  it) on `Skybox/Panoramic` (`SceneBuilder.ImportSkyHdri`, `SkyRotation` 120 = the blue, sun-lit
  cumulus side ahead; 200/330 put the grey overcast mass overhead), skybox ambient lighting, fog
  colour = the HDRI horizon haze (0.8, 0.87, 0.95). The sea plane is 1200 × 1200 (past the far clip, so
  the HDRI's grey below-horizon half never shows), the near puff clouds are at alpha 0.72. If the .hdr
  is missing the builder falls back to the old procedural gradient.

### 3.2 The squad

- Every attempt starts with **1 plane** (`startCount`; 50 for a few hours on 2026-09-18, "I want to start with 50 planes", then "I want to start the game with one plane"; at most `maxVisiblePlanes` 28 are drawn), **at the ceiling** (`SquadController.ResetForLevel`: `Alt = altitudeMax`, the enemies' altitude, so the guns engage the swarm first — requested 2026-09-17: "the plane should go for the planes first, not down at the boxes"; it started at `supplyAlt` in the crate band before).
- `Count` is the number of planes; at most `maxVisiblePlanes` = 28 are drawn (`VisibleCount`).
- **Formation** (`SquadController.BuildSlots`): up to 5 planes fly an inverted V (leader at the apex,
  each pair one row back and one step out: `formationSpacingX` 1.4, `formationSpacingZ` 1.1); beyond 5
  a phyllotaxis spiral (r = 0.8·√i, θ = i·golden angle) so the crowd stays packed and symmetric.
- Losing a plane: `SquadController.Damage(n, reason)` → count drops, a red "−n" floats up, red
  screen flash, shake; at 0 planes `GameManager.Lose(reason)`. `FXManager.Fallers` tumbles the lost
  plane models into the sea; `Joiners` fly new ones in from the sides when you gain planes.
- **DPS** (used by the bot and by nothing else important):
  `Count × weapon.damage × DamageMult / (weapon.fireInterval / FireRateMult)`.
- Shields: `Shield` hits are consumed before planes in `Damage`; the shield gate (3.5) grants 1–3 via `SetShield`; `shieldBubble` shows while any is left; the HUD pill shows the count.

### 3.3 Shooting (yours)

`AutoFire.cs` fires a **volley** every `weapon.fireInterval / Progress.FireRateMult` seconds
(gatling: 0.5 s). Each volley fires **one bullet per plane** (all `Count` planes, not just visible).
**Every weapon keeps firing with nothing to hit** (requested 2026-09-16: "the planes never stop firing, like
the first plane"): Gatling bullets fly to an idle point ahead, rockets fly straight and burn out after
0.45 s, and the laser beam is drawn 40 ahead and lasts until the next volley (life = 1.1 × the volley
interval) so it never blinks off. Rockets used to fire only with a target; the beam used to last 0.08 s.

- **High band** (you are at/above the split): candidates are enemies with
  `|enemy.X − squad.X| < laneHalfWidthAim (0.6)` (a wide boss adds his `halfWidth` 3.4, so he is
  targetable from any lane), `Z > 1` and `Z ≤ lineOfFireRange (48)`. Sorted nearest-first by Z. Plane
  *i* takes the first candidate whose `Pending` (damage already in the air toward it) is still below
  its HP, so five planes drop five different fighters instead of overkilling one. Planes with no
  candidate fire an **idle** bullet straight ahead.
- **Low band**: every bullet goes into the **front crate**, but only if the crate is roughly in front of
  you (`|crate.X − squad.X| < 0.6 + crate.halfWidth`).
- Damage per bullet = `weapon.damage × Progress.DamageMult`.
- The "same lane" rule is deliberate and was requested twice: bullets only *target* enemies in your
  own X column, so you must sweep left and right to cover the sky. Altitude within the band does not
  matter.
- Rockets and Laser exist as `WeaponDef`s and are reached through the weapon crates of the fixed table
  (crate 3 = Rockets, crate 6 = Laser, section 3.5). **All three fire `ProjectileKind.Tracer`** (real
  `BulletPool` bullets, damage on impact) since 2026-09-17; the Rockets pass `splashRadius` to
  `BulletPool.Fire`, and `Land` deals ×0.6 to the fighters in that box around the one hit. The instant-hit
  `Rocket` / `Beam` branches in `AutoFire.FireOne` are legacy (the old rockets dealt damage on fire and
  flew as a visual, so "enemy planes were destroyed before the shot reached them").
  The Rockets plane (`MeshFactory.Plane("attacker")`) is the fighter's family and size — same fuselage,
  cowl and canopy — with swept wings, arrow tips, rocket pods and twin fins (requested: "like the main
  plane but a different shape, the same size").

### 3.4 Bullets (`BulletPool.cs`)

- Bullets are pooled `Bullet` prefabs (glowing slug + short additive trail) living under a
  **world-root "Bullets" object — never under the squad**. (They used to be parented to the squad,
  which made fired bullets move with the player; that bug is fixed.)
- A bullet's direction is fixed when the trigger is pulled (toward the target's position at that
  moment, or toward an idle point ~30 units ahead) and **never changes**. Speed 38 u/s
  (`bulletSpeed`), visual scale 1.6 (`bulletSize`), fades after 1.45 s (`bulletLife`; × 38 = 55 u, past the gun range).
- **Hit detection** each frame: first its own target (distance ≤ half a step + a radius: 0.6 for a
  fighter, 1.1 for a crate, 2.5 for the zeppelin boss, or the column-crossing test below). If the target
  is gone or missed, **any enemy the bullet crosses** takes it: same column (`|enemy.X − bullet.x| <
  bulletHitRadius 0.55`, plus `halfWidth` for a wide boss), same band (`|dy| < 1.4`) and the bullet's z
  passed the enemy's z this frame. Idle bullets can hit crossing enemies too.
- `Pending` bookkeeping: `Fire` adds the bullet's damage to its target's `Pending`; `Land`/`Retire`
  subtract it again whichever plane was actually hit.
- **The one exception**: the boss's shots at the squad (`target is SquadController`) **home** onto the
  formation slot they were aimed at. A landed enemy shot must always cost a plane, so it cannot miss.
  On landing: `squad.Damage(round(dmg), "enemy fire from above")`.

### 3.5 The LOW band: supply crates (`SupplyLane.cs`, `Breakable.cs`)

- A queue of `supplyVisible` = 10 crates (a long line to the horizon, requested; new ones join at z ≈ 103, out of sight) **rides boats on the sea** at altitude 0.65 (`supplyAlt`: the hull sits in the water; the crates hung under parachutes at 1.5 until 2026-09-18, briefly 2.2 — "no more parachutes, put them on boats to save space": the tall canopies covered the swarm behind them), the front
  one 17 units ahead (`supplyFrontZ`), 6.5 apart (`supplySpacing`) plus room for the gates each carries (`SlotZ`, below). Break the front one and the rest
  slide forward; a new one joins at the back.
- **The crate ladder is a fixed table** (`GameConfig.crates`, `CrateDef { hp, planes, weapon }`,
  given by the user on 2026-09-16, replacing the ×2.2 ladder and the seeded reward roll):

  | # | HP | behind it | on top |
  |---|---|---|---|
  | 1 | 15 | +2 planes | |
  | 2 | 275 | +2 | |
  | 3 | 780 | +3 | **ROCKETS** (the next plane) |
  | 4 | 7 380 | +4 | |
  | 5 | 12 850 | +5 | |
  | 6 | 28 900 | +5 | **LASER** |
  | 7 | 45 500 | +7 | |
  | 8 | 68 500 | +7 | |
  | 9 | 115 890 | +9 | |

  Past the table every crate is `crateHpGrowthAfter` 1.7× the last (197 013, 334 922…) and pays the last
  row's +9. The whole ladder is × `boxHpPerLevel 1.15^(level−1)`. Row index = queue index
  (`SupplyLane.nextIndex`), reset per attempt.
- Reward on break: `round(maxHp × coinsPerHp)` coins (`coinsPerHp` is **0** since 2026-09-16: boxes pay nothing, coins come from shot-down planes only), and **its gate is launched** (below). With
  gates off (`gatesEnabled = false`) the crate itself pays the row's planes (`Value`).
- The crate shows its remaining HP as a 3D label and its reward as the hint ("+3 PLANES", or
  "ROCKETS · +3 PLANES" on a weapon crate, "$ n" for a row with 0 planes), flashes white and rocks
  when hit.
- **Weapon crates** (`CrateDef.weapon`, `BreakableKind.Weapon`): the next `WeaponDef` up from the last
  one queued (`SupplyLane.queuedWeapon` — the whole queue is spawned before the squad takes any, so
  crate 3 is Rockets and crate 6 is Laser even though the squad still flies Gatling) **hovers on top
  of the crate** (`Breakable.showcase`: its `planePrefab` at 1.5× on the box at 1.5, turning slowly, on **the weapon crate's own boat** — `Breakable.weaponBoatMesh` = `MeshFactory.BoatWeapon()`: a bigger hull in the weapon colour with a white waterline stripe (submesh 2, a white instance of the hull material), two masts with white pennants and a white bow cap. **Boats since 2026-09-18** ("no more parachutes, put them on boats to save space"): every crate is **the WoodenBoxes pack's `SquareBoxClosed`** (since 2026-09-18, "I want to use this box": dark planks, blue steel corners, rope handles; `Assets/WoodenBoxes`, its Standard material copied to URP as `Imported_WoodenBox_Mat` with the albedo **recoloured to brown wood** (`SceneBuilder.CrateWoodTexture` → `Generated/Textures/CrateWood.png`: the pack's planks are grey — "I want the box brown, wooden, why this colour", 2026-09-18; grey pixels tinted by brightness, saturated ones kept), fitted **5.2 wide / 3.7 tall** (4.4 = the gate width, then "bigger still": "make the box the size of the ones behind it… and the green ones behind it smaller"; 2.1 tall at first) on a boat widened to 2.5× in x under a "Crate" pivot object, `Breakable.boxTop` places the number / hint / prize plane so `Breakable.model` still rocks it about its centre, outline grown about the centre; the hit flash sets `_BaseColor` to HDR (3, 3, 3) because it multiplies the wood texture now; the banded `MeshFactory.Crate` is the fallback without the pack) on a separate boat object (`MeshFactory.Boat`: low hull, pointed bow, dark gunwale, a stern mast with a flag in the crate colour; `Breakable.boat`, the hull tinted like the old canopy was). **On break the box explodes and the boat sinks**: `Breakable.Break` detaches it and adds `SinkingBoat`, which drops it straight down at once (about 6 units in 0.6 s, drifting back with the sea at `scrollSpeed`; "I want the boat to sink after the crate is destroyed", then "when the small box is destroyed the big one falls straight down immediately" — a bow-up, listing 1–2 s sink was tried first and dropped). Before: a parachute canopy, and for the weapon crate a bigger, taller one with gores striped weapon-colour / white, six cords, a scalloped skirt and a knob on top (requested 2026-09-16 after two misreads: "a distinctive shape — it has a parachute, but a distinctive one"; a glow quad behind the plane was tried and cancelled: "a rectangle around it") —
  requested: "a new plane shape on top of it, my plane changes shape", then "on the crate, not above the parachute"; the hint label moved above the canopy so it never covers it). On break every plane changes
  to it (`SquadController.SetWeapon`, ring, banner) **and** its +planes gate launches like any other.
  Past Laser `NextWeapon` is null and the row falls back to an ordinary crate.
- **Reward gates** (`UpgradeGate.cs`, prefab `UpgradeGate`: mint `GateFrame` 2.2 half-width × 3.4 (1.5 × 2.4 for an hour on 2026-09-18: "the green ones behind the box smaller", then "put them back to their original size"; the big box in front hides most of a gate until it breaks)
  tall with outline, translucent additive `GatePanel` fill, two labels) — added 2026-09-15. Revert =
  `c.gatesEnabled = false` in the builder lambda + Build Everything (all gate code stays inert).
  - **A +n crate carries n gates of +1, one behind the other** (`Breakable.Gates`, created together
    in `SupplyLane.SpawnNext`, all `GateKind.Planes` with Amount 1; the first rides `gateGap` 3.5
    behind the crate, then `gateStep` 2 apart — requested 2026-09-16: "when I have +5, five come one
    behind the other, +1 each", replacing the single "+5" gate). The group slides in from far
    *together* and `Breakable.SetSlot` → `UpgradeGate.SetHold` keeps them together as the queue moves
    (requested: "not coming from the back, directly behind the thing that blocks me"). The crate is
    the barrier. With gates on a crate never pays planes itself (`Value` 0).
  - **Queue spacing is no longer uniform**: `SupplyLane.SlotZ(slot)` = `supplyFrontZ` + Σ over the
    crates ahead of (`supplySpacing` 6.5 + `gateStep` × that crate's gate count), so a crate's train
    of gates always fits before the next crate (crate 1 at 17, its two gates at 20.5/22.5, crate 2 at
    27.5; a +9 crate pushes the one behind it 24.5 back).
  - `GateKind.Shield` and `GateKind.Plane` still exist in `UpgradeGate` (SHIELD: `SetShield(Amount)`
    soaks Amount hits; PLANE: next weapon, past Laser `PowerTier++` → `PowerMult = 1 + tier ×
    gatePowerBonus 0.25`, "MK n") but **nothing spawns them any more** — the table only makes +planes
    gates and the weapon rides on the crate. The `gateWeight*`, `gatePlanesSmall/Big`,
    `gateShieldMin/Max`, `weaponAt/Every`, `boxHpBase/Growth`, `boxPlanes` fields are gone.
  - **Launch**: `Breakable.Break` → every gate `Launch()`: the train flies at the squad at `gateSpeed` 34 u/s
    (~0.6 s from 20.5 to 0, then one gate every ~60 ms — requested: "very fast, I destroy what is in front to take it").
  - **Pass** (`UpgradeGate.Pass`, when its z reaches 0.4 with the squad in the low band and
    `|squad.X − gate.X| < 2.2`): +1 plane, ring, sparks, a scattered "+1 PLANE" text. Each gate passes or misses on its own. **Miss** (squad high or off to
    the side): past z −6 it is removed silently — **a missed gate means one plane less from that crate**,
    that is the skill element.
  - Labels: "+1" + "PLANE"; the fill pulses faster once launched.
  - Balance: not measured with the new table. Note the jump 780 → 7 380 (×9.5) right after the first
    weapon: with Rockets (3 dmg, splash) and ~8 planes that crate is ~1.5 min of fire at base upgrades.

### 3.6 The HIGH band: the kamikaze swarm (`WaveSpawner.cs`, `Enemy.cs`)

This is the **latest** mechanic, replacing two earlier ones (see section 12). Fighters do not stop and
do not shoot. They come at you.

- **Lanes**: the sky is split into `swarmLanes` = **6 lanes** spread evenly from −3.8 to +3.8
  (`swarmXRange`; centres −3.8, −2.28, −0.76, 0.76, 2.28, 3.8, i.e. 1.52 apart; `GameConfig.LaneX(i)`).
  A fighter picks one lane at spawn and **never leaves it** (no drift toward the player, no sideways
  closing in the dive — the old `followSpeed`/`diveFollow` were removed on the user's request: "they
  come back to the centre while flying; I want each plane to stay in its own lane"). The stop line
  draws one dash per lane.
- **Opening crowd**: `openingCrowd` 35 fighters are already in the sky when the attempt starts, spread
  between z `openingCrowdNearZ` 62 and `openingCrowdFarZ` 148 — a dense column to the horizon (the nearest reaches the strike line ~10 s: enough to break the first crate and take its +2 gate
  in), so the round opens right in the fight (requested first "a crowd at the front from the start, not too
  many", then "close to me, dangerous, and more of them"). They count toward horde 1.
- **Spawning**: continuous stream, no gaps, at `swarmRate` 4.5 planes/s (+1.5 per horde,
  `swarmRatePerHorde`). Each fighter spawns in a random lane, altitude 5.0 ±0.8 (5.8 until 2026-09-18)
  (`swarmAltSpread`), depth `spawnDistance` 150 + random 0–12 (`swarmDepth`). The spawner refuses to
  spawn while `maxAliveEnemies` (300) are alive. All randomness comes from `System.Random(7)`, reset
  every attempt, so **the round is identical every attempt**.
  **Why 150**: at 80 the fighters spawned inside the fog gradient (fog started 70 from the camera) and
  popped in half-transparent; now the fog starts at 175 (ends 340, past the water edge), so nothing in
  play is ever fogged and a spawn happens where the eye cannot resolve it. The round therefore opens on
  a long column of fighters stretching to the horizon (requested: "a big swarm coming from the back
  from the moment I start, not planes spawning one by one, transparent"). Consequence: a fighter
  takes ~29 s from spawn to the strike line; the opening column fills that gap.
- **Flight**: base net approach speed = `scrollSpeed 9 + approachSpeed 2` = **11 units/s toward you**
  (−4 = 5 u/s until 2026-09-16: "the planes are far too slow, speed them up"). **Opening ramp** (same day:
  "only the start slow, the first 10 seconds like before, then fast"): for the first `swarmOpeningSeconds` 10 s
  of an attempt every fighter flies at `swarmOpeningApproach` −4 (net 5 u/s, the old pace), then eases up to
  the kind's `approachSpeed` over `swarmOpeningBlend` 2 s (`Enemy.Tick`, driven by `GameManager.LevelTime`).
  Bosses are not ramped. **Every fighter has its own pace**: `Enemy.SpeedMult` = 1 ± `swarmSpeedSpread` 0.4
  (3–7 u/s), drawn from the seeded rng at spawn, so neighbours never fly abreast — one races ahead,
  the next lags. Spawn intervals are jittered too (`swarmSpawnJitter` 0.6: each gap is 0.4–1.6× the
  nominal one, average rate unchanged). Both were added because 4–5 fighters spawned close together at
  the same speed arrived as a horizontal row. A fighter weaves ±0.2 (`weave`) inside its lane.
- **The strike line is invisible** (z = `diveZ` 7). The warning is a **lock-on reticle on each
  incoming fighter** (`ThreatMarkers.cs`): a billboarded quad (`Reticle.png`: ring + four corner
  brackets + centre dot, generated by `SceneBuilder.ReticleTexture`, material `ThreatMarker`) pinned
  1.4 u in front of every fighter within `threatWarnRange` 20 of the line. Far: big (2.8×), faint white,
  slowly turning. Closing (weighted by n²): tightens to 1.25×, spins up to 240°/s, turns red and pulses.
  When the fighter crosses and commits (`Enemy.StrikeT` < 0.3 s) the reticle **pops** outward and fades:
  the lock is released. **The boss** wears a big slow orange reticle (`bossColor`, 1.7× his scale,
  3.5 u in front) from the moment he spawns until he parks, and his model gets 60 % of the
  `enemyFarScale` distance boost, so he is unmistakable from the horizon (requested: "the boss must be
  clear while coming from far"). Pooled (40 quads), `LateUpdate`, no per-frame allocation. This replaced a
  green→red dashed line per lane (`DiveLine`, deleted) that the user found ugly: "something used in
  this kind of game, more professional and effective".
- **The strike run** (`Enemy.cs`, past the line) — **every fighter that crosses `diveZ` hits a plane;
  there is no dodging** (requested: "I want it to be forced to crash into one of the planes"). On
  crossing it locks the visible formation slot nearest in x to its lane and records `strikeStart`.
  Then, each frame, with `p` = how far Z has come from the line to the slot's z (0..1) and
  `e = smoothstep(p)`:
  - Z keeps flowing at its own cruise speed (no hitch at the line) and accelerates into the dive
    (`strikeAccel` 0.8: ×1.8 by impact);
  - X and altitude are `Lerp(strikeStart, slot, e)` — the slot is re-read every frame so it tracks the
    squad, and `e → 1` guarantees it lands on the plane;
  - **one of five figures** (`Enemy.StrikeStyle`, drawn from the seeded rng at spawn, so runs are
    never all alike — requested: "4–5 ways to destroy me, chosen randomly, not all the same") is layered
    on the straight path; every figure is scaled by `arc = sin(p·π)`, so it is 0 at the line and 0 on
    the plane (no jumps at either end):
    0 **HOP** — up `strikeLift` 1.2 into the air, down onto the plane;
    1 **SWOOP** — dips 0.8×lift under, climbs into the plane from below;
    2 **BARREL ROLL** — shallow hop (0.35×lift) with one full 360° roll (`strikeRoll = 360·e`);
    3 **SLALOM** — an S-curve `sin(2πp) × strikeSide 1.3` (side chosen by `seed`), half lift;
    4 **CORKSCREW** — two spiral turns, radius `arc × strikeSide`, with a ±35° roll following the turn;
  - it shrinks to `strikeShrink` 0.5 (half) on a **smootherstep** curve, with a soft 8 % puff as it commits;
  - the model's pitch/bank follow the actual velocity (nose up over the arc, down onto the plane,
    wings into the turn) plus the figure's roll, smoothed with a 12/s exponential so nothing snaps; the
    bob is off on the run;
  - **it is untouchable on the run**: `Enemy.Striking` is true, `TakeDamage` ignores it, `AutoFire`
    does not target it, `BulletPool.Alive`/crossing tests skip it (requested: "once it crosses the line
    bullets must never affect it"). Shoot them *before* the green line or lose a plane.
  - When Z reaches the slot: `Ram(slot)` → `squad.FallSlot = slot` + `squad.Damage(1)`, so the
    **struck plane is the one that tumbles** (`FXManager.Fallers` honours `FallSlot`). Explosion, red
    "RAMMED", **no coins, no kill**. If its plane is gone by then it takes the last slot left.
- **Miss** only happens when there is nobody to strike (`VisibleCount` 0, i.e. the game is already over):
  past z = −4 it vanishes (`Enemy.Vanish()`). The old `ramZ`/`ramHitX`/`ramHitPerPlane` box test and
  `diveClimb` are gone.
- **Balance consequence (not yet re-measured)**: dodging no longer exists, so every fighter not shot
  before z = 7 costs a plane. Attempt 1's "8 rammed of 100" from the bot runs will be higher; the bot's
  crate dives (which leave the high band) now cost planes. Re-run the bot and retune `swarmRate`,
  the crate table, or `lineOfFireRange` before trusting the curve in section 4.
- **Shot down** (`Enemy.Kill(false)`): coins (`coins` 1 × RevenueMult, via `GameManager.AddCoins`),
  `FXManager.CoinBurst` (gold discs + "+N"), a falling wreck (`UnitFall`), explosion, kill counter.
- **The bosses are the Sparrow Fighter Spacecraft, each its own colour** (2026-09-18, the Sparrow_Fighter pack, "every boss a different colour, use the Sparrow for the bosses"): `EnsureSparrowLow` decimates the pack's 24k mesh to 6k once into `Art/Enemies/Sparrow_low.asset` (the 840 MB pack is git-ignored; 1k copies of its grey albedo / normal / emissive are committed, `SparrowBody` material with emission); `SparrowBossPrefab` ("BossSparrow": nose +Z so BossPrefab's 180° applies, fitted 2.6 wide, outline, flash at the nose, HP label) is the only entry of `WaveSpawner.bossPrefabs` (the four procedural looks remain the fallback), and `WaveSpawner.bossColors` = `SceneBuilder.BossTints` — seven HDR tints (blue, orange, green, red, violet, yellow, white, ×2.2–2.6 because the grey texture averages 25% brightness) applied per boss number through `Enemy.SetTint` (a `_BaseColor` property block; the hit flash now goes through `ApplyBodyColor`, HDR white, and `Init` clears the tint for pooled bodies).
- **The fighter is the Kawasaki OH-1 "Ninja"** (2026-09-18, the OH-1_Complex pack, "I want the enemy planes to be the OH-1 Ninja JGSDF"): `SceneBuilder.EnsureOH1Low` builds `Assets/_Game/Art/Enemies/OH1_Ninja_low.prefab` (+ a mesh container) once from the pack — outer shell only (fuselage, glass, doors, rotor hub, tail rotor, fixed gear; no cockpit interior / pilots / lights / 9k-shard blades), each part decimated with the git package **com.whinarn.unitymeshsimplifier** (~10.7k triangles; the defaults protecting borders and seams stall on these scans, so they are off; aggressiveness 12 with a link distance glued it to 69k) at the pack prefab's own transforms; the 836 MB pack is git-ignored, the light prefab and 1k copies of the fuselage albedo / normal (`OH1_Fuselage_*.png`, `OH1Fuselage` / `OH1Glass` materials) are committed. `OH1EnemyPrefab`: the pack's nose is −Z so the helicopter sits turned 180° inside the "Body" that `Enemy` turns toward the player, fitted 3.3 long (rotor disc ≈ 2.8; `scale` 0.72 still applies), the rotor hub is `propeller` with the prop mesh as a translucent blur disc at 11.5 / 0.62, the tail rotor spins through a pivot whose Z is the hub axis, outline on the fuselage only, chin flash at the nose, smoke at the tail; the enemy hit flash is HDR (3, 3, 3) because the base colour multiplies the texture. The crimson procedural fighter is the fallback without the low prefab.
- Fighter definition: `Enemy_Fighter` — hp **1** (one Gatling hit; hp 2 was tried and dropped on 2026-09-16: "I didn't like two hits"), scale **0.85** (0.72 until 2026-09-18, "make the enemy planes a little bigger"; 1.25 long before), coins **20** (10 earlier on 2026-09-16), `approachSpeed 2`,
  `shotDamage 1` (used as ram damage). `fireEvery` is unused (fighters never fire).
- **Hp over its head**: every fighter carries an `HpLabel` (TMP, size 6, 1.25 up), hidden at spawn and switched on by the
  first hit that counts (`Enemy.TakeDamage`), showing the hp left ("I want its hp to show above it when I shoot it",
  2026-09-16). A boss shows his all the time.
- Guns only engage inside `lineOfFireRange` 48 units (34 until 2026-09-15: "let my bullets reach farther"), so the swarm is visible flying in for several
  seconds before it starts dying. Do not raise this back to 95: the swarm then dies at the horizon and
  the game looks empty.

### 3.7 Hordes and bosses

- **Bosses come on a fixed clock** (2026-09-16, replacing the horde plane counts): boss k **starts
  moving** (spawns at `spawnDistance + 2`) at `bossFirstAt 20 + (k−1) × bossEvery 23` seconds into the attempt (20, 43, 66, 89, 112,
  135, 158 s — requested "20 s until he starts moving, not until he has reached me", then "between 22 and 24 s apart"). His
  flight to the alarm line takes `WaveSpawner.BossLead()` — from `spawnDistance + 2` to
  `enemyStopZ + 14` at `scrollSpeed + approachSpeed` = (152 − 26) / 11 ≈ 11.5 s — so boss 1 is announced at
  ~31.5 s and parks ~1.3 s later (`BossSpawnTime(k)`, `BossAnnounceTime(k)`). **Horde k** is simply everything streamed before boss
  k; `HordeTarget` (the HUD bar) is the estimate `openingCrowd + rate × time` for horde 1 and `rate ×
  (bossEvery − bossSpawnGap)` after.
- **HP is a table** (`bossHp`): **555, 3945, 15960, 27500, 60500, 76500, 125200** for bosses 1–7 (given by
  the user); past it × `bossHpGrowthAfter 1.6` per boss. His shot takes `1 + (k−1) ×
  miniBossShotPerBoss 1` planes: **boss k takes k planes per hit** — 1, 2, 3, 4… (was 1, 3, 5…, requested
  2026-09-16). All bosses share `Enemy_MiniBoss` (scale 3.2,
  `Wide`, `halfWidth` 3.4).
- **Four looks, two bosses each** (`WaveSpawner.bossPrefabs`, `bossesPerLook 2`; the last look serves
  every boss past the table — requested "every two bosses the same shape, then the last one
  different"): **1–2** `EnemyMiniBoss` the slate/orange four-engine gunship (`MeshFactory.BossPlane`),
  **3–4** `EnemyMiniBoss2` the olive/yellow twin-boom heavy fighter (`BossTwinBoom`, two big props),
  **5–6** `EnemyMiniBoss3` the crimson/cream flying-wing fortress (`BossFlyingWing`, six props along
  the sweep), **7+** `EnemyMiniBoss4` the purple/gold war airship with a skull nose (`BossAirship`,
  pusher props). All built by `SceneBuilder.BossPrefab(name, mesh, prop, M, propPositions, propScale,
  flashPos, mats…)`; same submesh layout (body, accent, glass, dark, glow). `hordePlanesBase/PerHorde`
  and `miniBossHpBase/Growth` are gone. Each announcement logs `[boss] BOSS k announced at t s (started moving at t0)`.
- The boss flies in at net 11 u/s (`approachSpeed 2`), brakes over the last 3 units and **parks at
  `enemyStopZ` 12** (the front line). The moment he parks he fires, then every `fireEvery` **4 s** (was 1.6; requested 2026-09-16). His
  bullets home (see 3.4). `Parked` is true while he sits there.
- **Announcement**: the boss only "counts" (HUD health bar, "BOSS k" banner, red warning vignette,
  warning sound, bot logic) once he is within 14 units of the line (`bossAnnounced`). Before that the
  HUD keeps showing the horde you are still fighting. `WaveSpawner.CurrentBoss` is null until then.
- **The next horde** starts `bossSpawnGap` 3 s after the boss spawns and streams in behind him. While
  he lives, fighters of a later horde **loiter** behind him (each holds at `boss.Z + holdBehindBoss 4 +
  a personal 0–6 offset`, `Enemy.Held`); the moment he dies they flood forward.
- **Stop line** (`StopLine.cs`): one red dash per swarm lane (6) across ±3.8 at the boss's parking z (11.1, just in
  front of his nose) and just under his altitude. Visible **only while a boss is announced**, pulsing,
  flaring brighter as he closes in. It tells the player where he will stop and when.
- Progress accounting: `WaveSpawner.Release` increments `killedPerHorde[hordeIndex]` for every fighter
  that leaves the sky (shot, rammed, or flown past), so the HUD bar "HORDE k  gone/target" fills
  regardless of how they left. `GameManager.UnitsKilled` counts only shot-down planes (and bosses).
- `Horde` (public) is the horde **being fought**: while a boss is flying in but not yet announced it
  reports the previous horde, so the HUD does not jump to "HORDE 2 0/200" at 3 s.

### 3.8 Coins and the meta loop (`Progress.cs`, `GameManager.cs`, `HUD.cs`)

- The bank is `Progress.Coins`, persisted in PlayerPrefs (`sq_coins`, `sq_attempts`, `sq_best`,
  `sq_fr`, `sq_dmg`, `sq_rev`). `GameManager.Awake` loads it.
- `GameManager.AddCoins(c)` banks `max(1, round(c × RevenueMult))` immediately (no "collect at the
  end"), adds to `RunCoins`, pops "+N" under the HUD counter, and **returns the banked amount** so the
  world burst shows the multiplied value.
- **Lobby** (state `Title`): shows the bank, "ATTEMPT n · best: horde m", and three cards with level,
  effect and price. `HUD.OnBuy(int)` buys (button wired with a persistent int listener),
  `HUD.OnStartButton` starts. Only buttons work in the lobby, not taps.
- Upgrades: cost = `base × upgradeCostGrowth 2.4^level` with bases **20 / 20 / 20** up to level 7 (20, 48, 115, 276, 663, 1592,
  3822, 9172); **from level 8 on** (`upgradeLinearFromLevel`) the price climbs by a flat `upgradeLinearStep` 5000 per level
  instead: 14172, 19172, 24172 ... (`Progress.Cost`; "at level 8 the cost goes up by 5 thousand", 2026-09-16)
  Effects: `FireRateMult = 1 + 0.4·lvl`, `DamageMult = 1 + 1.0·lvl`,
  `RevenueMult = 1 + 0.2·lvl`. Damage matters against crates and bosses only (fighters have 1 HP).
- `StartGame()`: `Attempts++`, save, `StartLevel(1)`: resets spawner, supply lane, zeppelin boss,
  squad, FX, shows the "ATTEMPT n" banner. `Lose(reason)`: saves `BestHorde`, state `GameOver`, the
  death panel shows the reason, attempt, horde, kills and "+RunCoins coins for the next attempt". A tap
  returns to the lobby.
- States: `Title` (lobby) → `Playing` ⇄ `Paused` (pause button, tap resumes) → `GameOver` → `Title`.
  `LevelClear` exists but is unreachable while `endless = true`.

### 3.9 HUD (`HUD.cs`)

Top bar: "ATT n", "$ bank" with the "+N" pop (one pop per reward, never summed with the previous one: it used to add kills landing within 1.2 s and "+20" was read as 20 per plane; 2026-09-16), a progress bar that is **blue "HORDE k  gone/target"**
normally and **red "BOSS k  hp"** while a boss is announced. Bottom: PLANES pill, weapon name and
description, KILLS, a fading hint ("DRAG TO FLY · DIVE for crates · CLIMB to fight"). Center: banner
text (attempt / boss), red warning vignette, screen flash. Overlays: lobby, pause, level clear
(unused), squadron lost. Sound toggle: the speaker hex button on the settings card (`ToggleSound`, `soundIcon` swaps the AIRIDev on/off icons).

**The look (2026-09-19, the hyper-casual pass: "convert the UI to GUI Pro - Casual Game", then a reference screenshot - "I want it like
this")**: every screen is drawn with the Layer Lab *GUI Pro - Casual Game* kit (`Assets/Layer Lab/GUI Pro-CasualGame`, only the sprite
components the UI uses are tracked, see .gitignore): its pre-sliced Button01 pills (green / blue / yellow for the cards, orange for the
modal prompts, red for BOSS and the death reason), the big Button02 as TAP TO START, `Popup01_Single_Navy` cards with a `Title_Flag01`
hanging over the top edge, `Title_Ribbon_Bg_Orange` as the banner, `ResourceBar_Bg` pills with the coin / plane overhanging the right end,
`Slider_Basic02` for the horde bar and the settings slider, the `Switch` for sound, and its flat white pictos (gear, pause, play, target,
thunder, coin). Type is Lilita One with the navy outline (`fontOutline` / `fontOutlineSmall`) - the same face as the in-world labels.
Layout follows the reference: bare gear / pause glyphs top left (`GlyphButton`: Outline + Shadow, no plate), "Attempt n" top centre,
the bank and the plane count as bars top right, the horde bar under them; the lobby has the three tall upgrade cards along the bottom
(coloured frame, name in the head, the level as a bare number in a grey corner badge, the picture in a darker well, five pips = level
mod 5 lit, an UPGRADE pill with the coin and the price; `HUD.cardPips`, `badgeLevel`, `pricePlain`). Kit helpers in `SceneBuilder`:
`GImg` (a sprite sliced at `Fit(designHeight, wantHeight)`), `Type`, `Plate`, `CoinBar`, `GButton` / `GButtonClick`, `GlyphButton`,
`IconButton`, `SquareButton`, `Bar`, `UISlider`, `Card`. From the user's five reference screenshots (2026-09-19, `C:SERSSERDESKTOPGAME IMAGES`): A
**LOADING SPLASH** (`HUD.SPLASHPANEL`: THE TWO-TONE SKY / SQUAD LOGO, THE JET, A YELLOW BAR FILLING OVER `SPLASHSECONDS` 2.2, THEN GONE), THE
**PLAY TOP BAR** (A BLUE SQUARE PAUSE AT THE LEFT, THE HORDE BAR WITH ITS PERCENT AND A FLAG IN THE MIDDLE, THE BANK AND PLANE COUNT AT THE
RIGHT), THE **PAUSE SCREEN** (A BLUE DIM, SPEAKER + GEAR GLYPHS, HOME (`GAMEMANAGER.HOME`: CLEARS THE SKY, KEEPS THE COINS, BACK TO THE
LOBBY) AND RESUME PILLS), THE **SETTINGS SCREEN** (A FULL LIGHT-BLUE DOTTED PAGE: SETTINGS, THE BANK, THE PLANE SPEED BAR OVER ITS SLIDER,
THE SPEAKER, CREDITS + VERSION, A BIG WHITE X). THE REFERENCE SHOP (GEMS / NO-ADS) HAS NO COUNTERPART: THE GAME SELLS NOTHING.
`IconButton`, `Bar`, `UISlider`, `Card`. The lobby's hero is still the *EmbersStorm* jet in 3D (`HangarShowcase`). Earlier passes the
same week - the generated "tactical glass", the Strategic Warfare / AIRIDev kits, the flat glyphs - are in git history only.

From the user's five reference screenshots (2026-09-19, `C:\Users\user\Desktop\game images`): a **loading splash** (`HUD.splashPanel`: the
two-tone SKY / SQUAD logo over a dotted sky, the jet, a yellow bar filling over `splashSeconds` 2.2, then gone), the **play top bar** (a blue
square pause at the left - `SquareButton` -, the horde bar with its percent and a flag in the middle, the bank and plane count at the right;
the gear moved to the pause screen), the **pause screen** (a blue dim, speaker + gear glyphs - `HUD.soundIcons` swap the picto -, HOME
(`GameManager.Home`: the sky cleared, the coins kept, back to the lobby) and RESUME pills), the **settings screen** (a full light-blue dotted
page: SETTINGS, the bank, the PLANE SPEED bar over its slider, the speaker, credits + version, a big white X). The reference shop (gems /
no-ads) has no counterpart: the game sells nothing.
