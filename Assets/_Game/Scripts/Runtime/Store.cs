// Store.cs
// The one door to in-app purchases (2026-10-07), the way Ads.cs is the one door to rewarded video. No store is connected yet:
// Purchase answers "paid" at once, so the diamonds shop works in the editor and the test builds. Connecting a store (Unity IAP,
// Google Play Billing, StoreKit ...) changes only this file: register GemShop's product ids as consumables, PriceText returns the
// store's localized price string, Purchase opens the store's payment sheet, sets Busy while it is up and calls onDone(true) from
// the purchase callback (receipt validated), onDone(false) when the player cancels or the payment fails.
using System;
using UnityEngine;

namespace SkySquad
{
    public static class Store
    {
        /// <summary>A payment sheet is on screen: the shop ignores further taps on its packs.</summary>
        public static bool Busy { get; private set; }

        /// <summary>The price of a product as the store shows it to this player; fallback until a store is connected.</summary>
        public static string PriceText(string productId, string fallback) => fallback;

        /// <summary>Buys a product; onDone(true) once it is paid, (false) if cancelled or failed.</summary>
        public static void Purchase(string productId, Action<bool> onDone)
        {
            Busy = true;
            Debug.Log("[Store] purchase '" + productId + "': no store connected yet, granted");
            Busy = false;
            onDone?.Invoke(true);
        }
    }
}
