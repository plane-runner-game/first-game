// Ads.cs
// The one door to rewarded video (2026-10-03). No ad network is connected yet: ShowRewarded answers "watched to the end"
// at once, so the death screen's REVIVE works in the editor and the web build. Connecting a network (LevelPlay, AdMob ...)
// changes only this file: RewardedReady from the SDK's "loaded" state, ShowRewarded opens its rewarded video, sets Showing
// while it plays and calls onDone(true) from the reward callback, onDone(false) when the video is closed early or fails.
using System;
using UnityEngine;

namespace SkySquad
{
    public static class Ads
    {
        /// <summary>A rewarded video is loaded and can be shown now (the death screen hides REVIVE when not).</summary>
        public static bool RewardedReady => true;

        /// <summary>A rewarded video is on screen: the death screen's countdown waits.</summary>
        public static bool Showing { get; private set; }

        /// <summary>Shows a rewarded video for placement ("revive"); onDone(true) once it was watched to the end, (false) if skipped or failed.</summary>
        public static void ShowRewarded(string placement, Action<bool> onDone)
        {
            Showing = true;
            Debug.Log("[Ads] rewarded '" + placement + "': no ad network connected yet, granted");
            Showing = false;
            onDone?.Invoke(true);
        }
    }
}
