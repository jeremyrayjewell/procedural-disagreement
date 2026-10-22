using System.Collections.Generic;
using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// The materials one reality is built from. Builders only ever ask for a role (Body, Joint, ...),
    /// so the same builder produces a solid reality or a translucent one.
    /// </summary>
    public sealed class MaterialSet
    {
        static readonly int EmissionId = Shader.PropertyToID("_EmissionColor");
        static readonly int GlowId = Shader.PropertyToID("_Glow");
        static readonly int OpacityId = Shader.PropertyToID("_Opacity");
        static MaterialPropertyBlock _block;

        public bool IsGhost;
        public Material Body;
        public Material Joint;
        public Material Structure;
        /// <summary>Conduit segments: carry animated energy.</summary>
        public Material Conduit;
        /// <summary>Indicator cells on infrastructure: carry animated energy.</summary>
        public Material Cell;
        public Color EnergyColor;

        /// <summary>Per-renderer energy level (0 = dead, 1 = nominal). Works for solid and ghost sets.</summary>
        public void SetEnergy(Renderer renderer, float energy)
        {
            if (_block == null) _block = new MaterialPropertyBlock();
            _block.Clear();
            if (IsGhost) _block.SetFloat(GlowId, energy);
            else _block.SetColor(EmissionId, EnergyColor * energy);
            renderer.SetPropertyBlock(_block);
        }

        /// <summary>Whole-reality opacity. Only meaningful for ghost sets.</summary>
        public void SetOpacity(float opacity)
        {
            if (IsGhost) Body.SetFloat(OpacityId, opacity);
        }
    }

    /// <summary>Creates and owns every material in the scene so they can be destroyed on rebuild.</summary>
    public sealed class MaterialLibrary
    {
        public static readonly Color PlaneAColor = new Color(0.30f, 0.82f, 1.00f, 0.36f);
        public static readonly Color PlaneBColor = new Color(1.00f, 0.60f, 0.18f, 0.36f);
        /// <summary>The alternate reality is tinted like the plane that produces it.</summary>
        public static readonly Color GhostTint = new Color(1.00f, 0.62f, 0.22f, 1.00f);
        static readonly Color EnergyColor = new Color(0.55f, 0.90f, 1.00f) * 1.3f;

        readonly List<Material> _owned = new List<Material>();

        public Material Opaque(string name, Color albedo)
        {
            Material m = Create("Standard", name);
            m.color = albedo;
            m.SetFloat("_Glossiness", 0.12f);
            m.SetFloat("_Metallic", 0f);
            // No environment reflections: the chamber has no skybox and must not pick up a tint from one.
            m.SetFloat("_GlossyReflections", 0f);
            m.EnableKeyword("_GLOSSYREFLECTIONS_OFF");
            return m;
        }

        public Material Emissive(string name, Color albedo, Color emission)
        {
            Material m = Opaque(name, albedo);
            m.EnableKeyword("_EMISSION");
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            m.SetColor("_EmissionColor", emission);
            return m;
        }

        public Material Ghost(string name, Color tint)
        {
            Material m = Create("Disagreement/GhostShell", name);
            m.color = tint;
            m.SetFloat("_Opacity", 0f);
            return m;
        }

        public Material Plane(string name, Color color)
        {
            Material m = Create("Disagreement/TranslucentPlane", name);
            m.color = color;
            m.SetFloat("_Opacity", 0f);
            return m;
        }

        public MaterialSet CreateSolidSet()
        {
            return new MaterialSet
            {
                IsGhost = false,
                Body = Opaque("Body", new Color(0.78f, 0.77f, 0.74f)),
                Joint = Opaque("Joint", new Color(0.20f, 0.21f, 0.23f)),
                Structure = Opaque("Structure", new Color(0.40f, 0.42f, 0.44f)),
                Conduit = Emissive("Conduit", new Color(0.28f, 0.30f, 0.32f), EnergyColor),
                Cell = Emissive("Cell", new Color(0.14f, 0.14f, 0.15f), EnergyColor),
                EnergyColor = EnergyColor,
            };
        }

        public MaterialSet CreateGhostSet(Color tint)
        {
            Material ghost = Ghost("Ghost", tint);
            return new MaterialSet
            {
                IsGhost = true,
                Body = ghost,
                Joint = ghost,
                Structure = ghost,
                Conduit = ghost,
                Cell = ghost,
                EnergyColor = tint,
            };
        }

        public void DestroyAll()
        {
            foreach (Material m in _owned)
            {
                if (m != null) Object.DestroyImmediate(m);
            }
            _owned.Clear();
        }

        Material Create(string shaderName, string name)
        {
            Shader shader = Shader.Find(shaderName);
            if (shader == null)
            {
                throw new System.InvalidOperationException("Shader '" + shaderName + "' not found. Is the project using the Built-in render pipeline?");
            }
            Material m = new Material(shader) { name = name };
            _owned.Add(m);
            return m;
        }
    }
}
