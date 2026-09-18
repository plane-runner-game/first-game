using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// LargeLaserFightersSample01
/// 
/// Shows how to generate a single plane, with some
/// basic animation of dynamic parts.
/// </summary>

public class LargeLaserFightersSample01 : MonoBehaviour
{
    public Text SeedText;

    LargeLaser.IRand random;
    LargeLaser.Plane currentPlane;
    LargeLaser.PlaneUtils.WingState wingState;
    float wingTime;
    float wingDirection;
    float propAngle;
    float flapAngle;

    void Start()
    {
        random = LargeLaser.Rand.Create(System.DateTime.Now.Millisecond);

        // init the scene with a random plane
        CreatePlane();
    }

    void Update()
    {
        if (Input.GetKeyUp(KeyCode.Space))
        {
            // generate a new random plane whenever space is pressed
            CreatePlane();
        }
        else
        {
            // cyclicly rotate wings if the plane has a swept wing design
            LargeLaser.PlaneUtils.UpdateWingSweep(currentPlane, ref wingState, ref wingTime, ref wingDirection);

            // cyclicly rotate wing flaps if the plane has them
            LargeLaser.PlaneUtils.UpdateFlaps(currentPlane, ref flapAngle);

            // spin the prop if it has any
            LargeLaser.PlaneUtils.RotatePropeller(currentPlane, ref propAngle);
        }
    }

    void CreatePlane()
    {
        // scrap the existing one.
        if(currentPlane != null)
        {
            currentPlane.Destroy();
        }

        int seed = random.Int();

        // generate a new one
        currentPlane = LargeLaser.Plane.Create(new LargeLaser.PlaneInit()
        {
            Seed = seed
        });

        // init state for demo wing oscillation
        LargeLaser.PlaneUtils.InitWingSweep(ref wingState, ref wingTime, ref wingDirection);

        // display current seed on screen in case we want to duplicate it
        SeedText.text = $"Seed: {seed}";
    }
}
