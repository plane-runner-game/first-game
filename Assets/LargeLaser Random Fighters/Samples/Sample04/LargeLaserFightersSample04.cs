using UnityEngine;

/// <summary>
/// LargeLaserFightersSample04
/// 
/// Shows how to override the random implementation used to
/// generate planes. this demo will use the Unity Random interfaces.
/// </summary>

public class LargeLaserFightersSample04 : MonoBehaviour
{
    LargeLaser.IRand random;

    // Our random class. Implement the IRand interface using the Unity Random functions.
    class UnityRand : LargeLaser.IRand
    {
        public void Init(int seed)
        {
            Random.InitState(seed);
        }

        public int Int()
        {
            return Random.Range(0, int.MaxValue);
        }

        public int Int(int min, int max)
        {
            return Random.Range(min, max + 1);
        }

        public float Float()
        {
            return Random.value;
        }

        public float Float(float min, float max)
        {
            return Random.Range(min, max);
        }
    }

    void Start()
    {
        // Populate the plane engine with rand factory.
        LargeLaser.Rand.SetCreate((seed) =>
        {
            var res = new UnityRand();
            res.Init(seed);
            return res;
        });

        random = LargeLaser.Rand.Create(System.DateTime.Now.Millisecond);

        int seed = random.Int();

        // generate a plane using our rand class.
        LargeLaser.Plane.Create(new LargeLaser.PlaneInit()
        {
            Seed = seed
        });
    }
}
