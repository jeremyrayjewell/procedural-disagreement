using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// The dependency of one piece of remote infrastructure on one body region:
    /// region -> conduit -> tower. Severing the region is the only thing that can make it fail.
    /// </summary>
    public sealed class DependencyLink
    {
        /// <summary>Sever time for a link whose region is never removed.</summary>
        public const float Never = 1e9f;

        Conduit _conduit;
        InfrastructureTower _tower;

        /// <summary>Builds the link for the arm on <paramref name="side"/> (+1 / -1), mirrored across X.</summary>
        public static DependencyLink Build(Transform parent, int side, MaterialSet mats, int seed)
        {
            DependencyLink link = new DependencyLink();
            string suffix = side > 0 ? "PlusX" : "MinusX";

            // From behind the upper arm, up and over to the side wall, back along the room, down to the tower base.
            Vector3[] path =
            {
                new Vector3(side * 0.58f, 2.98f, 0.14f),
                new Vector3(side * 0.58f, 2.98f, 0.90f),
                new Vector3(side * 0.58f, 5.20f, 0.90f),
                new Vector3(side * 6.30f, 5.20f, 0.90f),
                new Vector3(side * 6.30f, 5.20f, 6.50f),
                new Vector3(side * 6.30f, 0.90f, 6.50f),
                new Vector3(side * 5.60f, 0.90f, 6.50f),
            };
            link._conduit = Conduit.Build(parent, "Conduit" + suffix, path, mats);
            link._tower = InfrastructureTower.Build(parent, "Tower" + suffix, new Vector3(side * 5f, 0f, 6.5f), mats, seed + (side > 0 ? 1 : 2));
            return link;
        }

        public void Evaluate(float t, float severTime, ProcedureVariant variant)
        {
            _conduit.Evaluate(t, severTime, variant.SignalTravelDuration);
            _tower.Evaluate(t, severTime + variant.SignalTravelDuration, variant);
        }
    }
}
