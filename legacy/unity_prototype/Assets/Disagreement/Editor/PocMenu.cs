using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Disagreement.EditorTools
{
    /// <summary>Editor entry points. These menus are tooling only; nothing here appears in the picture.</summary>
    public static class PocMenu
    {
        /// <summary>Every 75th frame: 12 stills across the excerpt, for checking composition quickly.</summary>
        const int StillsStep = 75;

        [MenuItem("Disagreement/New Graybox Scene")]
        static void NewGrayboxScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            ProjectBootstrap.EnsureLinearColorSpace();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            PocDirector director = new GameObject("Director").AddComponent<PocDirector>();
            director.Build(director.PlayProfile);
            Selection.activeGameObject = director.gameObject;
        }

        [MenuItem("Disagreement/Render Preview Stills")]
        static void RenderPreviewStills()
        {
            RenderProfile profile = RenderProfile.Preview;
            OfflineRenderer.Render(profile, OfflineRenderer.DefaultOutputDirectory(profile, StillsStep), 0, -1, StillsStep);
        }

        [MenuItem("Disagreement/Render Preview Frames")]
        static void RenderPreviewFrames()
        {
            RenderProfile profile = RenderProfile.Preview;
            OfflineRenderer.Render(profile, OfflineRenderer.DefaultOutputDirectory(profile, 1), 0, -1, 1);
        }

        [MenuItem("Disagreement/Render Final Frames")]
        static void RenderFinalFrames()
        {
            RenderProfile profile = RenderProfile.Final;
            OfflineRenderer.Render(profile, OfflineRenderer.DefaultOutputDirectory(profile, 1), 0, -1, 1);
        }
    }
}
