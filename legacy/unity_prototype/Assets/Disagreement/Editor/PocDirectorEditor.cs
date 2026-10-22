using UnityEditor;
using UnityEngine;

namespace Disagreement.EditorTools
{
    /// <summary>Scrub the timeline in edit mode from the director's inspector.</summary>
    [CustomEditor(typeof(PocDirector))]
    public sealed class PocDirectorEditor : Editor
    {
        float _time;

        public override void OnInspectorGUI()
        {
            DrawDefaultInspector();
            if (Application.isPlaying) return;

            PocDirector director = (PocDirector)target;

            EditorGUI.BeginChangeCheck();
            _time = EditorGUILayout.Slider("Scrub Time", _time, 0f, PocTimeline.Duration);
            bool scrubbed = EditorGUI.EndChangeCheck();
            bool rebuild = GUILayout.Button("Rebuild");

            if (!scrubbed && !rebuild) return;
            if (rebuild || !director.IsBuilt) director.Build(director.PlayProfile);
            director.Evaluate(_time);
            UnityEditorInternal.InternalEditorUtility.RepaintAllViews();
        }
    }
}
