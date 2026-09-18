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

### 3.7b The levels (2026-09-19: "10 levels, easy first and harder each one; level k has k bosses; the game as it was is level 7")

- **Level n has n bosses** (`GameManager.BossCount = Level`, which replaces `config.lastBoss` in `WaveSpawner.AfterLastBoss` /
  `Horde`; the boss clock is unchanged, so level n runs `bossFirstAt + (n-1) × bossEvery` seconds plus the last fight: ~45 s for
  level 1, ~4 min for level 10). Ten levels (`config.levelCount`).
- **Difficulty is one line through the tuned game**: every number in the config describes `levelBaseline` 7; boss hp is multiplied by
  `HpScale` and the swarm's stream rate and opening crowd by `RateScale`, both `LerpUnclamped(level1Scale, 1, (n-1)/6)` -
  `level1HpScale 0.35`, `level1RateScale 0.55`, so level 1 bosses have 35% of the table's hp and the swarm streams at 55%; level 7 is
  exactly the old game; levels 8-10 keep climbing (10: hp ×1.33, stream ×1.23). Boss shot damage still grows per boss number only.
- **Progress**: `Progress.Stage` (the level the next attempt plays) and `Progress.Cleared` (highest cleared), PlayerPrefs `sq_stage` /
  `sq_cleared`. `StartGame` plays `Stage`; a level's last boss down → `Win()`: `Cleared = max`, `Stage = n+1` (or `Progress.Won` on
  level 10 → `GameCompleted`), the clear card says "LEVEL n / CLEARED! / LEVEL n+1 UNLOCKED" (VICTORY / ALL 10 LEVELS at the end);
  dying keeps the level. The lobby's level row ("LEVEL 3 / 10 · 3 BOSSES") has kit chevrons (`GameManager.SelectLevel(±1)`,
  `HUD.OnLevelPrev/Next`) that step through levels 1..Cleared+1, dimmed at the ends. The HUD chip says "LV n" (was "ATT n"); the
  start banner "LEVEL n"; the death card "LEVEL n · attempt · boss k of n".

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

**The look (2026-09-18, third pass - the bought kits, "make the UI from these three packages, best practice")**: every frame, button,
bar and slider track is the *Strategic Warfare Sci-fi UI Starter Pack* sheet (`Assets/Strategic Warfare UI Starter Pack`), 9-sliced
on import by `SceneBuilder.ImportKit` (the pack's own demo stretches each sprite; the sheet is a 6000-px source imported at 2048, so
borders and pixels-per-unit are converted to texture pixels there) and tinted per use the way the pack tints its own demo: charcoal
frames under a cool steel tint (`UiFrame`), the light button under amber for the one primary action of a screen, the warning bar under
red for BOSS / the death reason, the hazard-striped plate for the hint. The pictorial icons are the *AIRIDev Sci-Fi UI Icon Pack*
(`Assets/AIRIDev_Scifi_UI_Icons`): coin, pause, settings, play, retry, trophy, plane, boost / energy on the upgrade cards, volume.
The lobby's hero is an *EmbersStorm AirStrike* fighter turning in 3D (`HangarShowcase`). Type stays Barlow Condensed with amber
accents. Kit helpers in `SceneBuilder`: `Kit` (a slice as a sliced or whole Image), `Plate`, `Card` (the framed panel with a 120-px head
for a header), `IconBar`, `Flat` / `FlatButton`, `HexButton`, `Bar`, `UISlider`. If a pack is missing the build warns and the generated
chamfer plates stand in.

### 3.10 Feedback and FX (`FXManager.cs`)

Explosions (particle prefab + expanding ring + shake), sparks on every bullet impact, rings (also
used as the old "charging" telegraph), floating world text (`FloatText`), joiners/fallers for the
squad, wrecks (`UnitFall`), **`CoinBurst(pos, value)`** (1–5 gold discs tossed up that fall, spin and
shrink, plus a gold "+N"), screen shake and flash. `ClearAll` wipes everything at level start.

### 3.11 Sound (`AudioManager.cs`)

Procedural blips behind an `Sfx` enum (`Gun`, `Rocket`, `Laser`, `Flak`, `Boom`, `Unit`, `Bad`,
`Warn`, `Pickup`, `Tick`, `ShieldHit`, …). Mute toggle on the HUD. Nothing was tuned; treat all audio
as placeholder.

### 3.12 Determinism

`WaveSpawner` uses `System.Random(7)`, re-seeded in `ResetForLevel`, and consults nothing about the
player when spawning. Fighters do follow the player *after* spawning, so what you see differs run to
run, but the spawn script (when, where, how many, when the boss comes) is fixed. `UnityEngine.Random`
is used only for visuals (bob phase, coin scatter). The bot's runs are therefore comparable.

---

## 4. The difficulty curve — intent and measurement

**Intent (the user's words, paraphrased):** every attempt is the same round and it should be hard.
Attempt 1 must reach boss 1 and die no matter what, but bank coins. Attempt 2 damages him a bit,
attempt 3 more, attempt 4 kills him and continues into the next horde until boss 2 kills the player
instantly. "Each attempt is a gathering attempt for the next."

**Measured with the bot** (runs 26 + 27, fresh bank, boss 1 at 300 HP, the bot buys the cheapest
affordable upgrade each lobby):

| Attempt | Upgrades (fire/dmg/rev) | Result |
|---|---|---|
| 1 | 0/0/0 | 92 of 100 shot down, 8 rammed; reached boss 1, died with 260/300 left |
| 2 | 1/0/1 | boss at 180 |
| 3 | 1/1/2 | boss at 137 |
| 4 | 2/2/2 | boss at **6** |
| 5 | 3/2/3 | killed boss 1, cleared all 200 of horde 2, died at boss 2 with 558/750 left |

Boss 1 was then lowered to **280** so attempt 4 gets the kill. That value is committed but **was not
re-run**. Attempts last ~55–60 s. A 200 s bot run covers three attempts; run a second one without
`RESET=1` to see attempts 4–6 (progress persists in PlayerPrefs).

Earlier tuning data for the abandoned mechanics is in section 12 and in the Claude memory file, for
context only.

---

## 5. Architecture — every script

All runtime code is in namespace `SkySquad`. Singletons use a static `I` set in `Awake`.

### Runtime (`Assets/_Game/Scripts/Runtime/`)

| Script | Responsibility | Key API |
|---|---|---|
| `GameManager.cs` | State machine, wiring hub (`config, squad, input, enemies, supply, boss, hud, fx, sfx, world`), coins, level start/lose | `State`, `StartGame()`, `StartLevel(n)`, `Lose(reason)`, `AddCoins(c) → int`, `OnTap()`, `Pause/Resume/Lobby()`, `LevelTime`, `LevelDuration` (∞ when endless), `BossPhase`, `ScrollSpeed`, `RunCoins`, `UnitsKilled`, `OnStateChanged` event |
| `GameConfig.cs` | Every tunable, a ScriptableObject (section 7) | fields only |
| `Progress.cs` | Static meta: bank, attempts, best horde, 3 upgrade levels, PlayerPrefs | `Coins`, `Attempts`, `Levels[3]`, `FireRateMult/DamageMult/RevenueMult`, `Cost(u)`, `CanBuy`, `Buy`, `Effect(u)`, `Load/Save/Reset` |
| `SquadController.cs` | The player: count, position, formation slots, plane visuals, damage | `Count`, `X`, `Alt`, `IsHigh`, `VisibleCount`, `Dps`, `SlotWorld(i)`, `SlotLocal(i)`, `Grow(n)`, `SetCount`, `Damage(n, reason)`, `MuzzleFlash()`, `AutoInput/AutoAxis` (bot hooks), `OnCountChanged` |
| `SquadInput.cs` | Touch/mouse drag, keyboard axis, tap detection (Input System) | `DragDelta`, `KeyAxis`, `Tapped` |
| `AutoFire.cs` | Volleys, target selection per band and lane, weapon kinds | `Primary` (current target, for debugging) |
| `BulletPool.cs` | Straight projectiles, hit tests, enemy homing shots | `Fire(from, target, aim, dmg, color, speed, size)` |
| `WaveSpawner.cs` | The round script: swarm stream, hordes, bosses, hold-behind, announcement, progress counters | `Active`, `Horde`, `HordeKilled`, `HordeTarget`, `HordeProgress`, `Bosses`, `CurrentBoss`, `BossAlive`, `ParkedCount`, `Flight`, `Release(e)`, `KillAll(silent)`, `ResetForLevel(n)` |
| `Enemy.cs` | One enemy: kamikaze flight or boss parking/shooting, damage, death kinds | `Tick(dt, limitZ)`, `TakeDamage`, `Kill(silent)`, `Ram()`, `Vanish()`, `Kind`, `Hp`, `Wide`, `Parked`, `Held`, `Pending`, `HordeIndex`, `HoldOffset`, `X/Z/Alt` |
| `EnemyKindDef.cs` | ScriptableObject: id, displayName, hp, halfWidth, approachSpeed, fireEvery, shotDamage, coins, scale, miniBoss, prefab, color | |
| `ThreatMarkers.cs` | Lock-on reticles on incoming fighters (the "danger" indicator); pops on strike commit | `material`, `poolSize`, `farColor`, `nearColor`, `popSeconds` |
| `SupplyLane.cs` | Crate queue in the low band, each crate with its reward gate behind it | `Front`, `Active`, `Release(b)`, `NextWeapon(w)`, `ReleaseGate(g)`, `ResetForLevel(n)` |
| `UpgradeGate.cs` | The reward gate behind a crate: +n planes from the crate table (shield / next-plane kinds coded but unused; `gatesEnabled`) | `Init(kind, planes)`, `SetHold(z)`, `Launch()`, `Kind`, `Planes`, `Launched`, `Done`, `X/Z/Alt`, `HalfWidth` |
| `Breakable.cs` | One crate: HP, label, hint, hit flash, the next plane hovering on top (weapon crate), break → coins (+ weapon) + launches its gate | `Shoot(dmg)`, `Gate`, `X/Z/Alt`, `HalfWidth`, `AimPoint`, `Dead`, `Kind`, `Value` |
| `StopLine.cs` | The boss's red dashed parking line (boss-only, shown while he is announced) | `dashes[]`, `color` |
| `DiveLine.cs` | The green dashed line at `diveZ`, one dash per lane, green→red as a fighter in that lane closes in | `dashes[]`, `farColor`, `nearColor` |
| `FXManager.cs` | All juice (section 3.10) | `Explosion`, `Sparks`, `Ring`, `FloatText`, `CoinBurst`, `Joiners`, `Fallers`, `UnitFall`, `Shake`, `Flash`, `ClearAll` |
| `HUD.cs` | Screen UI, lobby, overlays | `Banner`, `Warn`, `Flash`, `ShowHint`, `CoinPop`, `RefreshLobby`, `OnBuy(i)`, `OnStartButton`, `OnPauseButton`, `ToggleSound` |
| `HangarShowcase.cs` | The title screen's 3D aircraft: turns the EmbersStorm jet under its own camera (RenderTexture `Generated/Textures/Hangar.renderTexture`, layer `Hangar`); HUD switches the rig with the title panel | `model`, `turnSpeed`, `bank` |
| `CameraFollow.cs` | Soft follow + shake | `basePosition`, `followX`, `followAlt`, `smoothing` |
| `WorldScroller.cs` | Scrolls water texture, buoys, clouds, cloud rails | `water`, `buoys`, `clouds`, `waterTilesPerUnit` |
| `PlaneVisual.cs` | One squad plane model: slot bob, bank, leader material, muzzle flash | `SetBase`, `SetLeader`, `Flash(color)`, `index` |
| `AudioManager.cs` | Procedural SFX, mute | `Play(Sfx)`, `Muted` |
| `AutoPilot.cs` | The test bot (section 10) | command-line args, `autoplayInEditor` |
| `BossController.cs` | **Legacy** zeppelin end-of-level boss with HP/timer bars. Never activates while `endless = true` | `Active`, `Fighting`, `Dead`, `TakeDamage` |
| `RocketPool.cs`, `TracerPool.cs` | **Both unused since 2026-09-17** (every weapon fires `BulletPool` bullets now; kept compiled in). Rocket / laser-beam visuals. Rockets (2026-09-16): straight out of the pods at 55 → 100 u/s with a little spread, snap onto the target line, a short additive fire tail (`Rocket` prefab trail = `Tracer` material, tinted yellow → orange) and orange-tinted body, a spark burst on arrival (no explosion/shake per rocket). Damage is still dealt on fire in `AutoFire` | `Fire(...)` |

### Editor (`Assets/_Game/Scripts/Editor/`)

| Script | Responsibility |
|---|---|
| `SceneBuilder.cs` | `Prepare()` imports TMP resources; `BuildAll()` deletes stale generated assets, creates the font, materials, textures, meshes, prefabs, data assets (with **all values set in a lambda**), the scene (camera rig, sun, sky, post FX volume, world, managers, squad, enemies, supply, stop line, HUD canvas, lobby, overlays, EventSystem), applies URP asset settings and player settings, saves the scene. Menu items **Sky Squad/1. Prepare (import TMP resources)** and **Sky Squad/2. Build Everything**. |
| `MeshFactory.cs` | Procedural low-poly meshes via a small `MeshBuilder` (boxes, ellipsoids): `Plane(style)`, `EnemyPlane()`, `Propeller()`, `Crate()`, `Bullet()`, `Coin()`, `Zeppelin()`, `Blimp()`, `Rocket()`, `Buoy()`, `Drone()`, `GateFrame`, `Panel` |
| `BuildScript.cs` | `BuildWindows()` → `Builds/Windows/SkySquad.exe` (StandaloneWindows64); `BuildAndroid()` → `Builds/Android/SkySquad.apk`. Menus **Sky Squad/Build Windows (test player)** and **Sky Squad/Build Android (APK)** |

### Frame order (who calls whom)

1. `SquadInput` reads the device → `SquadController.Update` moves the squad (or takes `AutoAxis`
   from the bot).
2. `WaveSpawner.Update` spawns, then calls `Enemy.Tick(dt, limitZ)` for every enemy (a copy of the
   list, because a ram or kill removes entries). A ram may end the game mid-loop; the loop checks the
   state after each tick.
3. `AutoFire.Update` picks targets and calls `BulletPool.Fire`.
4. `BulletPool.Update` moves bullets and lands them (`Enemy.TakeDamage`, `Breakable.Shoot`,
   `SquadController.Damage`).
5. `SupplyLane.Update` refills the crate queue. `StopLine`, `HUD`, `FXManager`, `CameraFollow`
   (LateUpdate) render state.

---

## 6. Everything is generated — the SceneBuilder pipeline

**Rule zero: never edit the scene, prefabs, materials or data assets by hand.** Edit
`SceneBuilder.cs` (or `MeshFactory.cs`) and run **Sky Squad → 2. Build Everything**. The builder:

1. Deletes stale generated assets from a list (checked with `File.Exists`, since assets whose script
   class no longer exists cannot be loaded).
2. Creates the TMP font asset and two outline presets (`fontOutline`, `fontOutlineSmall`).
3. Creates materials (URP Lit / Unlit / transparent / particle): plane bodies, enemy body (crimson)/accent (cream)/glass (sky blue)/cowl (dark), `propDisc` (translucent spin disc),
   bomber (boss) body/accent/glow, crate/band/canopy, `outline` (Unlit, `_Cull = 1`, inside-out hull),
   `bullet` (white, tinted per shot by a property block), `coin` (gold Lit), `stopLine` (transparent
   red, alpha driven by `StopLine`), water (with a procedural texture), cloud (soft sprite),
   buoy, tracer, particle, smoke, shield bubble, bars, muzzle flash, prop, rocket.
4. Saves meshes from `MeshFactory` (`fighter`, `attacker`, `jet`, `prop`, `enemy`, `zeppelin`,
   `crate`, `rocket`, `buoy`, `bullet`, `coin`).
5. Builds prefabs: three squad planes — **Asset Store models since 2026-09-18** ("use this airplane instead of the airplane in my game"): `ModelPlanePrefab` wraps a pack model (Gatling = **Zero Fighter** `Assets/Klareh Games/Zero/zero.prefab`, Rockets = **Aircraft C-130** assembled from its part prefabs by `AssembleC130` like the pack's demo scene — its lava texture is the pack's own, Cannon = **Space shuttle of the future** `Assets/SpaceShuttle/Assets/Prefabs/SpaceShuttle v2.prefab`, **pitched nose-up 24°** so the camera behind sees its back and cockpit, not only the engine nozzle — "the third plane with its nose raised, show its back", 2026-09-18): nose to +Z, scaled to a 1.6 / 1.7 / 1.6 wingspan (no longer than 2), centred, Built-in Standard materials copied to URP Lit as `Generated/Materials/Imported_<name>` (metallic capped 0.2, smoothness 0.6), landing gear / exhaust particles / scripts / lights / colliders dropped, toon outline per part, flash on the nose, every child named "prop…" spins (`PlaneVisual.propellers` + `propellerAxis`: Z on the Zero, Y on the C-130's four paddles); the procedural `MeshFactory` planes are the fallback when a pack is not imported. Then `EnemyFighter` and `EnemyMiniBoss` (`EnemyPrefab`: body rotated
   180° nose-forward, outline hull at 1.07, propeller, muzzle-flash quad, HP label for the boss),
   `Breakable` (crate 1.5× + outline + labels), `Boss` (zeppelin + bars), `Explosion`, `Sparks`,
   `FloatText`, `Ring`, `Rocket`, `Bullet` (TrailRenderer time 0.22, width 0.22→0.05 + `Slug` child),
   `Coin`.
6. Creates the data assets with `Asset<T>(name, init)`. **The init lambda sets every number that
   matters**, because an existing asset keeps old values for fields the lambda does not touch. If you
   add a field to `GameConfig`, add it to the lambda too or the asset will silently keep the C#
   default from whenever it was first created.
7. Builds the scene: camera rig + `CameraFollow`, sun (soft shadows), skybox, `PostFX` volume
   profile (Bloom intensity 0.85 / threshold 0.7 / scatter 0.6; Vignette 0.28 / smoothness 0.45; Color
   Adjustments saturation 12 / contrast 10 / exposure 0.1), world (water plane, 16 buoys, 9 sky clouds,
   20 "cloud rail" puffs along both edges at the split altitude), `Game` object (GameManager,
   AudioManager, FXManager), `Squad` object (SquadController, SquadInput, AutoFire, TracerPool,
   RocketPool, BulletPool, AutoPilot, Formation child), `Enemies` (WaveSpawner), `Supply`
   (SupplyLane), `Boss` (zeppelin), `StopLine` (7 dash quads), the HUD canvas (top bar, pills, banner,
   warn, flash, lobby with 3 cards and start button, pause / clear / over panels), an EventSystem with
   `InputSystemUIInputModule`.
8. Sets both URP assets under `Assets/` (MSAA 4×, main light shadows, soft shadows, shadow distance
   70), FXAA + post-processing on the camera, portrait orientation and identifiers in PlayerSettings.
9. Saves `Assets/_Game/Scenes/Main.unity` and logs `[SkySquad] BUILD COMPLETE`.

Button wiring uses `UnityEventTools.AddPersistentListener` / `AddIntPersistentListener` so the
listeners survive in the saved scene.

---

## 7. All tunables (`GameConfig.asset`, current values)

World: `scrollSpeed 9`, `laneHalfWidth 4.2`, `altitudeMax 5.85`, `altitudeSplit 4.4`, `spawnDistance 150` (was
80: fighters popped in half-fogged), `endless true`.

Squad: `startCount 50`, `startCountPerLevel 0`, `steerSpeed 8`, `climbSpeed 7.5`, `dragUnitsPerScreen
20` (the SETTINGS slider, 1–20, overrides it), `maxVisiblePlanes 28`, `formationSpacingX 1.4`, `formationSpacingZ 1.1`, `spiralSpacing 0.8`.

Combat: `lineOfFireRange 48`, `pierceHalfWidth 1.2` (laser only), `bulletSpeed 38`,
`enemyBulletSpeed 28`, `bulletHitRadius 0.55`, `bulletLife 1.45`, `bulletSize 1.6`.

Level pacing (only if `endless` is turned off): `levelDurationBase 55`, `levelDurationPerLevel 8`.

Enemy swarm: `laneHalfWidthAim 0.6`, `swarmRate 4.5`, `swarmRatePerHorde 1.5`, `openingCrowd 35`, `openingCrowdNearZ 62`, `openingCrowdFarZ 148`, `swarmXRange 3.8`,
`swarmAltSpread 0.8`, `swarmDepth 12`, `swarmSpeedSpread 0.4`, `swarmSpawnJitter 0.6`, `swarmLanes 6`,
`weave 0.2`, `swarmBank 7`, `diveZ 7`,
`threatWarnRange 20`, `strikeLift 1.2`, `strikeSide 1.3`, `strikeAccel 0.8`, `strikeShrink 0.5`,
`maxAliveEnemies 300`,
`bossSpawnGap 3`, `holdBehindBoss 4`, `enemyStopZ 12`, `enemyAltAboveSplit 1.4`, `enemyHeightScale 1.35`, `enemyFarScale 1.7`, `enemyFarScaleZ 22`, `miniBossShotPerBoss 1`.

Bosses: `bossHp` (555, 3945, 15960, 27500, 60500, 76500, 125200), `bossHpGrowthAfter 1.6`, `bossFirstAt 20`, `bossEvery 23`, `bossesPerLook 2`, `lastBoss 7` (superseded by the levels, §3.7b: level n has n bosses; nothing streams after the last boss spawns; when he dies `GameManager.Win()` clears the sky, shows VICTORY on the clear panel, and the lobby says GAME COMPLETED after level 10). `levelCount 10`, `levelBaseline 7`, `level1HpScale 0.35`, `level1RateScale 0.55`.

Upgrades: `upgradeCostFire 20`, `upgradeCostDamage 20`, `upgradeCostRevenue 20`,
`upgradeCostGrowth 2.4`, `upgradeLinearFromLevel 8`, `upgradeLinearStep 5000`, `fireRatePerLevel 0.4`, `damagePerLevel 1.0`, `revenuePerLevel 0.1` (a fighter pays 20 coins, x1.10 per revenue level).
**Start levels** (2026-09-17: "I want to start at fire rate level 11, damage 12 and revenue 9"): `startLevelFire 0`, `startLevelDamage 0`, `startLevelRevenue 0` (**all 0 since 2026-09-17 "zero everything and publish"**; 11 / 12 / 9 then 7 / 7 / 5 for testing that day) — `forceStartLevels` **false** (true = TEST MODE, turn off for a player build): every launch `Progress.Load` sets the three levels to exactly these, whatever was bought last time ("when I enter I want it 7 7 5"); false: `Load` and `Reset` only lift every level to at least these (`ApplyStartLevels`). With 0 / 0 / 0 and the flag off this is the plain old behaviour: a new player starts at level 0. Coins are never touched. The editor's saved progress (PlayerPrefs sq_*) was wiped the same day.

Supply lane: `supplyAlt 1.5`, `supplyFrontZ 17`, `supplySpacing 6.5`, `supplyVisible 10`, `crates` (the table in
section 3.5), `crateHpGrowthAfter 1.7`, `boxHpPerLevel 1.15`, `coinsPerHp 0` (was 0.3), `gatesEnabled true`, `gateGap 3.5`, `gateStep 2`, `gateSpeed 34`, `gatePowerBonus 0.25`.

Zeppelin boss (legacy, inert while endless): `bossHpPerDps 2`, `bossHpPerPlane 0.4`,
`bossFightSeconds 10`, `bossFireEvery 2.2`, `bossStartDistance 22`, `bossEndDistance 10.5`.

Definitions: `weapons = [Gatling, Rockets, Laser]`, `enemyFighter = Enemy_Fighter`,
`enemyMiniBoss = Enemy_MiniBoss`.

### Which knob does what (practical guide)

- Attempt too short / player never reaches the boss → lower `swarmRate`, lower `swarmLanes` (fewer lanes: more of them
  funnel into your lane and die), lower the crate table hp (`crates`), or raise `lineOfFireRange`.
- Boss too hard/easy → the `bossHp` table, `Enemy_MiniBoss.fireEvery`, `miniBossShotPerBoss`; too early/late → `bossFirstAt`, `bossEvery`.
- Later attempts progress too slowly → `fireRatePerLevel`, `damagePerLevel`, or lower costs.
- Swarm looks thin → `swarmRate` up (2.5 → 3.2 → 4 → 6 → 4.5 on 2026-09-15; untested against the curve), `approachSpeed` closer to −6 (slower, more on screen at once),
  `swarmDepth` up.
- Strike run feel → `strikeLift` (arc height), `strikeSide` (slalom/corkscrew width), `strikeAccel` (dive speed-up), `strikeShrink`; where it starts → `diveZ`; the figures themselves are the `switch` in `Enemy.Tick`.
- Fighters arrive as a row / abreast → `swarmSpeedSpread` up (more speed variety), `swarmSpawnJitter` up.
- Squad grows too big → crate table hp up or its planes down (`crates`).

---

## 8. Definitions (current values)

| Asset | Values |
|---|---|
| `Weapon_Gatling` | damage 1, fireInterval 0.5, Tracer, color pale gold, plane `PlaneFighter` (**the Zero Fighter pack since 2026-09-18**, §6 step 5; before: prefab root scale **0.8** — all three squad prefabs were 1.05 until 2026-09-17: "the planes are big, shrink them, on the phone they leave the screen"; the formation tightened with them: `formationSpacingX 1.1`, `Z 0.9`, `spiralSpacing 0.65`, were 1.4 / 1.1 / 0.8; chunky white/blue model with a round blue cowl: `MeshFactory.Plane("fighter")`), "one bullet per plane" |
| `Weapon_Rockets` (crate 3) | damage **1.7** (2 for a few hours on 2026-09-17, then "a little weaker"), fireInterval 0.4, **Tracer** (the Gatling's real bullets, damage on impact, 2026-09-17) **drawn as the rocket** (`BulletPool.Fire(..., rocket: true)`: the `Rocket` prefab with its yellow-to-orange fire tail and orange body, scale 1, at `bulletSpeed × 1.8` ≈ 68 u/s; `BulletPool.rocketPrefab`, taken from `RocketPool` when empty — "the rocket-firing look was beautiful, bring it back, only the look"), splash 1.2 (×0.6 dmg on landing, `BulletPool.Land`; 1.2 kills a 1-hp fighter), plane `PlaneAttacker` (**the C-130 pack since 2026-09-18**) — ×2.1 dps per plane. Was `ProjectileKind.Rocket` (damage 1.2, dealt the moment it was fired, the rocket only a visual) until 2026-09-17: "the enemy planes are destroyed before the shot reaches them — take the first plane, recolour it, and make its damage stronger" |
| `Weapon_Laser` ("CANNON", crate 6) | damage **2.5** (1 until 2026-09-17: "the third plane's damage is weak too, make it stronger"; 3 for a few hours, then "a little weaker"), fireInterval 0.3 (0.2 until 2026-09-16: "a little slower"), Tracer bullets (same range as the Gatling), no pierce, plane `PlaneJet` (**the Space Shuttle pack since 2026-09-18**) — ×4.2 dps per plane. Was a piercing Beam until 2026-09-16 ("no laser, bullets") |
| `Enemy_Fighter` | hp 1 (2 tried and dropped 2026-09-16), halfWidth 1.0, approachSpeed 2 (−4 until 2026-09-16: net 11 u/s, was 5), fireEvery 3 (unused), shotDamage 1 (= ram damage), coins 20 (10 earlier on 2026-09-16), scale 0.72 (wingspan = a squad plane; the model is stretched ×1.35 vertically by `enemyHeightScale` and boosted up to ×1.7 while far by `enemyFarScale`/`enemyFarScaleZ` 22, see `Enemy.ApplyModelScale`), prefab `EnemyFighter`, fat-bodied crimson with cream nose ring, wing bands and fin tip, dark cowl (`MeshFactory.EnemyPlane`, 4 submeshes, designed to read head-on) |
| `Enemy_MiniBoss` | hp 10 (overridden per boss by the spawner), halfWidth 3.4, approachSpeed −1, fireEvery 4, shotDamage 1 (+1 per boss), coins 60, scale 3.2, miniBoss true, prefab `EnemyMiniBoss`, orange |

---

## 9. Daily workflow

### 9.1 With the Unity editor open (the normal case)

The editor holds the project, so batch-mode Unity cannot open it a second time. Use the menu items
(manually or through the *MCP for Unity* server, which is how the AI sessions did it).

1. Edit C# files.
2. Let Unity compile (focus the editor, or MCP `refresh_unity` with `compile: request`). Check the
   console for errors (`read_console` with `types: error`).
   *Verify the compile really happened*: `Library/ScriptAssemblies/Assembly-CSharp.dll` (runtime)
   and `Assembly-CSharp-Editor.dll` must be newer than your edited files.
3. **Sky Squad → 2. Build Everything** (regenerates data assets + scene). Verify on disk: grep the
   value you changed in `Assets/_Game/Generated/Data/GameConfig.asset`, check the scene file's
   timestamp.
4. **Sky Squad → Build Windows (test player)**. Verify `Builds/Windows/SkySquad_Data/level0` has a
   fresh timestamp (the `.exe` itself is often not rewritten by an incremental build — check the data
   files, not the exe).
5. Bot test (section 10).

**Play mode must be OFF during steps 3–4.** `Build Everything` fails with
`InvalidOperationException: This cannot be used during play mode` (from `NewScene`), and the console
fills with harmless "Setting the duration while system is still playing" particle warnings. Data
assets may still regenerate while the scene does not, which leaves them inconsistent until you rerun
the builder. MCP `manage_editor stop` exits play mode.

**MCP quirks seen**: the player build makes the editor unresponsive, so the MCP call often returns
`TimeoutError` or "plugin session disconnected" — the build still runs; wait for the data files. The
console retains old errors until cleared (`read_console clear`).

### 9.2 Without the editor (batch mode)

`Tools/build_and_test.sh <run> [seconds] [level] [skip_scene]` runs
`Unity.exe -batchmode -executeMethod SkySquad.EditorTools.SceneBuilder.BuildAll` then
`...BuildScript.BuildWindows`, greps the logs in `Builds/Logs/` for compiler errors / `BUILD
COMPLETE` / `Build Succeeded`, then runs the bot. Only works when the editor is closed.

### 9.3 Git

`Builds/`, `Library/`, `Temp/`, `Logs/`, `obj/` are ignored. The generated assets **are committed**
(scene, data, prefabs, materials, meshes, textures, font) so a clone opens and plays without running
the builder. LFS is configured (an `URP.png` pointer once broke a fast-forward; `git lfs pull` fixed
it).

### 9.4 Tool gotchas (for AI sessions)

- The Bash tool fails on commands longer than ~8 KB with a bogus ``unexpected EOF while looking for
  matching `'` `` — write big edits as a Python script file first and run it, or use the Write tool.
- `git reset --hard`, `rm -f`, `mv` were blocked by the permission classifier in auto mode; the user
  ran those by hand.
- A single Bash call is capped at 600 s; a 200 s bot run fits, a 540 s one does not (detach it with
  `nohup … &` and poll, or split).
- The shell's working directory sometimes resets to the stale `Dev\SkySquad` folder: use absolute
  paths or `cd /c/Users/test2/first-game &&`.

---

### 9.5 Web build (GitHub Pages)

**The game plays in the browser at https://plane-runner-game.github.io/first-game/** (since 2026-09-17: "run it as web on GitHub"). Source: the `gh-pages` branch (root, `.nojekyll`), which holds a copy of `Builds/WebGL` (gitignored on `main`) - it is not a build of `main` on every push; re-publish by hand:
1. `Sky Squad/Build WebGL (browser)` in the open editor (`BuildScript.BuildWebGL`: compression **disabled**, so the plain `.wasm`/`.data` work on Pages with no server config; ~15 min, ~50 MB; the MCP call times out but the build goes on - watch `Builds/WebGL/Build/WebGL.data`). Building switches the active target (was iOS) and dirties a dozen materials + `Mobile_RPAsset` in git: leave those uncommitted.
2. Orphan `gh-pages` in a scratch worktree, copy `Builds/WebGL/.` + `.nojekyll`, force-push.
3. Patch the published `index.html`: desktop canvas/container **450 x 800** (portrait) instead of the template's 960 x 600 (mobile already fills the screen). Pages builds in ~1 min (`gh api repos/plane-runner-game/first-game/pages --jq .status` = built).

## 10. The bot (`AutoPilot.cs`) and the test scripts

### 10.1 Running

```bash
RESET=1 SKIP_UNITY=1 bash Tools/build_and_test.sh run30 200
```

- `SKIP_UNITY=1`: skip both batch-mode Unity steps (editor is open; you built via the menus).
- `RESET=1`: pass `-reset` to the player → wipes PlayerPrefs progress (fresh bank, attempt 1).
  Omit it to continue from the saved progress (attempts 4+).
- `SHOT_EVERY=<s>`: screenshot interval (default 3 s).
- Third arg `level` is passed as `-level n` (starts a level directly; not useful in the meta loop).
- The player runs windowed 540×960 with `-autoplay -shots <dir> -seconds N -logFile <dir>/player.log`
  and quits itself after N seconds. Afterwards `python Tools/summarize_run.py Builds/Shots/run30`
  prints state changes, every-5-s rows, and the exception count from `player.log`.
- The player has crashed natively once right after a fresh build (exit 139); rerunning worked.

### 10.2 What the bot does

- In the lobby: after 0.8 s buys the **cheapest affordable upgrade repeatedly**, logs
  `lobby: attempt n levels a/b/c bank x`, then starts.
- In play (`Steer`): finds the nearest kamikaze still coming (not one loitering behind a boss) and
  whether a boss is parked. Decides to dive for the crate when it is quick to break
  (`crateHp / dps ≤ 2.5 s` if a boss is parked, `≤ 4.5 s` if a fighter is within 20 units, `≤ 8 s`
  otherwise) **or** the squad is down to 1 plane. Otherwise it climbs to `altitudeMax` and slides
  under the nearest kamikaze (it moves into its lane), or lines up on the boss when nothing
  is within 26 units. It drives `SquadController.AutoAxis` like a keyboard.
- A "crates low, climb only when a fighter is within 28 u or a boss is on the line" policy plus a
  `-quitonwin` flag were tried on 2026-09-16 and reverted (the user wanted nothing changed): 15 attempts,
  ~21 min, stuck on boss 4 (27,500 hp) with upgrades 11/11/10 (fighters 20 coins, +5000/level from 8).
- On level clear / game over it "taps" after 1.3 s, which returns to the lobby.
- Every 0.5 s it appends a JSON line to `status.jsonl`, every `shotEvery` seconds a PNG.

### 10.3 `status.jsonl` schema

```json
{"t":12.5,"state":"Playing","level":1,"levelTime":11.5,"count":5,"coins":31,"kills":27,
 "enemies":42,"parked":0,"wave":56,"attempt":1,"horde":1,"front":"Box:15","weapon":"gatling",
 "boss":-1,"fps":58,"x":-1.2,"alt":5.6}
```

`count` planes, `coins` bank, `kills` shot-down, `enemies` alive, `parked` bosses parked + fighters
held, `wave` planes spawned this attempt, `boss` HP of the announced boss or −1, `front` the front
crate's kind:hp. Non-JSON lines are `note:` lines (autopilot on/off, lobby purchases).

### 10.4 Reading a run

Use the state-change list: one `GameOver` line per attempt shows the horde reached, kills, bank, and
the boss HP left. "horde 2" at death means the boss of horde 1 was up (the stream counter is one
ahead). For a per-2-s timeline, load `status.jsonl` in Python and print `count/kills/front/alt`.

Run names used so far: `run18`–`run27` (`run18`–`run20` lane-stream era, `run21`–`run23` wall era,
`run24`–`run27` kamikaze era). Their folders are in `Builds/Shots/` locally (not in git).

---

## 11. Visual reference

The reference screenshots the user provided show a bridge with a dense red enemy crowd ahead and
gates/loot on the side; a blue or yellow player crowd; a boss health bar at the top; coins and upgrade
cards between runs. Our version keeps: dense enemies ahead (as a scattered swarm), loot as a crate
column, +N feedback on every kill, a boss bar, the same three-upgrade loop.

Frames from the last runs (`Builds/Shots/run26/shot_007.png`, `shot_016.png`, `shot_050.png`) show the
swarm flying in, boss 1 parked on the stop line with horde 2 loitering behind him, and a 7-plane squad
breaking a crate.

---

## 12. Design history — what was tried and rejected (do not reintroduce)

The mechanic went through five versions in one day. Each was replaced on explicit user instruction.

1. **Horizontal split (left enemies / right loot)** → rejected: "make the enemies come from above and
   the lower altitude will have the additions". Now vertical bands.
2. **Horde clusters with labels and warnings; start with several planes** → rejected: start with 1
   plane, no hordes-as-groups, no warnings, enemies never leave the high band.
3. **Enemies park at a front line and shoot** (one shot on arrival, then every 3 s, front row only,
   each hit −1 plane) with **V-wing flights** → rejected: "instead of sending them in batches… make
   them come infinitely like right after the other, no gaps".
4. **Continuous 5-lane stream** with blocking/queuing, band-wide aim → aim narrowed to
   **lane-limited** ("I have to be in the same lane of that enemy"), enemies made smaller ("their
   plane asset is way too big").
5. **Solid 7-lane wall** (rows nose to tail, brick pattern, crowd fires one shot per 4.5 s from the
   front row nearest you, charging telegraph) → rejected: "instead of the planes stopping and
   shooting, they come towards you to explode… only the boss stops to shoot… don't send the planes
   structured, they should be scattered, random, and slowly follow you."
6. **Current: scattered kamikaze swarm, boss parks and shoots.**

Other explicit requests that shaped the code and must be kept:

- Bullets must fly straight once fired and never move with the player (fixed: pool un-parented,
  fixed direction).
- The player cannot fly above the enemies' altitude (`altitudeMax` = their altitude).
- An indicator of where/when enemies stop and shoot (the red stop line; now boss-only since only he
  stops).
- "Enemy count is too small" → 100/200/300 per horde, all visible flying in.
- Keep test durations around 200 s.
- A simple coin animation on every kill (`CoinBurst`).
- "The game looks pixelly and dry" → the visual stack (AA, shadows, post FX, outlines, animations).
- The 15-bullet crate giving +2 planes; one bullet kills one fighter; our fire rate slower (0.5 s).
- The same deterministic round every attempt; upgrades are the only progression.

Balance lessons: a parked wall that fires per plane is unwinnable with 1-plane starts; bullets with a
95-unit range kill the swarm at the horizon so nothing is ever seen; a free weapon crate (×2.5 damage)
flattens the curve; the crate ladder growth factor is the strongest single lever on run length.

---

## 13. Known issues, dead code, caveats

- **Stale exe**: rebuild the player before testing (boss 1 = 280 in the scene, 300 in the exe).
- **Legacy/unused code compiled in**: `BossController` (zeppelin), `RocketPool`, `TracerPool`,
  weapons Rockets/Laser and their `AutoFire` branches, `SquadController.TakeShot/Shield`,
  `Enemy_Fighter.fireEvery`, `LevelClear` state, `levelDuration*`, `startCountPerLevel`,
  `boxHpPerLevel` (only matters if real levels come back). Safe to delete or keep for phase 2.
- **Stray bullets**: wingmen's bullets converge on the target and continue past it, so a bullet can
  hit a fighter in a neighbouring column *behind* a dead target. Accepted as "spray"; tighten
  `bulletHitRadius` or stop bullets at their target's z if it bothers anyone.
- **Kamikazes that miss fly through the camera** and look huge for a frame as they pass. Consider
  fading them past z < −1.
- **Camera**: `followAlt 0.7` was raised for the wall era so the block showed depth; with a swarm a
  lower value (0.45) may frame better. Re-check by eye.
- **Performance**: 150 enemies max, each with body + outline + propeller + flash quad, plus MSAA 4×,
  soft shadows and post FX. 56–58 fps in the 540×960 test window on the dev PC; **nothing profiled on a
  phone**. Outlines and shadow distance are the first things to cut on mobile.
- **Audio is placeholder.**
- **"−1" float text** occasionally renders near the top-left of the screen (a world-space text
  spawned at the squad when the camera is low). Cosmetic; not investigated.
- **Android**: the APK menu exists; identifiers are set; never built or tested on a device.
- **Emulator study of the reference game**: possible through ADB (`adb shell input tap/swipe`,
  `adb exec-out screencap`, `adb shell screenrecord`) with Android Studio's emulator, LDPlayer, MuMu
  or BlueStacks with ADB enabled. Not started.
- Unity's `ProjectSettings/ProjectSettings.asset` and `QualitySettings.asset` are modified by the
  builder (`ApplyPlayerSettings`); expect them to show as changed after every rebuild.

---

## 14. Suggested next steps

1. Rebuild the player and **play it by hand** on the PC build (drag = move). The bot is a proxy; the
   curve should be re-tuned to a human's accuracy (a human dodges better but aims worse).
2. Decide the swarm's feel with three knobs: `swarmRate`, `swarmLanes`, `swarmSpeedSpread`.
3. Trim the legacy code if phase 2 will not bring real levels or weapon pickups back; otherwise
   re-enable weapon crates with a much smaller multiplier.
4. Mobile: build the APK, profile, drop MSAA to 2× / outlines off if needed, test touch drag feel
   (`dragUnitsPerScreen`).
5. Lobby polish: card art, purchase feedback, a "best horde" celebration, a settings screen (sound,
   vibration), a proper title.
6. Sound design.
7. Optionally study the reference game through an emulator with ADB to match spawn density, boss
   pacing and upgrade pricing exactly.

---

## 15. Quick reference

```bash
# fresh-progress bot run, 200 s, with the editor open (build via menus first)
RESET=1 SKIP_UNITY=1 bash Tools/build_and_test.sh run30 200
```

```bash
# continue from saved progress (attempts 4+)
SKIP_UNITY=1 bash Tools/build_and_test.sh run31 200
```

```bash
# summarize an existing run
python Tools/summarize_run.py Builds/Shots/run30
```

```bash
# did the rebuild take? (value + timestamps)
grep -E "bossFirstAt|swarmRate:" Assets/_Game/Generated/Data/GameConfig.asset; ls -la Assets/_Game/Scenes/Main.unity Builds/Windows/SkySquad_Data/level0
```

Menus: **Sky Squad → 1. Prepare (import TMP resources)** (first time only) · **2. Build Everything** ·
**Build Windows (test player)** · **Build Android (APK)**.

Player args: `-autoplay -shots <dir> -seconds N [-level n] [-shotevery s] [-reset] [-staylow]`.

**Unity Remote 5 (iPhone over USB, Windows editor)** — set up 2026-09-17: Apple's USB service (iTunes / Apple Devices)
must run; Edit → Project Settings → Editor → Unity Remote → Device = Any iOS Device; the editor must be on the **iOS**
platform (the manual says so; switch back to Windows for test builds); the app must be open on the phone *before*
Play. Touches only work thanks to `Editor/UnityRemoteInputShim.cs` (the same fix was written twice on 2026-09-17 on two machines, as `UnityRemoteInputFix.cs` here and `UnityRemoteInputShim.cs` on the iPhone machine; the Shim was kept when the two were merged: it also sets the sharp JPEG stream and removes its handler before adding it, so it never registers twice): Input System 1.20 looks for
`UnityEditor.Remote.GenericRemote` in CoreModule, but in 6000.6 it lives in `UnityEditor.GenericRemoteModule`, so
the package never registered its handler (picture streamed, every tap dropped). The console says
`Unity Remote connected to input!` when it works.

PlayerPrefs keys: `sq_coins`, `sq_attempts`, `sq_best`, `sq_fr`, `sq_dmg`, `sq_rev`.
