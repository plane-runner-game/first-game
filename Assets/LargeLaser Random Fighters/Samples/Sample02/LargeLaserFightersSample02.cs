using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// LargeLaserFightersSample02
/// 
/// Basic cinematic view of randomly generated plane instances
/// planes move in an oscillating circle to give the impression of flight.
/// and some very basic camera transition between 2 current plane instances
/// 
/// Also demonstrates overloading the plane's body type, by cycling
/// through the different body configs at each new generation.
/// </summary>

public class LargeLaserFightersSample02 : MonoBehaviour
{
    public Camera Camera;

    public GameObject TrailPrefab;

    public GameObject EnginePrefab;

    const float TRANSITION_TIME = 2;

    const float FOCUS_TIME = 8;

    enum State
    {
        Focal,
        WaitForVision,
        Transition,
        DestroyOld
    }

    class PlaneContainer
    {
        public LargeLaser.Plane Plane;

        // angle of plane around the cirumfrence of the flight path
        public float circleAngle;

        // plane roll
        public float zAngle;
        public float zAngleSpeed;
        public float zAngleAmount;

        // swept wing state
        public LargeLaser.PlaneUtils.WingState wingState;
        public float wingTime;
        public float wingDirection;

        // propeller rotation angle
        public float propAngle;

        // wing flap angle
        public float flapAngle;
    }


    LargeLaser.Plane.BodyConfiguration bodyConfiguration;
    PlaneContainer[] planes;
    Vector3 cameraRotation;
    LargeLaser.IRand random;
    float newPlaneTimeout;
    float transitionTime;
    State state;
    int focal;

    void Start()
    {
        random = LargeLaser.Rand.Create(System.DateTime.Now.Millisecond);

        planes = new PlaneContainer[2];

        focal = 1;

        CreatePlane(0);

        focal = 0;

        newPlaneTimeout = FOCUS_TIME;
    }

    private void Update()
    {
        UpdatePlane();

        UpdateCamera();

        UpdateNewPlane();
    }

    void UpdateNewPlane()
    {
        if (newPlaneTimeout > 0)
        {
            newPlaneTimeout -= Time.deltaTime;

            if (newPlaneTimeout < 0)
            {
                float angle = Vector3.Dot(Camera.transform.forward, planes[focal].Plane.transform.forward);
                
                CreatePlane(Mathf.Sign(angle));

                state = State.WaitForVision;
            }
        }

        if(state == State.WaitForVision)
        {
            state = State.Transition;

            transitionTime = TRANSITION_TIME;
        }

        if(state == State.Transition)
        {
            transitionTime -= Time.deltaTime;

            if(transitionTime <= 0)
            {
                state = State.DestroyOld;

                ++focal;
                focal %= 2;
            }
        }

        if (state == State.DestroyOld)
        {
            int nextIndex = (focal == 0) ? 1 : 0;
            float angle = AngleToPlane(nextIndex);
            if (angle < 0.5f)
            {
                state = State.Focal;

                newPlaneTimeout = FOCUS_TIME + random.Float(0, FOCUS_TIME / 2);

                planes[nextIndex].Plane.Destroy();
                planes[nextIndex] = null;
            }
        }
    }

    float AngleToPlane(int index)
    {
        Vector3 ray = planes[index].Plane.transform.position;
        ray -= Camera.transform.position;
        ray.Normalize();
        return Vector3.Dot(Camera.transform.forward, ray);
    }

    void UpdatePlane()
    {
        for(int c1 = 0; c1 < 2; ++c1)
        {
            if (planes[c1] != null)
            {
                UpdatePlane(planes[c1]);
            }
        }
    }

    void UpdatePlane(PlaneContainer plane)
    {
        // move round in a circle
        plane.circleAngle += Time.deltaTime * 10;
        plane.circleAngle %= 360f;

        Quaternion rot = Quaternion.Euler(0, plane.circleAngle, 0);

        Quaternion facing = Quaternion.Euler(0, plane.circleAngle - 180, 0);

        Vector3 pos = rot * Vector3.right * 300;

        plane.zAngleSpeed += Time.deltaTime * 0.75f;
        plane.zAngleAmount = Mathf.Sin(plane.zAngleSpeed * 1.5f) * 40;
        plane.zAngle = Mathf.Sin(plane.zAngleSpeed) * plane.zAngleAmount;
        facing *= Quaternion.Euler(0, 0, plane.zAngle);

        plane.Plane.transform.position = pos;
        plane.Plane.transform.rotation = facing;

        // cyclicly rotate wings if the plane has a swept wing design
        LargeLaser.PlaneUtils.UpdateWingSweep(plane.Plane, ref plane.wingState, ref plane.wingTime, ref plane.wingDirection);

        // cyclicly rotate wing flaps if the plane has them
        LargeLaser.PlaneUtils.UpdateFlaps(plane.Plane, ref plane.flapAngle);

        // spin the prop if it has any
        LargeLaser.PlaneUtils.RotatePropeller(plane.Plane, ref plane.propAngle);
    }

    void UpdateCamera()
    {
        Vector3 target;

        if (state == State.Transition)
        {
            float perc = 1f - (transitionTime / TRANSITION_TIME);

            perc = Mathf.SmoothStep(0f, 1f, perc);

            int next = (focal == 0) ? 1 : 0;

            target = Vector3.Lerp(planes[focal].Plane.transform.position, planes[next].Plane.transform.position, perc);
        }
        else
        {
            target = planes[focal].Plane.transform.position;
        }

        cameraRotation.y += Time.deltaTime * 20;
        cameraRotation.x += Time.deltaTime * 0.8f;

        float x = Mathf.Sin(cameraRotation.x) * 50;

        Quaternion camOffset = Quaternion.Euler(x, cameraRotation.y, cameraRotation.z);

        Vector3 camPos = camOffset * Vector3.forward * 15;
        camPos += target;

        Vector3 ray = target;
        ray -= camPos;
        ray.Normalize();

        Camera.transform.position = camPos;
        Camera.transform.rotation = Quaternion.LookRotation(ray);
    }

    void CreatePlane(float direction)
    {
        int nextIndex = (focal == 0) ? 1 : 0;

        planes[nextIndex] = new PlaneContainer();

        int seed = random.Int();

        planes[nextIndex].Plane = LargeLaser.Plane.Create(new LargeLaser.PlaneInit()
        {
            Seed = seed,

            // override and specify the body type
            BodyConfiguration = bodyConfiguration
        });

        LargeLaser.PlaneUtils.InitWingSweep(ref planes[nextIndex].wingState, ref planes[nextIndex].wingTime, ref planes[nextIndex].wingDirection);

        if (planes[focal] != null)
        {
            // init the new plane based on the current position
            planes[nextIndex].zAngle = random.Float(0, Mathf.PI);
            planes[nextIndex].zAngleSpeed = random.Float(0, 10);
            planes[nextIndex].circleAngle = planes[focal].circleAngle + (30 * direction * -1);
        }

        // add streams on the wing tips
        foreach(var wingTipLocator in planes[nextIndex].Plane.WingTipLocators)
        {
            var trail = GameObject.Instantiate(TrailPrefab, wingTipLocator.transform);
            trail.transform.localPosition = Vector3.zero;
        }

        // add jet streams to the engines.
        foreach(var engineLocator in planes[nextIndex].Plane.EngineLocators)
        {
            var trail = GameObject.Instantiate(EnginePrefab, engineLocator.transform);
            trail.transform.localPosition = Vector3.zero;
        }


        UpdatePlane(planes[nextIndex]);

        // cycle through the different body types on each generation
        ++bodyConfiguration;

        if(bodyConfiguration == LargeLaser.Plane.BodyConfiguration.Count)
        {
            bodyConfiguration = LargeLaser.Plane.BodyConfiguration.Standard;
        }
    }
}
