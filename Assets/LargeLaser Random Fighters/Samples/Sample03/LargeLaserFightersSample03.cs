using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// LargeLaserFightersSample03
/// 
/// Show how to pre-generate a plane texture, and apply that texture to
/// any subsequent generated plane instance.
/// 
/// Also demonstrates how to create instances of an original plane, so the
/// original can be used as a prefab or template for many subsequent instances.
/// </summary>

public class LargeLaserFightersSample03 : MonoBehaviour
{
    public Text TextureSeed;

    List<LargeLaser.Plane> planes;
    LargeLaser.IRand random;
    int textureSeed;

    void Start()
    {
        random = LargeLaser.Rand.Create(System.DateTime.Now.Millisecond);

        planes = new List<LargeLaser.Plane>();

        CreatePlanes();
    }

    void Update()
    {
        // generate a new set of planes on each Space press.
        if(Input.GetKeyUp(KeyCode.Space))
        {
            CreatePlanes();
        }
    }

    void CreatePlanes()
    {
        foreach(var plane in planes)
        {
            plane.Destroy();
        }
        planes.Clear();

        LargeLaser.TextureManager.DestroyTextures(textureSeed);


        // create a seed which will be used to generate textures
        textureSeed = random.Int();

        // display current texture seed on screen.
        TextureSeed.text = $"Texture Seed = {textureSeed}";

        // generate textures using this seed.
        LargeLaser.TextureManager.GenerateTextures(textureSeed);

        // make a grid of planes; make 6 random planes in a row.
        for (int c1 = 0; c1 < 6; ++c1)
        {
            int seed = random.Int();

            var plane = LargeLaser.Plane.Create(new LargeLaser.PlaneInit()
            {
                Seed = seed,

                // override and specify the texture
                TextureSeed = textureSeed
            });

            planes.Add(plane);


            plane.transform.position = Vector3.right * c1 * 16;
            
            // make 4 more planes identical to this one, position in a column behind the original.
            for(int c2 = 0; c2 < 4; ++c2)
            {
                var planeCopy = plane.Duplicate();
                planeCopy.transform.position = plane.transform.position + Vector3.forward * (c2 + 1) * -16;
                planes.Add(planeCopy);
            }
        }
    }
}
