using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    using CreateInterface = System.Func<int, IRand>;

    public interface IRand
    {
        void Init(int seed);

        /// <summary>
        /// Generate an int
        /// </summary>
        /// <returns>value between 0 and max int</returns>
        int Int();

        /// <summary>
        /// Generate an integer within the range
        /// </summary>
        /// <param name="min"></param>
        /// <param name="maxInclusive"></param>
        /// <returns></returns>
        int Int(int min, int maxInclusive);

        /// <summary>
        /// Generate a float
        /// </summary>
        /// <returns>value between 0 and max float</returns>
        float Float();

        /// <summary>
        /// Generate a float within the range
        /// </summary>
        /// <param name="min"></param>
        /// <param name="maxInclusive"></param>
        /// <returns></returns>
        float Float(float min, float maxInclusive);
    }

    /// <summary>
    /// Overridable wrapper for an RNG used internally by the Plane classes.
    /// </summary>
    public class Rand
    {
        public static CreateInterface CreateInstance = DefaultRand.Create;

        /// <summary>
        /// Define which RNG the Plane generation will use.
        /// </summary>
        /// <param name="createRand"></param>
        public static void SetCreate(CreateInterface createRand)
        {
            CreateInstance = createRand;
        }

        public static IRand Create(int seed)
        {
            return CreateInstance(seed);
        }
    }

    /// <summary>
    /// RNG using the System.Random class
    /// </summary>
    public class DefaultRand : IRand
    {
        System.Random rand;

        public static IRand Create(int seed)
        {
            var res = new DefaultRand();
            res.Init(seed);
            return res;
        }

        public void Init(int seed)
        {
            rand = new System.Random(seed);
        }

        public int Int()
        {
            return rand.Next();
        }

        public int Int(int min, int maxInclusive)
        {
            return min + Mathf.RoundToInt((float)rand.NextDouble() * (maxInclusive - min));
        }

        public float Float()
        {
            return (float)rand.NextDouble();
        }

        public float Float(float min, float max)
        {
            return min + ((float)rand.NextDouble() * (max - min));
        }
    }
}