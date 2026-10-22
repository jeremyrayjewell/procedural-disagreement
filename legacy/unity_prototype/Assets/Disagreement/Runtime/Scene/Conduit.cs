using System.Collections.Generic;
using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// A segmented duct along a polyline from a body region (u = 0) to its infrastructure (u = 1).
    /// Energy pulses travel body-to-infrastructure; when the region is severed, darkness follows
    /// the same route, so the viewer can trace cause to effect across the room.
    /// </summary>
    public sealed class Conduit
    {
        const float Thickness = 0.09f;
        const float Pitch = 0.40f;
        const float SegmentGap = 0.07f;
        const float Waves = 5f;
        const float WaveSpeed = 0.55f;

        readonly List<Renderer> _segments = new List<Renderer>();
        readonly List<float> _u = new List<float>();
        MaterialSet _mats;

        public static Conduit Build(Transform parent, string name, Vector3[] path, MaterialSet mats)
        {
            Conduit conduit = new Conduit();
            conduit._mats = mats;
            Transform root = Geo.Group(name, parent);

            float total = 0f;
            for (int i = 1; i < path.Length; i++) total += Vector3.Distance(path[i - 1], path[i]);

            float travelled = 0f;
            for (int i = 1; i < path.Length; i++)
            {
                Vector3 a = path[i - 1];
                Vector3 b = path[i];
                float legLength = Vector3.Distance(a, b);
                Vector3 dir = (b - a) / legLength;
                Vector3 up = Mathf.Abs(dir.y) > 0.99f ? Vector3.forward : Vector3.up;
                Quaternion rotation = Quaternion.LookRotation(dir, up);

                int count = Mathf.Max(1, Mathf.FloorToInt(legLength / Pitch));
                float step = legLength / count;
                for (int s = 0; s < count; s++)
                {
                    float along = (s + 0.5f) * step;
                    Renderer r = Geo.Box("Segment", root, a + dir * along, new Vector3(Thickness, Thickness, step - SegmentGap), mats.Conduit);
                    r.transform.localRotation = rotation;
                    conduit._segments.Add(r);
                    conduit._u.Add((travelled + along) / total);
                }
                travelled += legLength;

                if (i < path.Length - 1)
                {
                    Geo.Box("Elbow", root, b, Vector3.one * (Thickness * 1.6f), mats.Structure);
                }
            }
            return conduit;
        }

        /// <param name="severTime">When the body end is cut; pass <see cref="DependencyLink.Never"/> for an intact conduit.</param>
        /// <param name="travelDuration">Seconds for the darkness to reach the infrastructure end.</param>
        public void Evaluate(float t, float severTime, float travelDuration)
        {
            // Front of the darkness, slightly overshooting both ends so every segment fully dies.
            float front = Mathf.Lerp(-0.06f, 1.06f, Ease.Window(t, severTime, severTime + travelDuration));
            bool severed = t >= severTime;

            for (int i = 0; i < _segments.Count; i++)
            {
                float u = _u[i];
                float wave = 0.5f + 0.5f * Mathf.Sin(2f * Mathf.PI * (u * Waves - t * WaveSpeed));
                float energy = 0.22f + 0.78f * wave * wave * wave;
                if (severed) energy *= Ease.SmoothWindow(u, front - 0.05f, front + 0.05f);
                _mats.SetEnergy(_segments[i], energy);
            }
        }
    }
}
