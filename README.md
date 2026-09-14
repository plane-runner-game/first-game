# Sky Squad (Unity 6, URP, portrait mobile)

Plane-squadron horde shooter split into two altitude bands (the bridge-runner "enemies on one
side, loot on the other" layout, turned vertical):
- **High band** - a constant stream of enemy planes in V-wing flights on a steady beat, every 4th a
  mini boss with escorts followed by a short pause. They never leave the high band; when one reaches the
  front line (or a plane ahead of it) it parks there and shoots down at you until you climb up and clear
  it - only the front row fires. The crowd only grows while you farm.
- **Low band** - the supply lane: a conveyor queue of crates with HP numbers a fixed distance ahead.
  A crate is +2 planes and its hp in coins, each one tougher than the last (15, 22, 32 ...), with a weapon
  crate now and then. Only the front crate takes fire; break it and the queue slides forward.
- Your guns aim within **your band**: up high they find the nearest enemy plane (no lining up), down low
  the front crate. Damage is discrete - one bullet per plane per volley - so a "15" crate takes 15 bullets.
  Every level starts with 1 plane (V-wing up to 5, a phyllotaxis spiral beyond) and ends with the boss
  zeppelin. The cloud puffs along the lane edges mark the split altitude.

Prototype design lives in the HTML version (OneDrive\Desktop\SkySquad\index.html); this is the real build.

## Layout
- `Assets/_Game/Scripts/Runtime` - gameplay (GameManager, SquadController, Horde*, SupplyLane/Breakable, AutoFire, Boss, FX, HUD, Audio)
- `Assets/_Game/Scripts/Editor` - `SceneBuilder` (builds materials/meshes/prefabs/scene from code), `BuildScript`
- `Assets/_Game/Generated` - everything SceneBuilder produces (safe to delete and rebuild)
- `Assets/_Game/Fonts` - Lilita One (OFL)

## Rebuild the scene from scratch
Menu: **Sky Squad > 1. Prepare**, then **Sky Squad > 2. Build Everything** (or the batch commands in SceneBuilder.cs).

## Test player with the bot
Build `Sky Squad > Build Windows`, then run:
`Builds\Windows\SkySquad.exe -autoplay -shots C:\path	o\shots -seconds 60`
It plays itself, drops a screenshot every 3 s and a status.jsonl log.

## Replacing placeholder art
Every model is a prefab under `Assets/_Game/Generated/Prefabs`. Drop a Blender export in,
keep the prefab name and the scripts on the root, and the game picks it up.
