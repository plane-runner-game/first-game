# Sky Squad (Unity 6, URP, portrait mobile)

Plane-squadron horde shooter. Hordes come down the middle and ram you if you don't shoot
them down; growth gates wait on the sides. Prototype design lives in the HTML version
(OneDrive\Desktop\SkySquad\index.html); this is the real build.

## Layout
- `Assets/_Game/Scripts/Runtime` - gameplay (GameManager, SquadController, Horde*, Pickup*, AutoFire, Boss, FX, HUD, Audio)
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
