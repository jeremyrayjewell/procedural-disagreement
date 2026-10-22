using UnityEngine;

namespace Disagreement
{
    /// <summary>Stateless easing helpers. Every animation in the project is built from these and absolute time.</summary>
    public static class Ease
    {
        /// <summary>0 before <paramref name="start"/>, 1 after <paramref name="end"/>, linear between.</summary>
        public static float Window(float t, float start, float end)
        {
            if (end <= start) return t >= end ? 1f : 0f;
            return Mathf.Clamp01((t - start) / (end - start));
        }

        public static float Smooth(float u)
        {
            return u * u * (3f - 2f * u);
        }

        public static float Smoother(float u)
        {
            return u * u * u * (u * (u * 6f - 15f) + 10f);
        }

        public static float OutCubic(float u)
        {
            float v = 1f - u;
            return 1f - v * v * v;
        }

        public static float SmoothWindow(float t, float start, float end)
        {
            return Smooth(Window(t, start, end));
        }

        /// <summary>Rises over [inStart, inEnd], holds at 1, falls over [outStart, outEnd].</summary>
        public static float Pulse(float t, float inStart, float inEnd, float outStart, float outEnd)
        {
            return SmoothWindow(t, inStart, inEnd) * (1f - SmoothWindow(t, outStart, outEnd));
        }
    }
}
