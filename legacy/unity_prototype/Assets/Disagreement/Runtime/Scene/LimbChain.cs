using System.Collections.Generic;
using UnityEngine;

namespace Disagreement
{
    /// <summary>One module of a limb chain: a box slice, or a ball joint.</summary>
    public struct SegmentSpec
    {
        public bool Joint;
        /// <summary>Extent along the chain.</summary>
        public float Length;
        public float Width;
        public float Depth;
        /// <summary>Extra offset of the module from the chain axis.</summary>
        public Vector3 Offset;

        public static SegmentSpec Slice(float length, float width, float depth)
        {
            return new SegmentSpec { Length = length, Width = width, Depth = depth };
        }

        public static SegmentSpec Ball(float length, float diameter)
        {
            return new SegmentSpec { Joint = true, Length = length, Width = diameter, Depth = diameter };
        }
    }

    /// <summary>
    /// An ordered stack of modules hanging along the root's local -Y.
    /// A cut is an index into that stack: every module at or beyond the index is moved under
    /// <see cref="Detached"/>, which the owning reality then animates. Different realities
    /// disagree simply by choosing a different index.
    /// </summary>
    public sealed class LimbChain
    {
        public const float Gap = 0.006f;

        public string RegionId;
        public Transform Root;
        public readonly List<Transform> Segments = new List<Transform>();
        public Transform Detached { get; private set; }

        readonly List<float> _tops = new List<float>();
        Vector3 _detachedRest;

        public static LimbChain Build(string regionId, Transform parent, Vector3 origin, Quaternion rotation,
            SegmentSpec[] specs, Material sliceMaterial, Material jointMaterial)
        {
            LimbChain chain = new LimbChain();
            chain.RegionId = regionId;
            chain.Root = Geo.Group(regionId, parent, origin, rotation);

            float cursor = 0f;
            for (int i = 0; i < specs.Length; i++)
            {
                SegmentSpec spec = specs[i];
                Vector3 center = new Vector3(0f, -(cursor + spec.Length * 0.5f), 0f) + spec.Offset;
                Renderer r = spec.Joint
                    ? Geo.Sphere("Joint" + i, chain.Root, center, spec.Width, jointMaterial)
                    : Geo.Box("Slice" + i, chain.Root, center, new Vector3(spec.Width, spec.Length, spec.Depth), sliceMaterial);
                chain.Segments.Add(r.transform);
                chain._tops.Add(cursor);
                cursor += spec.Length + Gap;
            }
            return chain;
        }

        /// <summary>Point on the chain axis, in root space, where module <paramref name="index"/> begins.</summary>
        public Vector3 BoundaryLocal(int index)
        {
            return new Vector3(0f, -(_tops[index] - Gap * 0.5f), 0f);
        }

        public Vector3 CutWorldPoint(int index)
        {
            return Root.TransformPoint(BoundaryLocal(index));
        }

        /// <summary>World direction pointing back up the limb, i.e. the normal of a clean cut.</summary>
        public Vector3 AxisWorld
        {
            get { return Root.up; }
        }

        /// <summary>Regroups modules from <paramref name="index"/> onward under a pivot at the cut.</summary>
        public void PrepareCut(int index)
        {
            _detachedRest = BoundaryLocal(index);
            Detached = Geo.Group("Detached", Root, _detachedRest, Quaternion.identity);
            for (int i = index; i < Segments.Count; i++)
            {
                Segments[i].SetParent(Detached, true);
            }
        }

        /// <summary>Pose of the detached group relative to where it was attached, in root space.</summary>
        public void SetDetachedPose(Vector3 localOffset, Quaternion localRotation)
        {
            Detached.localPosition = _detachedRest + localOffset;
            Detached.localRotation = localRotation;
        }
    }
}
