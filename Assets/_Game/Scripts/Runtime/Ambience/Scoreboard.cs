// Scoreboard.cs
// The stadium's big screen (2026-10-08): the score of the match - planes your squad shot down against the planes it lost - and the clock,
// live through the attempt.
using TMPro;
using UnityEngine;

namespace SkySquad
{
    public class Scoreboard : MonoBehaviour
    {
        public TextMeshPro score, clock;
        int lastKills = -1, lastLost = -1, lastSec = -1, peak;

        void Update()
        {
            var gm = GameManager.I; if (gm == null) return;
            int count = gm.squad != null ? gm.squad.Count : 0;
            if (gm.State == GameState.Title) peak = count; else peak = Mathf.Max(peak, count);
            int kills = gm.State == GameState.Title ? 0 : gm.UnitsKilled, lost = Mathf.Max(0, peak - count);
            if (score != null && (kills != lastKills || lost != lastLost)) { lastKills = kills; lastLost = lost; score.text = kills + " : " + lost; }
            int sec = Mathf.FloorToInt(gm.State == GameState.Title ? 0f : gm.LevelTime);
            if (clock != null && sec != lastSec) { lastSec = sec; clock.text = (sec / 60).ToString("00") + ":" + (sec % 60).ToString("00"); }
        }
    }
}
