using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    public class MeshBuilder
    {
        public static Vector3 GetDims(List<Vector3> dims, float percent)
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
        }

        public static int Box(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 position, Quaternion rotation, BoxInfo box)
        {
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * 0.5f, 0, 0))));
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * -0.5f, 0, 0))));
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * -0.5f, 0, box.bottomLength))));
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * 0.5f, 0, box.bottomLength))));

            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * 0.5f, box.height, 0))));
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * -0.5f, box.height, 0))));
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * -0.5f, box.height, box.topLength))));
            verts.Add(rotation * (position + (box.preRotation * new Vector3(box.width * 0.5f, box.height, box.topLength))));


            //uvs.Add(new Vector2(0, 0)); // 0
            //uvs.Add(new Vector2(0, 1)); // 1
            //uvs.Add(new Vector2(0, 0)); // 2
            //uvs.Add(new Vector2(1, 0)); // 3

            //uvs.Add(new Vector2(0, 1)); // 4
            //uvs.Add(new Vector2(1, 1)); // 5
            //uvs.Add(new Vector2(0, 1)); // 6
            //uvs.Add(new Vector2(1, 1)); // 7

            uvs.Add(new Vector2(0, 0)); // 0
            uvs.Add(new Vector2(0, 1)); // 1
            uvs.Add(new Vector2(0, 0)); // 2
            uvs.Add(new Vector2(1, 0)); // 3

            uvs.Add(new Vector2(0, 1)); // 4
            uvs.Add(new Vector2(1, 1)); // 5
            uvs.Add(new Vector2(0, 1)); // 6
            uvs.Add(new Vector2(1, 1)); // 7

            //for (int c1 = 0; c1 < 8; ++c1)
            {
                //uvs.Add(Vector2.zero);
            }

            int i1 = c + 0;
            int i2 = c + 1;
            int i3 = c + 2;
            int i4 = c + 3;

            int i5 = c + 4;
            int i6 = c + 5;
            int i7 = c + 6;
            int i8 = c + 7;

            // bottom
            tris.Add(i1);
            tris.Add(i3);
            tris.Add(i2);

            tris.Add(i1);
            tris.Add(i4);
            tris.Add(i3);

            // top
            tris.Add(i5);
            tris.Add(i6);
            tris.Add(i7);

            tris.Add(i5);
            tris.Add(i7);
            tris.Add(i8);

            for (int c1 = 0; c1 < 4; ++c1)
            {
                i1 = c + c1 + 0;
                i2 = c + c1 + 1;

                i5 = c + c1 + 4;
                i6 = c + c1 + 5;

                if (c1 == 3)
                {
                    i2 = c + c1 - 3;
                    i5 = c + c1 + 4;
                    i6 = c + c1 + 1;
                }

                tris.Add(i1);
                tris.Add(i2);
                tris.Add(i5);

                tris.Add(i2);
                tris.Add(i6);
                tris.Add(i5);
            }

            c += 8;

            return c;
        }

        public static int Quad(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 position, Quaternion rotation, float xLength, float yLength)
        {
            AddVert(verts, new Vector3(xLength * -0.5f, 0, 0), position, rotation);
            AddVert(verts, new Vector3(xLength * -0.5f, yLength, 0), position, rotation);
            AddVert(verts, new Vector3(xLength * 0.5f, yLength, 0), position, rotation);
            AddVert(verts, new Vector3(xLength * 0.5f, 0, 0), position, rotation);

            uvs.Add(new Vector2(0, 0.5f));
            uvs.Add(new Vector2(0, 0));
            uvs.Add(new Vector2(0.5f, 0));
            uvs.Add(new Vector2(0.5f, 0.5f));

            tris.Add(c + 0);
            tris.Add(c + 1);
            tris.Add(c + 2);

            tris.Add(c + 0);
            tris.Add(c + 2);
            tris.Add(c + 3);

            c += 4;

            return c;
        }

        public static int Disc(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 offset, Quaternion rotation, float xRadius, float yRadius)
        {
            int numVerts = (int)(Mathf.Max(10f, xRadius * 40));

            float angle = 0;
            float angleAdd = (Mathf.PI * 2) / numVerts;
            for (int c2 = 0; c2 < numVerts; ++c2, angle += angleAdd)
            {
                float x = Mathf.Sin(angle) * xRadius;
                float y = Mathf.Cos(angle) * yRadius;

                Vector3 pos = new Vector3(x, 0, y);

                pos = rotation * pos;

                pos += offset;

                verts.Add(pos);

                uvs.Add(new Vector2(0, 0));
            }

            for (int c2 = 0; c2 < numVerts - 2; ++c2)
            {
                int i1 = c + 0;
                int i2 = c + c2 + 1;
                int i3 = c + c2 + 2;

                tris.Add(i1);
                tris.Add(i2);
                tris.Add(i3);
            }

            c += numVerts;

            return c;
        }

        public static int Prop(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 offset, Quaternion rotation, float length, float width)
        {
            int numVerts = (int)(length * 10);

            Vector3 pos;

            float angle = 0;
            float angleAdd = (Mathf.PI * 2) / numVerts;
            for (int c2 = 0; c2 < numVerts; ++c2, angle += angleAdd)
            {
                float x = Mathf.Sin(angle) * width;
                float y = Mathf.Cos(angle) * length;
                float z = Mathf.Sin(angle) * width * 0.5f;

                pos = rotation * new Vector3(x, y, z);
                pos += offset;
                verts.Add(pos);

                uvs.Add(new Vector2(0, 0));
            }

            float thickness = 0.05f;

            pos = rotation * new Vector3(0, 0, -thickness);
            pos += offset;
            verts.Add(pos);

            uvs.Add(new Vector2(0, 0));

            pos = rotation * new Vector3(0, 0, thickness);
            pos += offset;
            verts.Add(pos);

            uvs.Add(new Vector2(0, 0));

            for (int c2 = 0; c2 < numVerts; ++c2)
            {
                int i1 = c + numVerts;
                int i2 = c + c2;
                int i3 = c + c2 + 1;

                if (c2 == numVerts - 1)
                {
                    i3 = c;
                }

                tris.Add(i1);
                tris.Add(i2);
                tris.Add(i3);
            }

            for (int c2 = 0; c2 < numVerts; ++c2)
            {
                int i1 = c + numVerts + 1;
                int i2 = c + c2;
                int i3 = c + c2 + 1;

                if (c2 == numVerts - 1)
                {
                    i3 = c;
                }

                tris.Add(i1);
                tris.Add(i3);
                tris.Add(i2);
            }

            c += numVerts + 2;

            return c;
        }

        public static int Cone(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 offset, Quaternion rotation, float length, float radius)
        {
            int numRingVerts = (int)(Mathf.Max(10, radius * 40));

            Vector3 pos;

            float angle = 0;
            float angleAdd = (Mathf.PI * 2) / numRingVerts;
            for (int c2 = 0; c2 < numRingVerts; ++c2, angle += angleAdd)
            {
                float x = Mathf.Sin(angle) * radius;
                float y = Mathf.Cos(angle) * radius;

                pos = new Vector3(x, 0, y);

                pos = rotation * pos;

                pos += offset;

                verts.Add(pos);

                uvs.Add(new Vector2(0, 0));
            }

            pos = new Vector3(0, length, 0);
            pos = rotation * pos;
            pos += offset;
            verts.Add(pos);

            uvs.Add(new Vector2(0, 0));

            for (int c2 = 0; c2 < numRingVerts; ++c2)
            {
                int i1 = c + numRingVerts;
                int i2 = c + c2;
                int i3 = c + c2 + 1;

                if (c2 == numRingVerts - 1)
                {
                    i3 = c;
                }

                tris.Add(i1);
                tris.Add(i2);
                tris.Add(i3);
            }

            c += numRingVerts + 1;

            return c;
        }

        public static int Tube(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 offset, Quaternion rotation, float length, float startRadius, Vector2 endRadius, float thickness)
        {
            int numRings = (int)(Mathf.Max(2, length / 0.25f));
            int numRingVerts = (int)(Mathf.Max(10f, startRadius * 40));
            float z = 0;
            float zAdd = length / (numRings - 1);

            for (int c3 = 0; c3 < 2; ++c3)
            {
                for (int c1 = 0; c1 < numRings; ++c1, z += zAdd)
                {
                    float zPerc = (float)c1 / (numRings - 1);

                    if (c3 == 1)
                    {
                        zPerc = 1f - zPerc;
                    }

                    float angle = 0;
                    float angleAdd = (Mathf.PI * 2) / numRingVerts;
                    for (int c2 = 0; c2 < numRingVerts; ++c2, angle += angleAdd)
                    {
                        float p = 1f;

                        float xRadius = Mathf.Lerp(startRadius, endRadius.x, zPerc);
                        float yRadius = Mathf.Lerp(startRadius, endRadius.y, zPerc);

                        float x = Mathf.Sin(angle) * xRadius * p;
                        float y = Mathf.Cos(angle) * yRadius * p;

                        Vector3 pos = new Vector3(x, y, z);

                        AddVert(verts, pos, offset, rotation);
                        uvs.Add(new Vector2(0, 0));
                    }
                }

                z -= zAdd;

                zAdd *= -1;
                startRadius -= thickness;
                endRadius.x -= thickness;
                endRadius.y -= thickness;
            }

            int start = c;

            for (int c3 = 0; c3 < 2; ++c3)
            {
                int end = numRings - 1;
                if (c3 == 1)
                {
                    end = numRings + 1;
                }

                for (int c1 = 0; c1 < end; ++c1)
                {
                    for (int c2 = 0; c2 < numRingVerts; ++c2)
                    {
                        int i1 = c + 0 + c2;
                        int i2 = c + numRingVerts + 1 + c2;
                        int i3 = c + numRingVerts + 0 + c2;
                        int i4 = c + 1 + c2;

                        if (c3 == 1 && c1 == end - 1)
                        {
                            i2 = start + 1 + c2;
                            i3 = start + 0 + c2;
                        }

                        if (c2 == numRingVerts - 1)
                        {
                            i2 -= numRingVerts;
                            i4 -= numRingVerts;
                        }

                        tris.Add(i1);
                        tris.Add(i3);
                        tris.Add(i2);

                        tris.Add(i1);
                        tris.Add(i2);
                        tris.Add(i4);
                    }

                    c += numRingVerts;
                }
            }

            return c;
        }

        public static int HollowTube(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 position, Quaternion rotation, float length, float xRadius, float yRadius, float frontPercent, float rearPercent)
        {
            float frontPointStart = 0.7f;
            float rearPointEnd = 0.3f;

            int numRings = 12;
            //int numRingVerts = 20;
            int numRingVerts = (int)(Mathf.Max(10, Mathf.Max(xRadius, yRadius) * 40));

            float z = 0;
            float zAdd = length / (numRings - 1);
            for (int c1 = 0; c1 < numRings; ++c1, z += zAdd)
            {
                float zPerc = (float)c1 / (numRings - 1);

                float angle = 0;
                float angleAdd = (Mathf.PI * 2) / numRingVerts;
                for (int c2 = 0; c2 < numRingVerts; ++c2, angle += angleAdd)
                {
                    float p = 1f;

                    if (zPerc <= rearPointEnd)
                    {
                        float f = zPerc / rearPointEnd;
                        p = Easing.CubicEaseOut(f, rearPercent, 1f - rearPercent, 1f);
                    }
                    else if (zPerc >= frontPointStart)
                    {
                        float f = (zPerc - frontPointStart) / (1f - frontPointStart);
                        p = 1f - Easing.CubicEaseIn(f, 0, 1f - frontPercent, 1f);
                    }



                    float x = Mathf.Sin(angle) * xRadius * p;
                    float y = Mathf.Cos(angle) * yRadius * p;

                    Vector3 pos = new Vector3(x, y, z);

                    AddVert(verts, pos, position, rotation);

                    float u = (float)c2 / (numRingVerts - 1);
                    uvs.Add(new Vector2(u, zPerc));
                }
            }

            for (int c1 = 0; c1 < numRings - 1; ++c1)
            {
                int start = c;
                for (int c2 = 0; c2 < numRingVerts; ++c2)
                {
                    int up = c + 1;
                    if (up == start + numRingVerts)
                    {
                        up = start;
                    }

                    int next = c + 0 + numRingVerts;

                    tris.Add(c);
                    tris.Add(next);
                    tris.Add(up);

                    int nextUp = c + 1 + numRingVerts;
                    if (nextUp == start + numRingVerts * 2)
                    {
                        nextUp = start + numRingVerts;
                    }

                    tris.Add(up);
                    tris.Add(next);
                    tris.Add(nextUp);


                    c += 1;
                }
            }

            c += numRingVerts;

            return c;
        }

        static void AddVert(List<Vector3> verts, Vector3 pos, Vector3 position, Quaternion rotation)
        {
            pos = rotation * pos;
            pos += position;
            verts.Add(pos);
        }

        static void AddVert(List<Vector3> verts, Body body, Vector3 dims, float zPerc, Vector3 dir, Vector3 pos, Vector3 position, Quaternion rotation)
        {
            pos = rotation * pos;
            pos += position;


            float z = pos.z - body.offset.z;
            z /= body.length;

            //Vector3 p = Utils.GetPositionOnBody(body, dir, z);
            Vector3 p = GetPositionOnBody(body, dir, z);

            float perc = 1f - zPerc;
            perc = Easing.SineEaseIn(perc, 0f, 1f, 1f);

            pos.x += p.x;

            pos.y *= Mathf.Lerp(1, 0.5f, perc);
            pos.x *= Mathf.Lerp(1, 0.25f, perc);

            verts.Add(pos);
        }

        static void AddRing(List<Vector3> verts, List<Vector2> uvs, Vector3 anchor, float radius, float startAngle, float arc, int numVerts, Vector3 position, Quaternion rotation)
        {
            float angle = startAngle;
            float angleAdd = arc / numVerts;
            for (int c1 = 0; c1 < numVerts; ++c1, angle += angleAdd)
            {
                float x = Mathf.Sin(angle) * radius;
                float y = Mathf.Cos(angle) * radius;

                Vector3 pos = new Vector3(x + anchor.x, y + anchor.y, anchor.z);
                AddVert(verts, pos, position, rotation);

                uvs.Add(new Vector2(0, 0));
            }
        }

        static void AddRing(List<Vector3> verts, List<Vector2> uvs, Body body, Vector3 dims, float zPerc, Vector3 dir, Vector3 anchor, float radius, float startAngle, float arc, int numVerts, Vector3 position, Quaternion rotation)
        {
            float angle = startAngle;
            float angleAdd = arc / numVerts;
            for (int c1 = 0; c1 < numVerts; ++c1, angle += angleAdd)
            {
                float x = Mathf.Sin(angle) * radius;
                float y = Mathf.Cos(angle) * radius;

                Vector3 pos = new Vector3(x + anchor.x, y + anchor.y, anchor.z);
                AddVert(verts, body, dims, zPerc, dir, pos, position, rotation);

                uvs.Add(new Vector2(0, 0));
            }
        }

        public static int RoundedRect(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 offset, Quaternion rotation, Vector3 dims, float radius, float thickness)
        {
            int numRings = (int)(Mathf.Max(2, dims.z / 0.25f));
            float z = 0;
            float zAdd = dims.z / (numRings - 1);

            int numRectVerts = 8;

            int numRingVerts = 5;

            float arc = Mathf.PI * 0.5f;

            for (int c3 = 0; c3 < 2; ++c3)
            {
                Vector2 len = new Vector2(dims.x - (radius * 2), dims.y - (radius * 2));
                Vector3 pos;

                for (int c1 = 0; c1 < numRings; ++c1, z += zAdd)
                {
                    float angleStart = 0;

                    // top
                    pos = new Vector3(len.x * -0.5f, dims.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(len.x * 0.5f, dims.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * 0.5f, len.y * 0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;



                    // right
                    pos = new Vector3(dims.x * 0.5f, len.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(dims.x * 0.5f, len.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * 0.5f, len.y * -0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;


                    // bottom
                    pos = new Vector3(len.x * 0.5f, dims.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(len.x * -0.5f, dims.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * -0.5f, len.y * -0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;


                    // left
                    pos = new Vector3(dims.x * -0.5f, len.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(dims.x * -0.5f, len.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * -0.5f, len.y * 0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                }

                z -= zAdd;

                zAdd *= -1;
                radius -= thickness;

                dims.x -= (thickness * 2);
                dims.y -= (thickness * 2);
            }

            int start = c;

            int totalRingVerts = numRectVerts + (numRingVerts * 4);

            for (int c3 = 0; c3 < 2; ++c3)
            {
                int end = numRings - 1;
                if (c3 == 1)
                {
                    end = numRings + 1;
                }

                for (int c1 = 0; c1 < end; ++c1)
                {
                    for (int c2 = 0; c2 < totalRingVerts; ++c2)
                    {
                        int i1 = c + 0 + c2;
                        int i2 = c + totalRingVerts + 1 + c2;
                        int i3 = c + totalRingVerts + 0 + c2;
                        int i4 = c + 1 + c2;

                        if (c3 == 1 && c1 == end - 1)
                        {
                            i2 = start + 1 + c2;
                            i3 = start + 0 + c2;
                        }

                        if (c2 == totalRingVerts - 1)
                        {
                            i2 -= totalRingVerts;
                            i4 -= totalRingVerts;
                        }

                        tris.Add(i1);
                        tris.Add(i3);
                        tris.Add(i2);

                        tris.Add(i1);
                        tris.Add(i2);
                        tris.Add(i4);
                    }

                    c += totalRingVerts;
                }
            }

            return c;
        }

        public static int RoundedRect(int c, RoundedRectInfo info, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 offset, Quaternion rotation, Vector2 frontDims, Vector2 rearDims, float frontRadius, float rearRadius)
        {
            int numRings = (int)(Mathf.Max(2, info.length / 0.25f));
            float z = 0;
            float zAdd = info.length / (numRings - 1);

            int numRectVerts = 8;

            int numRingVerts = 5;

            float arc = Mathf.PI * 0.5f;

            for (int c3 = 0; c3 < 2; ++c3)
            {
                Vector3 pos;

                for (int c1 = 0; c1 < numRings; ++c1, z += zAdd)
                {
                    float zPerc = z / info.length;

                    float radius = Mathf.Lerp(rearRadius, frontRadius, zPerc);

                    Vector2 dims = Vector2.Lerp(rearDims, frontDims, zPerc);
                    dims.x -= (info.thickness * 2 * c3);
                    dims.y -= (info.thickness * 2 * c3);

                    Vector2 len = new Vector2(dims.x - (radius * 2), dims.y - (radius * 2));

                    float angleStart = 0;

                    // top
                    pos = new Vector3(len.x * -0.5f, dims.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(len.x * 0.5f, dims.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * 0.5f, len.y * 0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;



                    // right
                    pos = new Vector3(dims.x * 0.5f, len.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(dims.x * 0.5f, len.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * 0.5f, len.y * -0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;


                    // bottom
                    pos = new Vector3(len.x * 0.5f, dims.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(len.x * -0.5f, dims.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * -0.5f, len.y * -0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;


                    // left
                    pos = new Vector3(dims.x * -0.5f, len.y * -0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(dims.x * -0.5f, len.y * 0.5f, z);
                    AddVert(verts, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, new Vector3(len.x * -0.5f, len.y * 0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                }

                z -= zAdd;

                zAdd *= -1;
                rearRadius -= info.thickness;
                frontRadius -= info.thickness;
            }

            int start = c;

            int totalRingVerts = numRectVerts + (numRingVerts * 4);

            for (int c3 = 0; c3 < 2; ++c3)
            {
                int end = numRings - 1;
                if (c3 == 1)
                {
                    end = numRings + 1;
                }

                for (int c1 = 0; c1 < end; ++c1)
                {
                    for (int c2 = 0; c2 < totalRingVerts; ++c2)
                    {
                        int i1 = c + 0 + c2;
                        int i2 = c + totalRingVerts + 1 + c2;
                        int i3 = c + totalRingVerts + 0 + c2;
                        int i4 = c + 1 + c2;

                        if (c3 == 1 && c1 == end - 1)
                        {
                            i2 = start + 1 + c2;
                            i3 = start + 0 + c2;
                        }

                        if (c2 == totalRingVerts - 1)
                        {
                            i2 -= totalRingVerts;
                            i4 -= totalRingVerts;
                        }

                        tris.Add(i1);
                        tris.Add(i3);
                        tris.Add(i2);

                        tris.Add(i1);
                        tris.Add(i2);
                        tris.Add(i4);
                    }

                    c += totalRingVerts;
                }
            }

            return c;
        }

        public static int RoundedRect(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Body body, Vector3 dir, Vector3 offset, Quaternion rotation, Vector3 dims, float radius, float thickness)
        {
            int numRings = (int)(Mathf.Max(2, dims.z / 0.25f));
            float z = 0;
            float zAdd = dims.z / (numRings - 1);

            int numRectVerts = 8;

            int numRingVerts = 5;

            float arc = Mathf.PI * 0.5f;

            for (int c3 = 0; c3 < 2; ++c3)
            {
                Vector2 len = new Vector2(dims.x - (radius * 2), dims.y - (radius * 2));
                Vector3 pos;

                for (int c1 = 0; c1 < numRings; ++c1, z += zAdd)
                {
                    float angleStart = 0;

                    float zPerc = z / dims.z;

                    // top
                    pos = new Vector3(len.x * -0.5f, dims.y * 0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(len.x * 0.5f, dims.y * 0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, body, dims, zPerc, dir, new Vector3(len.x * 0.5f, len.y * 0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;



                    // right
                    pos = new Vector3(dims.x * 0.5f, len.y * 0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(dims.x * 0.5f, len.y * -0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, body, dims, zPerc, dir, new Vector3(len.x * 0.5f, len.y * -0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;


                    // bottom
                    pos = new Vector3(len.x * 0.5f, dims.y * -0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(len.x * -0.5f, dims.y * -0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, body, dims, zPerc, dir, new Vector3(len.x * -0.5f, len.y * -0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                    angleStart += arc;


                    // left
                    pos = new Vector3(dims.x * -0.5f, len.y * -0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));

                    pos = new Vector3(dims.x * -0.5f, len.y * 0.5f, z);
                    AddVert(verts, body, dims, zPerc, dir, pos, offset, rotation);
                    uvs.Add(new Vector2(0, 0));


                    AddRing(verts, uvs, body, dims, zPerc, dir, new Vector3(len.x * -0.5f, len.y * 0.5f, z), radius, angleStart, arc, numRingVerts, offset, rotation);
                }

                z -= zAdd;

                zAdd *= -1;
                radius -= thickness;

                len.x -= (thickness * 2);
                len.y -= (thickness * 2);

                dims.x -= (thickness * 2);
                dims.y -= (thickness * 2);
            }

            int start = c;

            int totalRingVerts = numRectVerts + (numRingVerts * 4);

            for (int c3 = 0; c3 < 2; ++c3)
            {
                int end = numRings - 1;
                if (c3 == 1)
                {
                    end = numRings + 1;
                }

                for (int c1 = 0; c1 < end; ++c1)
                {
                    for (int c2 = 0; c2 < totalRingVerts; ++c2)
                    {
                        int i1 = c + 0 + c2;
                        int i2 = c + totalRingVerts + 1 + c2;
                        int i3 = c + totalRingVerts + 0 + c2;
                        int i4 = c + 1 + c2;

                        if (c3 == 1 && c1 == end - 1)
                        {
                            i2 = start + 1 + c2;
                            i3 = start + 0 + c2;
                        }

                        if (c2 == totalRingVerts - 1)
                        {
                            i2 -= totalRingVerts;
                            i4 -= totalRingVerts;
                        }

                        tris.Add(i1);
                        tris.Add(i3);
                        tris.Add(i2);

                        tris.Add(i1);
                        tris.Add(i2);
                        tris.Add(i4);
                    }

                    c += totalRingVerts;
                }
            }

            return c;
        }

        public static int EngineHousing(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 pos, EngineInfo engine)
        {
            c = MeshBuilder.Tube(c, verts, tris, uvs, pos, Quaternion.identity, engine.length, engine.radius, Vector2.one * engine.radius, 0.1f);

            engine.metal.c = MeshBuilder.Tube(engine.metal.c, engine.metal.verts, engine.metal.tris, engine.metal.uvs, pos, Quaternion.Euler(0, 180, 0), engine.funnelLength, engine.radius, new Vector2(engine.radius * 0.75f, engine.radius * 0.75f * engine.funnelEndHeight), 0.05f);

            // rear facing disc
            c = MeshBuilder.Disc(c, verts, tris, uvs, pos + Vector3.forward * 0.25f, Quaternion.Euler(-90, 0, 0), engine.radius, engine.radius);

            // forward facing disc
            c = MeshBuilder.Disc(c, verts, tris, uvs, pos + Vector3.forward * engine.length * 0.5f, Quaternion.Euler(90, 0, 0), engine.radius, engine.radius);

            if (engine.struts != 0)
            {
                float boxSize = 0.05f;
                BoxInfo box = new BoxInfo()
                {
                    width = boxSize,
                    height = boxSize,
                    topLength = 1,
                    bottomLength = 1,
                };
                
                float angle = 0;
                float angleAdd = 360f / engine.struts;
                for (int c1 = 0; c1 < engine.struts; ++c1, angle += angleAdd)
                {
                    Quaternion rot = Quaternion.Euler(0, 0, angle);
                    Vector3 boxPos = pos + (rot * (Vector3.up * (engine.radius - (boxSize * 0.5f))));
                    box.preRotation = rot * Quaternion.Euler(5, 0, 0);
                    engine.metal.c = MeshBuilder.Box(engine.metal.c, engine.metal.verts, engine.metal.tris, engine.metal.uvs, boxPos, Quaternion.Euler(0, 0, 0), box);
                }
            }

            return c;
        }

        static public int Body(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Body body)
        {
            int numRings = (int)(body.length / 0.25f);
            int numRingVerts = 20;
            //int numRingVerts = (int)(Mathf.Max(10f, body.dims[1].x * 40));
            float z = 0;
            float zAdd = body.length / (numRings - 1);
            for (int c1 = 0; c1 < numRings; ++c1, z += zAdd)
            {
                float zPerc = (float)c1 / (numRings - 1);

                Vector3 dim = GetDims(body.dims, zPerc);

                float angle = 0;
                float angleAdd = (Mathf.PI * 2) / numRingVerts;
                for (int c2 = 0; c2 < numRingVerts; ++c2, angle += angleAdd)
                {
                    float xInflate = 1;
                    float yInflate = 1;

                    float half = Mathf.PI;
                    float a = Mathf.PI * 0.5f;
                    if (angle > half - a && angle < half + a)
                    {
                        //float p = (angle - (half - a)) / a;
                        xInflate = 1 - ((zPerc) * body.lowerInflate.x);// 2 * p;         -0.25 = wider

                        yInflate = 1 - ((zPerc) * body.lowerInflate.y);// 2 * p;           0.9 = extreme
                    }

                    float yAngle = Mathf.Cos(angle);

                    float x = Mathf.Sin(angle) * (dim.x * xInflate);
                    float y = yAngle * (dim.y * yInflate);

                    if (body.pinchEdge)
                    {
                        y *= Mathf.Lerp(1f, Mathf.Abs(yAngle), zPerc);
                    }


                    Vector3 pos = new Vector3(x, y, z);

                    pos += body.offset;

                    verts.Add(pos);

                    float v = zPerc;
                    int iu = (c2 + (numRingVerts / 2)) % numRingVerts;
                    float u = (float)iu / numRingVerts;

                    uvs.Add(new Vector2(u, v));
                }
            }

            for (int c1 = 0; c1 < numRings - 1; ++c1)
            {
                int start = c;
                for (int c2 = 0; c2 < numRingVerts; ++c2)
                {
                    int up = c + 1;
                    if (up == start + numRingVerts)
                    {
                        up = start;
                    }

                    int next = c + 0 + numRingVerts;

                    tris.Add(c);
                    tris.Add(next);
                    tris.Add(up);

                    int nextUp = c + 1 + numRingVerts;
                    if (nextUp == start + numRingVerts * 2)
                    {
                        nextUp = start + numRingVerts;
                    }

                    tris.Add(up);
                    tris.Add(next);
                    tris.Add(nextUp);


                    c += 1;
                }
            }

            c += numRingVerts;

            return c;
        }

        static Vector3 GetPositionOnBody(Body body, Vector3 dir, float perc)
        {
            Vector3 dim = GetDims(body.dims, perc);

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

        public static int BodyPanel(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Body body, float perc, float direction)
        {
            int nx = 5;
            int ny = 5;

            float positionPerc = perc;
            float lengthPerc = 0.2f;
            float addPerc = lengthPerc / (nx - 1);

            for (int y = 0; y < ny; ++y)
            {
                float py = (float)y / (ny - 1);

                for (int x = 0; x < nx; ++x)
                {
                    float px = (float)x / (nx - 1);

                    Quaternion rot = Quaternion.Euler(0, 0, -45f + (px * 90f));

                    Vector3 dir = rot * Vector3.right * direction;

                    Vector3 pos = GetPositionOnBody(body, dir, positionPerc);

                    pos += Vector3.right * 0.025f * direction;

                    verts.Add(pos);

                    if (direction < 0)
                    {
                        uvs.Add(new Vector2(0.5f * (1 - py), 0.5f * px));
                    }
                    else
                    {
                        uvs.Add(new Vector2(0.5f * py, 0.5f * (1 - px)));
                    }
                }

                positionPerc += addPerc;// 0.04f;
            }
            int c1 = 0;
            for (int y = 0; y < ny - 1; ++y)
            {
                for (int x = 0; x < nx - 1; ++x)
                {
                    tris.Add(c + c1);
                    tris.Add(c + c1 + 1);
                    tris.Add(c + c1 + nx);

                    tris.Add(c + c1 + 1);
                    tris.Add(c + c1 + nx + 1);
                    tris.Add(c + c1 + nx);

                    ++c1;
                }

                ++c1;
            }

            c += nx * ny;

            return c;
        }

        public static SubObject Missile(Vector3 pos, MissileInfo missile, Transform parent, Material material)
        {
            Vector3 missilePos = pos + Vector3.forward * missile.length * -0.5f;

            SubObject subObject = new SubObject();
            subObject.Create("Missile", parent, missilePos, Quaternion.identity, material);


            subObject.c = MeshBuilder.HollowTube(subObject.c, subObject.verts, subObject.tris, subObject.uvs, Vector3.zero, Quaternion.identity, missile.length, missile.radius, missile.radius, 1, 1);

            subObject.c = MeshBuilder.Cone(subObject.c, subObject.verts, subObject.tris, subObject.uvs, Vector3.forward * missile.length, Quaternion.Euler(90, 0, 0), missile.coneLength, missile.radius);

            subObject.c = MeshBuilder.Disc(subObject.c, subObject.verts, subObject.tris, subObject.uvs, Vector3.zero, Quaternion.Euler(-90, 0, 0), missile.radius, missile.radius);

            subObject.c = MeshBuilder.Tube(subObject.c, subObject.verts, subObject.tris, subObject.uvs, Vector3.zero, Quaternion.Euler(0, 180, 0), 0.1f, missile.radius, Vector2.one * missile.radius * 0.75f, 0.025f);





            BoxInfo box = new BoxInfo()
            {
                topLength = missile.rearFinBaseLength * 0.5f,
                bottomLength = missile.rearFinBaseLength,
                height = missile.finHeight,
                width = 0.025f
            };

            // rear fins
            int numFins = 4;
            float angleAdd = 360f / numFins;
            float angle = angleAdd * 0.5f;
            for (int c1 = 0; c1 < numFins; ++c1, angle += angleAdd)
            {
                subObject.c = MeshBuilder.Box(subObject.c, subObject.verts, subObject.tris, subObject.uvs, Vector3.up * missile.radius, Quaternion.Euler(0, 0, angle), box);
            }




            if (missile.noseLength > 0)
            {
                // nose
                box.bottomLength = box.topLength;

                float noseLength = missile.noseLength;
                float noseRadius = missile.radius * 0.33f;
                Vector3 nosePos = Vector3.forward * (missile.length + missile.coneLength * 0.5f);
                subObject.c = MeshBuilder.HollowTube(subObject.c, subObject.verts, subObject.tris, subObject.uvs, nosePos, Quaternion.identity, noseLength, noseRadius, noseRadius, 1, 1);

                subObject.c = MeshBuilder.Disc(subObject.c, subObject.verts, subObject.tris, subObject.uvs, (Vector3.forward * noseLength) + nosePos, Quaternion.Euler(90, 0, 0), noseRadius, noseRadius);

                angle = angleAdd * 0.5f;
                for (int c1 = 0; c1 < 4; ++c1, angle += angleAdd)
                {
                    subObject.c = MeshBuilder.Box(subObject.c, subObject.verts, subObject.tris, subObject.uvs, nosePos + (Vector3.forward * noseLength * 0.25f), Quaternion.Euler(0, 0, angle), box);
                }
            }
            else
            {
                box.bottomLength = missile.frontFinBaseLength;

                // front fins
                angle = angleAdd * 0.5f;
                for (int c1 = 0; c1 < numFins; ++c1, angle += angleAdd)
                {
                    subObject.c = MeshBuilder.Box(subObject.c, subObject.verts, subObject.tris, subObject.uvs, Vector3.up * missile.radius + Vector3.forward * ((missile.length * missile.frontfinPosition) - box.bottomLength * 0.5f), Quaternion.Euler(0, 0, angle), box);
                }
            }


            subObject.Publish();

            return subObject;
        }

        public static int VerticalWing(int c, List<Vector3> verts, List<int> tris, List<Vector2> uvs, Vector3 position, Quaternion rotation, float endXOffset, float endZOffset, float baseLength, float endLength, float baseWidth, float frontCurve)
        {
            int numPanels = 3;
            int numEdges = 6;

            float leadingFrontLength = 0.25f;
            float leadingRearLength = 0.5f;

            float height = 0.1f;

            float panelWidth = baseWidth / (numPanels - 1);

            {
                float x = 0;
                float y = height;
                for (int c1 = 0; c1 < numPanels; ++c1)
                {
                    float widthPerc = (float)c1 / (numPanels - 1);

                    float rearOffset = Mathf.Lerp(0, endZOffset, widthPerc);

                    float topOffset = Mathf.Lerp(0, endXOffset, widthPerc);

                    float frontOffset = rearOffset;
                    frontOffset += Mathf.Sin(widthPerc * Mathf.PI) * frontCurve;


                    float length = Mathf.Lerp(baseLength, endLength, widthPerc);

                    AddVert(verts, new Vector3(y + topOffset, x, 0 + rearOffset), position, rotation);
                    AddVert(verts, new Vector3(y + topOffset, x, length + frontOffset), position, rotation);

                    AddVert(verts, new Vector3(0f + topOffset, x, length + leadingFrontLength + frontOffset), position, rotation);

                    AddVert(verts, new Vector3(-y + topOffset, x, length + frontOffset), position, rotation);
                    AddVert(verts, new Vector3(-y + topOffset, x, 0 + rearOffset), position, rotation);

                    AddVert(verts, new Vector3(0f + topOffset, x, -leadingRearLength + rearOffset), position, rotation);

                    for (int c2 = 0; c2 < 6; ++c2)
                    {
                        uvs.Add(new Vector2(widthPerc, (float)c2 / (6 - 1)));
                    }

                    x += panelWidth;

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

                        tris.Add(i1);
                        tris.Add(i3);
                        tris.Add(i2);

                        tris.Add(i1);
                        tris.Add(i2);
                        tris.Add(i4);
                    }

                    c += numEdges;
                }

                // end
                {
                    CapWing(c, tris, numEdges, 1);
                }

                c += numEdges;
            }

            return c;
        }

        public static void CapWing(int c, List<int> tris, int numEdges, float side)
        {
            for (int c1 = 1; c1 < numEdges - 1; ++c1)
            {
                tris.Add(c + 0);

                if (side > 0)
                {
                    tris.Add(c + c1 + 1);
                    tris.Add(c + c1);
                }
                else
                {
                    tris.Add(c + c1);
                    tris.Add(c + c1 + 1);
                }
            }
        }
    }
}