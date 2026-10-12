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
        static readonly string[] CampingBossIds = { "firefly", "owl", "ember", "moth", "bigfoot" };
        static readonly string[] CampingBossTitles = { "FIREFLY QUEEN", "GREAT HORNED OWL", "CAMPFIRE KING", "LUNA MOTH EMPRESS", "SASQUATCH KING" };

        // the christmas village's five (the same evening, "bosses for the christmas village"; Tools/blender/christmas_bosses.py): the CHRISTMAS
        // EXPRESS (a flying toy train, wheels turning, smoke, presents; the gingerbread zeppelin until "change the first boss"), SANTA'S SLEIGH (two reindeer galloping, a red nose glowing), the FROST CRYSTAL (a snowflake
        // turning face-on, a glowing heart with eyes), the SNOW GIANT (a snowman under a propeller on his top hat, candy canes) and the GRAND
        // CHRISTMAS TREE (baubles, a gold garland, a turning star, presents beneath)
        const string ChristmasBossDir = Root + "/Art/Enemies/ChristmasBosses";
        static readonly string[] ChristmasBossIds = { "nutcracker", "sleigh", "crystal", "snowman", "icequeen" };
        static readonly string[] ChristmasBossTitles = { "NUTCRACKER KING", "SANTA'S SLEIGH", "FROST CRYSTAL", "SNOW GIANT", "ICE QUEEN" };

        // the autumn forest's five (the same evening, "now for the autumn forest"; Tools/blender/autumn_bosses.py): the ACORN AIRSHIP (an acorn
        // balloon, leaf sails, propellers), the HARVEST SCARECROW (a glowing pumpkin head, crows circling), the FOX SPIRIT (five tails waving,
        // foxfire circling), the ROYAL STAG (antlers hung with leaves, legs galloping) and the PUMPKIN CASTLE (glowing windows, witch-hat turrets,
        // a ring of falling leaves)
        const string AutumnBossDir = Root + "/Art/Enemies/AutumnBosses";
        static readonly string[] AutumnBossIds = { "squirrel", "scarecrow2", "fox", "stag", "oakking" };
        static readonly string[] AutumnBossTitles = { "SQUIRREL KNIGHT", "HARVEST SCARECROW", "FOX SPIRIT", "ROYAL STAG", "OAK KING" };

        // the desert pyramids' and the japanese island's five (the same evening, "give me for desert pyramids and japanese island";
        // Tools/blender/desert_bosses.py, japan_bosses.py): the MAGIC CARPET (a lamp smoking, a chest of gold), the ANUBIS GUARDIAN (a jackal-
        // headed statue, sceptre and ankh), the WINGED SPHINX (nemes headdress, wings beating), the SUN BARQUE (a golden boat, the sun disc's rays
        // turning, oars rowing), the SKY PYRAMID (the Eye of Horus, obelisks, rings of glyphs turning); the KOI STREAMER (a carp streamer, fins
        // rowing, tail sweeping), the SNOW CRANE (wings beating), the SAMURAI SPIRIT (an empty armour with a katana, spirit flame, wisps), the
        // SKY DRAGON (an eastern dragon in coils with a pearl) and the PAGODA ISLE (a floating island, pagoda, torii, cherry petals turning)
        const string DesertBossDir = Root + "/Art/Enemies/DesertBosses", JapanBossDir = Root + "/Art/Enemies/JapanBosses";
        static readonly string[] DesertBossIds = { "carpet", "anubis", "sphinx", "cobra", "pyramid" };
        static readonly string[] DesertBossTitles = { "MAGIC CARPET", "ANUBIS GUARDIAN", "WINGED SPHINX", "PHARAOH COBRA", "SKY PYRAMID" };
        static readonly string[] JapanBossIds = { "koi", "crane", "samurai", "ryu", "isle" };
        static readonly string[] JapanBossTitles = { "KOI STREAMER", "SNOW CRANE", "SAMURAI SPIRIT", "SKY DRAGON", "PAGODA ISLE" };

        // the last five land worlds' five (2026-10-11, "do the bosses for the rest of the maps"; Tools/blender/city_bosses.py, soccer_bosses.py,
        // shuttle_bosses.py, treasure_bosses.py, west_bosses.py): downtown's BILLBOARD BLIMP (LED screens, propellers), NEWS CHOPPER (a camera
        // turret, gatling arms, rotors), KING PIGEON (a crowned pigeon, wings beating), TRAFFIC TITAN (a taxi chest, a traffic-light head, legs
        // swinging) and SKYSCRAPER FORTRESS (a lit art-deco tower top, a ring of drones turning); the soccer field's STRIKER BOT (a football
        // rolling inside a steel ring), WHISTLE REFEREE (red and yellow cards, a propeller cap), STADIUM BLIMP (side-on, a scoreboard), GOALKEEPER
        // GIANT (the goal on his back, gloves waving) and GOLDEN TROPHY TITAN (laurel wings, a halo of stars, confetti); the treasure island's CAPTAIN PARROT, TREASURE MIMIC (a chest on bat wings, the lid snapping), GHOST CAPTAIN,
        // CANNON CRAB (cannons in its claws, legs swinging) and SKULL ROCK (gold fire in its eyes, doubloons circling); the space launch's RETRO
        // ROCKET, ORBITAL SATELLITE (solar wings sway, the dish turns face-on), ASTRO MECH, LUNAR LANDER and SPACE STATION (a turning ring); the
        // wild west's THUNDERBIRD (lightning on its wings), SHERIFF ROBOT (a steam robot, a cog turning on his chest), RATTLESNAKE (the rattle
        // shakes), OUTLAW ZEPPELIN (a saloon gondola, three propellers) and GOLD MINE MESA (a saloon, a water tower, the windmill turns, gold coins
        // circle)
        const string CityBossDir = Root + "/Art/Enemies/CityBosses", SoccerBossDir = Root + "/Art/Enemies/SoccerBosses";
        const string ShuttleBossDir = Root + "/Art/Enemies/ShuttleBosses", TreasureBossDir = Root + "/Art/Enemies/TreasureBosses", WestBossDir = Root + "/Art/Enemies/WestBosses";
        static readonly string[] CityBossIds = { "kong", "chopper", "pigeon", "titan", "tycoon" };
        static readonly string[] CityBossTitles = { "CHROME KONG", "NEWS CHOPPER", "KING PIGEON", "TRAFFIC TITAN", "THE TYCOON" };
        static readonly string[] SoccerBossIds = { "ballbot", "referee", "blimp", "keeper", "trophy" };
        static readonly string[] SoccerBossTitles = { "STRIKER BOT", "WHISTLE REFEREE", "STADIUM BLIMP", "GOALKEEPER GIANT", "GOLDEN TROPHY TITAN" };
        static readonly string[] ShuttleBossIds = { "rocket", "satellite", "mech", "lander", "station" };
        static readonly string[] ShuttleBossTitles = { "RETRO ROCKET", "ORBITAL SATELLITE", "ASTRO MECH", "LUNAR LANDER", "SPACE STATION" };
        static readonly string[] TreasureBossIds = { "parrot", "mimic", "ghost", "crab", "skull2" };
        static readonly string[] TreasureBossTitles = { "CAPTAIN PARROT", "TREASURE MIMIC", "GHOST CAPTAIN", "CANNON CRAB", "DREAD SKULL" };
        static readonly string[] WestBossIds = { "thunderbird", "sheriff", "rattler2", "zeppelin", "mesa" };
        static readonly string[] WestBossTitles = { "THUNDERBIRD", "SHERIFF ROBOT", "RATTLESNAKE", "OUTLAW ZEPPELIN", "GOLD MINE MESA" };

        /// <summary>A land world's own five FBX bosses where it has them (camping, christmas, autumn, desert, japan, city, soccer, shuttle,
        /// treasure, west), with their names; null
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
                    width = new[] { 3.6f, 4.2f, 3.4f, 4f, 3.4f }; maxHeight = new[] { 2.4f, 2.6f, 3.2f, 2.6f, 4.2f }; maxLength = new[] { 3.6f, 3.0f, 2.6f, 3.4f, 3f };
                    beat = new[] { 7f, 2.2f, 2.2f, 2f, 2f };
                    break;
                case "christmas":
                    dir = ChristmasBossDir; prefix = "BossChristmas_"; ids = ChristmasBossIds; titles = ChristmasBossTitles;
                    width = new[] { 2.4f, 2.4f, 3.8f, 3.4f, 4f }; maxHeight = new[] { 4.2f, 2.6f, 3.4f, 3.6f, 4f }; maxLength = new[] { 2f, 4.2f, 2.0f, 2.6f, 3f };
                    beat = new[] { 2.5f, 4f, 2f, 2f, 1.6f };
                    break;
                case "autumn":
                    dir = AutumnBossDir; prefix = "BossAutumn_"; ids = AutumnBossIds; titles = AutumnBossTitles;
                    width = new[] { 3.4f, 4.0f, 3.4f, 2.8f, 4.2f }; maxHeight = new[] { 2.8f, 3.4f, 2.4f, 3.4f, 4.2f }; maxLength = new[] { 2.4f, 3.0f, 3.8f, 3.2f, 3.6f };
                    beat = new[] { 3f, 2f, 2.6f, 3.5f, 1.5f };
                    break;
                case "desert":
                    dir = DesertBossDir; prefix = "BossDesert_"; ids = DesertBossIds; titles = DesertBossTitles;
                    width = new[] { 3.2f, 2.4f, 4.2f, 4.2f, 4.0f }; maxHeight = new[] { 2.6f, 3.6f, 2.4f, 3.8f, 3.4f }; maxLength = new[] { 4.4f, 2.4f, 3.0f, 3.2f, 4.0f };
                    beat = new[] { 2f, 2f, 2.2f, 2f, 2f };
                    break;
                case "japan":
                    dir = JapanBossDir; prefix = "BossJapan_"; ids = JapanBossIds; titles = JapanBossTitles;
                    width = new[] { 2.8f, 4.4f, 3.0f, 3.2f, 4.2f }; maxHeight = new[] { 2.4f, 2.0f, 3.8f, 2.8f, 4.0f }; maxLength = new[] { 4.4f, 3.0f, 2.6f, 4.6f, 4.0f };
                    beat = new[] { 2.5f, 2f, 2f, 2f, 2f };
                    break;
                case "city":
                    dir = CityBossDir; prefix = "BossCity_"; ids = CityBossIds; titles = CityBossTitles;
                    width = new[] { 3.4f, 3.4f, 4.4f, 2.8f, 3.8f }; maxHeight = new[] { 3.8f, 2.4f, 2.6f, 3.8f, 4.2f }; maxLength = new[] { 2.8f, 4.2f, 3.0f, 2.4f, 2.2f };
                    beat = new[] { 2.2f, 2f, 2.6f, 2.2f, 2f };
                    break;
                case "soccer":
                    dir = SoccerBossDir; prefix = "BossSoccer_"; ids = SoccerBossIds; titles = SoccerBossTitles;
                    width = new[] { 3.6f, 2.4f, 4.2f, 3.8f, 4.4f }; maxHeight = new[] { 3.2f, 3.8f, 2.6f, 3.8f, 3.8f }; maxLength = new[] { 2.6f, 2.4f, 2.4f, 2.4f, 3.4f };
                    beat = new[] { 2f, 3.5f, 2f, 2.2f, 1.8f };
                    break;
                case "shuttle":
                    dir = ShuttleBossDir; prefix = "BossShuttle_"; ids = ShuttleBossIds; titles = ShuttleBossTitles;
                    width = new[] { 2.2f, 4.4f, 2.8f, 3.2f, 4.4f }; maxHeight = new[] { 4.2f, 2.4f, 3.6f, 3.6f, 3.0f }; maxLength = new[] { 2.0f, 2.2f, 2.6f, 3.2f, 3.4f };
                    beat = new[] { 2f, 1.5f, 2.2f, 2f, 2f };
                    break;
                case "treasure":
                    dir = TreasureBossDir; prefix = "BossTreasure_"; ids = TreasureBossIds; titles = TreasureBossTitles;
                    width = new[] { 4.0f, 3.6f, 3.0f, 3.8f, 4.2f }; maxHeight = new[] { 2.4f, 2.6f, 3.8f, 2.6f, 3.6f }; maxLength = new[] { 3.6f, 2.6f, 2.8f, 3.2f, 3.6f };
                    beat = new[] { 2.6f, 2.4f, 2f, 3.2f, 2f };
                    break;
                case "west":
                    dir = WestBossDir; prefix = "BossWest_"; ids = WestBossIds; titles = WestBossTitles;
                    width = new[] { 4.2f, 2.4f, 2.8f, 3.0f, 4.2f }; maxHeight = new[] { 2.4f, 3.8f, 3.8f, 2.6f, 3.8f }; maxLength = new[] { 3.0f, 2.4f, 3.6f, 4.6f, 4.0f };
                    beat = new[] { 2.2f, 2f, 9f, 2f, 2f };
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
