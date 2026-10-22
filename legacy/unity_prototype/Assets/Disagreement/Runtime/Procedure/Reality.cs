using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// One complete version of events: a figure, its dependent infrastructure and the procedure
    /// performed on it. The primary reality is solid; alternates are built by the same code with
    /// a ghost material set and a different <see cref="ProcedureVariant"/>.
    /// </summary>
    public sealed class Reality
    {
        public ProcedureVariant Variant { get; private set; }
        public Transform Root { get; private set; }

        Figure _figure;
        LimbChain _cutChain;
        DependencyLink _cutLink;
        DependencyLink _idleLink;
        MaterialSet _mats;

        public static Reality Build(Transform parent, ProcedureVariant variant, MaterialSet mats, int seed)
        {
            Reality reality = new Reality();
            reality.Variant = variant;
            reality._mats = mats;
            reality.Root = Geo.Group("Reality_" + variant.Name, parent);

            reality._figure = FigureBuilder.Build(reality.Root, new Vector3(0f, ChamberBuilder.PlinthHeight, 0f), mats);
            reality._cutChain = reality._figure.Chains[variant.RegionId];
            reality._cutChain.PrepareCut(variant.CutSegmentIndex);

            reality._cutLink = DependencyLink.Build(reality.Root, variant.Side, mats, seed);
            if (variant.IncludeIdleDependencies)
            {
                // The opposite arm keeps its own tower running throughout: the control case.
                reality._idleLink = DependencyLink.Build(reality.Root, -variant.Side, mats, seed);
            }
            if (variant.IncludeReceiver) BuildReceiver(reality.Root, mats);

            return reality;
        }

        /// <summary>Where this reality's cut falls, in world space (follows the reality's drift).</summary>
        public Vector3 CutWorldPoint
        {
            get { return _cutChain.CutWorldPoint(Variant.CutSegmentIndex); }
        }

        public Vector3 CutAxisWorld
        {
            get { return _cutChain.AxisWorld; }
        }

        public void Evaluate(float t)
        {
            ProcedureVariant v = Variant;

            // Alternates start coincident with the primary and invisible, then split off.
            float presence = v.IsGhost ? Ease.SmoothWindow(t, PocTimeline.DisagreementStart, PocTimeline.DivergenceEnd) : 1f;
            Root.localPosition = v.RealityOffset * presence;
            if (v.IsGhost)
            {
                bool visible = presence > 0.001f;
                if (Root.gameObject.activeSelf != visible) Root.gameObject.SetActive(visible);
                _mats.SetOpacity(v.GhostOpacity * presence);
            }

            _figure.EvaluateIdle(t);

            // Detachment: a short release along the limb axis, then the authored travel.
            float release = Ease.OutCubic(Ease.Window(t, v.CutTime, v.CutTime + 0.9f));
            float travel = Ease.Smoother(Ease.Window(t, v.CutTime + 0.6f, v.CutTime + v.DetachDuration));
            Vector3 offset = Vector3.down * (v.ReleaseGap * release)
                + _cutChain.Root.InverseTransformVector(v.DetachTravel) * travel;
            Quaternion rotation = Quaternion.Slerp(Quaternion.identity, Quaternion.Euler(v.DetachEuler), travel);
            _cutChain.SetDetachedPose(offset, rotation);

            _cutLink.Evaluate(t, v.CutTime, v);
            if (_idleLink != null) _idleLink.Evaluate(t, DependencyLink.Never, v);
        }

        /// <summary>Tray that collects the removed arm in the primary reality.</summary>
        static void BuildReceiver(Transform parent, MaterialSet mats)
        {
            Transform root = Geo.Group("Receiver", parent, new Vector3(2.15f, 0f, -0.6f), Quaternion.identity);
            Geo.Cylinder("Foot", root, new Vector3(0f, 0.03f, 0f), 0.35f, 0.06f, mats.Structure);
            Geo.Cylinder("Post", root, new Vector3(0f, 0.64f, 0f), 0.08f, 1.28f, mats.Structure);
            Geo.Box("Tray", root, new Vector3(0f, 1.31f, 0f), new Vector3(1.7f, 0.06f, 0.55f), mats.Joint);
        }
    }
}
