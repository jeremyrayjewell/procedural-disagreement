# procedural-disagreement

Source for the pre-rendered procedural music video **MINOR_CONTROVERSIES_IN_AMPUTATION 截肢中的小爭議**,
built with Blender and Python.

This repository currently holds a graybox proof of concept for 00:35–01:05 of the track. It exists
to prove composition, camera movement, timing, and the visual logic of amputation, infrastructure
dependency and disagreement. It is not polished and is not meant to be yet.

## How the project is meant to be used

The video is developed on a weak machine and finished on a strong one. The same code runs on both:

| | `preview` (local) | `lookdev` (local) | `final` (collaborator) |
| --- | --- | --- | --- |
| Engine | Workbench | Cycles, CPU | Cycles, GPU |
| Resolution | 640 × 360 | 1920 × 1080 | 3840 × 2160 |
| Samples | 5× anti-aliasing | 48, denoised | set by the GPU benchmark (provisionally 128), denoised |
| Look (materials, light, fog, CRTs, lyric) | no | yes | yes |
| Scene content | the film | the preview's, object for object | lookdev's, object for object |
| Atmosphere, motion blur | none | none | none |

`final` is the approved lookdev scene at final output quality, and nothing else (director,
2026-10-22): it once added scene content of its own (more ghost realities, split limb slices,
wall pipework, a denser landfill and conduits, smooth and bevelled primitives), none of which was
ever approved. See [docs/final_render.md](docs/final_render.md).

What a profile may **not** change: camera position and movement, event timing, random seeds,
placement of major geometry, choreography. `tools/check.py` enforces this by building both profiles
and comparing the camera and every animated pivot; they currently agree exactly.

## Rules that hold for the whole project

- **No visible written language** in the picture: no text, labels, numbers, diagnostic UI or typography.
  **One exception** (director, 2026-10-21): the sung lyric, in its final Traditional Chinese
  translation, shown only on the rear wall's CRTs or, where those cannot be read in the shot, as
  text standing in the scene; never as screen-space subtitles. It is described in
  [docs/look.md](docs/look.md#the-lyric-crt-and-world-space-text-2026-10-21). The exception is the
  lyric only: it is no permission for labels, interface text, numbers, logos or any other writing.
- **Everything is a function of absolute track time.** No physics simulation, no per-frame
  accumulation, no wall clock. Frame *n* shows `t = n / 30` seconds of the music and looks the same
  whether it is rendered first, last, alone, or on another machine.
- **The scene is built from code.** No `.blend` file is a source file.

## Requirements

- Blender 5.1 (developed and tested on 5.1.2), on `PATH` or given with `--blender` / `BLENDER`.
  The code allows for the older animation and material APIs back to 4.4, but that is untested.
- ffmpeg, on `PATH` or given with `--ffmpeg` / `FFMPEG`.
- Git LFS, for the audio master, the CRT footage and the lock references (`git lfs pull`). The full
  list of what a render machine needs, and how to check it has exactly the right media
  (`python tools/assets_manifest.py --verify`), is in [docs/final_render.md](docs/final_render.md).
- Python 3.9+ to run the tools. Rendering uses the standard library only; `tools/analyze_audio.py`
  also needs numpy and scipy, and only when the analysis is regenerated.
- The music, placed in `audio/` (any common format), or given with `--audio`.

## Rendering

Times are absolute track time, as seconds or `m:ss`.

```sh
python tools/render.py --stills 12                    # 12 stills + contact sheet: the fastest check
python tools/render.py                                # the whole section, 0:35-1:05
python tools/render.py --start 0:48 --end 0:54        # any interval
python tools/render.py --open                         # build the scene and open it in Blender
python tools/render.py --profile final                # on the rendering machine
python tools/render.py --profile final --resume       # continue an interrupted render
```

Output goes to `renders/<profile>/`: `frames/frame_NNNNNN.png`, then
`pd_<profile>_f<first>-<last>.mp4` with the matching stretch of the music.

File numbers are frame numbers, so ranges rendered separately (or on several machines) share one
`frames/` folder and can be encoded together with `--encode-only`.

| Option | Meaning |
| --- | --- |
| `--profile preview\|final` | Default `preview`. |
| `--start`, `--end` | Interval in track time; end is exclusive. Default 0:35–1:05. |
| `--stills N` | N evenly spaced stills and a contact sheet instead of a video. |
| `--engine workbench\|eevee\|cycles` | Override the profile's engine. |
| `--samples N`, `--scale PERCENT` | Override samples; scale the resolution. |
| `--device auto\|cpu\|optix\|cuda\|hip\|metal\|oneapi` | Cycles device. `auto` picks the best GPU and falls back to CPU with a warning. |
| `--resume` | Skip frames whose file already exists. Assumes they were rendered with the same settings. |
| `--no-encode`, `--encode-only` | Split rendering from encoding. |
| `--save-blend` | Also save the built, baked scene as a `.blend`. |
| `--open` | Build the scene, bake the interval and leave Blender open on it for scrubbing. |
| `--audio FILE` | Music file. Without one the video is silent and the tool says so. |
| `--verbose` | Show all of Blender's output. |

Useful combinations:

```sh
# Look at the final profile cheaply, without a big GPU
python tools/render.py --profile final --stills 4 --scale 10 --samples 16 --device cpu

# On the render machine, first: time the sample counts (see docs/final_render.md)
python tools/benchmark_final.py

# Render the final in two halves, then encode once
python tools/render.py --profile final --start 0:35 --end 0:50 --no-encode
python tools/render.py --profile final --start 0:50 --end 1:05 --no-encode
python tools/render.py --profile final --encode-only
```

### Measured on the development machine (i3-10110U, Intel UHD, 12 GB)

- Preview, Workbench: about 0.24 s per frame; the 30 s section renders in under four minutes.
- Final profile at 10 % scale, 16 samples, CPU: 20–30 s per frame. Enough to inspect it, not to render it.
- **EEVEE does not render correctly on this machine**: with the installed 2021 Intel driver even
  Blender's default cube comes out empty. `--engine eevee` is there for machines where EEVEE works.

### The pit and render time

The lower space is about 9,000 objects in `preview` (they share four meshes) plus a tiled terrain. No shot above the
floor can see any of it, so the render loop leaves its collection out of every frame before the cut
at 1:36.9; that changes no pixel. Frames below the floor take about 1.5 s each on the development
machine, frames above it well under a second. A `.blend` saved with `--save-blend` and rendered by
hand has no such switch: it is correct, only slower.

### Reproducibility

Scene data is exactly reproducible: the same frame always has the same transforms, colours and
camera, in any range, on any machine. Image files carry no dates or host names and are not dithered.

Pixels are as reproducible as the renderer allows. Workbench frames without translucent objects are
bit-identical between runs; translucent objects add rounding noise of at most 1/255 on scattered
pixels (PSNR above 80 dB between runs), from the GPU's order-independent transparency. Cycles is
repeatable on one device but not bit-identical between CPU and GPU or between GPU models.

## Checks

```sh
python tools/check.py
```

Runs the unit tests of the core (pure Python, no Blender), the profile parity check, and the
locked-sequence check (both in Blender). The last compares every object's transform and colour
against the references in `tests/reference/` (currently 0:00–0:35, 0:35–1:05, 1:05–1:20, 1:20–1:30,
1:30–1:52.5, 1:52.5–2:20, 2:20–3:00, 3:00–3:30, 3:30–4:00, 4:00–4:15, 4:15–4:25 and 4:25–4:40), the approved film;
new objects may be added, but nothing recorded may move. Record a reference (`tests/blender_locked.py -- --write NAME`) only
when that interval has been approved, and before changing the code.

## Timing: two layers

The video is directed, not audio-reactive. Timing comes from two separate files.

**1. Audio features** — [analysis/audio_features.json](analysis/audio_features.json). Objective
measurements of the whole track, produced by `python tools/analyze_audio.py`: RMS and A-weighted
loudness, low / mid / high band energy, spectral centroid, onset strength (overall and low-band),
detected onsets, tempo, beats, estimated bar starts, a structural-novelty curve with section-change
candidates, and a harmonic-novelty curve (pitch-class content only) with harmonic-change candidates. Plain JSON; it describes the music and decides nothing.

```sh
python tools/analyze_audio.py                       # re-run if the mix changes (about 6 s)
python tools/analyze_audio.py --report 0:30 1:10    # readable per-second and per-beat breakdown
```

**2. Directorial cues** — [cues/poc_0035_0105.json](cues/poc_0035_0105.json). Every visual event,
with the time chosen for it and a note on the musical event it answers. It also records the measured timing of the sung words the disposal passage is cut to. Edited by hand. Nothing in
it is computed from the analysis: change a number, re-render, and the film changes. Durations (how
long the arm travels, how long the darkness takes to cross the room) follow from pairs of cues.

The only thing taken from the music mechanically is its pulse: the cue file states the tempo
(96 BPM) and a downbeat, and cyclic motion is locked to that grid. One conduit pulse leaves the body
every two beats, one rotor blade passes per beat, and the planes trade lunges every two beats.

## What happens in the section

The track is in four-bar phrases of exactly 10 s (beat 0.625 s, bar 2.5 s).

| Track time | Event | Musical event |
| --- | --- | --- |
| 0:00–0:35 | **Opening: the system before the case.** Black, then one acknowledgement per heavy low transient, each lighting one piece of the apparatus and moving it once: tower head (0:02.0), wall carriage (0:04.5), tray (0:07.0), rear panel (0:09.5). Then light alone reaches the plinth and legs (0:12.0) and the shoulders and torso (0:17.0): there is a body among the apparatus. On the bass entry (0:20.0) the conduit ends close on the shoulders and the system couples: pulses, rotors, a dimly visible room. The tower head seats (0:26.25). On 0:30.0 the lamp docks on the risers over the body and the room comes up to full light: ready. The camera leaves the outer frame at 0:06 and joins the approach at 0:35.0 with the approach's own velocity. Detail in [docs/outer_frame.md](docs/outer_frame.md). | A near-silent bed with one heavy low transient per bar; the bass enters at 0:20.0; a strong hit at 0:30.0. |
| 0:35–1:05 | Camera approaches down the chamber. It never comes to rest. | |
| 0:35–0:40 | Everything works: pulses run from each arm to its tower in time with the beat; rotors turn. | Lead-in, thinning to its quietest at 0:39. |
| 0:40.0 | **Plane A appears**, with a flare, and slides to the shoulder. Camera starts to favour the arm. | The big entrance: loudness up about 9 dB. |
| 0:42.5 | Plane A locks on. **Plane B appears.** | Downbeat of bar 2. |
| 0:45.0 | Plane B in place. **Disagreement begins**: the planes contest, the alternate reality splits off. | Loudest accent of the phrase. |
| 0:47.5 | The alternate is fully separate. | Last bar of the phrase. |
| 0:50.0 | **Primary cut.** The arm releases. Camera has settled on it. | Phrase repeats; the bass is absent on this downbeat. |
| 0:52.5 | Darkness reaches the tower: **primary infrastructure failure**. Rotor runs down, cells die, head lifts. | Next downbeat: the darkness takes one bar to cross the room. |
| 0:55.0 | **Alternate cut**, in the translucent reality only. The removed section strokes away from the stump, the stump swings back the other way, and the whole alternate steps further from the primary. The section then drifts sideways and turns to hang vertically. | Loudest accent of the repeated phrase. |
| 0:56.25 | The primary arm comes to rest on the tray. | Heaviest bass hit of the phrase. |
| 0:57.5 | **Alternate infrastructure failure**: the tower is crippled, not stopped. Plane A starts to withdraw. | The music starts thinning out. |
| 1:00.0 | Plane A gone. **The system branches**: a second interpretation of the right-hand conduit route, its tower and the wall ribs beside it emerges from the primary and hinges away about the riser behind the shoulder. **Camera surges forward** and turns toward it. | The largest change in the interval: highs open by about 8 dB. |
| 1:01.25–1:05 | Plane B, unresolved, fades. | Strongest low hit of the new section. |
| 1:06.25 | **Phantom load.** The alternate figure begins a movement with the arm it no longer has: the stump turns at the shoulder, the torso compensates. Nothing is drawn where the limb was. The load of the absent forearm travels the conduit and the tower braces against it. The removed piece does not move. | First strong hit after 1:05, one phrase after the arm came to rest. |
| 1:07.5–1:10 | The load peaks and settles to a residue: nothing returns to where it was. | Loudest beat of the passage; end of the phrase. |
| 1:10.0–1:19.3 | **Re-indexing.** Routine procedure: the room measures the state it is now in and accepts it. Two pieces of solid apparatus act, one bar apart, each in single eased strokes. *1:10.0, first index:* the head of the tower the cut brought down, left lifted and turned aside since 0:56, levels, lowers 0.3 m and turns 59.5° to face the shoulder the arm was removed from. *1:12.5, second index:* a cabinet on the right wall, which is a carriage on the wall rail, runs 0.75 m toward the body's line and stops. *1:15.0, cross-check:* the head turns 50.4° from the body to the carriage, and 0.6 s after it starts the carriage extends 0.5 m upward. *1:17.5, accepted:* the carriage retracts and backs off, the head stays on it and rises. Neither goes back to where it was: the head ends level, 0.08 m lower and 7.1° from where the failure left it, and the carriage 0.2 m along the wall and 0.12 m taller. They keep that arrangement for the rest of the film. The body does nothing. | The full, steady phrase in which nothing in the music changes; one action per bar. All still 0.7 s before the bass drops out at 1:20.0. |
| 1:20.0–1:30.0 | **Absent attractor.** The phantom hand's position, where nothing is, becomes a coordinate the room agrees on. One bar apart, the alternate conduit's end re-aims at it, the alternate tower head turns to face it, and a panel of the far wall turns until its normal passes through it. Nothing travels toward it; everything keeps its new orientation. The camera is completely still from 1:17 on. | The bass drops out at 1:20.0 and returns at 1:30.0: the phrase in which the low end is absent. |
| 1:30.0–1:35.6 | **Prosthetic recruitment**, as a brief bridge. The stump makes one slow, deliberate movement (8.8° about the shoulder socket). Two beats later one solid wall rib, across the room and attached to nothing, turns about its foot through a fixed fraction (0.765) of the rotation the phantom forearm has made, 7.5° at most: the first solid rib to move in the film. Both settle to a fifth of their extent. | "I'd like if it'd never been" (1:30.0–1:34.5). The rib answers at 1:31.25, when the bass lands. |
| 1:32.5–1:36.65 | **Disposal.** The chamber processes the removed parts as waste. The alternate's forearm, hanging since 0:55, is turned flat and set down on the black tray beside the primary's arm (1:32.5). The tray runs along the floor channel, which is a track (1:33.75); the camera leaves its hold for a wider, higher frame. Where the tray stops the channel opens into an aperture. On *land-* (1:36.25) tray and load go down through the floor; the last of the load passes below it at 1:36.65. | "To know what landfill it is in" (1:34.7–1:39.4); *land-* meets the heaviest low hit of the phrase. |
| 1:36.9–1:38.8 | **The landfill.** A hard cut, the first in the film, to a camera below the floor. The forearm comes out of a chute in the ceiling of a pit hundreds of times the chamber's floor area, still falling at the speed the tray was lowering it, and falls 23 m. The camera goes down with it and closes in. Below is a terrain of compacted waste: benches and steep faces, ridges and basins, strata showing in the faces, and the upper world's own parts (wall panels, ribs, tower sections, cabinets, conduit, body modules, arms) buried in it at every depth and angle, with a berm under every chute. It lands on a broken platform on the nearest berm at 1:38.4, hops once, and has settled by 1:38.8. The primary's arm lands lower on the same berm. Above, the floor closes and the phantom machinery carries on. | *-fill* (cut on its onset); *it is in* (impact on *is*, at rest by *in*). |
| 1:38.8–1:52.5 | **Flyover, over a field that is still working.** The camera leaves the forearm: a slow low glide forward over the berm (the forearm is out of frame by 1:40.5), then from 1:40.0 it accelerates to 6 m/s and climbs 14.6 m, flying 54 m by 1:50.0. The field has no visible edge: it darkens to nothing well short of its walls, with chutes hanging out to where they can no longer be made out. Four other stations dispose of something as it passes, each on a bar line: a torso block close by at 1:42.5, a leg far off at 1:45.0, **a grey arm at 1:47.5**, and another arm at 1:50.0, falling through the widest view. The 1:47.5 arm is the film's second "landfill": the first showed where this severed limb goes, the second shows that another one is going there too. It comes out of an ordinary station about 35 m to the right of the flight, flexed at the elbow and broadside to the camera, and falls 21 m through the full height of the frame. It is grey like everything else in the pit, unlit, and the camera does not turn to it. The camera follows none of them. | The voice re-enters at 1:40.0 with the melody of 1:30 and sings to 1:49.4. The second *-fill* is held from about 1:46.9 to 1:48.0, and the arm leaves its chute at 1:47.5, inside it; it is still falling through *it is in*. At 1:50.0, the strongest downbeat of the passage, the voice falls silent. |
| 1:52.5–2:20 | **The hinge: leaving the individual case.** The flyover continues without a seam and rises. At 1:57.5 the darkness over the pit stops being a ceiling; at 1:58.6 the camera passes up through the level the chutes hang from. Above it, the scattered chutes turn out to be stations on a regular system: seventeen straight parallel trunks, four mains across them, a square unit over every chute and a spur to its trunk. From 2:00 the camera slows, climbs to 170 m and tips toward a plan view; refuse is seen only through the gaps, and stops being readable. From that height the level has heavy buses, a fine local layer, cell arrays and a broad rectangular field, and for a few seconds around 2:11–2:13 it resembles the routing of an integrated-circuit die, directly above the refuse it organises. At 2:15.0 a hard cut, the second in the film, to one trunk and one station in darkness from a camera that does not move. Detail and the state required at 2:20.0 in [docs/hinge.md](docs/hinge.md). | Full to 2:00; the low band drops at 2:00.0 and the level drains to 2:15; the largest break in the first half at 2:15.0. |
| 2:20–3:00 | **The refrain: the system without a subject, seen from inside.** From the hinge's last frame the camera travels along the trunk at station height. The level couples at 2:20.0, as the chamber did at 0:20, around no one. Stations come out of the dark as far as the camera can see: each has an empty platform, an overhead yoke, a head on a column and a carriage on a rail. Two conditions lie on the surfaces: scrawls (crooked, wandering, unreadable strokes) and medal bars (identical plates in ranked rows). From 2:40.0 the stations run their procedure around empty coordinates, passing from station to station, six metres a beat. Nothing is cued to the eight repetitions of the lyric. Detail and the state at 3:00.0 in [docs/refrain.md](docs/refrain.md). | The filtered refrain, eight times; the reprise of 0:20 at 2:20 and of the first verse's bed at 2:40. |
| 3:00–3:30 | **The network: one system, then the absence it is organised around.** No cut at 3:00: the camera completes its turn and travels east along the heavy main. The stations fall into step ring by ring around the junction of the heavy trunk and the heavy main, ending three phases a bar apart; an array of cells indexes down and back and a length of the heavy main rises and settles. At 3:20.0, as the bass leaves, the stations beside a diagonal lane in which nothing stands turn their heads to it and hold mid-procedure, what lies across it withdraws into the ground, and the camera travels down it. Nothing marks the lane. Detail and the state at 3:30.0 in [docs/network.md](docs/network.md). | The third big entrance at 3:00.0; the bass out from 3:20.0 to 3:30. |
| 3:30–4:00 | **Compensation: the network routes function round the absence.** Nothing fills or mends the lane. Along one path round its end (north bank, the two stations that close it, south bank), station by station, a station takes a single part: a **donor**'s head assembly reaches 1.2 m sideways and turns to the next station; the **relay**, station 224, a plain block, indexes 1.6 m along its trunk; a **receiver**'s yoke comes 1.8 m down over its empty platform; a **carrier**'s carriage runs from 0.8 m to 2.4 m and extends 0.5 m. Station 237, which already faced the lane, is first (3:31.25). Three stations join others as composites. Thirteen take part by 4:00. The camera turns right round station 224 while its gaze turns left, looking back across the lane the whole way. Nearby stations establish the four verbs; distant ones give depth and are not each meant to be read. Detail and the state at 4:00.0 in [docs/prosthesis.md](docs/prosthesis.md). | The bass returns at 3:31.3; steady and full to 4:00. |
| 4:00–4:15 | **The field.** The compensation stops being a route. It spreads outward from the lane, 10 m a beat, until all forty stations with machinery have a part; 21 plain blocks relay; fine runs pair, columns of holding cells shear, the heavy main and heavy trunk rise, and at saturation every trunk and main within 150 m rises. Everything comes onto one clock set by distance from the lane. The camera climbs from 12 m to 50 m without a cut. The lane stays empty. Detail and the state at 4:15.0 in [docs/climax.md](docs/climax.md). | Steady peak; harmonic change at 4:06.2; last heavy hit 4:14.4; the music gives way at 4:14.9. |
| 4:15–4:25 | **The coda.** One hard cut back to the room, seen from the outer frame; nobody is on the plinth. First statement of the refrain: scrawls come up on the rear wall and floor, then ranked bars on three panels. Second statement: the scrawls go, then the bars, the last group inside the last sung word. Circulation dies, the room goes down, the lamp lets go of the risers. It ends in exactly the ending's first state. Detail in [docs/coda.md](docs/coda.md). | The voice returns quietly and sings the refrain twice, five seconds apart. |
| 4:25–4:40 | **Ending: the system after the case** (a target; see [docs/outer_frame.md](docs/outer_frame.md) for the state required at 4:25.0). The outer frame again, dim, uncoupled, with nobody on the plinth. The tower head turns to face the shoulder that is not there (4:27.0); the carriage runs to the body's line and extends against nothing (4:30.7); the lamp docks on risers that end in mid-air over the empty plinth (4:35.7). From 4:36.3 nothing moves. It does not fade. | Isolated hard transients, further and further apart; silence from 4:36.3. |

(The code can still build three further seeded alternates, cut on the half-bars at 0:51.25, 0:52.5
and 0:53.75; no profile uses them since 2026-10-22.)

## The 1:10–1:20 lock exception

The film was locked through 1:52.5 when 1:10.0–1:20.0 was reopened, on the director's review
of the whole render, to add the re-indexing passage. The references as they stood before are
kept in `tests/reference_before_reindex/`. Against them, in 258,714 object-frame comparisons:

- nothing differs before 1:10.0, and the first reopened frame is identical to the one before it;
- five objects differ from 1:10.0 on: the failed tower's head and its three parts, and one cabinet;
- from 1:19.3 those five are at rest, and they hold exactly the same pose in every later frame.

So frames at and after 1:20.0 are not pixel-identical to the earlier lock: they show the
accepted arrangement (a few pixels at 360p). Every other object, and all later choreography,
is unchanged.

## Solid ribs: what the film does and does not show

The recruited rib at 1:30 is the first and only solid chamber rib that moves.

Earlier events were once written to move solid ribs as well: two were to give under the phantom
load at 1:06.25, and two were to lean toward the phantom locus during the absent attractor. They
were configured at odd y, where no rib stands (chamber ribs are at even y, `layout.rib_ys()`), so
they never matched any geometry and never produced any motion in any render. The footage was
approved as rendered and that is canonical: those responses have been removed from the code, not
activated. Earlier reports that these ribs moved, and the pixel displacements quoted for them, were
wrong.

For the same reason the system branch's four ribs (also at odd y) do not emerge from primary ribs
at 1:00; they appear in the gaps between them. Also approved as rendered.

The build now fails if the recruited rib does not match exactly one real rib.

## Planned: final audio-reactive layer (not implemented)

Recorded here as a requirement for later. Nothing in the code does this yet.

### Back-wall audio-responsive surfaces

The large square panels on the rear wall are intended to become architectural, audio-responsive
display / emissive surfaces in the high-power final render. They must not simply become identical
spectrum visualisers. The layer should allow spatially differentiated responses, for example:

| Audio feature | Response |
| --- | --- |
| Low-frequency energy | Broad emissive / luminance response |
| Mid-frequency energy | Larger-scale surface or pattern deformation |
| High-frequency energy | Fine texture and detail activity |
| Spectral brightness | Material sharpness, roughness / specular or secondary-light character |
| Structural musical events | Changes in which panels are grouped as active, or spatial propagation across them |

### Other final-render reactivity

- secondary architectural lighting
- emissive bounce
- material roughness / specular modulation
- texture displacement and detail
- subtle atmospheric / volumetric modulation
- reflected / rim illumination

### Constraints

- **Deterministic, from existing data.** Every parameter curve derives from absolute track time and
  the same `analysis/audio_features.json` the structural choreography was cued from. No live audio,
  no randomness.
- **A material, light and final-render layer only.** It must never obscure or substitute for the
  structural choreography. Narrative events stay explicit cues.
- **Identical curves in every profile.** Preview and final must evaluate the same parameter values
  at the same time. Expensive shading and detail may exist only in `final`, but the curve that
  drives them must be the one `preview` uses. That implies the curves belong in `core/`
  (profile-blind, covered by the parity check) and only their consumers in `scene/`.
- **No written language**, as everywhere else: display surfaces show no text, numbers or UI, with
  the one exception above: the sung lyric in Chinese, on the CRTs or as world-space text.

### What the lyric licenses

The lyric alignment ([docs/lyric_alignment.md](docs/lyric_alignment.md)) gives this layer a
vocabulary and some places to use it. None of it is implemented.

- **2:20–3:00.** One of the main places for material and detail. Scrawls can become scratches,
  etching, emissive traces, abrasion, displacement; medal bars can become metallic inlays, ranked
  emissive strips, raised plates, ordered screen regions. Audio response through global
  parameters that breathe with the soundtrack, never one event per repetition of the lyric.
  See [docs/refrain.md](docs/refrain.md).
- **1:52.5–2:15.** The scale change can gain most from a lit engine: atmospheric depth,
  volumetric extinction, aerial haze increasing with altitude, distant station lighting, detail
  disappearing with distance, selective emissive networks along the trunks, audio-responsive
  visibility of the infrastructure. See [docs/hinge.md](docs/hinge.md).
- **0:00–0:20.** The first, minimal appearance of soundtrack-responsive rendering: one or a few
  responses (a rear panel's emissive activation, a small specular change, a sparse secondary
  light, subtle atmospheric visibility). Not a visualiser.
- **4:25–4:37.** The same grammar returns, diminished. **4:37–4:40:** no audio-reactive change
  of any kind during the silence.
- **0:58.6, the second sung "stump".** The stump is already on screen (translucent, in the
  alternate). No structural choreography is to be added here. It is a possible place for a subtle
  lighting, material or screen accent.
- **1:20.0–1:24.6, the filtered refrain.** An environmental condition, not an announcement and not
  a speaker. Anything that answers it should behave like the room, not like an event.
- **Vocabulary from the refrain.**
  - *Scrawls*: non-linguistic irregular marks, scratches, traces, scribble-like surface patterns.
  - *Medal bars*: ordered rectilinear bands, serial blocks, ranked repeated modules.
  - No readable writing in either.
- **2:20–3:00, the refrain eight times, filtered.** This vocabulary should appear here mainly as
  environmental, material and screen behaviour, not as eight new narrative events.
- **4:15–4:25, the refrain in full voice.** Reserved: the scrawl and bar vocabulary established
  earlier may be made much more explicit here.

A further possibility for the high-power version: illumination in the landfill that reveals distant heaps and
disposal chutes selectively, in response to the soundtrack. Same constraints. Not implemented.

Note for whoever implements it: one of these panels (top row, centre) already turns to face the
phantom locus from 1:27.5 and keeps that orientation.

## Architecture

```
procedural_disagreement/
  core/                 Pure Python. No Blender. Fixes everything that must not vary.
    timeline.py         Frame rate, seed; loads the cue file and names its times; frame <-> time
    variants.py         ProcedureVariant: one version of the procedure; primary, alternate, seeded extras
    layout.py           Where things are: chamber, camera path, figure modules, conduit routes
    choreography.py     What everything is doing at time t: pure functions returning poses and levels
    profiles.py         preview / final: engine, resolution, samples, density
    ease.py             Stateless easing
    landfill.py         The disposal field below the chamber: terrain height, stations, other disposals
    stablehash.py       Seeded random that depends on (seed, index), not on call order
    vec.py              Vector and quaternion maths on tuples
  scene/                Blender layer.
    build.py            Assembles the scene for a profile and bakes a frame range
    animator.py         Samples choreography functions into keyframes
    geo.py              Primitives; tessellation and bevels by profile
    materials.py        Four materials driven by object colour; solid and ghost styles
    chamber.py          The room
    reality.py          Figure + conduits + towers for one variant, solid or translucent
    planes.py           The two competing cutting planes
    branch.py           The system branch: the primary's dependency, a second time, somewhere else
    landfill.py         Draws the disposal field from core/landfill.py, in its own collection
    stage.py            Camera, lights, haze, render settings
cues/
  poc_0035_0105.json    Directorial cues: hand-chosen event times, each with its musical reason
analysis/
  audio_features.json   Audio features for the whole track (generated; describes, decides nothing)
audio/                  The music
tools/
  render.py             Command line: render an interval, encode with audio
  analyze_audio.py      Extract audio features; print a breakdown of an interval
  blender_entry.py      Runs inside Blender
  check.py              Unit tests + profile parity + locked-sequence comparison
tests/
legacy/unity_prototype/ The abandoned first attempt. Reference only; safe to delete.
```

### The split that makes two profiles one film

`core` decides *what happens and where*. It never sees a render profile. `scene` decides *how it is
drawn*, and a profile can only reach it there: tessellation, bevels, how many fragments a slice is
split into, how many conduit segments sample the same energy function, how many extra realities
exist, which engine draws them.

### Baking

Builders register channels: "this property follows this function of *t*".
[animator.py](procedural_disagreement/scene/animator.py) samples every channel once per frame and
writes linear keyframes. The built scene is therefore an ordinary self-contained `.blend`: it scrubs
in the viewport, renders without running Python, and supports motion blur. Only the requested range
is baked, so short previews stay quick.

### One animated property for energy and translucency

Every material reads the object's colour and alpha. Workbench draws object colour directly; EEVEE
and Cycles read it through the Object Info node. So a conduit segment dimming, a cell dying and a
whole reality fading in are all the same kind of keyframe and look consistent across engines.

### How the three ideas are modelled

**Amputation.** A limb is an ordered stack of modules. A cut is an index into that stack. The
modules beyond the index are grouped under a pivot at the cut; detaching the region is the authored,
eased pose of that one pivot.

**Dependency.** Each arm keeps a tower alive through a conduit. Energy visibly flows body → tower.
When the arm is cut, darkness follows the same route and the tower fails when it arrives, so cause
can be traced across the room. The opposite arm is never cut and its tower keeps running: the control.

**Disagreement.** A reality is the figure and its dependencies built from one `ProcedureVariant`.
Primary and alternates come from the *same* builder; they differ only in their variant and their
style (solid or translucent). Each cutting plane belongs to one reality and tracks its cut.

## What was kept from the Unity prototype, and what was not

Kept, because it never depended on Unity: the cue structure, the variant model, the limb-as-stack
and cut-as-index idea, the region → conduit → tower dependency with its travelling darkness, the
closed-form rotor integral, the stutter hashed on a fixed clock, the stateless seeded hash, the
plane contest, the camera path and the chamber layout.

Changed in the move:

- Time is now absolute track time, so the same code extends to the full 4:40.
- Coordinates are Blender's (Z up, right-handed), re-authored rather than converted.
- The arms were hanging, which put the cutting planes edge-on to the camera and made them nearly
  invisible. They are now held forward, so the planes face the camera.
- The alternate reality used to drift toward the camera and swamped the primary. It now drifts
  sideways and behind, and reads as a fringe.

Dropped: the play-mode director, per-frame render-texture readback, custom shaders, quality-setting
toggles, the trick of making the room not cast shadows, and the PowerShell-only workflow.

## Extending

- **Retiming to the music:** edit the times in `cues/poc_0035_0105.json` and re-render. Nothing
  else needs to change; `python tools/analyze_audio.py --report START END` shows what the music is
  doing around any moment.
- **Another reality:** add a variant; `variants.for_profile` decides which profiles build it.
- **Another amputation:** legs are already module stacks; they need a conduit route in `layout.py`
  and a variant that targets them.
- **More of the video:** add a cue file per section and give `choreography.py` functions for it.
  The audio analysis already covers the whole track.
- **Look development:** materials in `materials.py`, lights in `stage.py`, density in `profiles.py`.
  Keep anything expensive behind the profile so `preview` stays fast.
