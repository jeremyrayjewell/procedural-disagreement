using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// The clinical chamber: a long ribbed room with ceiling light panels, a central plinth
    /// and an overhead lamp. Static; identical in every profile.
    /// World units are metres, Y up, the camera approaches along +Z.
    /// </summary>
    public static class ChamberBuilder
    {
        public const float HalfWidth = 7f;
        public const float Height = 7f;
        public const float ZMin = -17f;
        public const float ZMax = 11f;
        public const float PlinthHeight = 0.5f;
        /// <summary>Underside of the overhead lamp; the figure's risers end here.</summary>
        public const float LampUnderside = 6.03f;

        public static readonly Color FogColor = new Color(0.74f, 0.78f, 0.78f);

        public static Transform Build(Transform parent, MaterialLibrary library, int seed)
        {
            Transform root = Geo.Group("Chamber", parent);

            Material wall = library.Opaque("ChamberWall", new Color(0.62f, 0.65f, 0.64f));
            Material floor = library.Opaque("ChamberFloor", new Color(0.50f, 0.53f, 0.53f));
            Material trim = library.Opaque("ChamberTrim", new Color(0.30f, 0.32f, 0.33f));
            Material fixture = library.Opaque("ChamberFixture", new Color(0.70f, 0.72f, 0.71f));
            Material panelLight = library.Emissive("ChamberLight", new Color(0.9f, 0.9f, 0.9f), new Color(1.0f, 1.0f, 0.98f) * 1.2f);

            float length = ZMax - ZMin;
            float zMid = (ZMax + ZMin) * 0.5f;

            // Shell. It never casts shadows, otherwise the ceiling would black out the key light.
            Geo.Box("Floor", root, new Vector3(0f, -0.1f, zMid), new Vector3(HalfWidth * 2f + 0.4f, 0.2f, length + 0.4f), floor, false);
            Geo.Box("Ceiling", root, new Vector3(0f, Height + 0.1f, zMid), new Vector3(HalfWidth * 2f + 0.4f, 0.2f, length + 0.4f), wall, false);
            Geo.Box("WallPlusX", root, new Vector3(HalfWidth + 0.1f, Height * 0.5f, zMid), new Vector3(0.2f, Height, length), wall, false);
            Geo.Box("WallMinusX", root, new Vector3(-HalfWidth - 0.1f, Height * 0.5f, zMid), new Vector3(0.2f, Height, length), wall, false);
            Geo.Box("WallBack", root, new Vector3(0f, Height * 0.5f, ZMax + 0.1f), new Vector3(HalfWidth * 2f, Height, 0.2f), wall, false);
            Geo.Box("WallFront", root, new Vector3(0f, Height * 0.5f, ZMin - 0.1f), new Vector3(HalfWidth * 2f, Height, 0.2f), wall, false);

            // Ribs and a dark band along the side walls give the approach its parallax.
            Transform ribs = Geo.Group("Ribs", root);
            for (float z = ZMin + 1f; z < ZMax; z += 2f)
            {
                Geo.Box("Rib", ribs, new Vector3(HalfWidth - 0.175f, Height * 0.5f, z), new Vector3(0.35f, Height, 0.3f), wall);
                Geo.Box("Rib", ribs, new Vector3(-HalfWidth + 0.175f, Height * 0.5f, z), new Vector3(0.35f, Height, 0.3f), wall);
            }
            Geo.Box("BandPlusX", root, new Vector3(HalfWidth - 0.06f, 1.1f, zMid), new Vector3(0.12f, 0.08f, length), trim, false);
            Geo.Box("BandMinusX", root, new Vector3(-HalfWidth + 0.06f, 1.1f, zMid), new Vector3(0.12f, 0.08f, length), trim, false);

            // Floor channels converge on the plinth.
            Geo.Box("ChannelPlusX", root, new Vector3(2.4f, 0.011f, zMid), new Vector3(0.12f, 0.02f, length), trim, false);
            Geo.Box("ChannelMinusX", root, new Vector3(-2.4f, 0.011f, zMid), new Vector3(0.12f, 0.02f, length), trim, false);

            // Back wall panels with seeded relief.
            Transform panels = Geo.Group("BackPanels", root);
            for (int row = 0; row < 3; row++)
            {
                for (int col = 0; col < 5; col++)
                {
                    int index = row * 5 + col;
                    float depth = StableHash.Range(seed, index, 0.05f, 0.18f);
                    Vector3 center = new Vector3(-5.2f + col * 2.6f, 1.25f + row * 2.25f, ZMax - depth * 0.5f);
                    Geo.Box("Panel", panels, center, new Vector3(2.35f, 2.0f, depth), fixture, false);
                }
            }

            // Ceiling light panels.
            Transform lights = Geo.Group("LightPanels", root);
            for (float z = ZMin + 3f; z < ZMax; z += 4f)
            {
                Geo.Box("LightPanel", lights, new Vector3(2.6f, Height - 0.04f, z), new Vector3(2.2f, 0.06f, 0.7f), panelLight, false);
                Geo.Box("LightPanel", lights, new Vector3(-2.6f, Height - 0.04f, z), new Vector3(2.2f, 0.06f, 0.7f), panelLight, false);
            }

            // Seeded cabinets along the side walls. The bay around z = 6.5 is kept clear for the conduit drops.
            Transform cabinets = Geo.Group("Cabinets", root);
            for (int i = 0; i < 9; i++)
            {
                for (int side = -1; side <= 1; side += 2)
                {
                    int index = 100 + i * 2 + (side > 0 ? 1 : 0);
                    float z = ZMin + 2f + i * 3f + StableHash.Range(seed, index, -0.5f, 0.5f);
                    if (Mathf.Abs(z - 6.5f) < 1.8f) continue;
                    float h = StableHash.Range(seed, index + 1000, 0.8f, 1.7f);
                    float w = StableHash.Range(seed, index + 2000, 0.8f, 1.5f);
                    Geo.Box("Cabinet", cabinets, new Vector3(side * (HalfWidth - 0.65f), h * 0.5f, z), new Vector3(0.6f, h, w), fixture);
                }
            }

            // Plinth the figure stands on.
            Geo.Cylinder("PlinthStep", root, new Vector3(0f, 0.09f, 0f), 2.0f, 0.18f, floor);
            Geo.Cylinder("Plinth", root, new Vector3(0f, PlinthHeight * 0.5f, 0f), 1.5f, PlinthHeight, fixture);

            // Overhead lamp.
            Geo.Cylinder("LampStem", root, new Vector3(0f, (Height + 6.17f) * 0.5f, 0f), 0.08f, Height - 6.17f, trim);
            Geo.Cylinder("LampBody", root, new Vector3(0f, 6.1f, 0f), 0.95f, 0.14f, fixture);
            Geo.Cylinder("LampFace", root, new Vector3(0f, LampUnderside - 0.01f, 0f), 0.8f, 0.02f, panelLight, false);

            return root;
        }
    }
}
