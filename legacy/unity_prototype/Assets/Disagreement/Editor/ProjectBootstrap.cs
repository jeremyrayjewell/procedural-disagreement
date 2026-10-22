using UnityEditor;
using UnityEngine;

namespace Disagreement.EditorTools
{
    /// <summary>
    /// Project settings the look depends on. Applied from code so a freshly cloned project,
    /// whose ProjectSettings Unity generates on first open, renders the same on every machine.
    /// </summary>
    public static class ProjectBootstrap
    {
        [InitializeOnLoadMethod]
        static void OnLoad()
        {
            EditorApplication.delayCall += EnsureLinearColorSpace;
        }

        public static void EnsureLinearColorSpace()
        {
            if (PlayerSettings.colorSpace == ColorSpace.Linear) return;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            Debug.Log("[Disagreement] Switched project colour space to Linear.");
        }
    }
}
