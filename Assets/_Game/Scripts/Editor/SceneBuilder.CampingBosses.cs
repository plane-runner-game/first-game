// SceneBuilder.CampingBosses.cs (Editor only)
// The camping forest's five bosses (2026-10-10: "bosses now for the camping forest"), the night by the fire, modelled from code in Blender
// (Tools/blender/camping_bosses.py -> Art/Enemies/CampingBosses/Boss_<id>.fbx) in place of the tent, the lamppost, the bonfire and the two
// Star Sparrows the theme borrowed: the FIREFLY QUEEN (a lantern abdomen, four pale wings beating), the GREAT HORNED OWL (glowing amber eyes,
// a lantern in its talons, wings beating), the LANTERN BALLOON (a patchwork balloon carrying a log cabin, lanterns, a propeller), the STAR
// BEAR (a bear of the night sky, constellations on its back, legs running, a ring of stars turning) and the FOREST GUARDIAN (a tree spirit,
// lanterns hanging from its branches, roots swaying). A land world is five bosses long already (LandEntry, lastBoss 5).
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string CampingBossDir = Root + "/Art/Enemies/CampingBosses";
        static readonly string[] CampingBossIds = { "firefly", "owl", "balloon", "bear", "guardian" };
        static readonly string[] CampingBossTitles = { "FIREFLY QUEEN", "GREAT HORNED OWL", "LANTERN BALLOON", "STAR BEAR", "FOREST GUARDIAN" };

        // the christmas village's five (the same evening, "bosses for the christmas village"; Tools/blender/christmas_bosses.py): the CHRISTMAS
        // EXPRESS (a flying toy train, wheels turning, smoke, presents; the gingerbread zeppelin until "change the first boss"), SANTA'S SLEIGH (two reindeer galloping, a red nose glowing), the FROST CRYSTAL (a snowflake
        // turning face-on, a glowing heart with eyes), the SNOW GIANT (a snowman under a propeller on his top hat, candy canes) and the GRAND
        // CHRISTMAS TREE (baubles, a gold garland, a turning star, presents beneath)
        const string ChristmasBossDir = Root + "/Art/Enemies/ChristmasBosses";
        static readonly string[] ChristmasBossIds = { "train", "sleigh", "crystal", "snowman", "tree" };
        static readonly string[] ChristmasBossTitles = { "CHRISTMAS EXPRESS", "SANTA'S SLEIGH", "FROST CRYSTAL", "SNOW GIANT", "GRAND CHRISTMAS TREE" };

        // the autumn forest's five (the same evening, "now for the autumn forest"; Tools/blender/autumn_bosses.py): the ACORN AIRSHIP (an acorn
        // balloon, leaf sails, propellers), the HARVEST SCARECROW (a glowing pumpkin head, crows circling), the FOX SPIRIT (five tails waving,
        // foxfire circling), the ROYAL STAG (antlers hung with leaves, legs galloping) and the PUMPKIN CASTLE (glowing windows, witch-hat turrets,
        // a ring of falling leaves)
        const string AutumnBossDir = Root + "/Art/Enemies/AutumnBosses";
        static readonly string[] AutumnBossIds = { "acorn", "scarecrow", "fox", "stag", "castle" };
        static readonly string[] AutumnBossTitles = { "ACORN AIRSHIP", "HARVEST SCARECROW", "FOX SPIRIT", "ROYAL STAG", "PUMPKIN CASTLE" };

        // the desert pyramids' and the japanese island's five (the same evening, "give me for desert pyramids and japanese island";
        // Tools/blender/desert_bosses.py, japan_bosses.py): the MAGIC CARPET (a lamp smoking, a chest of gold), the ANUBIS GUARDIAN (a jackal-
        // headed statue, sceptre and ankh), the WINGED SPHINX (nemes headdress, wings beating), the SUN BARQUE (a golden boat, the sun disc's rays
        // turning, oars rowing), the SKY PYRAMID (the Eye of Horus, obelisks, rings of glyphs turning); the KOI STREAMER (a carp streamer, fins
        // rowing, tail sweeping), the SNOW CRANE (wings beating), the SAMURAI SPIRIT (an empty armour with a katana, spirit flame, wisps), the
        // SKY DRAGON (an eastern dragon in coils with a pearl) and the PAGODA ISLE (a floating island, pagoda, torii, cherry petals turning)
        const string DesertBossDir = Root + "/Art/Enemies/DesertBosses", JapanBossDir = Root + "/Art/Enemies/JapanBosses";
        static readonly string[] DesertBossIds = { "carpet", "anubis", "sphinx", "barque", "pyramid" };
        static readonly string[] DesertBossTitles = { "MAGIC CARPET", "ANUBIS GUARDIAN", "WINGED SPHINX", "SUN BARQUE", "SKY PYRAMID" };
        static readonly string[] JapanBossIds = { "koi", "crane", "samurai", "ryu", "isle" };
        static readonly string[] JapanBossTitles = { "KOI STREAMER", "SNOW CRANE", "SAMURAI SPIRIT", "SKY DRAGON", "PAGODA ISLE" };

        /// <summary>A land world's own five FBX bosses where it has them (camping, christmas, autumn, desert, japan), with their names; null
        /// otherwise, or when an FBX is missing, and the theme's pack models stand in.</summary>
        static GameObject[] LandModelBosses(LandTheme t, Mats M, Meshes X, out string[] names)
        {
            names = null;
            string dir, prefix; string[] ids, titles; float[] width, maxHeight, maxLength, beat;
            // width across, no taller than, no longer than (model units), how fast wings beat / legs and roots swing
            switch (t.id)
            {
                case "camping":
                    dir = CampingBossDir; prefix = "BossCamping_"; ids = CampingBossIds; titles = CampingBossTitles;
                    width = new[] { 3.6f, 4.2f, 2.6f, 3.2f, 3.8f }; maxHeight = new[] { 2.4f, 2.6f, 3.6f, 2.4f, 3.6f }; maxLength = new[] { 3.6f, 3.0f, 3.0f, 4.0f, 3.0f };
                    beat = new[] { 7f, 2.2f, 2f, 3.2f, 1.5f };
                    break;
                case "christmas":
                    dir = ChristmasBossDir; prefix = "BossChristmas_"; ids = ChristmasBossIds; titles = ChristmasBossTitles;
                    width = new[] { 3.6f, 2.4f, 3.8f, 3.4f, 3.8f }; maxHeight = new[] { 2.8f, 2.6f, 3.4f, 3.6f, 4.0f }; maxLength = new[] { 4.6f, 4.2f, 2.0f, 2.6f, 3.6f };
                    beat = new[] { 2f, 4f, 2f, 2f, 2f };
                    break;
                case "autumn":
                    dir = AutumnBossDir; prefix = "BossAutumn_"; ids = AutumnBossIds; titles = AutumnBossTitles;
                    width = new[] { 3.4f, 4.0f, 3.4f, 2.8f, 4.0f }; maxHeight = new[] { 3.8f, 3.4f, 2.4f, 3.4f, 3.6f }; maxLength = new[] { 2.4f, 3.0f, 3.8f, 3.2f, 3.8f };
                    beat = new[] { 2f, 2f, 2.6f, 3.5f, 2f };
                    break;
                case "desert":
                    dir = DesertBossDir; prefix = "BossDesert_"; ids = DesertBossIds; titles = DesertBossTitles;
                    width = new[] { 3.2f, 2.4f, 4.2f, 3.0f, 4.0f }; maxHeight = new[] { 2.6f, 3.6f, 2.4f, 3.4f, 3.4f }; maxLength = new[] { 4.4f, 2.4f, 3.0f, 4.2f, 4.0f };
                    beat = new[] { 2f, 2f, 2.2f, 2.4f, 2f };
                    break;
                case "japan":
                    dir = JapanBossDir; prefix = "BossJapan_"; ids = JapanBossIds; titles = JapanBossTitles;
                    width = new[] { 2.8f, 4.4f, 3.0f, 3.2f, 4.2f }; maxHeight = new[] { 2.4f, 2.0f, 3.8f, 2.8f, 4.0f }; maxLength = new[] { 4.4f, 3.0f, 2.6f, 4.6f, 4.0f };
                    beat = new[] { 2.5f, 2f, 2f, 2f, 2f };
                    break;
                default: return null;
            }
            var five = new GameObject[ids.Length];
            for (int i = 0; i < five.Length; i++)
            {
                five[i] = ModelBossPrefab(dir, ids[i], prefix + ids[i], M, X, width[i], maxHeight[i], maxLength[i], beat[i]);
                if (five[i] == null) { Debug.LogWarning("[SkySquad] " + t.id + " boss " + titles[i] + " could not be built (no " + dir + "/Boss_" + ids[i] + ".fbx): the theme keeps its old bosses"); return null; }
            }
            names = titles;
            return five;
        }
    }
}
