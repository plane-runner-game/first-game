// GemShop.cs
// The diamonds shop (2026-10-07: "create a shop for the diamonds when someone clicks on the + icon next to the diamonds ... you
// choose the amounts of each bundle and the prices, but not randomly: calculate everything based on a foundation"). Six packs,
// every number derived from three rules:
//  1. The prices are the app stores' standard price points, 0.99 / 4.99 / 9.99 / 19.99 / 49.99 / 99.99 USD: the ladder the big
//     mobile shops sell gems on, and points every store converts to each local currency on its own.
//  2. The first point sets the exchange rate from what diamonds buy: a respawn costs 2 diamonds and an extra soldier 5 (the user,
//     same day: "who is going to spend 15k, you respawn for like 2 diamonds or spawn an extra soldier for like 5"), and 0.99 buys
//     five respawns or two soldiers: 10 diamonds. About 10 cents a diamond, 20 a respawn, 50 a soldier. (It was 100 diamonds for
//     0.99 for a few hours: 15,000 in the last pack, thousands of respawns.)
//  3. A volume bonus: every doubling of the price buys 7.5% more diamonds per dollar, bonus = 7.5% x log2(price / 0.99). It grows
//     with the spend, ever slower, and puts the 99.99 pack (101 x the first price) at +50%.
//  diamonds = 10 x (price / 0.99) x (1 + bonus), rounded to the nearest 5 (nearest 50 from 1,000 up) so it reads at a glance:
//     0.99 -> 10, 4.99 -> 60, 9.99 -> 125, 19.99 -> 270, 49.99 -> 720, 99.99 -> 1,500
//     (respawns: 5, 30, 62, 135, 360, 750 - soldiers: 2, 12, 25, 54, 144, 300).
//  A pack's "+n%" is measured from that rounded amount against the first pack's rate and rounded down, so the tag never promises
//  more than the pack gives: +19, +23, +33, +42, +48. Every pack gives more per dollar than the one before it (10.1, 12.0, 12.5,
//  13.5, 14.4, 15.0 diamonds per dollar), so the last one is the best value.
// Paying goes through Store.cs, the one door to the app stores; no store is connected yet, so a pack is granted at once.
using System;
using System.Globalization;

namespace SkySquad
{
    public static class GemShop
    {
        /// <summary>The price points, in US dollars (rule 1).</summary>
        public static readonly decimal[] PricesUsd = { 0.99m, 4.99m, 9.99m, 19.99m, 49.99m, 99.99m };
        /// <summary>What the first price point buys (rule 2): five respawns (2 diamonds each) or two extra soldiers (5 each). The exchange
        /// rate every other pack is measured against.</summary>
        public const int BaseDiamonds = 10;
        /// <summary>Extra diamonds per dollar for every doubling of the price (rule 3).</summary>
        public const double BonusPerDoubling = 0.075;

        public static int Count => PricesUsd.Length;

        /// <summary>How many times the first price pack i costs (1 for the first pack).</summary>
        static double Ratio(int i) => (double)(PricesUsd[i] / PricesUsd[0]);

        /// <summary>The diamonds pack i gives: the base rate times the price ratio, plus the volume bonus, rounded to a clean number.</summary>
        public static int Diamonds(int i)
        {
            double r = Ratio(i);
            double raw = BaseDiamonds * r * (1.0 + BonusPerDoubling * Math.Log(r, 2.0));
            double step = raw < 1000.0 ? 5.0 : 50.0;
            return (int)(Math.Round(raw / step, MidpointRounding.AwayFromZero) * step);
        }

        /// <summary>The "+n%" on pack i: its diamonds against what the same money buys at the first pack's rate, rounded down (0 for the first pack).</summary>
        public static int BonusPercent(int i)
        {
            double atBaseRate = BaseDiamonds * Ratio(i);
            return Math.Max(0, (int)Math.Floor((Diamonds(i) / atBaseRate - 1.0) * 100.0 + 1e-9));
        }

        /// <summary>The pack with the most diamonds per dollar (the "best value" badge).</summary>
        public static int BestValue
        {
            get
            {
                int best = 0;
                for (int i = 1; i < Count; i++) if (Diamonds(i) / (double)PricesUsd[i] > Diamonds(best) / (double)PricesUsd[best]) best = i;
                return best;
            }
        }

        /// <summary>The product id the stores know pack i by (a consumable; register these when a store is connected).</summary>
        public static string ProductId(int i) => "gems_pack" + (i + 1);

        /// <summary>The price as the button shows it: the store's own localized price once one is connected, the US price until then.</summary>
        public static string PriceText(int i) => Store.PriceText(ProductId(i), "$" + PricesUsd[i].ToString("0.00", CultureInfo.InvariantCulture));

        /// <summary>Buys pack i through the store; when it is paid the diamonds go into the bank (saved) and onGranted gets the amount.
        /// onFailed runs when the player cancels or the payment fails.</summary>
        public static void Buy(int i, Action<int> onGranted, Action onFailed = null)
        {
            if (i < 0 || i >= Count || Store.Busy) { onFailed?.Invoke(); return; }
            int amount = Diamonds(i);
            Store.Purchase(ProductId(i), ok =>
            {
                if (!ok) { onFailed?.Invoke(); return; }
                Progress.Gems += amount;
                Progress.Save();
                onGranted?.Invoke(amount);
            });
        }
    }
}
