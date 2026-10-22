# MINOR_CONTROVERSIES_IN_AMPUTATION 截肢中的小爭議

Procedural music video, built in Unity. This repository currently holds **Phase 1**: a 30-second
graybox proof of concept covering roughly 00:35–01:05 of the track.

Phase 1 exists to prove composition, camera movement, timing, and the visual logic of amputation,
infrastructure dependency and disagreement. It is not polished and is not meant to be.

> Status: the scripts compile against a stub of the Unity API and the camera framing has been
> checked numerically, but the project has **not yet been opened or rendered in a Unity editor**.
> Expect a first pass of tuning (light levels, opacities) once it has.

## Rules that hold for the whole project

- **No visible written language** in the picture: no text, labels, numbers, diagnostic UI or typography.
- **Two render profiles, one film.** `preview` and `final` share timing, camera choreography, seeds,
  object positions and animation. A profile may only change image quality.
- **Everything is a function of time.** No real-time physics, no per-frame accumulation, no wall
  clock. Frame *n* looks the same whether it is rendered first, last, alone, or on another machine.

## Requirements

- Unity 6 LTS (6000.x) or 2022.3 LTS, **Built-in Render Pipeline**. No packages beyond built-in modules.
  Unity generates `ProjectSettings/` on first open; the project switches itself to Linear colour space.
- `ffmpeg` on `PATH` (or `-FfmpegPath` / `FFMPEG`), for encoding.
- Windows PowerShell 5.1 or later for `Tools/render.ps1`.

## Rendering

```powershell
.\Tools\render.ps1 -Stills                 # 12 stills + contact sheet: the fastest composition check
.\Tools\render.ps1                         # preview profile, full 30 s  -> Renders\preview\poc_preview.mp4
.\Tools\render.ps1 -RenderProfile final    # final profile, on the GPU workstation
```

The script runs Unity in batch mode, which writes a PNG sequence, then encodes it with ffmpeg.
Close the project in the Unity editor first: Unity will not open one project twice.

| Option | Meaning |
| --- | --- |
| `-RenderProfile preview\|final` | Quality profile. Default `preview`. |
| `-StartFrame`, `-EndFrame` | Render part of the timeline (frames 0–899). |
| `-FrameStep N` | Render every Nth frame, into `frames_stepN\`. |
| `-Stills` | `-FrameStep 75` and a contact sheet instead of a video. |
| `-NoEncode` / `-EncodeOnly` | Split rendering and encoding, e.g. to render ranges separately. |
| `-UnityPath` | Path to `Unity.exe`. Otherwise `UNITY_EDITOR`, otherwise the Unity Hub install. |
| `-Audio` | Music file to mux. Otherwise `Audio\track.*` if present; otherwise the video is silent. |

Audio is muxed starting at 00:35 of the track (`PocTimeline.MusicOffset`), so the excerpt lines up
with the music without the track ever entering the Unity project.

Inside the editor, the **Disagreement** menu offers the same renders, plus **New Graybox Scene**:
select the `Director` object and drag **Scrub Time** to pose any moment, or press Play to watch it
in real time. Play mode reads the wall clock for convenience only; rendered frames never do.

### Profiles

| | `preview` | `final` |
| --- | --- | --- |
| Resolution | 640 × 360 | 3840 × 2160 |
| MSAA | 2× | 8× |
| Key-light shadows | hard, medium, 2 cascades | soft, very high, 4 cascades |
| Lamp shadows | off | soft |
| Video encode | x264 CRF 23, veryfast | x264 CRF 14, slow |

Both run at 30 fps. Defined in [RenderProfile.cs](Assets/Disagreement/Runtime/Rendering/RenderProfile.cs).

## What happens in the 30 seconds

Times are local to the excerpt; add 35 s for track time. Cues live in
[PocTimeline.cs](Assets/Disagreement/Runtime/Core/PocTimeline.cs) and
[ProcedureVariant.cs](Assets/Disagreement/Runtime/Procedure/ProcedureVariant.cs).

| Time | Event |
| --- | --- |
| 0–30 | Camera approaches down the chamber and tightens on one arm. It never comes to rest. |
| 0–15 | Everything works: energy pulses run from each arm along a conduit to a tower at the far end of the room; rotors turn, cells are lit. |
| 5–9 | Plane A (cool) slides in to the shoulder. |
| 7.5–11 | Plane B (warm) descends to mid upper arm, tilted. |
| 10–15 | The planes contest each other's position. A translucent warm copy of the figure and its tower drifts out of the solid one: the alternate reality. |
| 15 | **Primary cut** at plane A. The whole arm releases and is carried to a tray. |
| 15–17.5 | Darkness travels the conduit from the body to the tower. |
| 17.5–22 | The tower's rotor runs down to a stop, its cells stutter and go dark top to bottom, its head lifts off and turns. |
| 16.5 | **Alternate cut** at plane B, in the translucent reality only: a stump remains, and the removed part sinks instead of being collected. |
| 19.5–24.5 | The alternate tower is only crippled: half its cells die, the rotor slows but keeps turning, the head slumps rather than separating. |
| 22–30 | Plane A withdraws. Plane B lingers. The other arm's tower runs throughout, untouched. |

## Architecture

```
Assets/Disagreement/
  Runtime/
    PocDirector.cs            Builds everything; Evaluate(t) poses the whole scene for time t
    Core/
      PocTimeline.cs          Duration, frame rate, seed, music offset, cue times
      Ease.cs                 Stateless easing: windows, pulses
      StableHash.cs           Seeded random that depends on (seed, index), not call order
    Rendering/
      RenderProfile.cs        preview / final quality settings
      MaterialLibrary.cs      Materials, and MaterialSet: the roles one reality is built from
    Scene/
      Geo.cs                  Primitive helpers (box, cylinder, sphere, quad); strips colliders
      ChamberBuilder.cs       The room, plinth, lamp
      LightingRig.cs          Lights, ambient, fog
      Figure.cs               The body/machine/infrastructure figure
      LimbChain.cs            Ordered stack of modules; a cut is an index into it
      Conduit.cs              Segmented duct carrying energy from region to infrastructure
      InfrastructureTower.cs  Remote object that depends on a region, and how it fails
      DependencyLink.cs       region -> conduit -> tower
      CameraRig.cs            The approach
    Procedure/
      ProcedureVariant.cs     One version of the procedure: cut, travel, consequences
      Reality.cs              Figure + dependencies + one variant, solid or translucent
      DisagreementSystem.cs   The two competing cutting planes
  Editor/
    OfflineRenderer.cs        Frame-by-frame PNG renderer; command-line entry point
    PocMenu.cs                Disagreement menu
    PocDirectorEditor.cs      Scrub slider on the director
    ProjectBootstrap.cs       Linear colour space
  Shaders/
    TranslucentPlane.shader   Cutting planes
    GhostShell.shader         Alternate realities
Tools/render.ps1              Unity batch render -> ffmpeg
```

### How the three ideas are modelled

**Amputation.** A limb is a `LimbChain`: an ordered stack of modules. A cut is an index into that
stack. Before anything moves, the modules beyond the index are regrouped under a pivot at the cut;
detaching the region is then an authored, eased pose of that one pivot.

**Dependency.** A `DependencyLink` ties a region to a tower through a conduit. Energy visibly flows
body → tower. When the region is cut, darkness follows the same route and the tower fails when it
arrives, so cause can be traced across the room. The opposite arm's link is never cut and keeps
running, as the control.

**Disagreement.** A `ProcedureVariant` describes one version of the procedure. A `Reality` is the
figure and its dependencies built from one variant with one `MaterialSet`. The primary and the
alternate are produced by the *same* builders; they differ only in their variant (cut index, cut
time, tilt, travel, consequences) and their materials (solid or translucent). Each cutting plane
belongs to one reality and tracks that reality's cut.

### Determinism

`PocDirector.Evaluate(t)` calls `Evaluate(t)` on each system, and each computes its pose from `t`
alone. Things that look cumulative are closed-form: the rotor angle is the analytic integral of its
speed curve; the cells' stutter is hashed on a fixed 14 Hz clock rather than on the frame count.
The offline renderer evaluates `t = frame / 30`, renders the camera into a texture and writes a PNG.

## Extending

- **Another reality:** add a `ProcedureVariant` factory, build a `Reality` from it in
  `PocDirector.Build`, and give it a plane in `DisagreementSystem`.
- **Another amputation:** legs are already `LimbChain`s (`leg+x`, `leg-x`); they need a
  `DependencyLink` path and a variant that targets them.
- **Retiming to the music:** change the constants in `PocTimeline` and `ProcedureVariant`. Downstream
  events are relative to the cut times and follow.
- **Look development:** all materials come from `MaterialLibrary`; all quality switches from
  `RenderProfile`. Keep expensive effects behind the profile so `preview` stays fast.
