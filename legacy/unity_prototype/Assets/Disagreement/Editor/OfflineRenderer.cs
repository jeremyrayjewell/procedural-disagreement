using System;
using System.Globalization;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Disagreement.EditorTools
{
    /// <summary>
    /// Renders the proof of concept to a PNG sequence without entering Play mode.
    /// For each frame: pose the scene for that frame's time, render the camera, write the image.
    /// Wall-clock time is never consulted, so output is reproducible and frames may be rendered
    /// in any order or range.
    ///
    /// Command line (see Tools/render.ps1):
    ///   Unity -batchmode -projectPath . -executeMethod Disagreement.EditorTools.OfflineRenderer.RenderFromCommandLine
    ///         -dgProfile preview|final [-dgOut dir] [-dgStart n] [-dgEnd n] [-dgStep n]
    /// </summary>
    public static class OfflineRenderer
    {
        public static void RenderFromCommandLine()
        {
            try
            {
                string[] args = Environment.GetCommandLineArgs();
                RenderProfile profile = RenderProfile.ByName(GetArg(args, "-dgProfile", "preview"));
                string outDir = GetArg(args, "-dgOut", DefaultOutputDirectory(profile, 1));
                int start = int.Parse(GetArg(args, "-dgStart", "0"), CultureInfo.InvariantCulture);
                int end = int.Parse(GetArg(args, "-dgEnd", "-1"), CultureInfo.InvariantCulture);
                int step = int.Parse(GetArg(args, "-dgStep", "1"), CultureInfo.InvariantCulture);

                Render(profile, outDir, start, end, step);
                EditorApplication.Exit(0);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                EditorApplication.Exit(1);
            }
        }

        public static string DefaultOutputDirectory(RenderProfile profile, int step)
        {
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string folder = step > 1 ? "frames_step" + step : "frames";
            return Path.Combine(projectRoot, "Renders", profile.Name, folder);
        }

        /// <summary>
        /// Renders frames start..end (inclusive; end &lt; 0 means the last frame), taking every
        /// <paramref name="step"/>th. Files are named by frame / step, so with step 1 the file
        /// number is the frame number and partial ranges can be rendered separately and merged.
        /// </summary>
        public static void Render(RenderProfile profile, string outDir, int start, int end, int step)
        {
            bool batch = Application.isBatchMode;
            if (!batch && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;

            ProjectBootstrap.EnsureLinearColorSpace();

            int last = PocTimeline.FrameCount - 1;
            step = Mathf.Max(1, step);
            end = end < 0 ? last : Mathf.Min(end, last);
            start = Mathf.Clamp(start, 0, end);
            start -= start % step;

            // A fresh scene guarantees nothing but the director's own content is in frame.
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            PocDirector director = new GameObject("Director").AddComponent<PocDirector>();
            director.Build(profile);
            Camera cam = director.Camera;

            Directory.CreateDirectory(outDir);

            int scale = Mathf.Max(1, profile.SuperSample);
            RenderTexture renderTarget = new RenderTexture(profile.Width * scale, profile.Height * scale, 24,
                RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            renderTarget.antiAliasing = Mathf.Max(1, profile.Msaa);
            // Resolving into a plain target handles both MSAA and the supersample downscale.
            RenderTexture resolved = new RenderTexture(profile.Width, profile.Height, 0,
                RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            Texture2D readback = new Texture2D(profile.Width, profile.Height, TextureFormat.RGB24, false);

            int total = (end - start) / step + 1;
            int done = 0;
            try
            {
                cam.targetTexture = renderTarget;
                for (int frame = start; frame <= end; frame += step)
                {
                    director.Evaluate(PocTimeline.TimeOfFrame(frame));
                    cam.Render();

                    Graphics.Blit(renderTarget, resolved);
                    RenderTexture.active = resolved;
                    readback.ReadPixels(new Rect(0, 0, profile.Width, profile.Height), 0, 0, false);
                    RenderTexture.active = null;

                    string file = Path.Combine(outDir, "frame_" + (frame / step).ToString("D5", CultureInfo.InvariantCulture) + ".png");
                    File.WriteAllBytes(file, readback.EncodeToPNG());

                    done++;
                    if (batch)
                    {
                        if (done % 30 == 0 || done == total) Debug.Log("[OfflineRenderer] " + done + " / " + total);
                    }
                    else if (EditorUtility.DisplayCancelableProgressBar("Rendering " + profile.Name, done + " / " + total, done / (float)total))
                    {
                        break;
                    }
                }
            }
            finally
            {
                cam.targetTexture = null;
                RenderTexture.active = null;
                renderTarget.Release();
                resolved.Release();
                UnityEngine.Object.DestroyImmediate(renderTarget);
                UnityEngine.Object.DestroyImmediate(resolved);
                UnityEngine.Object.DestroyImmediate(readback);
                if (!batch) EditorUtility.ClearProgressBar();
            }

            Debug.Log("[OfflineRenderer] Wrote " + done + " frame(s) to " + outDir);
        }

        static string GetArg(string[] args, string name, string fallback)
        {
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (string.Equals(args[i], name, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            }
            return fallback;
        }
    }
}
