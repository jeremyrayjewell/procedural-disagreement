using System.Collections.Generic;
using UnityEngine;

namespace Disagreement
{
    /// <summary>The body/machine/infrastructure entity: a fixed core plus detachable limb chains keyed by region id.</summary>
    public sealed class Figure
    {
        public Transform Root;
        public readonly Dictionary<string, LimbChain> Chains = new Dictionary<string, LimbChain>();

        readonly List<Transform> _slabs = new List<Transform>();
        readonly List<Vector3> _slabRest = new List<Vector3>();

        public void AddTorsoSlab(Transform slab)
        {
            _slabs.Add(slab);
            _slabRest.Add(slab.localScale);
        }

        /// <summary>Slow ventilation of the torso slabs. Purely a function of time.</summary>
        public void EvaluateIdle(float t)
        {
            for (int i = 0; i < _slabs.Count; i++)
            {
                float breath = 1f + 0.014f * Mathf.Sin(t * (2f * Mathf.PI / 4.5f) - i * 0.45f);
                Vector3 rest = _slabRest[i];
                _slabs[i].localScale = new Vector3(rest.x * breath, rest.y, rest.z * breath);
            }
        }
    }

    public static class FigureBuilder
    {
        /// <summary>The figure is authored at roughly human size and scaled up to be monumental.</summary>
        public const float Scale = 1.7f;

        public static string ArmRegion(int side) { return side > 0 ? "arm+x" : "arm-x"; }
        public static string LegRegion(int side) { return side > 0 ? "leg+x" : "leg-x"; }

        /// <summary>
        /// Builds the figure with its feet at <paramref name="localPosition"/>, facing -Z (the camera).
        /// Dimensions below are in figure units (multiply by <see cref="Scale"/> for metres).
        /// </summary>
        public static Figure Build(Transform parent, Vector3 localPosition, MaterialSet mats)
        {
            Figure figure = new Figure();
            Transform root = Geo.Group("Figure", parent, localPosition, Quaternion.identity);
            root.localScale = Vector3.one * Scale;
            figure.Root = root;

            Transform core = Geo.Group("Core", root);

            Geo.Box("Pelvis", core, new Vector3(0f, 1.06f, 0f), new Vector3(0.40f, 0.16f, 0.24f), mats.Body);

            // Torso: stacked slabs, widening toward the shoulders.
            float[] slabWidths = { 0.34f, 0.37f, 0.41f, 0.46f, 0.50f };
            for (int i = 0; i < slabWidths.Length; i++)
            {
                float y = 1.16f + 0.0425f + i * 0.097f;
                float depth = 0.22f + i * 0.01f;
                Renderer slab = Geo.Box("TorsoSlab" + i, core, new Vector3(0f, y, 0f), new Vector3(slabWidths[i], 0.085f, depth), mats.Body);
                figure.AddTorsoSlab(slab.transform);
            }

            // Machine parts on the back.
            Geo.Cylinder("Spine", core, new Vector3(0f, 1.38f, 0.14f), 0.035f, 0.60f, mats.Joint);
            Geo.Cylinder("TankPlusX", core, new Vector3(0.20f, 1.25f, 0.13f), 0.05f, 0.25f, mats.Structure);
            Geo.Cylinder("TankMinusX", core, new Vector3(-0.20f, 1.25f, 0.13f), 0.05f, 0.25f, mats.Structure);

            // Risers: the body is plumbed into the room through the overhead lamp.
            float riserBottom = 1.5f;
            float riserTop = (ChamberBuilder.LampUnderside - localPosition.y) / Scale;
            float riserMid = (riserBottom + riserTop) * 0.5f;
            Geo.Cylinder("RiserPlusX", core, new Vector3(0.09f, riserMid, 0.16f), 0.022f, riserTop - riserBottom, mats.Structure);
            Geo.Cylinder("RiserMinusX", core, new Vector3(-0.09f, riserMid, 0.16f), 0.022f, riserTop - riserBottom, mats.Structure);

            // Head: featureless block with a dark sensor band.
            Geo.Cylinder("Neck", core, new Vector3(0f, 1.69f, 0f), 0.05f, 0.08f, mats.Joint);
            Geo.Box("Head", core, new Vector3(0f, 1.85f, 0f), new Vector3(0.19f, 0.24f, 0.21f), mats.Body);
            Geo.Box("SensorBand", core, new Vector3(0f, 1.87f, -0.10f), new Vector3(0.15f, 0.07f, 0.03f), mats.Joint);

            for (int side = -1; side <= 1; side += 2)
            {
                // Arms hang from the shoulder, splayed slightly outward.
                LimbChain arm = LimbChain.Build(ArmRegion(side), root,
                    new Vector3(side * 0.31f, 1.60f, 0f), Quaternion.Euler(0f, 0f, side * 8f),
                    ArmSpecs(), mats.Body, mats.Joint);
                figure.Chains.Add(arm.RegionId, arm);

                LimbChain leg = LimbChain.Build(LegRegion(side), root,
                    new Vector3(side * 0.13f, 1.00f, 0f), Quaternion.identity,
                    LegSpecs(), mats.Body, mats.Joint);
                figure.Chains.Add(leg.RegionId, leg);
            }

            return figure;
        }

        // Module order matters: cut indices in ProcedureVariant refer to positions in these arrays.
        static SegmentSpec[] ArmSpecs()
        {
            return new[]
            {
                SegmentSpec.Ball(0.10f, 0.13f),             // 0  shoulder
                SegmentSpec.Slice(0.07f, 0.105f, 0.115f),   // 1  upper arm
                SegmentSpec.Slice(0.07f, 0.105f, 0.115f),   // 2
                SegmentSpec.Slice(0.07f, 0.105f, 0.115f),   // 3
                SegmentSpec.Slice(0.07f, 0.105f, 0.115f),   // 4
                SegmentSpec.Ball(0.08f, 0.10f),             // 5  elbow
                SegmentSpec.Slice(0.06f, 0.09f, 0.095f),    // 6  forearm
                SegmentSpec.Slice(0.06f, 0.09f, 0.095f),    // 7
                SegmentSpec.Slice(0.06f, 0.09f, 0.095f),    // 8
                SegmentSpec.Slice(0.06f, 0.09f, 0.095f),    // 9
                SegmentSpec.Slice(0.10f, 0.05f, 0.10f),     // 10 hand
            };
        }

        static SegmentSpec[] LegSpecs()
        {
            SegmentSpec foot = SegmentSpec.Slice(0.05f, 0.13f, 0.26f);
            foot.Offset = new Vector3(0f, 0f, -0.05f);
            return new[]
            {
                SegmentSpec.Ball(0.08f, 0.14f),             // 0  hip
                SegmentSpec.Slice(0.12f, 0.15f, 0.16f),     // 1  thigh
                SegmentSpec.Slice(0.12f, 0.15f, 0.16f),     // 2
                SegmentSpec.Slice(0.12f, 0.15f, 0.16f),     // 3
                SegmentSpec.Ball(0.08f, 0.12f),             // 4  knee
                SegmentSpec.Slice(0.11f, 0.12f, 0.13f),     // 5  shin
                SegmentSpec.Slice(0.11f, 0.12f, 0.13f),     // 6
                SegmentSpec.Slice(0.11f, 0.12f, 0.13f),     // 7
                SegmentSpec.Ball(0.04f, 0.09f),             // 8  ankle
                foot,                                       // 9  foot
            };
        }
    }
}
