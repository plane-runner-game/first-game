// HordeKindDef.cs - one enemy unit type (fighter / drone / bomber).
using UnityEngine;

namespace SkySquad
{
    [CreateAssetMenu(menuName = "Sky Squad/Horde Kind")]
    public class HordeKindDef : ScriptableObject
    {
        public string id = "fighter";
        public string displayName = "FIGHTERS";
        public float unitHp = 1f;
        public int contactPower = 1;        // planes lost per unit that reaches the squad
        public float approachSpeed = 13f;   // extra closing speed on top of world scroll
        public GameObject unitPrefab;
        public Color color = new Color(1f, 0.23f, 0.31f);
        public int minLevel = 1;
        public float weight = 1f;           // relative spawn chance
        public float unitScale = 1f;
        public float sizeFactor = 1f;       // horde unit count multiplier (drones 0.7, bombers 0.35)
    }
}
