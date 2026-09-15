#!/usr/bin/env bash
# Rebuild the scene + Windows player, then run the bot and summarize.
# Usage: bash Tools/build_and_test.sh <run_name> [seconds] [level] [skip_scene]
#   SKIP_UNITY=1  skip both Unity batch steps. Use this while the editor has the project open
#                 (batchmode can't open it twice): build via the "Sky Squad" menu, then run
#                 this for the bot + summary only.
# Output: Builds/Shots/<run_name>/ (screenshots, status.jsonl, player.log), Builds/Logs/.
set -u
cd "$(dirname "$0")/.." || exit 1
PROJ="$(pwd)"; PROJW="$(cygpath -w "$PROJ")"
NAME="${1:-shots}"; SECONDS_RUN="${2:-75}"; LEVEL="${3:-0}"; SKIP_SCENE="${4:-0}"
UNITY="/c/Program Files/Unity/Hub/Editor/6000.6.0f1/Editor/Unity.exe"
LOGS="$PROJ/Builds/Logs"; LOGSW="$PROJW\\Builds\\Logs"; mkdir -p "$LOGS"

run_unity() {
  local name="$1" method="$2" marker="$3"
  "$UNITY" -batchmode -projectPath "$PROJW" -executeMethod "$method" -quit -logFile "$LOGSW\\unity_$name.log"
  echo "== $name: unity exit=$?"
  grep -n -E "error CS[0-9]+|Scripts have compiler errors|Aborting batchmode|\[SkySquad\]|Exception: |Build Failed" "$LOGS/unity_$name.log" | grep -v Licensing | head -20
  if grep -q -E "error CS[0-9]+|Scripts have compiler errors|Aborting batchmode" "$LOGS/unity_$name.log"; then echo "== $name FAILED"; return 1; fi
  if ! grep -q "$marker" "$LOGS/unity_$name.log"; then echo "== $name: marker missing ($marker)"; return 1; fi
  echo "== $name OK"
}

if [ "${SKIP_UNITY:-0}" != "1" ]; then
  if [ "$SKIP_SCENE" != "1" ]; then
    run_unity build SkySquad.EditorTools.SceneBuilder.BuildAll "BUILD COMPLETE" || exit 1
  fi
  run_unity player SkySquad.EditorTools.BuildScript.BuildWindows "Build Succeeded" || exit 1
fi

S="$PROJ/Builds/Shots/$NAME"; SHOTS="$PROJW\\Builds\\Shots\\$NAME"
rm -rf "$S"; mkdir -p "$S"
EXTRA=""; if [ "$LEVEL" != "0" ]; then EXTRA="-level $LEVEL"; fi; if [ "${SHOT_EVERY:-}" != "" ]; then EXTRA="$EXTRA -shotevery $SHOT_EVERY"; fi; if [ "${RESET:-0}" = "1" ]; then EXTRA="$EXTRA -reset"; fi
./Builds/Windows/SkySquad.exe -autoplay -shots "$SHOTS" -seconds "$SECONDS_RUN" $EXTRA -screen-width 540 -screen-height 960 -screen-fullscreen 0 -logFile "$SHOTS\\player.log" >/dev/null 2>&1
echo "player exit=$?  shots: $(ls "$S" | grep -c png)"
python Tools/summarize_run.py "$S"
