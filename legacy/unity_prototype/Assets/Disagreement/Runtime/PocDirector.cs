using System;
using UnityEngine;

namespace Disagreement
{
    /// <summary>
    /// Builds the whole proof of concept under its own transform and poses it for any time t.
    ///
    /// <see cref="Evaluate"/> is a pure function of t: it keeps no state between calls, so frames
    /// can be rendered in any order, on any machine, in any profile, and come out the same.
    /// The offline renderer calls it once per frame; Play mode calls it from the wall clock
    /// purely as a viewing convenience.
    /// </summary>
    public sealed class PocDirector : MonoBehaviour
    {
        public enum ProfileKind { Preview, Final }

        [SerializeField] ProfileKind playProfile = ProfileKind.Preview;
        [SerializeField] bool loop = true;

        [NonSerialized] bool _built;
        MaterialLibrary _materials;
        Reality _primary;
        Reality _alternate;
        DisagreementSystem _disagreement;
        CameraRig _rig;
        float _playStart;

        public bool IsBuilt
        {
            get { return _built && _rig != null && _rig.Camera != null; }
        }

        public Camera Camera
        {
            get { return _rig.Camera; }
        }

        public RenderProfile PlayProfile
        {
            get { return playProfile == ProfileKind.Final ? RenderProfile.Final : RenderProfile.Preview; }
        }

        public void Build(RenderProfile profile)
        {
            Clear();

            _materials = new MaterialLibrary();
            Transform content = Geo.Group("Content", transform);

            ChamberBuilder.Build(content, _materials, PocTimeline.Seed);
            LightingRig.Build(content, profile);

            _primary = Reality.Build(content, ProcedureVariant.Primary(), _materials.CreateSolidSet(), PocTimeline.Seed);
            _alternate = Reality.Build(content, ProcedureVariant.Alternate(), _materials.CreateGhostSet(MaterialLibrary.GhostTint), PocTimeline.Seed);
            _disagreement = DisagreementSystem.Build(content, _materials, _primary, _alternate);
            _rig = CameraRig.Build(content, profile);

            profile.ApplyQualitySettings();
            _built = true;
            Evaluate(0f);
        }

        public void Evaluate(float t)
        {
            // Realities first: the planes read the cut points the realities have just placed.
            _primary.Evaluate(t);
            _alternate.Evaluate(t);
            _disagreement.Evaluate(t);
            _rig.Evaluate(t);
        }

        /// <summary>Removes everything a previous build created, including children saved with the scene.</summary>
        public void Clear()
        {
            for (int i = transform.childCount - 1; i >= 0; i--)
            {
                DestroyImmediate(transform.GetChild(i).gameObject);
            }
            if (_materials != null) _materials.DestroyAll();
            _materials = null;
            _built = false;
        }

        void Start()
        {
            Build(PlayProfile);
            _playStart = Time.time;
        }

        void Update()
        {
            float t = Time.time - _playStart;
            t = loop ? Mathf.Repeat(t, PocTimeline.Duration) : Mathf.Min(t, PocTimeline.Duration);
            Evaluate(t);
        }
    }
}
