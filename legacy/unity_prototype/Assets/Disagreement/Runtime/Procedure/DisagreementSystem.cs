using UnityEngine;

namespace Disagreement
{
    /// <summary>One translucent cutting plane and the timing of its appearance.</summary>
    public sealed class CuttingPlane
    {
        static readonly int OpacityId = Shader.PropertyToID("_Opacity");
        const float Size = 1.3f;

        public Reality Owner;
        public Reality Rival;
        public float Enter;
        public float Arrive;
        public float RetreatStart;
        public float RetreatEnd;
        /// <summary>Where the plane waits before sliding in, relative to its cut.</summary>
        public Vector3 EntryOffset;
        /// <summary>Phase of the contest oscillation; the two planes are in antiphase.</summary>
        public float Phase;

        Transform _transform;
        Renderer _renderer;
        Material _material;

        public static CuttingPlane Build(Transform parent, string name, Material material)
        {
            CuttingPlane plane = new CuttingPlane();
            plane._material = material;
            plane._renderer = Geo.Quad(name, parent, Size, material);
            plane._transform = plane._renderer.transform;
            return plane;
        }

        public void Evaluate(float t)
        {
            ProcedureVariant v = Owner.Variant;
            Vector3 cut = Owner.CutWorldPoint;
            float cutTime = v.CutTime;

            float arrive = Ease.Smoother(Ease.Window(t, Enter, Arrive));

            // The contest: while both planes are present each one lunges toward the other's cut,
            // then settles exactly on its own before it is carried out.
            float contest = Ease.Pulse(t, PocTimeline.DisagreementStart, PocTimeline.DisagreementStart + 1f, cutTime - 0.6f, cutTime);
            float wobble = Mathf.Sin(t * (2f * Mathf.PI / 1.7f) + Phase);
            float lunge = contest * Mathf.Max(0f, wobble);

            Vector3 position = cut + EntryOffset * (1f - arrive) + (Rival.CutWorldPoint - cut) * (0.3f * lunge);

            // Quad normal along the limb axis, plus this procedure's tilt and a little unrest.
            Quaternion clean = Quaternion.LookRotation(Owner.CutAxisWorld, Vector3.forward);
            Quaternion tilt = Quaternion.Euler(v.PlaneTiltEuler + new Vector3(2.5f, 0f, 3.5f) * (contest * wobble));

            // Flash as the cut is carried out, then stay as a dimmer record of it until the retreat.
            float flash = Ease.Pulse(t, cutTime - 0.15f, cutTime, cutTime + 0.1f, cutTime + 1.2f);
            float opacity = arrive * (0.6f + 0.3f * contest * wobble);
            opacity += 0.9f * flash;
            opacity *= 1f - 0.45f * Ease.SmoothWindow(t, cutTime + 1f, cutTime + 3f);
            opacity *= 1f - Ease.SmoothWindow(t, RetreatStart, RetreatEnd);

            _transform.position = position;
            _transform.rotation = clean * tilt;
            _transform.localScale = Vector3.one * (Size * (1f + 0.12f * flash));
            _material.SetFloat(OpacityId, opacity);
            _renderer.enabled = opacity > 0.002f;
        }
    }

    /// <summary>
    /// The two competing cutting planes. Plane A belongs to the primary reality and plane B to the
    /// alternate; each tracks its own reality's cut point, so when the alternate drifts away
    /// plane B goes with it.
    /// </summary>
    public sealed class DisagreementSystem
    {
        CuttingPlane _planeA;
        CuttingPlane _planeB;

        public static DisagreementSystem Build(Transform parent, MaterialLibrary library, Reality primary, Reality alternate)
        {
            DisagreementSystem system = new DisagreementSystem();
            Transform root = Geo.Group("Disagreement", parent);

            system._planeA = CuttingPlane.Build(root, "PlaneA", library.Plane("PlaneA", MaterialLibrary.PlaneAColor));
            system._planeA.Owner = primary;
            system._planeA.Rival = alternate;
            system._planeA.Enter = PocTimeline.PlaneAEnter;
            system._planeA.Arrive = PocTimeline.PlaneAArrive;
            system._planeA.RetreatStart = PocTimeline.PlaneARetreatStart;
            system._planeA.RetreatEnd = PocTimeline.PlaneARetreatEnd;
            system._planeA.EntryOffset = new Vector3(2.5f, 0.6f, 0f);
            system._planeA.Phase = 0f;

            system._planeB = CuttingPlane.Build(root, "PlaneB", library.Plane("PlaneB", MaterialLibrary.PlaneBColor));
            system._planeB.Owner = alternate;
            system._planeB.Rival = primary;
            system._planeB.Enter = PocTimeline.PlaneBEnter;
            system._planeB.Arrive = PocTimeline.PlaneBArrive;
            system._planeB.RetreatStart = PocTimeline.PlaneBRetreatStart;
            system._planeB.RetreatEnd = PocTimeline.PlaneBRetreatEnd;
            system._planeB.EntryOffset = new Vector3(0f, 1.8f, -1.2f);
            system._planeB.Phase = Mathf.PI;

            return system;
        }

        public void Evaluate(float t)
        {
            _planeA.Evaluate(t);
            _planeB.Evaluate(t);
        }
    }
}
