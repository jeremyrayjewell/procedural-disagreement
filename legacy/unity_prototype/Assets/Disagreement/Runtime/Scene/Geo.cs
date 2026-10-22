using UnityEngine;
using UnityEngine.Rendering;

namespace Disagreement
{
    /// <summary>Primitive-geometry helpers. Everything visible in the graybox is made through here.</summary>
    public static class Geo
    {
        public static Transform Group(string name, Transform parent)
        {
            return Group(name, parent, Vector3.zero, Quaternion.identity);
        }

        public static Transform Group(string name, Transform parent, Vector3 localPosition, Quaternion localRotation)
        {
            Transform t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = localPosition;
            t.localRotation = localRotation;
            return t;
        }

        public static Renderer Box(string name, Transform parent, Vector3 center, Vector3 size, Material material, bool castShadows = true)
        {
            return Make(PrimitiveType.Cube, name, parent, center, size, material, castShadows);
        }

        /// <summary>Cylinder along local Y.</summary>
        public static Renderer Cylinder(string name, Transform parent, Vector3 center, float radius, float height, Material material, bool castShadows = true)
        {
            // Unity's cylinder primitive is 2 units tall with radius 0.5.
            Vector3 scale = new Vector3(radius * 2f, height * 0.5f, radius * 2f);
            return Make(PrimitiveType.Cylinder, name, parent, center, scale, material, castShadows);
        }

        public static Renderer Sphere(string name, Transform parent, Vector3 center, float diameter, Material material, bool castShadows = true)
        {
            return Make(PrimitiveType.Sphere, name, parent, center, Vector3.one * diameter, material, castShadows);
        }

        /// <summary>Square sheet in local XY, never casts or receives shadows.</summary>
        public static Renderer Quad(string name, Transform parent, float size, Material material)
        {
            Renderer r = Make(PrimitiveType.Quad, name, parent, Vector3.zero, new Vector3(size, size, 1f), material, false);
            r.receiveShadows = false;
            return r;
        }

        static Renderer Make(PrimitiveType type, string name, Transform parent, Vector3 center, Vector3 scale, Material material, bool castShadows)
        {
            GameObject go = GameObject.CreatePrimitive(type);
            go.name = name;

            // Nothing in this project uses physics; colliders would only invite non-determinism.
            Collider collider = go.GetComponent<Collider>();
            if (collider != null) Object.DestroyImmediate(collider);

            Transform t = go.transform;
            t.SetParent(parent, false);
            t.localPosition = center;
            t.localScale = scale;

            Renderer r = go.GetComponent<Renderer>();
            r.sharedMaterial = material;
            r.shadowCastingMode = castShadows ? ShadowCastingMode.On : ShadowCastingMode.Off;
            return r;
        }
    }
}
