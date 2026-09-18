using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    public class Plane : MonoBehaviour
    {
        [System.Flags]
        enum ConfigFlag
        {
            BodyMissiles = 1 << 0,
            SideEngines = 1 << 1,
            BellyAirIntake = 1 << 2,
            LowSideAirIntakes = 1 << 3,
            HighSideAirIntakes = 1 << 4,
            //MigNose = 1 << 5,
            WingEngines = 1 << 6,
            BodyEngines = 1 << 7,
            UnderWingEngines = 1 << 8,
            WingFuelTanks = 1 << 9,
            BodyFuelTanks = 1 << 10,
            LowFrontWings = 1 << 11,
            HighFrontWings = 1 << 12,
            WingTipMissiles = 1 << 13,
            WingTipWings = 1 << 14,
            WingFlaps = 1 << 15
        }

        enum Type
        {
            Attack,
            Fighter,
        }

        public enum BodyConfiguration
        {
            /// <summary>
            /// Single body with regular properties
            /// </summary>
            Standard,

            /// <summary>
            /// Floating body, tail structure supported by booms attached to wing
            /// </summary>
            Boom,

            /// <summary>
            /// Engine central body flanked by engine structures
            /// </summary>
            Centre,

            /// <summary>
            /// Body embedded within wing
            /// </summary>
            FlyingWing,

            /// <summary>
            /// Flattened with minimal cross section
            /// </summary>
            ArrowHead,

            Count
        }

        enum WingConfiguration
        {
            Standard,
            Delta,
            Forward,
            Sweep,

            Max
        }

        enum TailConfiguration
        {
            Standard,
            T,
            V,
            Twin,
            NoWing,
            Duel,

            Max
        }

        public Material BodyMaterial;
        public Material MetalMaterial;
        public Material MissileMaterial;
        public Material DetailsMaterial;

        /// <summary>
        /// Filled in with GameObjects positioned at the wing tips.
        /// </summary>
        [HideInInspector]
        public List<GameObject> WingTipLocators;

        /// <summary>
        /// Filled in with GameObjects positioned at the engine exhaust.
        /// </summary>
        [HideInInspector]
        public List<GameObject> EngineLocators;

        /// <summary>
        /// Function for generating a plane instance.
        /// </summary>
        /// <param name="init"></param>
        /// <returns>Plane instance</returns>

        public static Plane Create(PlaneInit init)
        {
            var pre = Resources.Load<GameObject>("LargeLaserFighterGameObject");
            var root = GameObject.Instantiate(pre);
            root.name = "Plane";

            var plane = root.GetComponent<Plane>();
            plane.RootObj = root;

            plane.InternalInit(init);

            return plane;
        }

        GameObject RootObj;

        Type type;
        WingConfiguration wingConfiguration;
        TailConfiguration tailConfiguration;
        BodyConfiguration bodyConfiguration;

        SubObject metalObjects;
        SubObject detailsObjects;

        List<Vector3> verts;
        List<int> tris;
        List<Vector2> uvs;
        float[] sides = new float[] { 1, -1 };

        LargeLaser.IRand rand;

        ConfigFlag configFlags;

        List<SubObject> wings;
        List<SubObject> props;

        Dictionary<int, List<EntityId>> missileTextureMap;   // EntityId: Unity 6.6 retired the int instance id (patched 2026-09-18)       // key = texture index, value = gameobject ids

        /// <summary>
        /// Utility function for duplicating a Plane instance.
        /// </summary>
        /// <returns>A copy of the target Plane.</returns>
        public Plane Duplicate()
        {
            var obj = GameObject.Instantiate(gameObject);
            return obj.GetComponent<Plane>();
        }

        /// <summary>
        /// Utility function for destroying a Plane instance.
        /// </summary>
        public void Destroy()
        {
            GameObject.Destroy(gameObject);
        }

        BodyConfiguration CreateBodyConfiguration(IRand rand)
        {
            List<BodyConfiguration> possibleBodies = new List<BodyConfiguration>();
            for (BodyConfiguration c1 = 0; c1 < BodyConfiguration.Count; ++c1)
            {
                possibleBodies.Add(c1);
            };

            if (type == Type.Attack)
            {
                possibleBodies.Remove(BodyConfiguration.Centre);
            }

            return possibleBodies[rand.Int(0, possibleBodies.Count - 1)];
        }

        void InternalInit(PlaneInit init)
        {
            rand = Rand.Create(init.Seed);

            if(init.BodyConfiguration == BodyConfiguration.Count)
            {
                bodyConfiguration = CreateBodyConfiguration(rand);
            }
            else
            {
                bodyConfiguration = init.BodyConfiguration;
            }

            missileTextureMap = new Dictionary<int, List<EntityId>>();

            WingTipLocators = new List<GameObject>();

            EngineLocators = new List<GameObject>();

            float typeRnd = rand.Float();
            if (bodyConfiguration == BodyConfiguration.ArrowHead || typeRnd < 0.5f)
            {
                type = Type.Fighter;
            }
            else
            {
                type = Type.Attack;
            }

            List<TailConfiguration> possibleTails;

            if (bodyConfiguration == BodyConfiguration.FlyingWing ||
                bodyConfiguration == BodyConfiguration.Boom ||
                bodyConfiguration == BodyConfiguration.ArrowHead ||
                type == Type.Attack)
            {
                wingConfiguration = WingConfiguration.Standard;
            }
            else
            {
                List<WingConfiguration> possibleWings = new List<WingConfiguration>();
                for (WingConfiguration c1 = 0; c1 < WingConfiguration.Max; ++c1)
                {
                    possibleWings.Add(c1);
                };

                wingConfiguration = possibleWings[rand.Int(0, possibleWings.Count - 1)];
            }

            if (wingConfiguration == WingConfiguration.Delta)
            {
                possibleTails = new List<TailConfiguration>()
                {
                    TailConfiguration.T,
                    TailConfiguration.NoWing
                };
            }
            else if (wingConfiguration == WingConfiguration.Forward)
            {
                possibleTails = new List<TailConfiguration>()
                {
                    TailConfiguration.T,
                    TailConfiguration.V,
                    TailConfiguration.NoWing
                };
            }
            else if (wingConfiguration == WingConfiguration.Sweep)
            {
                possibleTails = new List<TailConfiguration>()
                {
                    TailConfiguration.Standard,
                    TailConfiguration.Twin
                };
            }
            else
            {
                possibleTails = new List<TailConfiguration>();
                for (TailConfiguration c1 = 0; c1 < TailConfiguration.Max; ++c1)
                {
                    if (c1 != TailConfiguration.NoWing)
                    {
                        possibleTails.Add(c1);
                    }
                };
            }

            if(bodyConfiguration == BodyConfiguration.Centre)
            {
                possibleTails.Remove(TailConfiguration.Duel);
            }

            tailConfiguration = possibleTails[rand.Int(0, possibleTails.Count - 1)];




            metalObjects = new SubObject();
            metalObjects.Create("Metal", RootObj.transform, Vector3.zero, Quaternion.identity, MetalMaterial);

            detailsObjects = new SubObject();
            detailsObjects.Create("Details", RootObj.transform, Vector3.zero, Quaternion.identity, DetailsMaterial);


            var meshFilter = RootObj.GetComponent<MeshFilter>();

            Mesh mesh = new Mesh();
            Vector3 dimensions = Vector3.zero;

            verts = new List<Vector3>();
            tris = new List<int>();
            uvs = new List<Vector2>();


            if (type == Type.Fighter || type == Type.Attack)
            {
                Small(rand.Int(), ref dimensions);
            }
            else
            {
                throw new System.Exception($"Plane Create. Type {type} not handled");
            }

            mesh.vertices = verts.ToArray();
            mesh.triangles = tris.ToArray();
            mesh.uv = uvs.ToArray();


            mesh.RecalculateNormals();

            meshFilter.mesh = mesh;

            float hue = 0;
            float gloss = 0;
            Texture2D mainColor;
            Texture2D detailTexture;
            var missileTextures = CreateMissileTextures(rand.Int());

            if(init.TextureSeed >= 0)
            {
                var textures = TextureManager.Instance.GetTextures(init.TextureSeed);

                mainColor = textures.MainTexture;

                detailTexture = textures.DetailTexture;
            }
            else
            {
                mainColor = TextureManager.Instance.GenerateMainColor(rand.Int(), ref hue, ref gloss);

                detailTexture = TextureManager.Instance.GenerateDetails(rand.Int());
            }


            Color c = Color.HSVToRGB(hue, 0.5f, 1);

            Vector3 tintRatio = new Vector3(rand.Float(0.6f, 1.2f), rand.Float(0.5f, 0.7f), rand.Float(0.8f, 1.2f));
            Vector3 noseTint = new Vector3(c.r, c.g, c.b);
            Vector3 wingTint = noseTint;

            float bottomShade = rand.Float(0.1f, 0.7f);
            Color bottom = new Color(bottomShade, bottomShade, bottomShade);

            if (bodyConfiguration == BodyConfiguration.FlyingWing)
            {
                tintRatio.z = 1.2f;
            }

            var renderers = RootObj.GetComponentsInChildren<Renderer>();
            foreach (var renderer in renderers)
            {
                if (renderer.gameObject.name == "Metal")
                {

                }
                else if (renderer.gameObject.name == "Details")
                {
                    renderer.material.SetTexture("_MainTex", detailTexture);
                }
                else if (renderer.gameObject.name == "Missile")
                {
                    var missile = GetMissileTexture(missileTextures, renderer.gameObject);
                    renderer.material.SetTexture("_MainTex", missile);
                }
                else
                {
                    renderer.material.SetTexture("_MainTex", mainColor);

                    renderer.material.SetVector("_Dimensions", dimensions);
                    renderer.material.SetVector("_TintRatios", tintRatio);
                    renderer.material.SetVector("_NoseTint", noseTint);
                    renderer.material.SetVector("_WingTint", wingTint);

                    renderer.material.SetColor("_BottomColor", bottom);

                    renderer.material.SetFloat("_Glossiness", gloss);
                    renderer.material.SetFloat("_Metallic", gloss * 0.25f);
                }
            }


            metalObjects.Publish();

            detailsObjects.Publish();
        }

        /// <summary>
        /// Rotates any propellers by the specified angle in degrees.
        /// </summary>
        /// <param name="angle"></param>

        public void SetPropAngle(float angle)
        {
            if(props != null)
            {
                int c1 = 0;
                foreach(var prop in props)
                {
                    prop.Transform.localRotation = Quaternion.Euler(0, 0, angle * sides[c1]);

                    ++c1;
                    c1 %= 2;
                }
            }
        }

        /// <summary>
        /// Sets the angle in degrees of swept wing, if applicable
        /// </summary>
        /// <param name="angle"></param>

        public void SetWingAngle(float angle)
        {
            if (wingConfiguration == WingConfiguration.Sweep)
            {
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    var wing = RootObj.transform.Find($"Wing{c1}");
                    wing.localRotation = Quaternion.Euler(0, angle * sides[c1], 0);

                    foreach (Transform child in wing)
                    {
                        child.localRotation = Quaternion.Euler(0, angle * sides[c1] * -1, 0);
                    }
                }
            }
        }

        /// <summary>
        /// Sets the angle of wing flap in degrees, if applicable.
        /// </summary>
        /// <param name="angle"></param>
        public void SetFlapAngle(float angle)
        {
            if (HasFlag(configFlags, ConfigFlag.WingFlaps))
            {
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    var flap = RootObj.transform.Find($"Flap{c1}");
                    flap.localRotation = Quaternion.Euler(angle * sides[c1], 0, 0);

                    foreach (Transform child in flap)
                    {
                        child.localRotation = Quaternion.Euler(0, angle * sides[c1] * -1, 0);
                    }
                }
            }
        }

        void Small(int seed, ref Vector3 dimensions)
        {
            Body mainBody = new Body();

            List<Body> boomBodies = new List<Body>();

            int c = 0;

            int xEngines = 1;
            int yEngines = 1;
            float engineRadius = 0.5f;
            float maxWingEndZ = 5;
            float minWingEndZ = 0;

            if (bodyConfiguration == BodyConfiguration.FlyingWing)
            {
                engineRadius = 0.25f;

                if (rand.Float() < 0.5f)
                {
                    SetFlag(ref configFlags, ConfigFlag.WingEngines);

                    xEngines = 0;
                    yEngines = 0;
                }
            }
            else if (bodyConfiguration == BodyConfiguration.ArrowHead)
            {
                if (rand.Float() < 0.3f)
                {
                    xEngines = 0;
                    yEngines = 0;

                    SetFlag(ref configFlags, ConfigFlag.UnderWingEngines);
                }
                else
                {
                    xEngines = 2;

                    engineRadius = 0.35f;
                }
            }
            else if (bodyConfiguration != BodyConfiguration.Boom &&
                    tailConfiguration == TailConfiguration.Duel &&
                    rand.Float() < 0.5f)
            {
                xEngines = 0;
                yEngines = 0;

                SetFlag(ref configFlags, ConfigFlag.BodyEngines);
            }
            else
            {
                if(bodyConfiguration != BodyConfiguration.Centre &&
                    rand.Float() < 0.25f)
                {
                    // under wing engines
                    SetFlag(ref configFlags, ConfigFlag.UnderWingEngines);

                    xEngines = 0;
                    yEngines = 0;
                }
                else
                {
                    // rear engines

                    float engineRnd = rand.Float();

                    if (engineRnd < 0.33f)
                    {
                    }
                    else if (engineRnd < 0.66f)
                    {
                        xEngines = 2;
                    }
                    else
                    {
                        yEngines = 2;
                    }

                    if (xEngines > 1 || yEngines > 1)
                    {
                        engineRadius = 0.35f;
                    }
                }
            }


            float rearWidth = engineRadius * xEngines;
            float rearHeight = engineRadius * yEngines;

            float frontDimPercent;
            if (type == Type.Attack)
            {
                frontDimPercent = rand.Float(0.6f, 0.8f);
            }
            else
            {
                frontDimPercent = rand.Float(0.55f, 0.65f);
            }


            if (bodyConfiguration == BodyConfiguration.Boom)
            {
                float width = rand.Float(0.8f, 1f);
                float height = width * rand.Float(1f, 1.25f);

                mainBody.length = 8;
                mainBody.lowerInflate = new Vector2(0, rand.Float(0.2f, 0.7f));

                mainBody.dims = new List<Vector3>()
                {
                    new Vector3(rearWidth,rearHeight,0),
                    new Vector3(width,height,frontDimPercent),
                    new Vector3(0,0,1)
                };
            }
            else if (bodyConfiguration == BodyConfiguration.Centre)
            {
                mainBody.length = 11;
                mainBody.lowerInflate = new Vector2(0, rand.Float(0.2f, 0.7f));

                float width = rand.Float(0.4f, 0.6f);
                float height = rand.Float(0.6f, 0.8f);

                mainBody.dims = new List<Vector3>()
                {
                    new Vector3(0.25f,0.25f,0),
                    new Vector3(width,height-0.15f,0.3f),
                    new Vector3(width,height,frontDimPercent),
                    new Vector3(0,0,1)
                };
            }
            else if (bodyConfiguration == BodyConfiguration.FlyingWing)
            {
                float width = rand.Float(1f, 1.2f);
                float height = width * rand.Float(0.4f, 0.5f);
                maxWingEndZ = 3;

                mainBody.length = rand.Float(4f, 5f);
                mainBody.lowerInflate = Vector2.zero;

                mainBody.dims = new List<Vector3>()
                {
                    new Vector3(rearWidth,rearHeight,0),
                    new Vector3(width,height,frontDimPercent),
                    new Vector3(0,0,1)
                };
            }
            else if (bodyConfiguration == BodyConfiguration.ArrowHead)
            {
                mainBody.length = rand.Float(10f, 11f);

                mainBody.pinchEdge = true;

                float width = rand.Float(1f, 1.2f);
                float height = rand.Float(0.35f, 0.45f);

                mainBody.dims = new List<Vector3>()
                {
                    new Vector3(rearWidth,rearHeight,0),
                    new Vector3(width,height-0.15f,0.3f),
                    new Vector3(width,height,frontDimPercent),
                    new Vector3(0,0,1)
                };
            }
            else
            {
                mainBody.length = 10;

                mainBody.lowerInflate = new Vector2(0, rand.Float(0.25f, 0.9f));

                float width = rand.Float(0.5f, 0.75f);
                float height = rand.Float(0.75f, 0.9f);

                if (HasFlag(configFlags, ConfigFlag.BodyEngines))
                {
                    rearWidth = 0.33f;
                    rearHeight = 0.33f;
                }
                else if (HasFlag(configFlags, ConfigFlag.UnderWingEngines))
                {
                    rearWidth = rand.Float(0f, 0.2f);
                    rearHeight = rand.Float(0.3f, 0.4f);
                }

                mainBody.dims = new List<Vector3>()
                {
                    new Vector3(rearWidth, rearHeight, 0),
                    new Vector3(rearWidth + 0.2f, rearHeight + 0.2f, 0.2f),
                    new Vector3(width, height, frontDimPercent),
                    new Vector3(0, 0, 1)
                };
            }

            mainBody.offset = Vector3.forward * -(mainBody.length * 0.5f);

            //c = Nose(c, mainBody);

            c = MeshBuilder.Body(c, verts, tris, uvs, mainBody);

            c = Canopy(c, mainBody, seed);



            if (bodyConfiguration == BodyConfiguration.Centre)
            {
                c = CenterBody(c, mainBody);
            }
            else
            {
                c = Engines(c, mainBody, xEngines, yEngines);
            }





            Wing wing;

            // MAIN WINGS
            {
                float wingPerc = 0.5f;
                bool flaps = false;

                if (type == Type.Attack)
                {
                    maxWingEndZ = 1;
                }

                wing = new Wing();

                if (wingConfiguration == WingConfiguration.Delta)
                {
                    wing.baseLength = mainBody.length * rand.Float(0.4f, 0.6f);
                    wing.endLength = wing.baseLength * rand.Float(0.2f, 0.3f);
                    wing.width = wing.baseLength * rand.Float(0.75f, 1.2f);
                    wing.endOffset.z = 0;
                    wing.endOffset.y = 0;
                    wing.wingHeightOfBody = rand.Float(-0.9f, 0.75f);

                    flaps = true;
                }
                else if (wingConfiguration == WingConfiguration.Forward)
                {
                    wing.baseLength = mainBody.length * rand.Float(0.25f, 0.35f);
                    wing.width = mainBody.length * rand.Float(0.35f, 0.45f);
                    wing.endLength = rand.Float(0.4f, 0.5f);
                    wing.endOffset.z = rand.Float(2.5f, 3.5f);
                    wing.endOffset.y = 0;
                    wing.wingHeightOfBody = -0f;
                    wing.frontCurve = -rand.Float(1f, 1.5f);

                    wingPerc = 0.33f;
                }
                else if (wingConfiguration == WingConfiguration.Sweep)
                {
                    wing.frontCurve = 0;
                    wing.baseLength = mainBody.length * 0.2f;
                    wing.endLength = mainBody.length * 0.05f;
                    wing.width = mainBody.length * 0.5f;
                    wing.endOffset.z = -1;
                    wing.endOffset.y = 0;
                    wing.wingHeightOfBody = 0.75f;
                }
                else if (bodyConfiguration == BodyConfiguration.FlyingWing)
                {
                    wing.frontCurve = 0;
                    wing.baseLength = mainBody.length * rand.Float(0.66f, 0.85f);
                    wing.endLength = rand.Float(0.5f, 1f);
                    wing.width = rand.Float(6f, 8f);
                    wing.endOffset = new Vector3(0, 0f, -rand.Float(1f, maxWingEndZ));
                    wing.wingHeightOfBody = 0;
                    wing.baseHeight = mainBody.dims[1].y * 0.4f;

                    wing.rearCurve = wing.endOffset.z * -0.5f;
                }
                else
                {
                    if (type == Type.Fighter)
                    {
                        minWingEndZ = 2;
                    }

                    wing.frontCurve = rand.Float(-0.5f, 0.5f);
                    wing.baseLength = mainBody.length * rand.Float(0.25f, 0.33f);
                    wing.endLength = wing.baseLength * rand.Float(0.25f, 0.5f);
                    wing.width = rand.Float(5f, 7f);
                    wing.endOffset = new Vector3(0, -rand.Float(0f, 1f), -rand.Float(minWingEndZ, maxWingEndZ));
                    wing.wingHeightOfBody = rand.Float(-0.75f, 0.75f);

                    if (type == Type.Fighter)
                    {
                        wingPerc = rand.Float(0.4f, 0.5f);
                        wing.width = rand.Float(4f, 6f);
                    }
                    else
                    {
                        wing.width = rand.Float(5f, 7f);
                    }

                    flaps = wing.endOffset.z == 0;
                }

                if(flaps)
                {
                    SetFlag(ref configFlags, ConfigFlag.WingFlaps);
                }    

                if (bodyConfiguration == BodyConfiguration.Boom)
                {
                    wing.wingHeightOfBody = rand.Float(0.75f, 0.9f);
                }
                else if(bodyConfiguration == BodyConfiguration.ArrowHead)
                {
                    wing.wingHeightOfBody = 0;
                }

                if (HasFlag(configFlags, ConfigFlag.SideEngines))
                {
                    if(bodyConfiguration == BodyConfiguration.Centre &&
                        HasFlag(configFlags, ConfigFlag.LowSideAirIntakes))
                    {
                        wing.wingHeightOfBody = 1;
                    }
                    else if (bodyConfiguration == BodyConfiguration.Centre &&
                        HasFlag(configFlags, ConfigFlag.HighSideAirIntakes))
                    {
                        wing.wingHeightOfBody = -1;
                    }
                    else if (wingConfiguration == WingConfiguration.Sweep ||
                        rand.Float() < 0.5f)
                    {
                        wing.wingHeightOfBody = 1;
                    }
                    else
                    {
                        wing.wingHeightOfBody = -1;
                    }
                }

                Vector3 anchor = Vector3.right + Vector3.up * wing.wingHeightOfBody;

                Vector3 wingPos = GetPositionOnBody(mainBody, anchor, wingPerc);

                if (wingConfiguration == WingConfiguration.Delta)
                {
                    wingPos.z += (wing.baseLength * -0.75f);
                }
                else if(bodyConfiguration == BodyConfiguration.ArrowHead)
                {
                    wingPos.z += (wing.baseLength * -0.75f);
                }
                else
                {
                    wingPos.z += (wing.baseLength * -0.5f);
                }

                float wingPercentOfBody = wing.baseLength / mainBody.length;
                Vector3 wingStart = GetPositionOnBody(mainBody, anchor, 0.5f - (wingPercentOfBody * 0.5f));
                Vector3 wingEnd = GetPositionOnBody(mainBody, anchor, 0.5f + (wingPercentOfBody * 0.5f));

                wingStart.x -= 0.2f;
                wingEnd.x -= 0.1f;

                if (bodyConfiguration == BodyConfiguration.FlyingWing)
                {
                    wingPos.x = 0;
                    wingStart.x = 0f;
                    wingEnd.x = 0f;
                }

                c = Wings(c, wing, wingPos, wingStart, wingEnd, wingConfiguration == WingConfiguration.Sweep, flaps);

                AddWingTipObjects(wing, wingPos);


                if (wingConfiguration == WingConfiguration.Sweep)
                {
                    Wing wingCover = new Wing()
                    {
                        frontCurve = 0f,
                        baseLength = wing.baseLength * 1.1f,
                        endLength = wing.baseLength * 1.1f,
                        width = 1,
                        endOffset = new Vector3(0, 0, wing.endOffset.z),
                        baseHeight = wing.baseHeight * 2
                    };

                    float lenPerc = wingCover.width / wing.width;
                    wingCover.endOffset.z = -((wing.baseLength - wing.endLength) - wing.endOffset.z) * lenPerc;

                    Vector3 coverPos = wingPos;
                    coverPos.y += wing.baseHeight * 0.25f;
                    Vector3 coverStart = wingStart;
                    Vector3 coverEnd = wingEnd;
                    coverStart.x -= 0.1f;
                    coverEnd.x -= 0.1f;

                    c = Wings(c, wingCover, coverPos, coverStart, coverEnd, false);
                }


                if (bodyConfiguration == BodyConfiguration.Boom)
                {
                    c = BoomBody(c, mainBody, wing, wingPos, boomBodies);
                }
                else if (HasFlag(configFlags, ConfigFlag.WingEngines))
                {
                    c = WingEngines(c, mainBody, wing, wingPos);
                }
                
                if (HasFlag(configFlags, ConfigFlag.UnderWingEngines))
                {
                    c = UnderWingEngines(c, mainBody, wing, wingPos);
                }


                if (wingConfiguration == WingConfiguration.Delta ||
                    wingConfiguration == WingConfiguration.Forward)
                {
                    if (rand.Float() < 0.75)
                    {
                        c = FrontWings(c, mainBody, wing);
                    }
                }

                c = AirIntakes(c, mainBody, wing);

                c = BodyWeapons(c, mainBody);

                c = FuelTanks(c, wing, wingPos, mainBody);

                c = WingWeapons(c, wing, wingPos, mainBody);

                if (wingConfiguration != WingConfiguration.Sweep)
                {
                    if (rand.Float() < 0.5f)
                    {
                        c = CreateWingTips(c, wing, wingPos);
                    }

                    c = WingRibs(c, wing, wingPos);
                }

                if (wingConfiguration != WingConfiguration.Sweep &&
                    !HasFlag(configFlags, ConfigFlag.WingTipMissiles) &&
                    !HasFlag(configFlags, ConfigFlag.WingTipWings) &&
                    rand.Float() < 0.5f)
                {
                    c = WingTubes(c, wing, wingPos);
                }

                BodyDetails(mainBody, wing, wingPos);
            }

            // TAIL

            if (bodyConfiguration == BodyConfiguration.FlyingWing)
            {
                c = CreateFlyingWingTail(c, mainBody);
            }
            else if (bodyConfiguration == BodyConfiguration.Boom)
            {
                c = BoomTail(c, boomBodies);
            }
            else if (tailConfiguration == TailConfiguration.Duel)
            {
                c = DuelTail(c, mainBody);
            }
            else
            {
                c = CreateTail(c, mainBody);
            }

            dimensions.z = mainBody.length;
            dimensions.x = mainBody.dims[mainBody.dims.Count - 2].x + wing.width;
        }

        void AddWingTipObjects(Wing wing, Vector3 wingPos)
        {
            Vector3 wp = GetPositionOnWing(wing, wingPos, 1f);
            wp.z -= wing.endLength * 0.5f;
            wp.z -= 0.5f;

            for (int c1 = 0; c1 < 2; ++c1)
            {
                wp.x *= sides[c1];

                GameObject wingTip = new GameObject($"WingTip{c1}");
                wingTip.transform.position = wp;
                if (wings != null)
                {
                    wingTip.transform.SetParent(wings[c1].Transform);
                }
                else
                {
                    wingTip.transform.SetParent(RootObj.transform);
                }
                WingTipLocators.Add(wingTip);
            }
        }

        int CreateWingTips(int c, Wing wing, Vector3 wingPos)
        {
            Vector3 tipPos = GetPositionOnWing(wing, wingPos, 1);
            tipPos.z -= wing.endLength * 0.5f;

            float xOffset = rand.Float(0, 0.75f);
            float zOffset = -rand.Float(0.25f, 1f);
            float endOffset = rand.Float(0, 0.5f);
            float height = rand.Float(1, 1.5f);

            float lowerOffset = 0;
            float lowerHeight = 0;

            if(rand.Float() < 0.5f)
            {
                lowerHeight = height * 0.5f;
                lowerOffset = xOffset * 0.5f * Mathf.Sign(rand.Float(-1f, 1f));
            }

            for (int c1 = 0; c1 < 2; ++c1)
            {
                tipPos.x *= sides[c1];
                if(c1 == 0)
                {
                    //wtf?
                    tipPos.x += -0.1f * sides[c1];
                }
    
                c = MeshBuilder.VerticalWing(c, verts, tris, uvs, tipPos, Quaternion.identity, xOffset * sides[c1], zOffset, wing.endLength, wing.endLength * endOffset, height, 0);

                if (lowerHeight > 0)
                {
                    c = MeshBuilder.VerticalWing(c, verts, tris, uvs, tipPos, Quaternion.Euler(0, 0, 180), lowerOffset * sides[c1], zOffset, wing.endLength, wing.endLength * endOffset, lowerHeight, 0);
                }
            }

            SetFlag(ref configFlags, ConfigFlag.WingTipWings);

            return c;
        }

        int WingRibs(int c, Wing wing, Vector3 wingPos)
        {
            float xOffset = 0;
            float zOffset = 0;
            float endOffset = 0.5f;
            float height =  rand.Float(0.1f, 0.2f);

            int numRibs = rand.Int(1, 4);

            float percAdd = 1f / (numRibs+1);
            float perc = percAdd;

            for (int c2 = 0; c2 < numRibs; ++c2, perc += percAdd)
            {
                if(bodyConfiguration == BodyConfiguration.Boom)
                {
                    // avoid booms
                    if (perc >= 0.4f && perc <= 0.6f)
                        continue;
                }
                else if (bodyConfiguration == BodyConfiguration.FlyingWing &&
                        HasFlag(configFlags, ConfigFlag.WingEngines))
                {
                    // avoid engines
                    if (perc < 0.5f)
                        continue;
                }

                if (wingConfiguration == WingConfiguration.Delta ||
                    wing.endOffset.z == 0)
                {
                    // avoid flaps
                    if (perc < 0.7f)
                        continue;
                }

                float length = GetWingWidth(wing, perc);
                length -= 0.25f; // wing leading edge

                Vector3 ribPos = GetPositionOnWing(wing, wingPos, perc);
                ribPos.z -= length * 0.6f;
                ribPos.y += Mathf.Lerp(wing.baseHeight, wing.endHeight, perc);

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    ribPos.x *= sides[c1];
                    if (c1 == 0)
                    {
                        //wtf?
                        ribPos.x += -0.1f * sides[c1];
                    }
                    //c = VerticalWing(c, ribPos, xOffset * sides[c1], zOffset, length, length * endOffset, height, 0);

                    c = MeshBuilder.VerticalWing(c, verts, tris, uvs, ribPos, Quaternion.identity, xOffset * sides[c1], zOffset, length, length * endOffset, height, 0);
                }
            }

            return c;
        }

        int WingTubes(int c, Wing wing, Vector3 wingPos)
        {
            Vector3 pos = GetPositionOnWing(wing, wingPos, 1f);

            float radius = rand.Float(0.1f, 0.15f);
            float length = 1 + (wing.endLength * rand.Float(1.25f, 1.6f));

            pos.z -= length * 0.5f;
            pos.x += radius * 0.5f;

            for (int c1 = 0; c1 < 2; ++c1)
            {
                pos.x *= sides[c1];

                c = MeshBuilder.HollowTube(c, verts, tris, uvs, pos, Quaternion.identity, length, radius, radius, 0, 0);
            }

            return c;
        }

        PropEngineInfo CreatePropEngineInfo(LargeLaser.IRand rand, float length, float radius)
        {
            return new PropEngineInfo(rand)
            {
                length = length,
                radius = radius,
                propLength = rand.Float(1f, 1.5f),
                propWidth = 0.08f,
                rear = true,
                airIntakeLength = length * rand.Float(0.75f, 1.5f),
                airIntakeCornerRadius = rand.Float(0.1f, radius)
            };
        }

        void BodyDetails(Body body, Wing wing, Vector3 wingPos)
        {
            if (bodyConfiguration != BodyConfiguration.FlyingWing &&
                bodyConfiguration != BodyConfiguration.Centre &&
                !HasFlag(configFlags, ConfigFlag.HighFrontWings))
            {
                if (rand.Float() < 0.5f)
                {
                    float perc = wingPos.z + (wing.baseLength) + (body.length * 0.5f);

                    if (wingConfiguration == WingConfiguration.Forward &&
                        HasFlag(configFlags, ConfigFlag.HighSideAirIntakes))
                    {
                        perc += wing.baseLength * 0.25f;
                    }

                    perc /= body.length;

                    for (int c1 = 0; c1 < 2; ++c1)
                    {
                        detailsObjects.c = MeshBuilder.BodyPanel(detailsObjects.c, detailsObjects.verts, detailsObjects.tris, detailsObjects.uvs, body, perc, sides[c1]);
                    }
                }
            }
        }

        int WingEngines(int c, Body mainBody, Wing wing, Vector3 wingPos)
        {
            float radius = 0.3f;
            float percentAlongWing = 0.25f;

            Vector3 pos = GetPositionOnWing(wing, wingPos, percentAlongWing);

            pos.y += radius * 0.5f;

            float wingDepth = Mathf.Lerp(wing.baseLength, wing.endLength, percentAlongWing);

            float length = wingDepth * 0.5f;

            float finBaseLength = 0;
            float finEndLength = 0;
            float finHeight = 0;
            float finXOffset = 0;
            float finZOffset = 0;

            if(rand.Float() < 0.5f)
            {
                finBaseLength = length * 0.6f;
                finEndLength = rand.Float(0.1f, 0.25f);
                finHeight = rand.Float(0.7f, 1.25f);
                finXOffset = -rand.Float(0, 0.25f);
                finZOffset = -rand.Float(0, 0.5f);
            }

            if (rand.Float() < 0.5f)
            {
                PropEngineInfo prop = CreatePropEngineInfo(rand, length, radius);

                float wingWidth = Mathf.Lerp(wing.baseLength, wing.endLength, percentAlongWing);

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    pos.x *= sides[c1];

                    Vector3 enginePos = pos + Vector3.forward * ((wingWidth * -1f) + (length * 0.5f));

                    c = PropEngine(c, enginePos, prop);

                    if (finBaseLength > 0)
                    {
                        //c = VerticalWing(c, enginePos + Vector3.forward * finBaseLength * 0.7f + Vector3.up * radius, finXOffset * sides[c1], finZOffset, finBaseLength, finEndLength, finHeight, 0);

                        c = MeshBuilder.VerticalWing(c, verts, tris, uvs, enginePos + Vector3.forward * finBaseLength * 0.7f + Vector3.up * radius, Quaternion.identity, finXOffset * sides[c1], finZOffset, finBaseLength, finEndLength, finHeight, 0);
                    }
                }
            }
            else
            {
                EngineInfo engine = new EngineInfo(rand)
                {
                    length = length,
                    radius = radius,
                    funnelLength = 0.6f,
                    funnelEndHeight = 0.5f,
                    metal = metalObjects,
                };

                RoundedRectInfo roundedRect = new RoundedRectInfo()
                {
                    length = 0.5f,
                    thickness = 0.05f
                };

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    pos.x *= sides[c1];

                    Vector3 enginePos = pos + Vector3.forward * length * -1f;

                    c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                    float rectWidth = radius * 2;
                    c = MeshBuilder.RoundedRect(c, roundedRect, verts, tris, uvs, pos, Quaternion.identity, new Vector2(rectWidth, rectWidth) * 0.8f, new Vector2(rectWidth, rectWidth), rectWidth * 0.2f, radius);

                    if (finBaseLength > 0)
                    {
                        //c = VerticalWing(c, enginePos + Vector3.forward * finBaseLength * 0.6f + Vector3.up * radius, finXOffset * sides[c1], finZOffset, finBaseLength, finEndLength, finHeight, 0);
                        c = MeshBuilder.VerticalWing(c, verts, tris, uvs, enginePos + Vector3.forward * finBaseLength * 0.6f + Vector3.up * radius, Quaternion.identity, finXOffset * sides[c1], finZOffset, finBaseLength, finEndLength, finHeight, 0);
                    }

                    AddEngineLocator(c1, enginePos + Vector3.forward * engine.funnelLength * -0.75f);
                }
            }
            return c;
        }

        void AddEngineLocator(int c1, Vector3 pos)
        {
            GameObject engineLocator = new GameObject($"Engine{c1}");
            engineLocator.transform.position = pos;
            engineLocator.transform.SetParent(RootObj.transform);
            EngineLocators.Add(engineLocator);
        }

        int UnderWingEngines(int c, Body body, Wing wing, Vector3 wingPos)
        {
            float percentAlongWing = rand.Float(0.15f, 0.18f);

            float radius = rand.Float(0.4f, 0.6f);
            float length = GetWingWidth(wing, percentAlongWing);
            float angle = -Mathf.Atan2(wing.width, wing.endOffset.y) * Mathf.Rad2Deg;
            float frontRadius = rand.Float(0.25f, 0.4f);

            Vector3 pos = GetPositionOnWing(wing, wingPos, percentAlongWing);
            pos.y -= radius;
            pos.z += length * 0.5f;

            EngineInfo engine = new EngineInfo(rand)
            {
                length = length,
                radius = radius,
                funnelLength = 0.6f,
                funnelEndHeight = 1f,
                metal = metalObjects,
            };

            RoundedRectInfo roundedRect = new RoundedRectInfo()
            {
                length = 0.5f,
                thickness = 0.05f
            };

            for (int c1 = 0; c1 < 2; ++c1)
            {
                pos.x *= sides[c1];

                Vector3 enginePos = pos + Vector3.forward * length * -1f;

                c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                float rectWidth = radius * 2;
                c = MeshBuilder.RoundedRect(c, roundedRect, verts, tris, uvs, pos, Quaternion.Euler(0,0, angle * sides[c1]), new Vector2(rectWidth, rectWidth) * 0.8f, new Vector2(rectWidth, rectWidth), rectWidth * frontRadius, radius);

                AddEngineLocator(c1, enginePos + Vector3.forward * engine.funnelLength * -0.75f);
            }

            return c;
        }

        int BoomBody(int c, Body mainBody, Wing wing, Vector3 wingPos, List<Body> boomBodies)
        {
            float boomLength = mainBody.length;
            float percentAlongWing = rand.Float(0.4f, 0.6f);

            float dim1 = rand.Float(0.4f, 0.6f);

            float width;
            float height;

            if (rand.Float() < 0.5f)
            {
                width = dim1;
                height = dim1 * 0.5f;
            }
            else
            {
                height = dim1;
                width = dim1 * 0.5f;
            }

            List<Vector3> boomDims = new List<Vector3>()
            {
                new Vector3(0,0,0),
                new Vector3(width,height,0.1f),
                new Vector3(width,height,0.7f),
                new Vector3(0,0,1)
            };

            float boomOffset = rand.Float(-0.75f, -0.9f);

            Vector3 pos = wingPos;
            pos.x += wing.width * percentAlongWing;
            pos.y += wing.endOffset.y * percentAlongWing;
            pos.z += boomLength * boomOffset;

            for (int c1 = 0; c1 < 2; ++c1)
            {
                Body body = new Body();
                body.dims = boomDims;
                body.length = boomLength;
                body.offset = Vector3.forward * pos.z + Vector3.right * pos.x * sides[c1] + Vector3.up * pos.y;
                body.lowerInflate = new Vector2(0, rand.Float(0, 0.5f));
                boomBodies.Add(body);

                c = MeshBuilder.Body(c, verts, tris, uvs, body);
            }

            return c;
        }

        int CenterBody(int c, Body body)
        {
            float stickLength = rand.Float(1f, 2f);

            // stick poking out of the back
            //c = Tube(c, body.offset + Vector3.forward * -stickLength, stickLength, body.dims[0].x, body.dims[0].y, 1, 0);

            c = MeshBuilder.HollowTube(c, verts, tris, uvs, body.offset + Vector3.forward * -stickLength, Quaternion.identity, stickLength, body.dims[0].x, body.dims[0].y, 1, 0);

            float angle = 0;
            float perc = 0.5f;

            bool onBody = true;

            if (onBody)
            {
                perc = rand.Float(0.45f, 0.55f);
                angle = rand.Float(-20, 20);

                if (angle > 0f)
                {
                    SetFlag(ref configFlags, ConfigFlag.LowSideAirIntakes);
                }
                else
                {
                    SetFlag(ref configFlags, ConfigFlag.HighSideAirIntakes);
                }
            }
            else
            {
                angle = 20;
            }

            float intakeAngle = 0f;
            if (wingConfiguration != WingConfiguration.Delta)
            {
                intakeAngle = angle * 0.1f;
            }

            float length = body.length * perc;

            float engineRadius = rand.Float(0.3f, 0.5f);

            Vector2 radius = new Vector2(engineRadius, engineRadius);

            //var dim = GetDims(body.dims, perc);
            var dim = MeshBuilder.GetDims(body.dims, perc);

            float width = rand.Float(0.7f, 1f);
            float height = rand.Float(0.7f, 1f);

            Vector3 ray = new Vector3(width * 0.5f, 0, 0);
            ray -= new Vector3(radius.x, 0, length);
            float yAngle = Mathf.Atan2(ray.x, ray.z) * 0.5f;
            float engineLength = stickLength * 0.5f;

            RoundedRectInfo roundedRectInfo = new RoundedRectInfo()
            {
                length = length,
                thickness = 0.1f
            };

            EngineInfo engine = new EngineInfo(rand)
            {
                length = engineLength,
                radius = radius.x,
                funnelLength = 0.5f,
                funnelEndHeight = 1f,
                metal = metalObjects
            };


            for (int c1 = 0; c1 < 2; ++c1)
            {
                Vector3 p1 = Vector3.right * ((dim.x + width) * 0.5f) * sides[c1] + Vector3.forward * length * -0.8f;

                if (!onBody)
                {
                    p1 += Vector3.up * (-radius.y - 0.1f);
                }

                c = MeshBuilder.RoundedRect(c, roundedRectInfo, verts, tris, uvs, p1, Quaternion.Euler(intakeAngle, yAngle * sides[c1], angle * sides[c1] * -1), new Vector2(width, height), radius * 2, 0.2f, radius.x * 0.9f);

                Vector3 enginePos = p1 + Vector3.forward * -engineLength;

                c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                AddEngineLocator(c1, enginePos + Vector3.forward * engine.funnelLength * -0.75f);

                SetFlag(ref configFlags, ConfigFlag.SideEngines);
            }

            if (rand.Float() < 0.5f)
            {
                float bulgeLength = length * rand.Float(0.7f, 0.9f);
                float bulgeHeight = rand.Float(0.35f, 0.5f);

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    float bulge = 0.5f;
                    Vector3 p1 = Vector3.right * ((dim.x) * 0.5f) * sides[c1] + Vector3.forward * bulgeLength * -0.9f + Vector3.up * bulge * bulgeHeight;
                    c = MeshBuilder.HollowTube(c, verts, tris, uvs, p1, Quaternion.identity, bulgeLength, bulge, bulge * 0.5f, 0, 0);
                }
            }

            return c;
        }

        int Engines(int c, Body body, int xEngines, int yEngines)
        {
            if (HasFlag(configFlags, ConfigFlag.BodyEngines))
            {
                float rad = rand.Float(0.4f, 0.6f);
                float length = rand.Float(1.5f, 2f);

                BoxInfo box = new BoxInfo()
                {
                    width = 0.2f,
                    height = rad * 0.5f,
                    topLength = length * 0.75f,
                    bottomLength = length,
                };

                EngineInfo engine = new EngineInfo(rand)
                {
                    length = length,
                    radius = rad,
                    funnelLength = 0.5f,
                    funnelEndHeight = 1f,
                    metal = metalObjects
                };

                float perc = 1f / body.length;
                Vector3 dir = Vector3.up + Vector3.right;
                Vector3 pos = GetPositionOnBody(body, dir, perc);
                float angle = 45f;
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    pos.x *= sides[c1];
                    dir.x *= sides[c1];

                    Vector3 enginePos = pos + dir * rad;

                    c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                    box.preRotation = Quaternion.Euler(0, 0, angle * sides[c1] * -1);
                    c = MeshBuilder.Box(c, verts, tris, uvs, pos, Quaternion.identity, box);

                    AddEngineLocator(c1, enginePos + Vector3.forward * engine.funnelLength * -0.75f);
                }
            }
            else if (xEngines == 0)
            {

            }
            else if (xEngines == yEngines)
            {
                float rad = body.dims[0].y;

                if (bodyConfiguration == BodyConfiguration.Boom && rand.Float() < 0.5f)
                {
                    PropEngineInfo prop = CreatePropEngineInfo(rand, 1, rad);

                    c = PropEngine(c, Vector3.forward * ((body.length * -0.5f) - 0.1f), prop);
                }
                else
                {
                    EngineInfo engine = new EngineInfo(rand)
                    {
                        length = 1,
                        radius = rad,
                        funnelLength = 0.5f,
                        funnelEndHeight = 1f,
                        metal = metalObjects
                    };

                    Vector3 enginePos = Vector3.forward * ((body.length * -0.5f) - 0.1f);

                    c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                    AddEngineLocator(0, enginePos + Vector3.forward * engine.funnelLength * -0.75f);
                }
            }
            else if (xEngines > yEngines)
            {
                float rad = body.dims[0].y;

                EngineInfo engine = new EngineInfo(rand)
                {
                    length = 1,
                    radius = rad,
                    funnelLength = 0.5f,
                    funnelEndHeight = 1f,
                    metal = metalObjects
                };

                for (int c1 = 0; c1 < xEngines; ++c1)
                {
                    Vector3 enginePos = Vector3.forward * ((body.length * -0.5f) - 0.1f) + Vector3.right * rad * sides[c1];

                    c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                    AddEngineLocator(c1, enginePos + Vector3.forward * engine.funnelLength * -0.75f);
                }
            }
            else
            {
                float rad = body.dims[0].x;

                EngineInfo engine = new EngineInfo(rand)
                {
                    length = 1,
                    radius = rad,
                    funnelLength = 0.5f,
                    funnelEndHeight = 1f,
                    metal = metalObjects
                };

                for (int c1 = 0; c1 < yEngines; ++c1)
                {
                    Vector3 enginePos = Vector3.forward * ((body.length * -0.5f) - 0.1f) + Vector3.up * rad * sides[c1];

                    c = MeshBuilder.EngineHousing(c, verts, tris, uvs, enginePos, engine);

                    AddEngineLocator(c1, enginePos + Vector3.forward * engine.funnelLength * -0.75f);
                }
            }

            c = MeshBuilder.Disc(c, verts, tris, uvs, Vector3.forward * body.length * -0.5f, Quaternion.Euler(-90, 0, 0), body.dims[0].x, body.dims[0].y);

            return c;
        }

        int AirIntakes(int c, Body body, Wing wing)
        {
            if (bodyConfiguration == BodyConfiguration.Centre)
            {
                return c;
            }


            int num;

            if (bodyConfiguration == BodyConfiguration.Boom ||
                bodyConfiguration == BodyConfiguration.FlyingWing ||
                bodyConfiguration == BodyConfiguration.ArrowHead ||
                HasFlag(configFlags, ConfigFlag.UnderWingEngines))
            {
                num = rand.Int(0, 1);
            }
            else
            {
                num = rand.Int(1, 3);
            }

            if (num >= 2)
            {
                List<Vector2> possibleRanges = new List<Vector2>()
            {
                new Vector2(wing.wingHeightOfBody, 1),
                new Vector2(-1, wing.wingHeightOfBody)
            };

                Vector2 range = Vector2.zero;
                float largest = 0;
                foreach (var pr in possibleRanges)
                {
                    float size = pr.y - pr.x;
                    if (size > largest)
                    {
                        largest = size;
                        range = pr;
                    }
                }


                float positionOnBody = Mathf.Lerp(range.x, range.y, 0.5f);
                float asPercent = (positionOnBody + 1f) * 0.5f;

                if (asPercent < 0.5f)
                {
                    SetFlag(ref configFlags, ConfigFlag.LowSideAirIntakes);
                }
                else
                {
                    SetFlag(ref configFlags, ConfigFlag.HighSideAirIntakes);
                }

                Vector3 upDir = Vector3.Lerp(Vector3.down, Vector3.up, asPercent);

                Vector3 dir = upDir + Vector3.right;

                float angle = Mathf.Atan2(dir.y, dir.x);
                angle *= Mathf.Rad2Deg;

                Vector3 pos = GetPositionOnBody(body, dir, 0.5f);
                //var dims = GetDims(body.dims, 0.5f);
                var dims = MeshBuilder.GetDims(body.dims, 0.5f);
                float length = body.length * 0.4f;
                float width = rand.Float(0.5f, 1.5f);
                float height = dims.y;
                Vector3 airDims = new Vector3(width, height, length);
                float rectRadius = 0.2f;

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    pos.x = 0f;
                    c = MeshBuilder.RoundedRect(c, verts, tris, uvs, body, upDir + Vector3.right * sides[c1], pos + Vector3.forward * length * -0.75f, Quaternion.Euler(0, 0, angle * sides[c1]), airDims, rectRadius, 0.1f); ;
                }
            }

            if (num == 1 || num == 3)
            {
                Vector3 upDir = Vector3.down;

                float length = body.length * 0.5f;

                float perc = 0.5f;
                Vector3 pos = GetPositionOnBody(body, upDir, perc);
                //var dims = GetDims(body.dims, perc);
                var dims = MeshBuilder.GetDims(body.dims, perc);

                float width = 0.5f;
                float height = dims.x;
                Vector3 airDims = new Vector3(width, height, length);
                float rectRadius = 0.2f;

                float lengthAsPercent = length / body.length;
                Vector3 frontPos = GetPositionOnBody(body, upDir, perc + (lengthAsPercent * 0.5f));

                pos.y = frontPos.y;

                pos.x = 0f;
                c = MeshBuilder.RoundedRect(c, verts, tris, uvs, body, upDir, pos + Vector3.forward * length * -0.5f, Quaternion.Euler(0, 0, 90), airDims, rectRadius, 0.1f);

                SetFlag(ref configFlags, ConfigFlag.BellyAirIntake);
            }

            return c;
        }

        int PropEngine(int c, Vector3 pos, PropEngineInfo prop)
        {
            float length = prop.length;
            float radius = prop.radius;
            bool rear = prop.rear;

            Quaternion rotation = rear ? Quaternion.Euler(0, 180, 0) : Quaternion.identity;

            float frontRad = rear ? 0 : 0.5f;
            float rearRad = rear ? 0.5f : 0;
            //c = Tube(c, pos, length, radius, radius, frontRad, rearRad);

            c = MeshBuilder.HollowTube(c, verts, tris, uvs, pos, Quaternion.identity, length, radius, radius, frontRad, rearRad);

            if (prop.airIntakeLength > 0)
            {
                RoundedRectInfo roundedRectInfo = new RoundedRectInfo()
                {
                    length = prop.airIntakeLength,
                    thickness = 0.05f
                };

                c = MeshBuilder.RoundedRect(c, roundedRectInfo, verts, tris, uvs, pos + Vector3.forward * length * 0.5f, Quaternion.identity, Vector2.one * radius * 2, Vector2.one * radius * 2, prop.airIntakeCornerRadius, radius * 0.9f);
            }

            float axleRadius = 0.1f;
            float axleLength = 0.3f;
            float axlePos = rear ? (axleLength * -0.5f) : (length - (axleLength * 0.5f));
            //c = Tube(c, pos + Vector3.forward * axlePos, axleLength, axleRadius, axleRadius, 1, 1);
            c = MeshBuilder.HollowTube(c, verts, tris, uvs, pos + Vector3.forward * axlePos, Quaternion.identity, axleLength, axleRadius, axleRadius, 1, 1);

            float coneLength = radius;
            float conePos = rear ? -0.1f : (length + 0.1f);
            c = MeshBuilder.Cone(c, verts, tris, uvs, pos + Vector3.forward * conePos, rotation * Quaternion.Euler(90, 0, 0), coneLength, radius * 0.5f);

            {
                float propPos = rear ? -0.1f * 0.5f : length;

                SubObject propObject = new SubObject();
                propObject.Create("Prop", RootObj.transform, pos + Vector3.forward * propPos, Quaternion.identity, BodyMaterial);

                int propC = 0;
                float angle = 0;
                float angleAdd = 360f / (prop.props * 2);
                for (int c1 = 0; c1 < prop.props; ++c1, angle += angleAdd)
                {
                    propC = MeshBuilder.Prop(propC, propObject.verts, propObject.tris, propObject.uvs, Vector3.zero, Quaternion.Euler(0, 0, angle), prop.propLength, prop.propWidth);
                }

                propObject.Publish();

                if(props == null)
                {
                    props = new List<SubObject>();
                }

                props.Add(propObject);
            }

            return c;
        }

        int TailWings(int c, Body body, VerticalFin fin)
        {
            if (tailConfiguration != TailConfiguration.V &&
                tailConfiguration != TailConfiguration.NoWing)
            {
                Wing tailWings = new Wing()
                {
                    frontCurve = 0,
                    baseLength = fin.length.x * 0.8f,
                    endLength = fin.length.x * 0.25f,
                    width = fin.length.x,
                    endOffset = new Vector3(0, 0, -1),
                };

                float lengthAsPercent = tailWings.baseLength / body.length;
                float zPosOnBody = lengthAsPercent;

                Vector3 tailPos;
                Vector3 wingStart;
                Vector3 wingEnd;


                if (tailConfiguration == TailConfiguration.T)
                {
                    // tail fins up upright
                    float percentUpTail = rand.Float(0.7f, 0.8f);

                    tailWings.baseLength = Mathf.Lerp(fin.length[0], fin.length[1], percentUpTail);
                    tailWings.endLength = tailWings.baseLength * 0.25f;
                    zPosOnBody = 0;

                    tailPos = GetPositionOnBody(body, Vector3.up, zPosOnBody);
                    tailPos.y += fin.height * percentUpTail;
                    tailPos.z = fin.zPos;
                    tailPos.z += fin.endOffset.z * percentUpTail;
                    wingStart = tailPos;
                    wingEnd = tailPos;
                }
                else
                {
                    // fins on body
                    tailPos = GetPositionOnBody(body, Vector3.right, zPosOnBody);
                    tailPos.z += (tailWings.baseLength * -0.5f);

                    wingStart = GetPositionOnBody(body, Vector3.right, zPosOnBody - (lengthAsPercent * 0.5f));
                    wingEnd = GetPositionOnBody(body, Vector3.right, zPosOnBody + (lengthAsPercent * 0.5f));

                    if (bodyConfiguration == BodyConfiguration.Centre)
                    {
                        // TODO: should be side engine radius
                        wingStart.x += 0.5f;
                        wingEnd.x += 0.5f;
                    }
                    else if (bodyConfiguration == BodyConfiguration.ArrowHead)
                    {
                        // to account for narrow waist
                        wingStart.x -= 0.1f;
                        wingEnd.x -= 0.1f;
                    }
                }

                c = Wings(c, tailWings, tailPos, wingStart, wingEnd, false);
            }

            return c;
        }

        int FrontWings(int c, Body body, Wing mainWing)
        {
            Wing frontWing = new Wing()
            {
                frontCurve = rand.Float(-0.1f, 0),
                baseLength = 0.75f,
                endLength = rand.Float(0.25f, 0.5f),//0.5f,
                width = rand.Float(1.5f, 2f),//2,
                endOffset = new Vector3(0, -rand.Float(0.25f, 0.5f), -rand.Float(0.5f, 1.5f)),
            };

            frontWing.wingHeightOfBody = (mainWing.wingHeightOfBody * -1) * 0.75f;

            Vector3 anchor = Vector3.right + Vector3.up * frontWing.wingHeightOfBody;

            Vector3 wingPos = GetPositionOnBody(body, anchor, 0.75f);
            wingPos.z += (frontWing.baseLength * -0.5f);

            float wingPercentOfBody = frontWing.baseLength / body.length;
            Vector3 wingStart = GetPositionOnBody(body, anchor, 0.75f - (wingPercentOfBody * 0.5f));
            Vector3 wingEnd = GetPositionOnBody(body, anchor, 0.75f + (wingPercentOfBody * 0.5f));

            wingStart.x -= 0.1f;
            wingEnd.x -= 0.1f;

            c = Wings(c, frontWing, wingPos, wingStart, wingEnd, false);

            if (frontWing.wingHeightOfBody < 0)
            {
                SetFlag(ref configFlags, ConfigFlag.LowFrontWings);
            }
            else
            {
                SetFlag(ref configFlags, ConfigFlag.HighFrontWings);
            }

            return c;
        }

        int Canopy(int c, Body body, int seed)
        {
            SubObject canopy = new SubObject();
            canopy.Create("Canopy", RootObj.transform, Vector3.zero, Quaternion.identity, BodyMaterial);

            float perc = 0.5f;
            float widthPerc = 0.75f;

            if (type == Type.Attack)
            {
                perc = 0.4f;
                widthPerc = 1;
            }

            float minHeight = 0.5f;
            float maxHeight = 0.7f;

            if (bodyConfiguration == BodyConfiguration.FlyingWing)
            {
                minHeight = 0.4f;
                maxHeight = 0.4f;
            }

            float height = rand.Float(minHeight, maxHeight);
            float length = body.length * perc;

            float start = 0.6f - perc;
            float end = start + perc;

            Vector3 p1 = GetPositionOnBody(body, Vector3.up + Vector3.right, start);
            Vector3 p2 = GetPositionOnBody(body, Vector3.up + Vector3.right, end);

            Vector3 p3 = GetPositionOnBody(body, Vector3.up, end);

            float h = p3.y;

            float w = Mathf.Lerp(p1.x, p2.x, 0.5f);

            Body canopyBody = new Body()
            {
                length = length,
                lowerInflate = new Vector2(0, 1),

                dims = new List<Vector3>()
                {
                    new Vector3(w * widthPerc * 0.5f, 0.1f, 0),
                    new Vector3(w * widthPerc * 1f, height, 0.75f),
                    new Vector3(w * widthPerc * 0.5f, 0.1f, 1)
                },

                offset = Vector3.forward * ((body.length * start * 0.5f) - (length * 0.5f)) + Vector3.up * (h + height * -0.4f)
            };

            canopy.c = MeshBuilder.Body(canopy.c, canopy.verts, canopy.tris, canopy.uvs, canopyBody);

            // airtake on canopy
            if (type != Type.Attack && rand.Float() < 0.5f)
            {
                Vector3 bp = GetPositionOnBody(canopyBody, Vector3.up, 0.5f);

                float airRadius = canopyBody.dims[1].x;
                float airLength = length * 0.5f;
                Vector3 intakePos = canopyBody.offset + Vector3.forward * airLength * 0.25f;
                intakePos.y = bp.y;

                canopy.c = MeshBuilder.RoundedRect(canopy.c, canopy.verts, canopy.tris, canopy.uvs, canopyBody, Vector3.up, intakePos, Quaternion.identity, new Vector3(airRadius, airRadius, airLength), 0.08f, 0.02f);
            }

            canopy.SetMaterialArg("_CanopyRatio", 1f);

            var texture = LargeLaser.TextureManager.Instance.GenerateCanopy(seed);
            canopy.SetMaterialArg("_CanopyTex", texture);

            canopy.Publish();


            if (type == Type.Attack &&
                bodyConfiguration != BodyConfiguration.FlyingWing)
            {
                if (rand.Float() < 0.5f)
                {
                    c = CanopyTurret(c, canopyBody);
                }
            }

            return c;
        }

        int CanopyTurret(int c, Body body)
        {
            float height = 0.7f;
            float radius = 0.5f;

            Vector3 pos = body.offset + Vector3.up * height * 0.5f + Vector3.forward * radius * 0;

            c = MeshBuilder.HollowTube(c, verts, tris, uvs, pos, Quaternion.Euler(90, 0, 0), height, radius, radius, 0, 0);


            SubObject turret = new SubObject();
            turret.Create("CanopyTurret", RootObj.transform, pos, Quaternion.identity, BodyMaterial);

            // base
            radius *= 0.9f;
            height *= 0.4f;
            turret.c = MeshBuilder.HollowTube(turret.c, turret.verts, turret.tris, turret.uvs, Vector3.up * height * 0.4f, Quaternion.Euler(90, 0, 0), height, radius, radius, 0, 0);

            // housing
            height *= 1.5f;
            turret.c = MeshBuilder.HollowTube(turret.c, turret.verts, turret.tris, turret.uvs, Vector3.up * radius * 0.25f + Vector3.right * height * -0.5f, Quaternion.Euler(0, 90, 0), height, radius, radius * 0.75f, 0, 0);

            turret.Publish();


            height = 1;
            radius *= 0.4f;
            
            Vector3 verticalPos = pos + Vector3.up * radius * 1.33f;

            SubObject vertical = new SubObject();
            vertical.Create("Elevation", turret.Transform, verticalPos, Quaternion.identity, BodyMaterial);


            SubObject verticalMetal = new SubObject();
            verticalMetal.Create("ElevationMetal", vertical.Transform, verticalPos, Quaternion.identity, MetalMaterial);


            vertical.c = MeshBuilder.HollowTube(vertical.c, vertical.verts, vertical.tris, vertical.uvs, Vector3.right * height * -0.5f, Quaternion.Euler(0, 90, 0), height, radius, radius, 0, 0);


            // guns
            int numRows = rand.Int(1, 2);

            float housingLength = rand.Float(0.3f, 0.5f);
            float housingRadius = (numRows == 1) ? 0.09f : 0.07f;
            CannonInfo cannon = new CannonInfo()
            {
                housingLength = housingLength,
                housingRadius = housingRadius,
                barrelLength = housingLength * rand.Float(0.4f, 0.75f),
                barrelRadius = housingRadius * 0.5f
            };


            float heightOffset = radius * ((numRows == 1) ? 0 : 0.5f);

            for (int c2 = 0; c2 < numRows; ++c2)
            {
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    Vector3 cannonPos = Vector3.right * height * 0.3f * sides[c1] + Vector3.up * heightOffset;

                    vertical.c = MeshBuilder.Tube(vertical.c, vertical.verts, vertical.tris, vertical.uvs, cannonPos, Quaternion.Euler(0, 180, 0), cannon.housingLength, cannon.housingRadius, Vector2.one * cannon.housingRadius, 0.05f);

                    verticalMetal.c = MeshBuilder.Tube(verticalMetal.c, verticalMetal.verts, verticalMetal.tris, verticalMetal.uvs, cannonPos - Vector3.forward * cannon.housingLength, Quaternion.Euler(0, 180, 0), cannon.barrelLength, cannon.barrelRadius, Vector2.one * cannon.barrelRadius, 0.01f);
                }

                heightOffset -= radius;
            }

            vertical.Publish();
            verticalMetal.Publish();

            return c;
        }

        int DuelTail(int c, Body body)
        {
            float length = rand.Float(0.6f, 1f);
            float mult = 1f;

            if(bodyConfiguration == BodyConfiguration.ArrowHead)
            {
                mult = 0.75f;
            }

            Wing tailWings = new Wing()
            {
                baseLength = length,
                endLength = length,
                width = rand.Float(1.8f, 2.2f),
                endOffset = new Vector3(0, 0, -rand.Float(0, 1f)),
                wingHeightOfBody = rand.Float(-0.5f, 0.5f)
            };

            tailWings.width *= mult;

            float lengthAsPercent = tailWings.baseLength / body.length;
            float zPosOnBody = lengthAsPercent;

            Vector3 anchor = Vector3.right + Vector3.up * tailWings.wingHeightOfBody;

            // fins on body
            Vector3 tailPos = GetPositionOnBody(body, anchor, zPosOnBody);
            tailPos.z += (tailWings.baseLength * -0.5f);

            Vector3 wingStart = GetPositionOnBody(body, anchor, zPosOnBody - (lengthAsPercent * 0.5f));
            Vector3 wingEnd = GetPositionOnBody(body, anchor, zPosOnBody + (lengthAsPercent * 0.5f));

            if (bodyConfiguration == BodyConfiguration.ArrowHead)
            {
                wingStart.x = 0;
                wingEnd.x = 0;
            }

            c = Wings(c, tailWings, tailPos, wingStart, wingEnd, false);

            tailPos += tailWings.endOffset;
            float tailHeight = rand.Float(2f, 2.5f) * mult;
            float tailBaseLength = tailWings.endLength;
            float tailEndLength = tailBaseLength * rand.Float(0.8f, 1f);
            float tailXOffset = rand.Float(0, 0.5f);
            float tailZOffset = -rand.Float(0, 1f);
            for (int c1 = 0; c1 < 2; ++c1)
            {
                tailPos.x *= sides[c1];
                //c = VerticalWing(c, tailPos + Vector3.right * tailWings.width * sides[c1], tailXOffset * sides[c1], tailZOffset, tailBaseLength, tailEndLength, tailHeight, 0);
                c = MeshBuilder.VerticalWing(c, verts, tris, uvs, tailPos + Vector3.right * tailWings.width * sides[c1], Quaternion.identity, tailXOffset * sides[c1], tailZOffset, tailBaseLength, tailEndLength, tailHeight, 0);
            }
            return c;
        }

        int BoomTail(int c, List<Body> boomBodies)
        {
            bool highTail = rand.Float() < 0.5f;

            VerticalFin fin = new VerticalFin();
            fin.height = rand.Float(1.5f, 2f);
            fin.length = new Vector2(1, 0.5f);
            fin.dir = new Vector2(0, 1);
            fin.endOffset = new Vector3(0, 0, -rand.Float(1f, 1.5f));
            fin.zPercent = boomBodies[0].dims[1].z;

            if (rand.Float() < 0.5f)
            {
                fin.detailPercent = rand.Float(0.2f, 0.7f);
            }

            // upright fins
            float offset = 0;
            if(!highTail && rand.Float() < 0.5f)
            {
                offset = rand.Float(-1f, 1f);
            }
            int c1 = 0;
            foreach (var boom in boomBodies)
            {
                fin.detailSide = c1 + 1;
                fin.endOffset.x = offset * sides[c1];
                c = CreateUprightFin(c, 1, boom, fin);
                ++c1;
            }

            // single wing between uprights
            {
                float percentUpTail = highTail ? 0.9f : 0f;

                float len = Mathf.Lerp(fin.length[0], fin.length[1], percentUpTail);

                Wing boomWing = new Wing()
                {
                    baseLength = len,
                    endLength = len,
                    width = boomBodies[0].offset.x
                };

                Vector3 tailPos = fin.outputPos;
                tailPos.x = 0;
                tailPos.y += fin.height * percentUpTail;
                tailPos.z += fin.endOffset.z * percentUpTail;

                Vector3 wingStart = tailPos;
                Vector3 wingEnd = tailPos;

                c = Wings(c, boomWing, tailPos, wingStart, wingEnd, false);
            }

            // downwards fins
            // TODO:
            if (!highTail)
            {
                if (rand.Float() < 0.5f)
                {
                    fin.height *= -0.5f;
                    fin.length *= 0.5f;
                    fin.endOffset *= 0.5f;
                    fin.dir *= -0.5f;
                    fin.zPercent = boomBodies[0].dims[1].z * 1.5f;
                    fin.detailPercent = 0;
                    fin.endOffset.x = -fin.endOffset.x;
                    c1 = 0;
                    foreach (var boom in boomBodies)
                    {
                        fin.endOffset.x *= sides[c1];

                        c = CreateUprightFin(c, 1, boom, fin);

                        ++c1;
                    }
                }
            }

            return c;
        }

        int CreateFlyingWingTail(int c, Body body)
        {
            if (rand.Float() < 0.5f)
            {
                float length = rand.Float(1f, 1.5f);
                float height = length * 0.5f;

                if (HasFlag(configFlags, ConfigFlag.WingEngines))
                {
                    c = MeshBuilder.HollowTube(c, verts, tris, uvs, Vector3.forward * body.length * -0.5f, Quaternion.Euler(0, 90, 0), 0.1f, length, height, 0, 0);
                }
                else
                {
                    for (int c1 = 0; c1 < 2; ++c1)
                    {
                        c = MeshBuilder.HollowTube(c, verts, tris, uvs, Vector3.right * body.dims[1].x * sides[c1] + Vector3.forward * body.length * -0.5f, Quaternion.Euler(0, 90, 0), 0.1f, length, height, 0, 0);
                    }
                }
            }

            return c;
        }

        int CreateTail(int c, Body body)
        {
            int numUprights = 1;

            VerticalFin fin = new VerticalFin();
            fin.height = rand.Float(1.5f, 2f);
            fin.length = new Vector2(rand.Float(1.5f, 2.25f), rand.Float(0.1f, 0.5f));
            fin.endOffset = new Vector3(0, 0, -rand.Float(0.5f, 1.5f));
            fin.dir = new Vector2(0, 1);
            fin.zPercent = (fin.length[0] / body.length) * 0.5f;

            if (tailConfiguration == TailConfiguration.V)
            {
                numUprights = 2;
                fin.endOffset.x = rand.Float(2f, 2.5f);
                fin.dir = (Vector3.up * 0.5f + Vector3.right * 0.5f);
            }
            else if (tailConfiguration == TailConfiguration.Twin)
            {
                numUprights = 2;
                fin.endOffset.x = rand.Float(0.25f, 0.75f);
                fin.dir = (Vector3.up + Vector3.right * 0.75f);
            }
            else
            {
                if (rand.Float() < 0.5f)
                {
                    fin.detailPercent = rand.Float(0.15f, 0.25f);
                }
            }

            if (tailConfiguration != TailConfiguration.T)
            {
                fin.frontCurve = -rand.Float(0, 0.5f);
            }

            c = CreateUprightFin(c, numUprights, body, fin);

            c = TailWings(c, body, fin);

            return c;
        }

        int CreateUprightFin(int c, int numUprights, Body body, VerticalFin fin)
        {
            float frontCurve = fin.frontCurve;
            float baseLength = fin.length[0];
            float endLength = fin.length[1];
            float positionZAsPercent = fin.zPercent;

            if (numUprights == 1)
            {
                Vector3 tailPos = GetPositionOnBody(body, fin.dir, positionZAsPercent);

                //c = VerticalWing(c, tailPos, fin.endOffset.x, fin.endOffset.z, baseLength, endLength, fin.height, frontCurve);
                c = MeshBuilder.VerticalWing(c, verts, tris, uvs, tailPos, Quaternion.identity, fin.endOffset.x, fin.endOffset.z, baseLength, endLength, fin.height, frontCurve);

                fin.zPos = tailPos.z;

                fin.outputPos = tailPos;

                // tube at top of tail
                if (bodyConfiguration != BodyConfiguration.Boom &&
                    rand.Float() < 0.5f)    
                {
                    float tubeLength = (endLength + 1) * rand.Float(1.25f, 1.5f);
                    float tubeRadius = rand.Float(0.07f, 0.1f);
                    Vector3 tubePos = tailPos + Vector3.up * (fin.height + tubeRadius);
                    tubePos.z += fin.endOffset.z + (tubeLength * -0.5f);
                    c = MeshBuilder.HollowTube(c, verts, tris, uvs, tubePos, Quaternion.identity, tubeLength, tubeRadius, tubeRadius, 0, 0);
                }

                if (fin.endOffset.x == 0)
                {
                    TailFinDetail(fin, tailPos, baseLength, endLength);
                }
            }
            else
            {
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    fin.dir.x *= sides[c1];

                    Vector3 tailPos = GetPositionOnBody(body, fin.dir, positionZAsPercent);

                    if (bodyConfiguration == BodyConfiguration.Centre)
                    {
                        // TODO: side tube radius:
                        tailPos.x += 0.5f * sides[c1];
                    }

                    //c = VerticalWing(c, tailPos, fin.endOffset.x * sides[c1], fin.endOffset.z, baseLength, endLength, fin.height, frontCurve);
                    c = MeshBuilder.VerticalWing(c, verts, tris, uvs, tailPos, Quaternion.identity, fin.endOffset.x * sides[c1], fin.endOffset.z, baseLength, endLength, fin.height, frontCurve);
                }
            }

            return c;
        }

        void TailFinDetail(VerticalFin fin, Vector3 tailPos, float baseLength, float endLength)
        {
            if (fin.detailPercent == 0)
                return;

            float detailPerc = fin.detailPercent;

            float widthAt = Mathf.Lerp(baseLength, endLength, detailPerc);

            float detailLength = (widthAt + (0.75f)) * 0.5f;
            float detailHeight = detailLength * 1f;
            float detailPos = (widthAt * 0.5f) + (detailLength * -0.5f);
            detailPos += fin.endOffset.z * detailPerc * 0.75f;

            for (int c1 = 0; c1 < 2; ++c1)
            {
                if (fin.detailSide != 0)
                {
                    if ((c1 == 1 && fin.detailSide == 1) ||
                        (c1 == 0 && fin.detailSide == 2))
                    {
                        // don't put detail on inside of boom fin
                        continue;
                    }
                }

                Vector3 pos = tailPos + Vector3.forward * detailPos + Vector3.right * 0.1f * sides[c1] + Vector3.up * ((fin.height * detailPerc) - (detailHeight * 0.5f));

                detailsObjects.c = MeshBuilder.Quad(detailsObjects.c, detailsObjects.verts, detailsObjects.tris, detailsObjects.uvs, pos, Quaternion.Euler(0, -90 * sides[c1], 0), detailLength, detailHeight);
            }
        }

        List<Texture2D> CreateMissileTextures(int seed)
        {
            List<Texture2D> res = new List<Texture2D>();

            LargeLaser.IRand random = LargeLaser.Rand.Create(seed);

            foreach (var p in missileTextureMap)
            {
                var missile = TextureManager.Instance.GenerateMissile(random.Int());
                res.Add(missile);
            }

            return res;
        }

        Texture2D GetMissileTexture(List<Texture2D> textures, GameObject gameObject)
        {
            foreach (var p in missileTextureMap)
            {
                foreach (var id in p.Value)
                {
                    if (id == gameObject.GetEntityId())
                    {
                        return textures[p.Key];
                    }
                }
            }

            throw new System.Exception("Plane GetMissileTexture. No texture found");
        }

        MissileInfo CreateMissileInfo()
        {
            int tex = missileTextureMap.Count;

            MissileInfo missile = new MissileInfo()
            {
                length = rand.Float(1.5f, 2.5f),
                radius = rand.Float(0.05f, 0.12f),
                rearFinBaseLength = rand.Float(0.2f, 0.3f),
                frontFinBaseLength = rand.Float(0.1f, 0.6f),
                finHeight = rand.Float(0.1f, 0.2f),
                frontfinPosition = rand.Float(0.5f, 0.8f),
                textureIndex = tex
            };
            missile.coneLength = missile.length * rand.Float(0.02f, 0.2f);

            if (missile.radius > 0.05f && rand.Float() < 0.5f)
            {
                missile.noseLength = missile.length * 0.2f;
            }

            missileTextureMap[tex] = new List<EntityId>();

            return missile;
        }

        void AssignTexture(SubObject subObject, MissileInfo missile)
        {
            missileTextureMap[missile.textureIndex].Add(subObject.Transform.gameObject.GetEntityId());
        }

        int FuelTanks(int c, Wing wing, Vector3 wingPos, Body body)
        {
            if (bodyConfiguration == BodyConfiguration.FlyingWing)
            {
                return c;
            }

            float radius = 0.3f;

            float percAlongWing = (radius * 2.5f) / wing.width;

            if (HasFlag(configFlags, ConfigFlag.SideEngines))
            {
                percAlongWing += 0.1f;
            }
            else if (HasFlag(configFlags, ConfigFlag.LowSideAirIntakes))
            {
                percAlongWing += 0.05f;
            }

            Vector3 pos = GetPositionOnWing(wing, wingPos, percAlongWing);

            float wingLength = Mathf.Lerp(wing.baseLength, wing.endLength, Mathf.Min(0.5f, percAlongWing));
            float length;
            float width = radius * rand.Float(0.8f, 1.25f);

            if (HasFlag(configFlags, ConfigFlag.LowFrontWings))
            {
                length = wingLength;
            }
            else
            {
                length = wingLength * rand.Float(1.2f, 1.5f);
            }

            BoxInfo box = new BoxInfo()
            {
                topLength = length * 0.5f,
                bottomLength = length * 0.45f,
                height = 0.2f,
                width = 0.1f
            };

            Body tankBody = new Body()
            {
                dims = new List<Vector3>()
                {
                    new Vector3(0, 0, 0),
                    new Vector3(width, radius, 0.25f),
                    new Vector3(width, radius, 0.75f),
                    new Vector3(0, 0, 1),
                },
                length = length,
                lowerInflate = new Vector2(0, 0.5f)
            };

            Vector3 boxOffset = Vector3.down * (box.height + (wing.baseHeight * 0.5f));

            if (!HasFlag(configFlags, ConfigFlag.UnderWingEngines))
            {
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    pos.x *= sides[c1];

                    c = MeshBuilder.Box(c, verts, tris, uvs, pos + boxOffset + Vector3.forward * box.topLength * -0.5f, Quaternion.identity, box);

                    tankBody.offset = pos + boxOffset + Vector3.down * radius + Vector3.forward * length * -0.5f;

                    c = MeshBuilder.Body(c, verts, tris, uvs, tankBody);
                }

                SetFlag(ref configFlags, ConfigFlag.WingFuelTanks);
            }



            // center
            if (rand.Float() < 0.5f && !HasFlag(configFlags, ConfigFlag.BodyMissiles))
            {
                pos = GetPositionOnBody(body, Vector3.down, 0.5f);

                boxOffset = Vector3.down * box.height;

                c = MeshBuilder.Box(c, verts, tris, uvs, pos + boxOffset + Vector3.forward * box.topLength * -0.5f, Quaternion.identity, box);

                tankBody.offset = pos + boxOffset + Vector3.down * radius + Vector3.forward * length * -0.5f;

                c = MeshBuilder.Body(c, verts, tris, uvs, tankBody);

                SetFlag(ref configFlags, ConfigFlag.BodyFuelTanks);
            }

            return c;
        }

        int BodyWeapons(int c, Body body)
        {
            if (!HasFlag(configFlags, ConfigFlag.BellyAirIntake))
            {
                if (rand.Float() < 0.5f)
                {
                    SetFlag(ref configFlags, ConfigFlag.BodyMissiles);

                    BoxInfo bodyBox = new BoxInfo()
                    {
                        topLength = body.length * 0.25f,
                        bottomLength = body.length * 0.225f,
                        height = 0.2f,
                        width = 0.05f
                    };

                    var missile = CreateMissileInfo();

                    Vector3 pos = GetPositionOnBody(body, Vector3.right * 0.5f + Vector3.down, 0.5f);

                    for (int c1 = 0; c1 < 2; ++c1)
                    {
                        pos.x *= sides[c1];

                        Vector3 boxPos = Vector3.down * bodyBox.height;

                        c = MeshBuilder.Box(c, verts, tris, uvs, pos + boxPos + Vector3.forward * bodyBox.topLength * -0.5f, Quaternion.identity, bodyBox);

                        var m = MeshBuilder.Missile(pos + boxPos + Vector3.down * missile.radius, missile, RootObj.transform, MissileMaterial);
                        AssignTexture(m, missile);
                    }
                }
            }

            if (type == Type.Attack)
            {
                if (rand.Float() < 0.5f)
                {
                    c = BodyCannons(c, body);
                }
            }

            return c;
        }

        int WingWeapons(int c, Wing wing, Vector3 wingPos, Body body)
        {
            int numPods = 2;
            int tipMissiles = -1;
            bool rockets = false;

            if (type == Type.Attack)
            {
                ++numPods;

                rockets = rand.Float() < 0.5f;
            }

            List<MissileInfo> missileInfo = new List<MissileInfo>();

            for (int c1 = 0; c1 < numPods; ++c1)
            {
                missileInfo.Add(CreateMissileInfo());
            }

            missileInfo.Sort(OnSortMissiles);

            if (wingConfiguration != WingConfiguration.Sweep &&
                bodyConfiguration != BodyConfiguration.FlyingWing)
            {
                if (rand.Float() < 0.5f)
                {
                    tipMissiles = missileInfo.Count;
                    missileInfo.Add(CreateMissileInfo());
                }
            }

            float boxLength = Mathf.Lerp(wing.baseLength, wing.endLength, 0.5f);
            boxLength *= 0.5f;

            float boxHeight = 0.3f;

            BoxInfo box = new BoxInfo()
            {
                topLength = boxLength * 0.75f,
                bottomLength = boxLength,
                height = boxHeight,
                width = 0.1f
            };

            BoxInfo lowerBox = new BoxInfo()
            {
                topLength = boxLength,
                bottomLength = boxLength * 0.75f,
                height = boxHeight * 0.75f,
                width = 0.1f
            };


            BoxInfo doubleLink = new BoxInfo()
            {
                topLength = box.bottomLength,
                bottomLength = box.bottomLength * 0.75f,
                height = 0.1f,
            };


            float percOfWing = 2f / wing.width;

            float perc = percOfWing;

            if (HasFlag(configFlags, ConfigFlag.SideEngines) ||
                HasFlag(configFlags, ConfigFlag.LowSideAirIntakes))
            {
                perc += 0.05f;
            }

            if(wingConfiguration == WingConfiguration.Sweep)
            {
                perc += 0.15f;
            }

            float percAdd = ((1f - percOfWing) - 0.1f) / numPods;

            for (int c2 = 0; c2 < numPods; ++c2, perc += percAdd)
            {
                if (c2 == 0 && type == Type.Attack)
                {
                    if (rockets)
                    {
                        c = RocketPod(c, wing, wingPos, perc);
                    }
                    else
                    {
                        c = WingCannons(c, wing, wingPos, perc);
                    }

                    continue;
                }

                Vector3 pos = GetPositionOnWing(wing, wingPos, perc);

                var missile = missileInfo[c2];

                int podSize = rand.Int(1, 3);

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    var v = verts;
                    var t = tris;
                    var u = uvs;
                    var wc = c;

                    Vector3 boxPos = pos + Vector3.forward * box.topLength * -0.6f + Vector3.up * -box.height;
                    boxPos.y -= wing.baseHeight * 0.5f;

                    Vector3 missilePos = boxPos;

                    SubObject so = null;
                    if (wings != null)
                    {
                        so = new SubObject();
                        so.Create("MissileRack", wings[c1].Transform, boxPos, Quaternion.identity, BodyMaterial);
                        v = so.verts;
                        t = so.tris;
                        u = so.uvs;
                        wc = so.c;

                        boxPos = Vector3.zero;
                    }


                    wc = MeshBuilder.Box(wc, v, t, u, boxPos, Quaternion.identity, box);

                    if (podSize == 2 || podSize == 3)
                    {
                        doubleLink.width = Mathf.Max(0.25f, missile.radius * 2);
                        doubleLink.bottomLength = doubleLink.topLength * ((podSize == 3) ? 1 : 0.75f);

                        wc = MeshBuilder.Box(wc, v, t, u, boxPos + Vector3.down * doubleLink.height, Quaternion.identity, doubleLink);

                        for (int c3 = 0; c3 < 2; ++c3)
                        {
                            var p = missilePos + Vector3.forward * box.bottomLength * 0.5f +
                                    Vector3.right * (doubleLink.width + (missile.radius * 2)) * sides[c3] * 0.5f +
                                    Vector3.up * doubleLink.height * -0.5f;
                            var m = MeshBuilder.Missile(p, missile, RootObj.transform, MissileMaterial);
                            AssignTexture(m, missile);

                            if (so != null)
                            {
                                m.Transform.SetParent(so.Transform);
                            }
                        }

                        if (podSize == 3)
                        {
                            missilePos.y -= lowerBox.height + doubleLink.height;
                            wc = MeshBuilder.Box(wc, v, t, u, boxPos + Vector3.down * (lowerBox.height + doubleLink.height), Quaternion.identity, lowerBox);

                            var m = MeshBuilder.Missile(missilePos + Vector3.forward * box.bottomLength * 0.5f + Vector3.up * missile.radius * -1f, missile, RootObj.transform, MissileMaterial);
                            AssignTexture(m, missile);

                            if (so != null)
                            {
                                m.Transform.SetParent(so.Transform);
                            }
                        }
                    }
                    else
                    {
                        var m = MeshBuilder.Missile(missilePos + Vector3.forward * box.bottomLength * 0.5f + Vector3.up * missile.radius * -1f, missile, RootObj.transform, MissileMaterial);
                        AssignTexture(m, missile);

                        if (so != null)
                        {
                            m.Transform.SetParent(so.Transform);
                        }
                    }

                    if (so != null)
                    {
                        so.c = wc;
                        so.Publish();
                    }
                    else
                    {
                        c = wc;
                    }

                    pos.x *= -1;
                }
            }

            if (tipMissiles >= 0)
            {
                SetFlag(ref configFlags, ConfigFlag.WingTipMissiles);

                BoxInfo tipBox = new BoxInfo()
                {
                    topLength = wing.endLength * 1.5f,
                    bottomLength = wing.endLength * 1.25f,
                    height = 0.1f,
                    width = 0.1f
                };

                var missile = missileInfo[tipMissiles];

                Vector3 endPos = GetPositionOnWing(wing, wingPos, 1);

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    endPos.x *= sides[c1];

                    c = MeshBuilder.Box(c, verts, tris, uvs, endPos + Vector3.back * tipBox.topLength * 0.5f + Vector3.down * tipBox.height * 0.5f + Vector3.right * tipBox.width * 0.5f * sides[c1], Quaternion.identity, tipBox);

                    var m = MeshBuilder.Missile(endPos + Vector3.right * (missile.radius + tipBox.width) * sides[c1], missile, RootObj.transform, MissileMaterial);
                    AssignTexture(m, missile);
                }
            }

            return c;
        }

        int RocketPod(int c, Wing wing, Vector3 wingPos, float percentAlongWing)
        {
            Vector3 pos = GetPositionOnWing(wing, wingPos, percentAlongWing);

            float wingDepth = Mathf.Lerp(wing.baseLength, wing.endLength, percentAlongWing);

            float length = wingDepth;

            float rad = rand.Float(0.28f, 0.35f);

            pos.z -= length * 0.5f;

            int numRockets = rand.Int(5, 7);
            float rocketRadius = 0.075f;
            float rocketLength = 0.15f;
            float angleAdd = 360f / numRockets;

            BoxInfo box = new BoxInfo()
            {
                topLength = length * 0.75f,
                bottomLength = length,
                height = 0.2f,
                width = 0.15f
            };

            for (int c1 = 0; c1 < 2; ++c1)
            {
                pos.x *= sides[c1];

                Vector3 boxPos = pos;
                boxPos.y -= (box.height + wing.baseHeight);

                c = MeshBuilder.Box(c, verts, tris, uvs, boxPos, Quaternion.identity, box);

                Vector3 podPos = boxPos;
                podPos.y -= rad;

                c = MeshBuilder.HollowTube(c, verts, tris, uvs, podPos, Quaternion.identity, length, rad, rad, 1, 1);

                c = MeshBuilder.Disc(c, verts, tris, uvs, podPos + Vector3.forward * length, Quaternion.Euler(90, 0, 0), rad, rad);

                c = MeshBuilder.Disc(c, verts, tris, uvs, podPos, Quaternion.Euler(-90, 0, 0), rad, rad);

                float angle = 0;
                for (int c2 = 0; c2 < numRockets; ++c2, angle += angleAdd)
                {
                    Vector3 off = Quaternion.Euler(0, 0, angle) * Vector3.right * rad * 0.7f;
                    metalObjects.c = MeshBuilder.Cone(metalObjects.c, metalObjects.verts, metalObjects.tris, metalObjects.uvs, podPos + off + Vector3.forward * length, Quaternion.Euler(90, 0, 0), rocketLength, rocketRadius);

                    metalObjects.c = MeshBuilder.HollowTube(metalObjects.c, metalObjects.verts, metalObjects.tris, metalObjects.uvs, podPos + off + Vector3.forward * -0.05f, Quaternion.identity, 0.1f, rocketRadius, rocketRadius, 0, 0);
                }

                metalObjects.c = MeshBuilder.Cone(metalObjects.c, metalObjects.verts, metalObjects.tris, metalObjects.uvs, podPos + Vector3.forward * length, Quaternion.Euler(90, 0, 0), rocketLength, rocketRadius);
 
                metalObjects.c = MeshBuilder.HollowTube(metalObjects.c, metalObjects.verts, metalObjects.tris, metalObjects.uvs, podPos + Vector3.forward * -0.05f, Quaternion.identity, 0.1f, rocketRadius, rocketRadius, 0, 0);
            }
            return c;
        }

        int WingCannons(int c, Wing wing, Vector3 wingPos, float percentAlongWing)
        {
            float width = 0.1f;
            float height = 0.2f;

            List<Vector3> bodyDims = new List<Vector3>()
            {
                new Vector3(0,0,0),
                new Vector3(width,height,0.1f),
                new Vector3(width,height,0.98f),
                new Vector3(0,0,1)
            };

            Vector3 pos = GetPositionOnWing(wing, wingPos, percentAlongWing);

            float wingDepth = Mathf.Lerp(wing.baseLength, wing.endLength, percentAlongWing);

            Body body = new Body();
            body.dims = bodyDims;
            body.length = wingDepth;
            body.offset = pos;
            body.lowerInflate = new Vector2(0, rand.Float(0, 0.5f));

            body.offset.z += body.length * -0.5f;
            body.offset.y -= height * 0.5f + wing.baseHeight;

            float housingLength = rand.Float(0.5f, 0.7f);
            float housingRadius = 0.1f;
            CannonInfo cannon = new CannonInfo()
            {
                housingLength = housingLength,
                housingRadius = housingRadius,
                barrelLength = housingLength * rand.Float(0.4f, 0.75f),
                barrelRadius = housingRadius * 0.5f
            };

            Vector3 basePos = body.offset;
            int numGuns = rand.Int(2, 3);
            float xPos = 0;
            float zPos = 0;
            float zOff = rand.Float(0f, 0.1f);
            for (int c2 = 0; c2 < numGuns; ++c2, xPos += width * 2.25f, zPos -= zOff)
            {
                body.offset = basePos;

                body.offset.x += xPos;
                body.offset.z += zPos;

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    body.offset.x *= sides[c1];

                    c = MeshBuilder.Body(c, verts, tris, uvs, body);

                    c = Cannon(c, body.offset + Vector3.forward * (body.length - (cannon.housingLength * 0.5f)), cannon);
                }
            }

            return c;
        }

        int BodyCannons(int c, Body body)
        {
            float dim = body.dims[body.dims.Count - 2].z;

            Vector3 pos = GetPositionOnBody(body, Vector3.right, dim + ((1f - dim) * 0.8f));

            float housingLength = rand.Float(0.25f, 0.5f);
            float housingRadius = 0.1f;

            CannonInfo cannon = new CannonInfo()
            {
                housingLength = housingLength,
                housingRadius = housingRadius,
                barrelLength = housingLength * 0.75f,
                barrelRadius = housingRadius * 0.5f
            };

            float xPerc = rand.Float(0.4f, 0.75f);

            pos.x *= xPerc;

            int rows = rand.Int(1, 2);

            float yOff = pos.x;

            if (rows == 1 && rand.Float() < 0.5f)
            {
                yOff -= yOff * 1.5f;

                pos.z -= housingLength * (0.25f + body.lowerInflate.y);
            }

            for (int c2 = 0; c2 < rows; ++c2)
            {
                for (int c1 = 0; c1 < 2; ++c1)
                {
                    Vector3 cannonPos = pos + Vector3.forward * housingLength * -(Mathf.Lerp(-0.2f, 0.75f, xPerc)) + Vector3.up * yOff;

                    cannonPos.x *= sides[c1];

                    c = Cannon(c, cannonPos, cannon);
                }

                yOff -= yOff * 2;

                pos.z -= housingLength * (0.25f + body.lowerInflate.y);
            }

            return c;
        }

        int OnSortMissiles(MissileInfo m1, MissileInfo m2)
        {
            return (int)((m2.length - m1.length) * 100);
        }

        int Cannon(int c, Vector3 pos, CannonInfo cannon)
        {
            c = MeshBuilder.Tube(c, verts, tris, uvs, pos, Quaternion.identity, cannon.housingLength, cannon.housingRadius, Vector2.one * cannon.housingRadius, 0.05f);

            metalObjects.c = MeshBuilder.Tube(metalObjects.c, metalObjects.verts, metalObjects.tris, metalObjects.uvs, pos + Vector3.forward * cannon.housingLength, Quaternion.identity, cannon.barrelLength, cannon.barrelRadius, Vector2.one * cannon.barrelRadius, 0.01f);

            return c;
        }

        Vector3 GetPositionOnBody(Body body, Vector3 dir, float perc)
        {
            //Vector3 dim = GetDims(body.dims, perc);
            Vector3 dim = MeshBuilder.GetDims(body.dims, perc);

            float start = 0;

            float xInflate = 1;
            float yInflate = 1;

            float angle = Mathf.Atan2(dir.x, dir.y);

            if (angle < 0)
            {
                angle = (Mathf.PI * 2) - Mathf.Abs(angle);
            }

            float half = Mathf.PI;
            float a = Mathf.PI * 0.5f;
            if (angle > half - a && angle < half + a)
            {
                xInflate = 1 - (perc * body.lowerInflate.x);// 2 * p;         -0.25 = wider

                yInflate = 1 - (perc * body.lowerInflate.y);// 2 * p;           0.9 = extreme
            }


            float x = Mathf.Sin(angle) * (dim.x * xInflate);
            float y = Mathf.Cos(angle) * (dim.y * yInflate);

            return body.offset + new Vector3(x, y, start + (body.length * perc));
        }

        float GetWingWidth(Wing wing, float percent)
        {
            float w = Mathf.Lerp(wing.baseLength, wing.endLength, percent);

            w += Mathf.Sin(percent * Mathf.PI) * wing.frontCurve;

            if (wing.frontCurve >= 0)
            {
                w -= Mathf.Sin(percent * Mathf.PI) * wing.rearCurve;
            }

            return w;
        }

        Vector3 GetPositionOnWing(Wing wing, Vector3 pos, float percent)
        {
            Vector3 res = new Vector3(pos.x + (wing.width * percent), 0, 0);

            float width = Mathf.Sin(percent * Mathf.PI) * wing.frontCurve;

            res.z = Mathf.Lerp(wing.baseLength, wing.endLength, percent) * 0.5f;
            res.z += width * 0.5f;
            res.z += percent * wing.endOffset.z;
            res.z += pos.z;

            if (wing.frontCurve >= 0)
            {
                width += Mathf.Sin(percent * Mathf.PI) * wing.rearCurve;
                res.z += width * 0.5f;
            }


            res.y = Mathf.Lerp(pos.y, pos.y + wing.endOffset.y, percent);

            return res;
        }

        int Wings(int c, Wing wing, Vector3 offset, Vector3 wingStart, Vector3 wingEnd, bool subObject, bool flaps = false)
        {
            int numPanels = flaps ? 6 : 3;
            int numEdges = 6;

            float leadingFrontLength = 0.25f;
            float leadingRearLength = 0.5f;

            float panelWidth = wing.width / (numPanels - 1 - (flaps ? 3 : 0));
            float startOfFlap = 0.25f;

            int cc = c;

            if (subObject)
            {
                wings = new List<SubObject>();
            }

            for (int s = 0; s < 2; ++s)
            {
                var v = verts;
                var t = tris;
                var uv = uvs;

                SubObject w = null;
                if (subObject)
                {
                    c = 0;

                    w = new SubObject();
                    w.Create($"Wing{s}", RootObj.transform, Vector3.zero, Quaternion.identity, BodyMaterial);
                    v = w.verts;
                    t = w.tris;
                    uv = w.uvs;

                    wings.Add(w);
                }


                Vector3 o = offset;
                o.x *= sides[s];

                float x = 0;
                float y = wing.baseHeight;
                for (int c1 = 0; c1 < numPanels; ++c1)
                {
                    float widthPerc = x / wing.width;

                    float rearOffset = Mathf.Lerp(0, wing.endOffset.z, widthPerc);


                    float frontOffset = rearOffset;
                    frontOffset += Mathf.Sin(widthPerc * Mathf.PI) * wing.frontCurve;

                    rearOffset += Mathf.Sin(widthPerc * Mathf.PI) * wing.rearCurve;


                    float heightOffset = Mathf.Lerp(0, wing.endOffset.y, widthPerc);

                    float length = Mathf.Lerp(wing.baseLength, wing.endLength, widthPerc);


                    Vector3 p1 = o;
                    Vector3 p2 = o;
                    if (c1 == 0)
                    {
                        p1.x = wingStart.x * sides[s];
                        p2.x = wingEnd.x * sides[s];
                    }

                    float flapGap = 0;

                    if (flaps && (c1 == 2 || c1 == 3))
                    {
                        flapGap = 0.5f;
                    }

                    v.Add(p1 + new Vector3(sides[s] * x, y + heightOffset, rearOffset + flapGap));
                    v.Add(p2 + new Vector3(sides[s] * x, y + heightOffset, length + frontOffset));

                    v.Add(p2 + new Vector3(sides[s] * x, 0f + heightOffset, length + leadingFrontLength + frontOffset));

                    v.Add(p2 + new Vector3(sides[s] * x, -y + heightOffset, length + frontOffset));
                    v.Add(p1 + new Vector3(sides[s] * x, -y + heightOffset, rearOffset + flapGap));

                    v.Add(p1 + new Vector3(sides[s] * x, 0f + heightOffset, -leadingRearLength + rearOffset + flapGap));

                    for (int c3 = 0; c3 < 6; ++c3)
                    {
                        uv.Add(new Vector2(widthPerc, (float)c3 / (6 - 1)));
                    }

                    if (flaps)
                    {
                        if (c1 == 0)
                        {
                            x += panelWidth * startOfFlap;
                        }
                        else if (c1 == 2)
                        {
                            x += panelWidth;
                        }
                        else if (c1 == 4)
                        {
                            x += panelWidth - (panelWidth * startOfFlap);
                        }
                    }
                    else
                    {
                        x += panelWidth;
                    }

                    y *= 0.75f;
                }





                for (int c1 = 0; c1 < numPanels - 1; ++c1)
                {
                    for (int c2 = 0; c2 < numEdges; ++c2)
                    {
                        int i1 = c + 0 + c2;
                        int i2 = c + numEdges + 1 + c2;
                        int i3 = c + numEdges + 0 + c2;
                        int i4 = c + 1 + c2;

                        if (c2 == numEdges - 1)
                        {
                            i2 -= numEdges;
                            i4 -= numEdges;
                        }

                        if (s == 0)
                        {
                            t.Add(i1);
                            t.Add(i2);
                            t.Add(i3);

                            t.Add(i1);
                            t.Add(i4);
                            t.Add(i2);
                        }
                        else
                        {
                            t.Add(i1);
                            t.Add(i3);
                            t.Add(i2);

                            t.Add(i1);
                            t.Add(i2);
                            t.Add(i4);
                        }
                    }

                    c += numEdges;

                    MeshBuilder.CapWing(c, t, numEdges, sides[s] * -1);
                }

                if (subObject)
                {
                    w.c = c;

                    w.Publish();
                }

                c += numEdges;
            }

            if (!subObject)
            {
                cc = c;
            }


            if (flaps)
            {
                BoxInfo box = new BoxInfo()
                {
                    width = panelWidth,
                    topLength = 0.5f,
                    bottomLength = 0.7f,
                    height = wing.baseHeight,
                    preRotation = Quaternion.Euler(0, 180, 0)
                };
                float boxYPos = offset.y + wing.baseHeight - ((box.height * 0.5f) + wing.baseHeight);
                Vector3 boxPos = new Vector3(offset.x + box.width * 0.5f + (panelWidth * startOfFlap), boxYPos, offset.z + box.topLength * 0f);

                for (int c1 = 0; c1 < 2; ++c1)
                {
                    boxPos.x *= sides[c1];
                    SubObject flap = new SubObject();
                    flap.Create($"Flap{c1}", RootObj.transform, boxPos, Quaternion.identity, BodyMaterial);
                    flap.c = MeshBuilder.Box(flap.c, flap.verts, flap.tris, flap.uvs, Vector3.zero, Quaternion.identity, box);
                    flap.Publish();
                }
            }

            return cc;
        }
        /*Vector3 GetDims(List<Vector3> dims, float percent)
        {
            for (int c1 = 0; c1 < dims.Count - 1; ++c1)
            {
                Vector3 p1 = dims[c1];
                Vector3 p2 = dims[c1 + 1];

                if (percent >= p1.z && percent < p2.z)
                {
                    float local = percent - p1.z;
                    local /= p2.z - p1.z;

                    if (p2.y < p1.y)
                    {
                        // front
                        local = Easing.CubicEaseIn(local, 0f, 1f, 1f);
                    }
                    else if (p2.y > p1.y)
                    {
                        // rear
                        local = Easing.CubicEaseOut(local, 0f, 1f, 1f);
                    }

                    return Vector3.Lerp(p1, p2, local);
                }
            }
            return dims[dims.Count - 1];
        }*/

        /*int Nose(int c, Body body)
        {
            if (HasFlag(configFlags, ConfigFlag.MigNose))
            {
                var penDim = body.dims[body.dims.Count - 2];

                var lastDim = body.dims[body.dims.Count - 1];

                float rad = Mathf.Min(penDim.x, penDim.y);

                lastDim.x = rad;
                lastDim.y = rad;

                body.dims[body.dims.Count - 1] = lastDim;

                c = MeshBuilder.Tube(c, verts, tris, uvs, Vector3.forward * body.length * 0.5f, Quaternion.identity, 1, rad, Vector2.one * rad, 0.1f);
            }

            return c;
        }*/

        void SetFlag(ref ConfigFlag flags, ConfigFlag flag)
        {
            flags |= flag;
        }

        bool HasFlag(ConfigFlag flags, ConfigFlag flag)
        {
            return (flags & flag) != 0;
        }
    }
}