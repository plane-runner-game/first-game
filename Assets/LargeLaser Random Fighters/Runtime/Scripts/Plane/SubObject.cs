using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    public class SubObject
    {
        public List<Vector3> verts;
        public List<int> tris;
        public List<Vector2> uvs;
        public int c;
        public Transform Transform;

        Mesh mesh;
        MeshFilter meshFilter;

        public void Create(string name, Transform parent, Vector3 position, Quaternion rotation, Material material)
        {
            verts = new List<Vector3>();
            tris = new List<int>();
            uvs = new List<Vector2>();

            mesh = new Mesh();

            var pre = Resources.Load<GameObject>("LargeLaserFighterGameObject");
            var obj = GameObject.Instantiate(pre, position, rotation);
            obj.name = name;
            obj.transform.SetParent(parent);
            Transform = obj.transform;

            meshFilter = obj.GetComponent<MeshFilter>();

            var renderer = obj.GetComponent<Renderer>();
            renderer.material = material;
        }

        public void Publish()
        {
            mesh.vertices = verts.ToArray();
            mesh.triangles = tris.ToArray();
            mesh.uv = uvs.ToArray();

            mesh.RecalculateNormals();

            meshFilter.mesh = mesh;
        }

        public void SetMaterialArg(string name, float val)
        {
            var renderer = meshFilter.gameObject.GetComponent<Renderer>();
            renderer.material.SetFloat(name, val);
        }

        public void SetMaterialArg(string name, Texture2D val)
        {
            var renderer = meshFilter.gameObject.GetComponent<Renderer>();
            renderer.material.SetTexture(name, val);
        }
    }
}