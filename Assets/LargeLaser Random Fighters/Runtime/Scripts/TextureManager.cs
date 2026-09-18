using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    public class TextureManager
    {
        static TextureManager instance;

        public class Textures
        {
            public Texture2D MainTexture;
            public Texture2D DetailTexture;
            public float Hue;
            public float Gloss;
        }

        Dictionary<int, Textures> textureMap;

        public static TextureManager Instance
        {
            get
            {
                if(instance == null)
                {
                    instance = new TextureManager();
                }

                return instance;
            }
        }

        /// <summary>
        /// Creates all textures for a Plane.
        /// </summary>
        /// <param name="seed"></param>
        public static void GenerateTextures(int seed)
        {
            float hue = 0;
            float gloss = 0;

            var textures = new Textures()
            {
                MainTexture = Instance.GenerateMainColor(seed, ref hue, ref gloss),
                DetailTexture = Instance.GenerateDetails(seed)
            };

            textures.Hue = hue;
            textures.Gloss = gloss;

            Instance.textureMap[seed] = textures;
        }

        /// <summary>
        /// Destroy all textures associated with the seed.
        /// </summary>
        /// <param name="seed"></param>
        public static void DestroyTextures(int seed)
        {
            if (Instance.textureMap.TryGetValue(seed, out Textures textures))
            {
                Object.Destroy(textures.MainTexture);
                Object.Destroy(textures.DetailTexture);

                Instance.textureMap.Remove(seed);
            }
        }

        public Textures GetTextures(int seed)
        {
            if(!Instance.textureMap.TryGetValue(seed, out Textures textures))
            {
                throw new System.Exception($"TextureManager GetTextures. No Textures found with seed={seed}");
            }

            return textures;
        }

        private TextureManager()
        {
            textureMap = new Dictionary<int, Textures>();
        }

        public Texture2D GenerateDetails(int seed)
        {
            IRand rand = Rand.Create(seed);

            var font = Resources.Load<Texture2D>("LargeLaserFighterFont01");
            var fontPixels = font.GetPixels();

            int size = 512;

            var tex = new Texture2D(size, size, TextureFormat.ARGB32, false);

            var pixels = new Color[size * size];

            var clear = Color.clear;

            for (int c1 = 0; c1 < size * size; ++c1)
            {
                pixels[c1] = clear;
            }

            Color shadowColor = Color.black;
            Color textColor = Color.HSVToRGB(rand.Float(0f, 0.6f), 0.8f, 0.8f);// Color.yellow;

            int pos = 0;
            for (int c1 = 0; c1 < 3; ++c1, pos += 70)
            {
                int index = rand.Int(0, 11);

                AddLetter(pixels, size, fontPixels, index, pos, 0, shadowColor);

                AddLetter(pixels, size, fontPixels, index, pos + 4, 4, textColor);
            }

            tex.SetPixels(pixels);

            tex.Apply(true);

            return tex;
        }

        void AddLetter(Color[] pixels, int size, Color[] font, int index, int xPos, int yPos, Color col)
        {
            int fsx = 75;
            int fsy = 150;

            int sourceX = index % 6;
            sourceX *= fsx;

            int sourceY = index / 6;
            sourceY *= fsy;

            int destX = Mathf.Max(0, xPos);
            int destY = Mathf.Max(0, yPos);
            int destSX = Mathf.Min(size - 1, xPos + fsx);
            int destSY = Mathf.Min(size - 1, yPos + fsy);

            int sy = sourceY;
            for (int y = destY; y < destSY; ++y, ++sy)
            {
                int sx = sourceX;
                for (int x = destX; x < destSX; ++x, ++sx)
                {
                    int pi = (y * size) + x;

                    int fi = ((size - 1 - sy) * size) + sx;

                    if (font[fi].a >= pixels[pi].a)
                    {
                        col.a = font[fi].a;

                        col.a *= 0.75f;

                        pixels[pi] = col;
                    }
                }
            }
        }

        public Texture2D GeneratePanel(int seed)
        {
            System.Random rand = new System.Random(seed);

            int size = 512;

            var tex = new Texture2D(size, size, TextureFormat.ARGB32, false);

            var pixels = tex.GetPixels(0, 0, size, size);


            for (int c1 = 0; c1 < size * size; ++c1)
            {
                pixels[c1] = Color.white;
            }

            for (int c1 = 0; c1 < 10; ++c1)
            {
                Panel(pixels, rand.Next(0, size), rand.Next(0, size), rand.Next(50, 200), rand.Next(50, 200));
            }

            tex.SetPixels(pixels);

            tex.wrapMode = TextureWrapMode.Mirror;

            tex.Apply(true);

            return tex;
        }

        public Texture2D GenerateMissile(int seed)
        {
            System.Random rand = new System.Random(seed);

            int xSize = 32;
            int ySize = 512;

            var tex = new Texture2D(xSize, ySize, TextureFormat.ARGB32, false);

            var pixels = new Color[xSize * ySize];

            float m = 0.5f + (float)(rand.NextDouble() * 0.5);
            Color mainCol = new Color(m, m, m);

            // main grey
            for (int c1 = 0; c1 < xSize * ySize; ++c1)
            {
                pixels[c1] = mainCol;
            }

            // background greys
            for(int c1 = 0; c1 < 3; ++c1)
            {
                m = 0.25f + (float)(rand.NextDouble() * 0.75);
                mainCol = new Color(m, m, m);
                Stripe(pixels, xSize, ySize, (float)rand.NextDouble(), 0.25f + (float)(rand.NextDouble() * 0.5), mainCol);
            }

            int numColors = Mathf.RoundToInt(1 + (float)rand.NextDouble());

            Color[] stripeColors = new Color[numColors];
            for(int c1 = 0; c1 < numColors; ++c1)
            {
                float s = 0.5f + (float)(rand.NextDouble() * 0.5);
                stripeColors[c1] = Color.HSVToRGB((float)rand.NextDouble(), s, 1f);
            }

            int numStripes = rand.Next(1, 5);
            int stripe = 0;
            //float pos = 0;
            for (int c1 = 0; c1 < numStripes; ++c1)
            {
                Stripe(pixels, xSize, ySize, (float)rand.NextDouble(), 0.025f + (float)(rand.NextDouble()* 0.05), stripeColors[stripe]);
                //Stripe(pixels, xSize, ySize, pos, 0.025f + (float)(rand.NextDouble() * 0.05), stripeColors[stripe]);

                ++stripe;
                stripe %= numColors;

                //pos += 0.2f;
            }

            tex.SetPixels(pixels);

            tex.wrapMode = TextureWrapMode.Mirror;

            tex.Apply(true);

            return tex;
        }

        void Stripe(Color[] pixels, int xSize, int ySize, float percent, float width, Color col)
        {
            int start = Mathf.RoundToInt(percent * ySize);
            int end = Mathf.Clamp(start + Mathf.RoundToInt(width * ySize), 0, ySize);

            for (int y = start; y < end; ++y)
            {
                for (int x = 0; x < xSize; ++x)
                {
                    pixels[(y * xSize) + x] = col;
                }
            }
        }

        public Texture2D GenerateCanopy(int seed)
        {
            System.Random rand = new System.Random(seed);

            Color glassColor = new Color(0,0,0,1);

            double glassRnd = rand.NextDouble();
            if (glassRnd < 0.33)
            {
                glassColor.r = 0.2f;
            }
            else if (glassRnd < 0.66)
            {
                glassColor.b = 0.2f;
            }

            int size = 512;

            var tex = new Texture2D(size, size, TextureFormat.ARGB32, false);

            var pixels = tex.GetPixels(0, 0, size, size);

            var white = Color.white;

            for (int c1 = 0; c1 < size * size; ++c1)
            {
                pixels[c1] = white;
            }

            float start = 0.4f + ((float)rand.NextDouble() * 0.3f);

            int len = Mathf.RoundToInt(start * size);

            int half = size / 2;

            Circle(pixels, half, size, len, glassColor, false);


            // rear ring
            if(start > 0.5f && rand.NextDouble() < 0.5)
            {
                start = 0.7f + ((float)rand.NextDouble() * 0.1f);
                int ring = Mathf.RoundToInt(start * len);
                int thickness = rand.Next(8, 14);

                Circle(pixels, half, size, ring + thickness, white, false);
                Circle(pixels, half, size, ring, glassColor, false);
            }

            // front ring
            if(rand.NextDouble() < 0.5)
            {
                start = 0.2f + ((float)rand.NextDouble() * 0.1f);
                int ring = Mathf.RoundToInt(start * len);
                int thickness = rand.Next(6, 10);

                Circle(pixels, half, size, ring + thickness, white, false);
                Circle(pixels, half, size, ring, glassColor, false);
            }

            // front disc
            if(rand.NextDouble() < 0.5f)
            {
                int ring = Mathf.RoundToInt(0.1f * len);
                Circle(pixels, half, size, ring, white, false);
            }

            // sides
            int amount = Mathf.RoundToInt((0.6f + ((float)rand.NextDouble() * 0.2f)) * size);
            for (int y = 0; y < size; ++y)
            {
                for (int x = 0; x < size; ++x)
                {
                    if(x > amount || (x < size-amount))
                    {
                        pixels[(y * size) + x] = white;
                    }
                }
            }

            tex.SetPixels(pixels);

            tex.wrapMode = TextureWrapMode.Mirror;

            tex.Apply(true);

            return tex;
        }

        public Texture2D GenerateMainColor(int seed, ref float h, ref float gloss)
        {
            IRand rand = Rand.Create(seed);

            int size = 1024;

            var tex = new Texture2D(size, size, TextureFormat.ARGB32, true);

            var pixels = new Color[size * size];

            float type = rand.Float();

            if (type < 0.4f)
            {
                NoiseCamouflage(pixels, size, rand, ref h);

                gloss = rand.Float(0.4f, 0.6f);
            }
            else if (type < 0.8f)
            {
                RectCamouflage(pixels, size, rand, ref h);

                gloss = rand.Float(0.4f, 0.6f);
            }
            else
            {
                Plain(pixels, size, rand, ref h);

                gloss = rand.Float(0.5f, 0.9f);
            }

            tex.SetPixels(pixels);

            tex.wrapMode = TextureWrapMode.Mirror;

            tex.Apply(true);

            return tex;
        }

        void Plain(Color[] pixels, int size, IRand rand, ref float h)
        {
            float hue = rand.Float();// 0.5f;
            float bright = 0.2f + (rand.Float() * 0.2f);
            float saturation = 0.5f + (rand.Float() * 0.4f);

            Color col1 = Color.HSVToRGB(hue, saturation, bright);

            float hue2 = hue + rand.Float(-0.1f, 0.1f);
            Color col2 = Color.HSVToRGB(hue2, saturation, bright * 0.1f);

            h = hue;

            for (int x = 0; x < size; ++x)
            {
                float nx = (float)x / (size-1);
                nx *= 2;
                nx -= 1;
                nx *= (nx < 0) ? -1f : 1f;

                var c = Color.Lerp(col1, col2, nx);

                for (int y = 0; y < size; ++y)
                {
                    pixels[(y * size) + x] = c;
                }
            }
        }

        void NoiseCamouflage(Color[] pixels, int size, IRand rand, ref float h)
        {
            float s = rand.Float() * 10f;

            float noiseSize = 0.005f;   // 0.0055=large   0.03=small
            float threshold = 0.5f;

            float hue = rand.Float();
            h = hue;
            float hueAdd = (rand.Float() * 0.15f) * (rand.Float() < 0.5 ? -1 : 1);
            float bright = 0.4f + (rand.Float() * 0.6f);
            
            float saturation = 0;
            if(rand.Float() > 0.1f)
            {
                saturation = 0.5f + (rand.Float() * 0.4f);
            }

            Color col = Color.HSVToRGB(hue, saturation, bright);

            for (int c1 = 0; c1 < size * size; ++c1)
            {
                pixels[c1] = col;
            }

            for (int c1 = 0; c1 < 3; ++c1)
            {
                bright *= 0.5f;
                hue += hueAdd;
                if (hue < 0)
                    hue += 1;
                else
                    hue %= 1f;
                col = Color.HSVToRGB(hue, saturation, bright);

                for (int y = 0; y < size; ++y)
                {
                    for (int x = 0; x < size; ++x)
                    {
                        float nx = x;
                        float ny = y;

                        float n = Mathf.PerlinNoise(s + nx * noiseSize, s + ny * noiseSize);

                        if (n > threshold)
                        {
                            pixels[(y * size) + x] = col;
                        }
                    }
                }

                noiseSize += 0.005f;
            }
        }

        void RectCamouflage(Color[] pixels, int size, IRand rand, ref float h)
        {
            float hue = rand.Float();
            h = hue;
            float hueAdd = (rand.Float() * 0.15f) * (rand.Float() < 0.5 ? -1 : 1);
            float bright = 0.4f + (rand.Float() * 0.6f);

            float saturation = 0;
            if (rand.Float() > 0.1f)
            {
                saturation = 0.5f + (rand.Float() * 0.4f);
            }

            Color col = Color.HSVToRGB(hue, saturation, bright);

            for (int c1 = 0; c1 < size * size; ++c1)
            {
                pixels[c1] = col;
            }

            int numR = 10;
            Vector4 sz = new Vector4(300, 500, 300, 500);

            for (int c1 = 0; c1 < 4; ++c1)
            {
                bright *= 0.5f;
                hue += hueAdd;
                if (hue < 0)
                    hue += 1;
                else
                    hue %= 1f;
                col = Color.HSVToRGB(hue, saturation, bright);

                for (int c2 = 0; c2 < numR; ++c2)
                {
                    AddRect(pixels, size, rand.Int(0, size), rand.Int(0, size), rand.Int((int)sz.x, (int)sz.y), rand.Int((int)sz.z, (int)sz.w), col);
                }

                sz *= 0.6f;
            }
        }

        void AddRect(Color[] pixels, int size, int xPos, int yPos, int xSize, int ySize, Color col)
        {
            int minX = Mathf.Max(0, xPos);
            int maxX = Mathf.Min(size-1, xPos + xSize);

            int minY = Mathf.Max(0, yPos);
            int maxY = Mathf.Min(size-1, yPos + ySize);

            for (int y = minY; y < maxY; ++y)
            {
                for (int x = minX; x < maxX; ++x)
                {
                    int index = (y * size) + x;
                    pixels[index] = col;
                }
            }
        }

        void Circle(Color[] pixels, int xPos, int yPos, int rad, Color col, bool clamp)
        {
            for (int x = -rad; x < rad; ++x)
            {
                int height = Mathf.RoundToInt(Mathf.Sqrt(rad * rad - x * x));

                for (int y = -height; y < height; ++y)
                {
                    int xx = x + xPos;
                    int yy = y + yPos;

                    if (clamp)
                    {
                        if (xx < 0)
                        {
                            xx += 512;
                        }
                        if (yy < 0)
                        {
                            yy += 512;
                        }

                        xx %= 512;
                        yy %= 512;
                    }
                    else if(xx < 0 || xx >= 512 || yy < 0 || yy >= 512)
                    {
                        continue;
                    }

                    pixels[(yy * 512) + xx] = col;
                }
            }
        }

        void Panel(Color[] pixels, int x, int y, int xSize, int ySize)
        {
            int hx = xSize / 2;
            int hy = ySize / 2;

            HorizontalLine(pixels, x - hx, xSize, y - hy);
            HorizontalLine(pixels, x - hx, xSize, y + hy);

            VerticalLine(pixels, y - hy, ySize, x - hx);
            VerticalLine(pixels, y - hy, ySize, x + hx);
        }

        void HorizontalLine(Color[] pixels, int xStart, int length, int yPos)
        {
            if (yPos < 0)
                yPos += 512;
            yPos %= 512;

            for (int c1 = 0; c1 < length; ++c1)
            {
                int x = xStart + c1;
                if (x < 0)
                    x += 512;
                x %= 512;

                pixels[(yPos * 512) + x] = Color.black;
            }
        }

        void VerticalLine(Color[] pixels, int yStart, int length, int xPos)
        {
            if (xPos < 0)
                xPos += 512;
            xPos %= 512;

            for (int c1 = 0; c1 < length; ++c1)
            {
                int y = yStart + c1;
                if (y < 0)
                    y += 512;
                y %= 512;

                pixels[(y * 512) + xPos] = Color.black;
            }
        }

        /*private void Blur(Color[] pixels, int blurSize)
        {
            // look at every pixel in the blur rectangle
            for (int xx = 0; xx < 1024; xx++)
            {
                for (int yy = 0; yy < 1024; yy++)
                {
                    float avgR = 0, avgG = 0, avgB = 0, avgA = 0;
                    int blurPixelCount = 0;

                    for (int x = xx; (x < xx + blurSize && x < 1024) ; x++)
                    {
                        for (int y = yy; (y < yy + blurSize && y < 1024) ; y++)
                        {
                            Color pixel = pixels[(y * 1024) + x];

                            avgR += pixel.r;
                            avgG += pixel.g;
                            avgB += pixel.b;
                            avgA += pixel.a;

                            blurPixelCount++;
                        }
                    }

                    avgR = avgR / blurPixelCount;
                    avgG = avgG / blurPixelCount;
                    avgB = avgB / blurPixelCount;
                    avgA = avgA / blurPixelCount;

                    for (int x = xx; x < xx + blurSize && x < 1024; x++)
                            for (int y = yy; y < yy + blurSize && y < 1024; y++)
                            pixels[(y * 1024) + x] = new Color(avgR, avgG, avgB, avgA);
                }
            }
        }*/
    }
}
