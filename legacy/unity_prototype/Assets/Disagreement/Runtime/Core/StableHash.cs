namespace Disagreement
{
    /// <summary>
    /// Stateless seeded random. A value depends only on (seed, index), never on call order,
    /// so adding or removing objects in one profile cannot shift the randomness of another.
    /// </summary>
    public static class StableHash
    {
        /// <summary>Uniform value in [0, 1).</summary>
        public static float Value(int seed, int index)
        {
            unchecked
            {
                uint h = (uint)seed * 374761393u + (uint)index * 668265263u;
                h = (h ^ (h >> 13)) * 1274126177u;
                h ^= h >> 16;
                return (h & 0xFFFFFFu) / 16777216f;
            }
        }

        public static float Range(int seed, int index, float min, float max)
        {
            return min + (max - min) * Value(seed, index);
        }
    }
}
