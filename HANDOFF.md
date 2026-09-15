# Sky Squad — Handoff

_Last updated: 2026-09-15 (third session: fixed crate table + blue reward squares; second session: lanes, strike runs, reticles, gates), on `main` of https://github.com/plane-runner-game/first-game — see `git log` for the commit._

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
  squad stays at z = 0). One unit ≈ 20 px of the original HTML prototype.
- The squad has an **X** (−4.2 … +4.2, `laneHalfWidth`) and an **altitude** (0 … 5.85,
  `altitudeMax`). World y = 1 + altitude.
- **Two bands** split at altitude 4.4 (`altitudeSplit`): below = LOW band (crates), at or above =
  HIGH band (enemies). `SquadController.IsHigh` = `Alt >= altitudeSplit`.
- **The ceiling equals the swarm's altitude** (5.85 ≈ 4.4 + 1.4). You can fly *at* the enemies' height
  but never over them. This was an explicit request ("you shouldn't allow me to go higher than the
  altitude of the coming enemies").
- Controls (`SquadInput.cs`): touch or mouse drag moves the squad (`DragDelta` as a fraction of screen
  height × `dragUnitsPerScreen` 18, so one full-screen drag = 18 units); arrows/WASD steer at
  `steerSpeed` 8 and climb at `climbSpeed` 7.5 units/s; a tap (press+release without moving) is `Tapped`.
- Camera (`CameraFollow.cs`): rig base position (0, 6.2, −9.5), looks at (0, 3.6, 9), FOV 52. The rig
  slides 0.55 × squad X sideways and 0.7 × squad altitude upward (`followAlt`), smoothed. Screen shake
  offset comes from `FXManager.ShakeOffset`.
- Visual stack: FXAA + MSAA 4×, soft shadows (distance 70), post-processing volume `PostFX.asset`
  (Bloom, Vignette, Color Adjustments), black inverted-hull toon outlines on planes and crates,
  spinning propellers, white hit-flash via MaterialPropertyBlock.

### 3.2 The squad

- Every attempt starts with **1 plane** (`startCount`).
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
- Rockets and Laser exist as `WeaponDef`s (splash / pierce code paths in `AutoFire.FireOne`) but are
  reachable only through a `Plane` reward in the crate table (none in the default table). Only the Gatling is ever used.

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

### 3.5 The LOW band: crates and their reward squares (`SupplyLane.cs`, `Breakable.cs`, `UpgradeGate.cs`)

Rewritten 2026-09-15 (third session) to the user's spec: "specific numbers for each crate and what each
crate gives; the first crate is 15 and gives two planes, but the planes don't come right away - break
it and two blue squares behind it come at you; you must go down and pass through them."

- A queue of `supplyVisible` = 10 crates hangs under parachutes at altitude 1.5 (`supplyAlt`), the front
  one 17 units ahead (`supplyFrontZ`), **8 apart** (`supplySpacing`, room for the squares). Break the
  front one and the rest slide forward; a new one joins at the back, out of sight.
- **The crate table** (`GameConfig.crates`, an array of `CrateSpec {hp, reward, amount}`, set in the
  builder lambda, editable in the Inspector). Crate n has exactly these numbers every attempt:

  | # | HP (bullets) | reward |
  |---|---|---|
  | 1 | 15 | 2 planes (two blue squares) |
  | 2 | 30 | 2 planes |
  | 3 | 60 | 3 planes |
  | 4 | 100 | shield, 2 hits (one cyan square) |
  | 5 | 160 | 3 planes |
  | 6 | 260 | 5 planes |
  | 7 | 420 | shield, 3 hits |
  | 8 | 650 | 5 planes |
  | 9+ | ×1.6 each (`crateHpGrowth`) | the last entry's reward again |

  Reward kinds (`CrateReward`): `Planes` (one square per plane), `Shield` (one square, soaks *amount*
  hits), `Plane` (one square, every plane becomes the next weapon; past the last weapon +25 % damage
  "MK n", `gatePowerBonus`), `Coins` (bonus coins on break, no squares). `GameConfig.CrateAt(i)` does
  the table lookup and the extrapolation.
- **The squares** (`UpgradeGate`, prefab `UpgradeGate`: a 2 × 2 frame `GateFrame(1.0, 2.0)` with a
  translucent fill, blue for planes, cyan for a shield, the weapon's colour for a new plane; labels
  "+1 / PLANE", "SHIELD / n HITS", weapon name / "NEW PLANES"). They **ride behind their crate in rows
  of two** (`gateGap` 3.5 behind it, rows `squareRowSpacing` 2.2 apart, the two squares of a row at
  x = ±`squareSideStep` 1.05 so they touch and never overlap); `Breakable.SetSlot` → `SetHold` keeps
  them with the crate as the queue moves. The crate's hint under the box names the reward ("+2 PLANES",
  "SHIELD 2", …) and its canopy is tinted the reward's colour.
- **Break** (`Breakable.Break`): the crate pays `round(maxHp × coinsPerHp 0.3)` coins at once (coin
  burst), then **launches all its squares** (`UpgradeGate.Launch`): they fly at the squad at `gateSpeed`
  22 u/s, about a second to arrive, rows 0.1 s apart.
- **Pass** (`UpgradeGate.Pass`, when a square's z reaches 0.4 with the squad **in the low band** and
  `|squad.X − square.X| < 1.0 + 0.9`): the reward via `UpgradeGate.Grant` (+1 plane with its own "+1"
  pop, joiner animation; shield/new plane also banner + flash). At x = 0 you take both squares of a row;
  lined up on one edge you take that one only. A square that reaches z = −6 untaken is gone: **stay high
  and the crate's planes are lost** - that is the skill element.
- `gatesEnabled = false` in the builder lambda + Build Everything makes the crate pay its reward directly
  on break (no squares); `Coins` crates always pay directly.
- The bot (`AutoPilot.Steer`) stays in the low band while `SupplyLane.Incoming` > 0 (launched squares
  still on their way).
- Weapon crates, the weighted gate roll (`gateWeight*`), `boxHpBase/Growth/PerLevel`, `boxPlanes`,
  `gatePlanesSmall/Big`, `gateShieldMin/Max`, `weaponAt/Every` and `BreakableKind`/`GateKind` are
  **gone**; the table replaces all of them.

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
  `swarmRatePerHorde`). Each fighter spawns in a random lane, altitude 5.8 ±0.8
  (`swarmAltSpread`), depth `spawnDistance` 150 + random 0–12 (`swarmDepth`). The spawner refuses to
  spawn while `maxAliveEnemies` (300) are alive. All randomness comes from `System.Random(7)`, reset
  every attempt, so **the round is identical every attempt**.
  **Why 150**: at 80 the fighters spawned inside the fog gradient (fog started 70 from the camera) and
  popped in half-transparent; now the fog starts at 175 (ends 340, past the water edge), so nothing in
  play is ever fogged and a spawn happens where the eye cannot resolve it. The round therefore opens on
  a long column of fighters stretching to the horizon (requested: "a big swarm coming from the back
  from the moment I start, not planes spawning one by one, transparent"). Consequence: a fighter
  takes ~29 s from spawn to the strike line; the opening column fills that gap.
- **Flight**: base net approach speed = `scrollSpeed 9 + approachSpeed (−4)` = **5 units/s toward you**
  ("slowly"). **Every fighter has its own pace**: `Enemy.SpeedMult` = 1 ± `swarmSpeedSpread` 0.4
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
- Fighter definition: `Enemy_Fighter` — hp 1, scale **1.25**, coins 1, `approachSpeed −4`,
  `shotDamage 1` (used as ram damage). `fireEvery` is unused (fighters never fire).
- Guns only engage inside `lineOfFireRange` 48 units (34 until 2026-09-15: "let my bullets reach farther"), so the swarm is visible flying in for several
  seconds before it starts dying. Do not raise this back to 95: the swarm then dies at the horizon and
  the game looks empty.

### 3.7 Hordes and bosses

- **Horde k** = `hordePlanesBase 120 + (k−1) × hordePlanesPerHorde 100` fighters: 120, 220, 320… (base scaled with the stream rate so boss 1 comes ~27 s in)
- When the k-th horde has fully spawned, **boss k** spawns at `spawnDistance + 2` (`Enemy_MiniBoss`,
  scale 3.2, `Wide`, `halfWidth` 3.4). HP = `miniBossHpBase 280 × miniBossHpGrowth 2.5^(k−1)`:
  280, 700, 1750… His shot takes `1 + (k−1) × miniBossShotPerBoss 2` planes: 1, 3, 5…
- The boss flies in at net 8 u/s (`approachSpeed −1`), brakes over the last 3 units and **parks at
  `enemyStopZ` 12** (the front line). The moment he parks he fires, then every `fireEvery` 1.6 s. His
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
- Upgrades: cost = `base × upgradeCostGrowth 1.6^level` with bases **10 / 10 / 10** (were 50 / 60 / 40; "make it ten")
  Effects: `FireRateMult = 1 + 0.15·lvl`, `DamageMult = 1 + 0.35·lvl`,
  `RevenueMult = 1 + 0.2·lvl`. Damage matters against crates and bosses only (fighters have 1 HP).
- `StartGame()`: `Attempts++`, save, `StartLevel(1)`: resets spawner, supply lane, zeppelin boss,
  squad, FX, shows the "ATTEMPT n" banner. `Lose(reason)`: saves `BestHorde`, state `GameOver`, the
  death panel shows the reason, attempt, horde, kills and "+RunCoins coins for the next attempt". A tap
  returns to the lobby.
- States: `Title` (lobby) → `Playing` ⇄ `Paused` (pause button, tap resumes) → `GameOver` → `Title`.
  `LevelClear` exists but is unreachable while `endless = true`.

### 3.9 HUD (`HUD.cs`)

Top bar: "ATT n", "$ bank" with the "+N" pop, a progress bar that is **blue "HORDE k  gone/target"**
normally and **red "BOSS k  hp"** while a boss is announced. Bottom: PLANES pill, weapon name and
description, KILLS, a fading hint ("DRAG TO FLY · DIVE for crates · CLIMB to fight"). Center: banner
text (attempt / boss), red warning vignette, screen flash. Overlays: lobby, pause, level clear
(unused), squadron lost. Sound toggle glyph exists (`ToggleSound`).

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
| `UpgradeGate.cs` | The reward gate behind a crate: +2/+5 planes, shield or next plane by weighted roll (provisional, `gatesEnabled`) | `Init(kind, planes)`, `SetHold(z)`, `Launch()`, `Kind`, `Planes`, `Launched`, `Done`, `X/Z/Alt`, `HalfWidth` |
| `Breakable.cs` | One crate: HP, label, hint, hit flash, break → coins + launches its gate | `Shoot(dmg)`, `Gate`, `X/Z/Alt`, `HalfWidth`, `AimPoint`, `Dead`, `Kind`, `Value` |
| `StopLine.cs` | The boss's red dashed parking line (boss-only, shown while he is announced) | `dashes[]`, `color` |
| `DiveLine.cs` | The green dashed line at `diveZ`, one dash per lane, green→red as a fighter in that lane closes in | `dashes[]`, `farColor`, `nearColor` |
| `FXManager.cs` | All juice (section 3.10) | `Explosion`, `Sparks`, `Ring`, `FloatText`, `CoinBurst`, `Joiners`, `Fallers`, `UnitFall`, `Shake`, `Flash`, `ClearAll` |
| `HUD.cs` | Screen UI, lobby, overlays | `Banner`, `Warn`, `Flash`, `ShowHint`, `CoinPop`, `RefreshLobby`, `OnBuy(i)`, `OnStartButton`, `OnPauseButton`, `ToggleSound` |
| `CameraFollow.cs` | Soft follow + shake | `basePosition`, `followX`, `followAlt`, `smoothing` |
| `WorldScroller.cs` | Scrolls water texture, buoys, clouds, cloud rails | `water`, `buoys`, `clouds`, `waterTilesPerUnit` |
| `PlaneVisual.cs` | One squad plane model: slot bob, bank, leader material, muzzle flash | `SetBase`, `SetLeader`, `Flash(color)`, `index` |
| `AudioManager.cs` | Procedural SFX, mute | `Play(Sfx)`, `Muted` |
| `AutoPilot.cs` | The test bot (section 10) | command-line args, `autoplayInEditor` |
| `BossController.cs` | **Legacy** zeppelin end-of-level boss with HP/timer bars. Never activates while `endless = true` | `Active`, `Fighting`, `Dead`, `TakeDamage` |
| `RocketPool.cs`, `TracerPool.cs` | **Legacy** visuals for rockets / laser beams (unused: Gatling only) | `Fire(...)` |

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
5. Builds prefabs: three squad planes, `EnemyFighter` and `EnemyMiniBoss` (`EnemyPrefab`: body rotated
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

Squad: `startCount 1`, `startCountPerLevel 0`, `steerSpeed 8`, `climbSpeed 7.5`, `dragUnitsPerScreen
18`, `maxVisiblePlanes 28`, `formationSpacingX 1.4`, `formationSpacingZ 1.1`, `spiralSpacing 0.8`.

Combat: `lineOfFireRange 48`, `pierceHalfWidth 1.2` (laser only), `bulletSpeed 38`,
`enemyBulletSpeed 28`, `bulletHitRadius 0.55`, `bulletLife 1.45`, `bulletSize 1.6`.

Level pacing (only if `endless` is turned off): `levelDurationBase 55`, `levelDurationPerLevel 8`.

Enemy swarm: `laneHalfWidthAim 0.6`, `swarmRate 4.5`, `swarmRatePerHorde 1.5`, `openingCrowd 35`, `openingCrowdNearZ 62`, `openingCrowdFarZ 148`, `swarmXRange 3.8`,
`swarmAltSpread 0.8`, `swarmDepth 12`, `swarmSpeedSpread 0.4`, `swarmSpawnJitter 0.6`, `swarmLanes 6`,
`weave 0.2`, `swarmBank 7`, `diveZ 7`,
`threatWarnRange 20`, `strikeLift 1.2`, `strikeSide 1.3`, `strikeAccel 0.8`, `strikeShrink 0.5`,
`maxAliveEnemies 300`,
`bossSpawnGap 3`, `holdBehindBoss 4`, `enemyStopZ 12`, `enemyAltAboveSplit 1.4`, `enemyHeightScale 1.35`, `enemyFarScale 1.7`, `enemyFarScaleZ 22`, `miniBossHpBase
280`, `miniBossHpGrowth 2.5`, `miniBossShotPerBoss 2`.

Hordes: `hordePlanesBase 120`, `hordePlanesPerHorde 100`.

Upgrades: `upgradeCostFire 10`, `upgradeCostDamage 10`, `upgradeCostRevenue 10`,
`upgradeCostGrowth 1.6`, `fireRatePerLevel 0.15`, `damagePerLevel 0.35`, `revenuePerLevel 0.2`.

Supply lane: `supplyAlt 1.5`, `supplyFrontZ 17`, `supplySpacing 8`, `supplyVisible 10`, `coinsPerHp 0.3`,
`crates` (the table in section 3.5), `crateHpGrowth 1.6`, `gatesEnabled true`, `gateGap 3.5`, `squareRowSpacing 2.2`,
`squareSideStep 1.05`, `gateSpeed 22`, `gatePowerBonus 0.25`.

Zeppelin boss (legacy, inert while endless): `bossHpPerDps 2`, `bossHpPerPlane 0.4`,
`bossFightSeconds 10`, `bossFireEvery 2.2`, `bossStartDistance 22`, `bossEndDistance 10.5`.

Definitions: `weapons = [Gatling, Rockets, Laser]`, `enemyFighter = Enemy_Fighter`,
`enemyMiniBoss = Enemy_MiniBoss`.

### Which knob does what (practical guide)

- Attempt too short / player never reaches the boss → lower `swarmRate`, lower `swarmLanes` (fewer lanes: more of them
  funnel into your lane and die), lower the crate table's numbers, or raise `lineOfFireRange`.
- Boss too hard/easy → `miniBossHpBase`, `Enemy_MiniBoss.fireEvery`, `miniBossShotPerBoss`.
- Later attempts progress too slowly → `fireRatePerLevel`, `damagePerLevel`, or lower costs.
- Swarm looks thin → `swarmRate` up (2.5 → 3.2 → 4 → 6 → 4.5 on 2026-09-15; untested against the curve), `approachSpeed` closer to −6 (slower, more on screen at once),
  `swarmDepth` up.
- Strike run feel → `strikeLift` (arc height), `strikeSide` (slalom/corkscrew width), `strikeAccel` (dive speed-up), `strikeShrink`; where it starts → `diveZ`; the figures themselves are the `switch` in `Enemy.Tick`.
- Fighters arrive as a row / abreast → `swarmSpeedSpread` up (more speed variety), `swarmSpawnJitter` up.
- Squad grows too big → raise the crate table's numbers / `crateHpGrowth`, or give fewer planes per crate.

---

## 8. Definitions (current values)

| Asset | Values |
|---|---|
| `Weapon_Gatling` | damage 1, fireInterval 0.5, Tracer, color pale gold, plane `PlaneFighter` (prefab scale 1.05, chunky white/blue model with a round blue cowl: `MeshFactory.Plane("fighter")`), "one bullet per plane" |
| `Weapon_Rockets` (unused) | damage 3, fireInterval 0.7, Rocket, splash 2.5, plane `PlaneAttacker` |
| `Weapon_Laser` (unused) | damage 1, fireInterval 0.2, Beam, pierce, plane `PlaneJet` |
| `Enemy_Fighter` | hp 1, halfWidth 1.0, approachSpeed −4, fireEvery 3 (unused), shotDamage 1 (= ram damage), coins 1, scale 0.72 (wingspan = a squad plane; the model is stretched ×1.35 vertically by `enemyHeightScale` and boosted up to ×1.7 while far by `enemyFarScale`/`enemyFarScaleZ` 22, see `Enemy.ApplyModelScale`), prefab `EnemyFighter`, fat-bodied crimson with cream nose ring, wing bands and fin tip, dark cowl (`MeshFactory.EnemyPlane`, 4 submeshes, designed to read head-on) |
| `Enemy_MiniBoss` | hp 10 (overridden per boss by the spawner), halfWidth 3.4, approachSpeed −1, fireEvery 1.6, shotDamage 1 (+2 per boss), coins 60, scale 3.2, miniBoss true, prefab `EnemyMiniBoss`, orange |

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
  `levelDuration*` (only matter if real levels come back). Safe to delete or keep for phase 2.
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
grep -E "miniBossHpBase|swarmRate:" Assets/_Game/Generated/Data/GameConfig.asset; ls -la Assets/_Game/Scenes/Main.unity Builds/Windows/SkySquad_Data/level0
```

Menus: **Sky Squad → 1. Prepare (import TMP resources)** (first time only) · **2. Build Everything** ·
**Build Windows (test player)** · **Build Android (APK)**.

Player args: `-autoplay -shots <dir> -seconds N [-level n] [-shotevery s] [-reset]`.

PlayerPrefs keys: `sq_coins`, `sq_attempts`, `sq_best`, `sq_fr`, `sq_dmg`, `sq_rev`.
