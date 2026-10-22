using UnityEngine;
using UnityEngine.Rendering;

namespace Disagreement
{
    /// <summary>
    /// Lights, ambient and fog. Positions, colours and intensities are fixed;
    /// a profile only chooses how shadows are rendered.
    /// </summary>
    public static class LightingRig
    {
        public static Transform Build(Transform parent, RenderProfile profile)
        {
            Transform root = Geo.Group("Lighting", parent);

            Light key = AddLight("Key", root, LightType.Directional);
            key.transform.localRotation = Quaternion.Euler(55f, -25f, 0f);
            key.color = new Color(0.95f, 0.98f, 1.0f);
            key.intensity = 0.75f;
            key.shadows = profile.KeyShadows;
            key.shadowStrength = 0.7f;

            Light lamp = AddLight("Lamp", root, LightType.Spot);
            lamp.transform.localPosition = new Vector3(0f, 5.95f, -0.6f);
            lamp.transform.LookAt(new Vector3(0f, 2.4f, 0f));
            lamp.color = new Color(1.0f, 0.97f, 0.92f);
            lamp.intensity = 1.2f;
            lamp.range = 10f;
            lamp.spotAngle = 75f;
            lamp.shadows = profile.SpotShadows;

            RenderSettings.skybox = null;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.36f, 0.38f, 0.39f);
            RenderSettings.reflectionIntensity = 0f;
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = ChamberBuilder.FogColor;
            RenderSettings.fogStartDistance = 12f;
            RenderSettings.fogEndDistance = 48f;

            return root;
        }

        static Light AddLight(string name, Transform parent, LightType type)
        {
            Light light = Geo.Group(name, parent).gameObject.AddComponent<Light>();
            light.type = type;
            light.renderMode = LightRenderMode.ForcePixel;
            return light;
        }
    }
}
