using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// One version of the procedure: where the cut falls, when, how the removed region travels,
    /// and what the dependent infrastructure does about it. A <see cref="Reality"/> is built from
    /// exactly one variant; realities disagree because their variants differ.
    /// Distances are world metres unless noted.
    /// </summary>
    public sealed class ProcedureVariant
    {
        public string Name;

        // Presentation of the reality as a whole.
        public bool IsGhost;
        public float GhostOpacity;
        /// <summary>How far this reality drifts from the primary once the disagreement starts.</summary>
        public Vector3 RealityOffset;

        // The cut.
        /// <summary>+1 or -1: which arm.</summary>
        public int Side;
        /// <summary>Index into the limb chain; modules at or beyond it are removed.</summary>
        public int CutSegmentIndex;
        /// <summary>Tilt of the visible cutting plane away from a clean perpendicular cut.</summary>
        public Vector3 PlaneTiltEuler;
        public float CutTime;

        // Travel of the removed region.
        /// <summary>Initial separation along the limb axis, in figure units.</summary>
        public float ReleaseGap;
        public float DetachDuration;
        public Vector3 DetachTravel;
        /// <summary>Final rotation of the removed region, in limb space.</summary>
        public Vector3 DetachEuler;

        // Consequences for the dependent infrastructure.
        /// <summary>Time for the loss of signal to travel the conduit from body to tower.</summary>
        public float SignalTravelDuration;
        public float TowerSpinDownDuration;
        /// <summary>Fraction of rotor speed that survives (0 = stops dead).</summary>
        public float TowerResidualSpin;
        public int TowerCellsLost;
        public float TowerHeadLift;
        public Vector3 TowerHeadEuler;

        // Scene dressing that only one reality should own.
        public bool IncludeIdleDependencies;
        public bool IncludeReceiver;

        public string RegionId
        {
            get { return FigureBuilder.ArmRegion(Side); }
        }

        /// <summary>Moment the loss of signal reaches the tower.</summary>
        public float TowerFailTime
        {
            get { return CutTime + SignalTravelDuration; }
        }

        /// <summary>
        /// Plane A's version: the whole arm comes off at the shoulder and is laid on the receiver;
        /// the tower stops, goes dark and its head separates.
        /// </summary>
        public static ProcedureVariant Primary()
        {
            return new ProcedureVariant
            {
                Name = "Primary",
                IsGhost = false,
                GhostOpacity = 1f,
                RealityOffset = Vector3.zero,
                Side = 1,
                CutSegmentIndex = 1,
                PlaneTiltEuler = Vector3.zero,
                CutTime = PocTimeline.PrimaryCut,
                ReleaseGap = 0.03f,
                DetachDuration = 6f,
                DetachTravel = new Vector3(0.95f, -1.60f, -0.60f),
                DetachEuler = new Vector3(0f, 0f, 80f),
                SignalTravelDuration = 2.5f,
                TowerSpinDownDuration = 4f,
                TowerResidualSpin = 0f,
                TowerCellsLost = InfrastructureTower.CellCount,
                TowerHeadLift = 0.5f,
                TowerHeadEuler = new Vector3(0f, 25f, 4f),
                IncludeIdleDependencies = true,
                IncludeReceiver = true,
            };
        }

        /// <summary>
        /// Plane B's version: a later, lower, tilted cut leaves a stump; the removed part sinks
        /// instead of being collected; the tower is only crippled and its head slumps.
        /// </summary>
        public static ProcedureVariant Alternate()
        {
            return new ProcedureVariant
            {
                Name = "Alternate",
                IsGhost = true,
                GhostOpacity = 0.55f,
                RealityOffset = new Vector3(0.14f, 0f, -0.08f),
                Side = 1,
                CutSegmentIndex = 4,
                PlaneTiltEuler = new Vector3(9f, 0f, -14f),
                CutTime = PocTimeline.AlternateCut,
                ReleaseGap = 0.03f,
                DetachDuration = 7f,
                DetachTravel = new Vector3(0.30f, -1.05f, -0.40f),
                DetachEuler = new Vector3(14f, 0f, -12f),
                SignalTravelDuration = 3f,
                TowerSpinDownDuration = 5f,
                TowerResidualSpin = 0.3f,
                TowerCellsLost = 3,
                TowerHeadLift = 0f,
                TowerHeadEuler = new Vector3(0f, 0f, -16f),
                IncludeIdleDependencies = false,
                IncludeReceiver = false,
            };
        }
    }
}
