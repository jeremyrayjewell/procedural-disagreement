using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// Remote infrastructure kept alive by a body region: a column with a turning rotor,
    /// a stack of indicator cells and a head section. While its region is attached it runs;
    /// once the loss of signal arrives it fails in the way its <see cref="ProcedureVariant"/> dictates.
    /// </summary>
    public sealed class InfrastructureTower
    {
        public const int CellCount = 6;
        const float SpinDegreesPerSecond = 120f;
        const float HeadBaseHeight = 3.7f;

        Transform _rotor;
        Transform _head;
        Renderer[] _cells;
        Renderer _headCell;
        MaterialSet _mats;
        int _seed;

        public static InfrastructureTower Build(Transform parent, string name, Vector3 position, MaterialSet mats, int seed)
        {
            InfrastructureTower tower = new InfrastructureTower();
            tower._mats = mats;
            tower._seed = seed;

            Transform root = Geo.Group(name, parent, position, Quaternion.identity);

            Geo.Box("Base", root, new Vector3(0f, 0.25f, 0f), new Vector3(1.4f, 0.5f, 1.4f), mats.Structure);
            Geo.Cylinder("Column", root, new Vector3(0f, 2.1f, 0f), 0.32f, 3.2f, mats.Body);

            // Rotor: six blades so the rotation, and its stopping, reads at a distance.
            tower._rotor = Geo.Group("Rotor", root, new Vector3(0f, 2.9f, 0f), Quaternion.identity);
            Geo.Cylinder("Hub", tower._rotor, Vector3.zero, 0.5f, 0.12f, mats.Joint);
            for (int i = 0; i < 6; i++)
            {
                Transform arm = Geo.Group("BladeArm" + i, tower._rotor, Vector3.zero, Quaternion.Euler(0f, i * 60f, 0f));
                Geo.Box("Blade", arm, new Vector3(0.85f, 0f, 0f), new Vector3(0.9f, 0.08f, 0.22f), mats.Structure);
            }

            // Indicator cells face the camera. Index 0 is the top cell and the first to be lost.
            tower._cells = new Renderer[CellCount];
            for (int i = 0; i < CellCount; i++)
            {
                float y = 2.4f - i * 0.3f;
                tower._cells[i] = Geo.Box("Cell" + i, root, new Vector3(0f, y, -0.36f), new Vector3(0.30f, 0.22f, 0.08f), mats.Cell);
            }

            // Head: the part that separates. Pivot at its base so it can tilt over.
            tower._head = Geo.Group("Head", root, new Vector3(0f, HeadBaseHeight, 0f), Quaternion.identity);
            Geo.Box("HeadBlock", tower._head, new Vector3(0f, 0.3f, 0f), new Vector3(1.0f, 0.5f, 1.0f), mats.Structure);
            Geo.Cylinder("HeadCap", tower._head, new Vector3(0f, 0.7f, 0f), 0.25f, 0.3f, mats.Body);
            tower._headCell = Geo.Box("HeadCell", tower._head, new Vector3(0f, 0.3f, -0.52f), new Vector3(0.6f, 0.16f, 0.06f), mats.Cell);

            return tower;
        }

        /// <param name="failTime">When the loss of signal arrives; <see cref="DependencyLink.Never"/> keeps the tower running.</param>
        public void Evaluate(float t, float failTime, ProcedureVariant variant)
        {
            _rotor.localRotation = Quaternion.Euler(0f, RotorAngle(t, failTime, variant), 0f);

            for (int i = 0; i < _cells.Length; i++)
            {
                float energy = 0.8f + 0.2f * Mathf.Sin(t * 1.7f + i * 0.9f);
                if (i < variant.TowerCellsLost)
                {
                    float darkTime = failTime + 0.5f + i * 0.4f;
                    if (t > darkTime - 0.6f && t < darkTime)
                    {
                        // Stutter before dying. Hashed on a fixed 14 Hz clock, so it does not depend on frame rate.
                        energy *= 0.35f + 0.65f * StableHash.Value(_seed + i, Mathf.FloorToInt(t * 14f));
                    }
                    energy *= 1f - Ease.Window(t, darkTime, darkTime + 0.2f);
                }
                _mats.SetEnergy(_cells[i], energy);
            }

            _mats.SetEnergy(_headCell, 1f - Ease.SmoothWindow(t, failTime, failTime + 0.3f));

            float h = Ease.Smoother(Ease.Window(t, failTime + 1f, failTime + 4.5f));
            _head.localPosition = new Vector3(0f, HeadBaseHeight + variant.TowerHeadLift * h, 0f);
            _head.localRotation = Quaternion.Slerp(Quaternion.identity, Quaternion.Euler(variant.TowerHeadEuler), h);
        }

        /// <summary>
        /// Closed-form integral of the rotor speed, so the angle at time t never depends on
        /// how many frames were evaluated before it.
        /// Speed is constant until failure, then eases quadratically to the residual fraction.
        /// </summary>
        static float RotorAngle(float t, float failTime, ProcedureVariant variant)
        {
            if (t <= failTime) return SpinDegreesPerSecond * t;

            float d = variant.TowerSpinDownDuration;
            float r = variant.TowerResidualSpin;
            float u = Mathf.Clamp01((t - failTime) / d);
            float v = 1f - u;
            float duringSpinDown = d * (r * u + (1f - r) * (1f - v * v * v) / 3f);
            float afterSpinDown = r * Mathf.Max(0f, t - failTime - d);
            return SpinDegreesPerSecond * (failTime + duringSpinDown + afterSpinDown);
        }
    }
}
