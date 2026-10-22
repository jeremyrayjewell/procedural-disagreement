using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// The slow approach. Position, aim and field of view are functions of time alone.
    /// The move never comes to rest inside the excerpt: it is a slice of a longer shot.
    /// </summary>
    public sealed class CameraRig
    {
        static readonly Vector3 StartPosition = new Vector3(0.5f, 2.9f, -15.5f);
        static readonly Vector3 EndPosition = new Vector3(-1.3f, 2.65f, -6.2f);
        /// <summary>Opens on the whole figure...</summary>
        static readonly Vector3 StartTarget = new Vector3(0f, 2.5f, 0f);
        /// <summary>...and settles on the arm that is being argued over.</summary>
        static readonly Vector3 EndTarget = new Vector3(0.75f, 2.75f, 0f);
        const float StartFov = 36f;
        const float EndFov = 33f;

        public Camera Camera { get; private set; }

        public static CameraRig Build(Transform parent, RenderProfile profile)
        {
            CameraRig rig = new CameraRig();
            GameObject go = Geo.Group("Camera", parent).gameObject;
            go.tag = "MainCamera";

            Camera cam = go.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = ChamberBuilder.FogColor;
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 90f;
            cam.allowHDR = false;
            cam.allowMSAA = profile.Msaa > 1;
            rig.Camera = cam;
            return rig;
        }

        public void Evaluate(float t)
        {
            float u = Mathf.Clamp01(t / PocTimeline.Duration);
            // Mostly linear with a gentle ease, so the camera is already moving on the first frame.
            float travel = Mathf.Lerp(u, Ease.Smoother(u), 0.5f);
            float aim = Ease.SmoothWindow(t, 6f, 20f);

            Transform tr = Camera.transform;
            tr.position = Vector3.Lerp(StartPosition, EndPosition, travel);
            tr.rotation = Quaternion.LookRotation(Vector3.Lerp(StartTarget, EndTarget, aim) - tr.position, Vector3.up);
            Camera.fieldOfView = Mathf.Lerp(StartFov, EndFov, travel);
        }
    }
}
