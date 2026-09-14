#!/usr/bin/env bash
# Rebuild the scene + Windows player, then run the bot and summarize.
# Usage: bash Tools/build_and_test.sh <shots_dir_name> [seconds] [level] [skip_scene]
set -u
cd "$(dirname "$0")/.." || exit 1
NAME="${1:-shots}"; SECONDS_RUN="${2:-75}"; LEVEL="${3:-0}"; SKIP_SCENE="${4:-0}"
UNITY="/c/Program Files/Unity/Hub/Editor/6000.6.0f1/Editor/Unity.exe"
SCRW='C:\Users\test2\AppData\Local\Temp\claude\C--Users-test2\e6e9f637-00b3-4ed4-a4b5-ecb8872a8d4d\scratchpad'
SCR="/c/Users/test2/AppData/Local/Temp/claude/C--Users-test2/e6e9f637-00b3-4ed4-a4b5-ecb8872a8d4d/scratchpad"

run_unity() {
  local name="$1" method="$2" marker="$3"
  "$UNITY" -batchmode -projectPath 'C:\Users\test2\Dev\SkySquad' -executeMethod "$method" -quit -logFile "$SCRW\\unity_$name.log"
  echo "== $name: unity exit=$?"
  grep -n -E "error CS[0-9]+|Scripts have compiler errors|Aborting batchmode|\[SkySquad\]|Exception: |Build Failed" "$SCR/unity_$name.log" | grep -v Licensing | head -20
  if grep -q -E "error CS[0-9]+|Scripts have compiler errors|Aborting batchmode" "$SCR/unity_$name.log"; then echo "== $name FAILED"; return 1; fi
  if ! grep -q "$marker" "$SCR/unity_$name.log"; then echo "== $name: marker missing ($marker)"; return 1; fi
  echo "== $name OK"
}

if [ "$SKIP_SCENE" != "1" ]; then
  run_unity build SkySquad.EditorTools.SceneBuilder.BuildAll "BUILD COMPLETE" || exit 1
fi
run_unity player SkySquad.EditorTools.BuildScript.BuildWindows "Build Succeeded" || exit 1

SHOTS="$SCRW\\$NAME"; S="$SCR/$NAME"; rm -rf "$S"
EXTRA=""; if [ "$LEVEL" != "0" ]; then EXTRA="-level $LEVEL"; fi
./Builds/Windows/SkySquad.exe -autoplay -shots "$SHOTS" -seconds "$SECONDS_RUN" $EXTRA -screen-width 540 -screen-height 960 -screen-fullscreen 0 -logFile "$SHOTS\\player.log" >/dev/null 2>&1
echo "player exit=$?  shots: $(ls "$S" | grep -c png)"
python Tools/summarize_run.py "$S"
