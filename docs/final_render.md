# The final render: production-profile audit (2026-10-22)

**Decided 2026-10-22 (director): option A, quality only.** `final` is now the approved lookdev
scene, object for object, at final output quality: 3840 × 2160 on the GPU, at the sample count
the GPU benchmark below chooses (provisionally 128). Every scene-content row in the second table
is at its lookdev value. A unit test holds `final` to lookdev in everything but its name,
resolution and samples.

Every approval of the look was made on the **lookdev** profile: the preview's own scene, object
for object, rendered by Cycles on the CPU at 1920 × 1080 (stills at 24 samples). The **final**
profile was defined before the look existed. The audit below lists everything that differed.

## Where the profiles differ

Profile fields are in `procedural_disagreement/core/profiles.py`; every code path that reads them
was traced (`scene/stage.py`, `scene/geo.py`, `scene/reality.py`, `scene/chamber.py`,
`scene/landfill.py`, `core/variants.py`, `scene/look.py`).

### Rendering quality

| Setting | Lookdev (approved) | Final (as defined) | Effect | Could it alter the approved look? | Needed? |
| --- | --- | --- | --- | --- | --- |
| Resolution | 1920 × 1080 | 3840 × 2160 | Everything twice as fine: texels, glyphs, edges | No change of design. CRT scanlines resolve at about 8 image pixels a row (4 at 1080), steadier still; the footage (960 × 540 stream) stays at about one texel to an image pixel even on the nearest screens; the 1-pixel box filter stays hard, at half the size | Yes (delivery) |
| Samples | 48 (approval stills at 24) | 512 | Less noise; the denoiser has less to smooth | Slightly: fine texture pattern (the PS1 maps' dither, the footage's grain) comes out a little crisper. No change to light, colour or brightness | Yes, but see render time below |
| Device | CPU | GPU (OptiX, else CUDA/HIP/Metal/oneAPI; chosen automatically) | Speed | No: the same Cycles, the same results within noise | Yes |
| Denoising | OIDN, albedo + normal, accurate | same | — | — | — |
| Motion blur | off | off (decided 2026-10-21) | — | — | — |
| Depth of field | none | none | — | — | — |
| Volumetrics (haze) | off | off (decided 2026-10-21); depth is the camera-only fog, the same in both | — | — | — |
| Light paths, bounces, clamping, adaptive sampling (0.03), pixel filter (1 px box), transparency (32) | `look.render_settings` | identical (one function for both) | — | — | — |
| Colour (AgX), 8-bit PNG, no dither | `stage.apply_profile` | identical | — | — | — |
| Look (materials, light, fog, CRTs, lyric, footage) | on | on | — | — | — |

### Scene content (geometric density)

These are not rendering quality: they change what is in the picture. The approvals never saw them.

| Setting | Lookdev (approved) | Final (as defined) | What it adds or changes | Alters the approved look? |
| --- | --- | --- | --- | --- |
| Extra alternate realities | 0 | 3 | Three more translucent ghost figures (opacity 0.28, warm tints), each with its own cut a few beats after the primary cut: the room from 0:47 on is much busier around the figure | **Yes** (figure, room, every room shot after the cut) |
| Slice subdivisions | 1 | 4 | Each of the figure's slices split into four thinner fragments in the same envelope: the limbs read finely striped instead of in the approved blocky slices | **Yes** (figure B1) |
| Wall pipes | 0 | 14 a side | Thin horizontal pipes high (5.6–6.7 m) on both side walls of the room | **Yes** (room) |
| Landfill density (driven by wall pipes) | 1 | 2 | Finer terrain and twice the refuse | **Yes** (landfill L1); also memory and render time |
| Conduit pitch | 0.40 m | 0.20 m | Twice as many conduit segments: the rhythm of the cyan dashes doubles | **Yes** (conduits' emission pattern) |
| Cylinder / sphere segments | 16 / 12 | 64 / 48 | Smooth instead of faceted cylinders and spheres (joints, lamp, columns) | Slightly (less faceted than the early-3D language) |
| Bevel | 0 | 6 mm, 2 segments | True-size meshes with tiny rounded edges | Barely; texture mapping is by bounding box and unchanged (checked on the CRT screens) |

The lyric layout was measured on the final geometry, so it holds for either density.

## The test (renders/final_test/, on this CPU)

| File | What | Compared with |
| --- | --- | --- |
| `compare_lookdev_vs_final_1080p.png`, `compare_lookdev_vs_final_crtbank.png` | 1:02, final profile at 1920 × 1080 and 24 samples (the same pixels and samples as the lookdev still) | The locked Stage B light still |
| `final_4k_crtbank_s128_1m02s00_f001860.png` | 1:02, final profile at native 3840 × 2160 and 128 samples, the CRT bank | — |
| `compare_lookdev_vs_final_clip_1m01_1m03.mp4` | 1:01–1:03 at 15 fps, 960 × 540, 24 samples, lookdev left, final right | The locked Stage B light clip |

Findings: the CRT footage, tint, scanlines, brightness and cyan hierarchy are unchanged by the final
profile, and clean at 4K. Everything else that differs comes from the scene-content rows above:
the extra ghosts and the striped figure are the obvious changes at 1:01–1:03; the pipes show high
on the right wall; the conduit dashes are twice as dense.

## Decision

Option A, quality only (above). Option B (the denser scene as first defined) was declined: the
approved ghost density is balanced, the blocky figure is intentional, the room and landfill were
approved as they are, the 0.40 m conduit rhythm belongs to the cyan hierarchy, faceted primitives
belong to the early-3D language, and there is no reason for a bevel this late.

## Render time

Measured here: the final profile's 4K CRT-bank crop (35% of the frame) took 24 minutes at 128
samples on this CPU, so a whole 4K frame of the room is about an hour at 128 samples and four at
512. A fast GPU is perhaps 15–30 times quicker, which still makes 512 samples × 8,400 frames
very long. Before the full render, the collaborator should time a few frames on the GPU at 128,
256 and 512 samples (the room, the landfill, the station level, the pull-out) and choose the
lowest count that is clean after denoising; the look does not depend on the sample count.

## The sample-count benchmark (on the render machine)

`python tools/benchmark_final.py` renders, at the final resolution on the GPU, three consecutive
frames of each of four environments at 128, 256 and 512 samples (after one untimed warm-up render
each, so loading the scene onto the GPU is not counted), writes them to `renders/benchmark/`, and
prints the seconds a frame and the projected cost of the whole film at each count, each
environment weighted by the stretch of the film it stands for:

| Environment | Frame | Stands for | Judge |
| --- | --- | --- | --- |
| `room_crt_bank` | 1:02 | 0:00–1:36.9, 4:15–4:40 | CRT footage, ghost translucency, dark surfaces, cyan edges, PS1 textures |
| `landfill` | 1:42 | 1:36.9–1:52.5 | refuse detail, world-space lyric text, darkness |
| `station_level` | 3:13.5 | 1:52.5–4:00 | network shadows, dark surfaces, cyan emission |
| `pullout` | 4:14.37 | 4:00–4:15 | the infinite network, fog, darkness |

The rule: the lowest count that is clean and temporally stable in every environment. 128 if it
is clean; 256 only if it fixes a real problem; 512 only if a problem survives at 256. Then set
`samples` in `FINAL` (`core/profiles.py`) to it.

## On another render machine

The repository is the whole film's source: code, data and media. Nothing is read from anywhere else
(every path is relative to the project), and a build with the look stops with a list of what is
missing rather than render without it (the lyric layout, the CRT stream, the font, the maps, the
audio envelopes).

**Software** (what the project was made and tested with):

| | Version | For |
| --- | --- | --- |
| Blender | 5.1.2 (the code allows 4.4 and later; untested) | everything that renders or builds |
| Python | 3.13 (any 3.x with the standard library should do) | `tools/*.py` outside Blender |
| numpy, Pillow | 2.2.6, 11.3.0 | only the asset-making tools (`make_crt_video.py`, `make_retro_maps.py`); rendering needs neither (Blender carries its own numpy) |
| ffmpeg | 7.1.1 (gyan.dev essentials build) | encoding the film; remaking the CRT stream |
| Git, Git LFS | 2.51, 3.7 | the media and the lock references are LFS files |
| GPU | NVIDIA (OptiX or CUDA), AMD (HIP), Apple (Metal) or Intel (oneAPI), as Cycles in Blender 5.1 supports | `--device auto` picks the best; `--device cpu` forces the CPU |

No environment variables are required; `BLENDER` and `FFMPEG` may name the executables if they are
not on `PATH` (or pass `--blender` / `--ffmpeg`).

**Steps:**

1. `git clone <repository>` then `git lfs pull` (the audio master, the CRT clips and stream, and the
   lock references are LFS files: without them they are small pointer files).
2. `python tools/assets_manifest.py --verify`: every required asset present and byte-identical to
   the manifest (SHA-256). Stop if not.
3. The CRT stream is committed (`assets/video/crt/canvas/`). It can be remade from the clips with
   `python tools/make_crt_video.py` (byte-identical with ffmpeg 7.1.1; another ffmpeg may encode
   differently, which step 2 will then report: keep the committed stream).
4. `python tools/check.py`: unit tests, preview/final parity and the locked sequences.
5. `python tools/benchmark_final.py`: the sample-count benchmark; send back `renders/benchmark/` and
   the printed table.
6. Render any range of absolute frame numbers into the one sequence, resumable:

   ```
   python tools/render.py --profile final --start-frame A --end-frame B --skip-existing --device auto
   ```

   Frames go to `renders/final/frames/frame_NNNNNN.png` (or `--output-dir DIR`); a frame counts as
   done only if it is a complete PNG at 3840 × 2160; an interrupted run resumes by running the same
   command again. `tools/render_queue.py --output-dir DIR --device auto` runs chunk after chunk
   unattended.

## Production on the development machine's CPU (started 2026-10-22)

(The paths below are this machine's; nothing in the render depends on them.)

The definitive render runs locally on the CPU in chunks, with the locked final profile unchanged
(`--device cpu` is only an execution override). It is the master: one lossless PNG sequence, never
encoded per chunk.

- **The canonical sequence** is `C:\Users\jerem\pd_render\final\frames\frame_NNNNNN.png`, absolute
  frame numbers 0–8399 (D: had too little room; `tools/render.py --output-dir` sets the place).
- **Chunks:** `tools/render_queue.py` (started by `C:\Users\jerem\pd_render\final\run_queue.bat`):
  25 frames each, with a 10-frame probe on entering each heavier environment (the landfill at frame
  2907, the level from above at 3375, the station level at 4200, the climax and pull-out at 7200,
  the coda's room at 7651), validation of every frame (a complete PNG at 3840 × 2160, written under a
  temporary name and renamed when whole), and a line a chunk in `progress.log`. It stops itself on a
  failed frame, abnormal memory, low disk, a dramatic slowdown, or a `STOP` file in the frames folder.
  Running the batch file again resumes.
- **Chunk safety** (checked): every system is a function of the absolute frame; a frame rendered alone
  in a fresh session is pixel-identical to the same frame rendered inside a chunk.
- **PNG compression** 50% (lossless; about 11% smaller than the default 15% for about 0.1 s a frame).
- **Measured** (frames 1–10, the dark opening): 30 s to build, a median 8.3 minutes a frame, working
  set 3.6–4.2 GB, peak 5.1 GB, steady.
- GPU-rendered ranges can fill the same sequence later, once CPU/GPU equivalence is confirmed.
