// Progress.cs
// What survives between attempts: the coin bank, the three upgrade levels (fire rate, damage,
// coin gathering) and the attempt counter. Every attempt is the same round - the only thing that
// changes between them is what you bought here.
using UnityEngine;

namespace SkySquad
{
    public enum Upgrade { FireRate = 0, Damage = 1, Revenue = 2 }

    public static class Progress
    {
        public static int Coins, Attempts, BestHorde;
        public static int Stage = 1, Cleared;   // the level the next attempt plays (1..levelCount) and the highest level cleared (levels, 2026-09-18)
        public static bool Won;   // the last boss has been beaten at least once: the lobby says GAME COMPLETED
        public static readonly int[] Levels = new int[3];

        static GameConfig Cfg => GameManager.I.config;
        public static float FireRateMult => 1f + Levels[0] * Cfg.fireRatePerLevel;
        public static float DamageMult => 1f + Levels[1] * Cfg.damagePerLevel;
        public static float RevenueMult => 1f + Levels[2] * Cfg.revenuePerLevel;

        public static int Cost(Upgrade u)
        {
            float b = u == Upgrade.FireRate ? Cfg.upgradeCostFire : u == Upgrade.Damage ? Cfg.upgradeCostDamage : Cfg.upgradeCostRevenue;
            int lvl = Levels[(int)u];
            int lin = Cfg.upgradeLinearFromLevel;
            if (lin > 0 && lvl >= lin)
            {   // past the knee the price climbs by a flat step per level instead of multiplying: the price of reaching the knee, plus the step for every level beyond it
                float knee = b * Mathf.Pow(Cfg.upgradeCostGrowth, lin - 1);
                return Mathf.RoundToInt(knee + (lvl - lin + 1) * Cfg.upgradeLinearStep);
            }
            return Mathf.RoundToInt(b * Mathf.Pow(Cfg.upgradeCostGrowth, lvl));
        }
        public static bool CanBuy(Upgrade u) => Coins >= Cost(u);
        public static bool Buy(Upgrade u)
        {
            if (!CanBuy(u)) return false;
            Coins -= Cost(u);
            Levels[(int)u]++;
            Save();
            return true;
        }

        /// <summary>Human-readable effect of the current level, for the lobby cards.</summary>
        public static string Effect(Upgrade u)
        {
            switch (u)
            {
                case Upgrade.FireRate: return "x" + FireRateMult.ToString("0.00") + " fire rate";
                case Upgrade.Damage: return "x" + DamageMult.ToString("0.00") + " damage";
                default: return "x" + RevenueMult.ToString("0.00") + " coins";
            }
        }

        public static void Load()
        {
            Coins = PlayerPrefs.GetInt("sq_coins", 0);
            Attempts = PlayerPrefs.GetInt("sq_attempts", 0);
            BestHorde = PlayerPrefs.GetInt("sq_best", 0);
            Levels[0] = PlayerPrefs.GetInt("sq_fr", 0);
            Levels[1] = PlayerPrefs.GetInt("sq_dmg", 0);
            Levels[2] = PlayerPrefs.GetInt("sq_rev", 0);
            Won = PlayerPrefs.GetInt("sq_won", 0) != 0;
            Cleared = PlayerPrefs.GetInt("sq_cleared", 0);
            Stage = Mathf.Clamp(PlayerPrefs.GetInt("sq_stage", 1), 1, Mathf.Max(1, Cleared + 1));
            ApplyStartLevels();
        }

        /// <summary>The config's start levels. forceStartLevels (test mode): every launch of the game sets the levels to exactly
        /// these, whatever was bought last time. Off: nobody starts below them - a new player begins there, an older save is lifted.</summary>
        static void ApplyStartLevels()
        {
            var cfg = GameManager.I != null ? GameManager.I.config : null;
            if (cfg == null) return;
            if (cfg.forceStartLevels)
            {
                Levels[0] = cfg.startLevelFire;
                Levels[1] = cfg.startLevelDamage;
                Levels[2] = cfg.startLevelRevenue;
                return;
            }
            Levels[0] = Mathf.Max(Levels[0], cfg.startLevelFire);
            Levels[1] = Mathf.Max(Levels[1], cfg.startLevelDamage);
            Levels[2] = Mathf.Max(Levels[2], cfg.startLevelRevenue);
        }

        public static void Save()
        {
            PlayerPrefs.SetInt("sq_coins", Coins);
            PlayerPrefs.SetInt("sq_attempts", Attempts);
            PlayerPrefs.SetInt("sq_best", BestHorde);
            PlayerPrefs.SetInt("sq_fr", Levels[0]);
            PlayerPrefs.SetInt("sq_dmg", Levels[1]);
            PlayerPrefs.SetInt("sq_rev", Levels[2]);
            PlayerPrefs.SetInt("sq_won", Won ? 1 : 0);
            PlayerPrefs.SetInt("sq_cleared", Cleared);
            PlayerPrefs.SetInt("sq_stage", Stage);
            PlayerPrefs.Save();
        }

        public static void Reset()
        {
            Coins = Attempts = BestHorde = 0;
            Won = false; Cleared = 0; Stage = 1;
            Levels[0] = Levels[1] = Levels[2] = 0;
            ApplyStartLevels();
            Save();
        }
    }
}
