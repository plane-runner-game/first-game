using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    public class Body
    {
        public List<Vector3> dims;
        public Vector3 offset;
        public float length;
        public Vector2 lowerInflate;        // x = -0.25 wider     y = 0 round, 0.9 shallow
        public bool pinchEdge;
    }

    class Wing
    {
        public float frontCurve; // -1 - 1
        public float rearCurve;
        public float baseLength;
        public float endLength;
        public float width;
        //public float height = 0.1f;
        public Vector3 endOffset;
        public float wingHeightOfBody;// 0.75f;
        public float baseHeight = 0.1f;
        public float endHeight = 0.1f;
    }

    class VerticalFin
    {
        public float height;
        public float zPos;
        public float zPercent;
        public float detailPercent;
        public float detailSide;
        public float frontCurve;
        public Vector2 length;
        public Vector2 dir;
        public Vector3 endOffset;
        public Vector3 outputPos;
    }

    public class MissileInfo
    {
        public float length;
        public float radius;
        public float coneLength;
        public float finHeight;
        public float frontfinPosition;
        public float rearFinBaseLength;
        public float frontFinBaseLength;
        public float noseLength;
        public int textureIndex;
    }

    class CannonInfo
    {
        public float housingLength;
        public float housingRadius;
        public float barrelLength;
        public float barrelRadius;
    }

    public class BoxInfo
    {
        public float width;
        public float height;
        public float topLength;
        public float bottomLength;
        public Quaternion preRotation = Quaternion.identity;
    }

    public class EngineInfo
    {
        public float length;
        public float funnelLength;
        public float funnelEndHeight;
        public float radius;
        public int struts;
        public SubObject metal;

        public EngineInfo(LargeLaser.IRand rand)
        {
            if (rand.Float() < 0.5f)
            {
                struts = rand.Int(5, 10) * 2;
            }
        }
    }

    public class PropEngineInfo
    {
        public float length;
        public float radius;
        public int props;
        public float propLength;
        public float propWidth;
        public float airIntakeLength;
        public float airIntakeCornerRadius;
        public bool rear;

        public PropEngineInfo(LargeLaser.IRand rand)
        {
            props = rand.Int(2, 3);
        }
    }

    public class RoundedRectInfo
    {
        public float length;
        public float thickness;
        public float bottomOffset;
    }
}