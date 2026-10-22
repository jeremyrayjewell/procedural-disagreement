using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// Single source of truth for the proof-of-concept's timing.
    /// All times are seconds local to the excerpt; add <see cref="MusicOffset"/> for track time.
    /// Shared by every render profile: nothing here may depend on quality settings.
    /// </summary>
    public static class PocTimeline
    {
        public const int FramesPerSecond = 30;
        public const float Duration = 30f;

        /// <summary>Track time at local t = 0 (the excerpt covers 00:35-01:05).</summary>
        public const float MusicOffset = 35f;

        /// <summary>Root seed for every seeded variation in the scene.</summary>
        public const int Seed = 4401;

        // Cutting plane A (the cut the primary reality performs).
        public const float PlaneAEnter = 5f;
        public const float PlaneAArrive = 9f;
        public const float PlaneARetreatStart = 22f;
        public const float PlaneARetreatEnd = 26f;

        // Cutting plane B (the cut the alternate reality performs).
        public const float PlaneBEnter = 7.5f;
        public const float PlaneBArrive = 11f;
        public const float PlaneBRetreatStart = 25.5f;
        public const float PlaneBRetreatEnd = 29.5f;

        // The planes contest each other's position and the alternate reality splits off.
        public const float DisagreementStart = 10f;
        public const float DivergenceEnd = 14f;

        // The cuts themselves. Everything downstream is timed relative to these
        // by ProcedureVariant (detach, signal loss, infrastructure failure).
        public const float PrimaryCut = 15f;
        public const float AlternateCut = 16.5f;

        public static int FrameCount
        {
            get { return Mathf.RoundToInt(Duration * FramesPerSecond); }
        }

        public static float TimeOfFrame(int frame)
        {
            return frame / (float)FramesPerSecond;
        }
    }
}
