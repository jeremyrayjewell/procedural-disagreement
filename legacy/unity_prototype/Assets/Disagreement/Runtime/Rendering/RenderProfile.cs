using System;
using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// Image-quality settings only. A profile must never influence timing, camera choreography,
    /// seeds, object positions or animation: those live in PocTimeline / ProcedureVariant / the builders.
    /// </summary>
    public sealed class RenderProfile
    {
        public string Name;
        public int Width;
        public int Height;
        /// <summary>1, 2, 4 or 8.</summary>
        public int Msaa;
        /// <summary>Render at Width*SuperSample and downsample. 1 = off.</summary>
        public int SuperSample;
        public ShadowResolution ShadowResolution;
        public float ShadowDistance;
        /// <summary>1, 2 or 4.</summary>
        public int ShadowCascades;
        public LightShadows KeyShadows;
        public LightShadows SpotShadows;
        public int PixelLightCount;

        /// <summary>Fast enough for integrated graphics.</summary>
        public static RenderProfile Preview
        {
            get
            {
                return new RenderProfile
                {
                    Name = "preview",
                    Width = 640,
                    Height = 360,
                    Msaa = 2,
                    SuperSample = 1,
                    ShadowResolution = ShadowResolution.Medium,
                    ShadowDistance = 40f,
                    ShadowCascades = 2,
                    KeyShadows = LightShadows.Hard,
                    SpotShadows = LightShadows.None,
                    PixelLightCount = 2,
                };
            }
        }

        /// <summary>For the GPU workstation.</summary>
        public static RenderProfile Final
        {
            get
            {
                return new RenderProfile
                {
                    Name = "final",
                    Width = 3840,
                    Height = 2160,
                    Msaa = 8,
                    SuperSample = 1,
                    ShadowResolution = ShadowResolution.VeryHigh,
                    ShadowDistance = 60f,
                    ShadowCascades = 4,
                    KeyShadows = LightShadows.Soft,
                    SpotShadows = LightShadows.Soft,
                    PixelLightCount = 4,
                };
            }
        }

        public static RenderProfile ByName(string name)
        {
            if (string.Equals(name, "preview", StringComparison.OrdinalIgnoreCase)) return Preview;
            if (string.Equals(name, "final", StringComparison.OrdinalIgnoreCase)) return Final;
            throw new ArgumentException("Unknown render profile '" + name + "'. Expected 'preview' or 'final'.");
        }

        public void ApplyQualitySettings()
        {
            QualitySettings.shadows = ShadowQuality.All;
            QualitySettings.shadowResolution = ShadowResolution;
            QualitySettings.shadowDistance = ShadowDistance;
            QualitySettings.shadowCascades = ShadowCascades;
            QualitySettings.pixelLightCount = PixelLightCount;
        }
    }
}
