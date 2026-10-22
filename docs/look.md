# Look development

The authored picture, 0:00–4:40, is locked. This is presentation: how the same film looks in a
lit engine. Nothing here moves, scales, shows or hides anything.

**Status.** Base look: approved. Hinge presentation fix: approved. Scrawl shader: approved. Scrawl tone lift (+18% in linear light): approved. Network emission 3:00–3:30: approved. Prosthesis passage 3:30–4:00: approved and locked. (So network emission is approved and locked for 3:00–4:15.) Climax 4:00–4:15: approved and locked (treatment v4). Opening light 0:00–0:35 and ending light 4:15–4:40: locked. Materials: room shell approved (A2, retro low-resolution; see below), with the 1 px box pixel filter; chamber floor approved (F1-LARGE); room props approved (X3); figure shell approved (B1); station level (N1) and landfill (L1) provisionally accepted; CRT physical treatment and display pipeline approved and locked, CRT screen content provisional; pull-out (fog, horizon gradient, echo network) approved and locked; plinth top, dark trim and tray clean by decision; the rear-wall display panels reserved as their own class; every other family not started (see `docs/material_inventory.md`). No animation has been rendered.

Code: `procedural_disagreement/scene/look.py` (materials, lights, render settings),
`procedural_disagreement/core/audio.py` (the soundtrack's level, as slow envelopes), the
`lookdev` profile in `procedural_disagreement/core/profiles.py`, and
`tools/lookdev_stills.py`.

## How it is kept from touching the film

- The `lookdev` profile builds the preview's own scene, object for object: the same density,
  the same realities, the same names.
- The look never writes an object's colour. The film's darkness, energy and translucency are
  carried there, as in the preview, so what can be seen and when is unchanged.
- Every opaque material ties its specular response to its own colour, so a surface the film
  has made dark answers no light at all. Without that, a lit engine would put a highlight on a
  black object and reveal what the film keeps unseen (the body before 0:12, the level before
  2:20, a station beyond the camera's sight).
- `tests/blender_locked.py -- --profile lookdev` compares the lookdev build against the twelve
  references recorded from the preview: every recorded transform and colour must still hold.

## The recorded notes, and what became of each

Every final-render note in the README, the film map and the section documents, by kind.

### 1. Global material treatment

| Note | Source | This pass |
| --- | --- | --- |
| Dark silicon-like structural surfaces | hinge | Station bodies: dark, smooth, not metal. |
| Restrained metallic interconnect, hierarchical roughness and specular | hinge | Trunks and mains are part metal; mains are smoother than trunks. |
| Copper- and aluminium-like variation between routing levels | hinge | Roughness only. No hue: colour is the film's, and is not touched. |
| Small highlights at the junction blocks | hinge | They share the trunks' material and catch the key as raised blocks. Nothing added. |
| Material distinction between station, group and network | climax | Machinery, station bodies and routing are three classes. |
| Scrawls as scratches, etching, relief; bars as metallic inlays or raised plates | refrain, coda | Scrawls are fully rough and take no highlight; bars are smoother and slightly metallic. Relief and etching are **not done**: they need texture work. |
| Bars told apart by material, not more geometry | coda | Done, within the limit above. |
| Material detail disappearing with distance | hinge | Left to the film's own sight falloff. |
| Material roughness / specular modulation by the music | README | **Not done.** |

### 2. Global lighting

| Note | Source | This pass |
| --- | --- | --- |
| Real darkness, indirect light, specular edges in place of the colour factor | outer frame | Real light and indirect light: yes. The colour factor is kept, because it is the film's visibility timing. |
| Secondary architectural lighting; reflected and rim illumination | README | The room is lit by what can be seen to light it: ceiling panels and the lamp. Two broad fills above the ceiling only lift the shadows. |
| Pools of light under chutes, distant chutes lit selectively | film map | The chute mouths are emissive and light what is under them. One broad dim fill under the pit's ceiling. |
| Distant station lighting, so the far field reads as points and lines | hinge | The station cells are emissive and read as points. No lights added per station. |
| Indirect light revealing the layering of the routing | hinge | One low key from the side: every raised thing throws a shadow. |
| 2:15–2:20: the layer going dark | film map | The film already does this in colour. |

### 3. Atmosphere and depth

| Note | Source | This pass |
| --- | --- | --- |
| Aerial haze, volumetric extinction increasing with altitude | hinge | **Not done**, deliberately: see below. |
| Atmospheric separation between the level and the refuse below | hinge | By light only: the pit has its own, much dimmer source. |
| Sight is the preview's stand-in for atmosphere; replace with real extinction | refrain, hinge | **Kept.** Sight decides what is visible when, and that is locked. |
| Atmospheric visibility giving depth down the lane | network | **Not done.** |
| Subtle atmospheric separation between plinth and rear wall | coda | **Not done.** |
| Subtle atmospheric / volumetric modulation by the music | README | **Not done.** |

Haze that adds light would show the outline of things the film keeps dark beyond the camera's
sight; haze that only removes light is what sight already does. So no atmosphere is added in
this pass. It should be tested on its own, on two or three frames, once the base look is agreed.

### 4. Emissive and network behaviour

| Note | Source | This pass |
| --- | --- | --- |
| Selective emissive networks along trunks and mains; sparse data-like activity | hinge | Done from 3:00, as inlays in the routing. Not during the hinge itself (1:52.5–2:20). |
| 3:00–3:20 route illumination, grouped emissive response by ring, propagation from the junction | network | **Done, approved.** See below. |
| 3:20–3:30 less low-frequency light; stronger negative space; the lane never lit | network | **Done, approved.** See below. |
| Sequential illumination of the route; role-specific responses for donor, receiver, carrier | prosthesis | **Done, approved.** See below. |
| Emissive propagation outward from the lane on the spread's clock; heat building to the peak; signal travel stopping at every cut end | climax | **Done, approved.** See below. |
| Reflected light from moving stations onto raised routing | climax | Indirect light does a little of this for free. |
| Residual network light dying through the room; last bars keeping light longer | coda | **Not done.** |
| Rear-wall panels as audio-responsive display surfaces | README | **Not done.** |

Up to 3:00 the only emission is what the film already has: cells, conduits, light panels,
chute mouths. From 3:00 to 4:15 the network layer is done and approved: it is driven by a
per-object value that does not go through object colour (see the sections below). After 4:15
it is not started.

### 5. Audio-responsive behaviour

| Note | Source | This pass |
| --- | --- | --- |
| Low-frequency energy: broad luminance response | README | The key over the level, the pit's fill and the room's fills lean up to 14% with the low band, smoothed over about a beat. In the room, only inside the film: the opening and ending keep their own light. |
| Mid, high, spectral brightness, structural events | README | **Not done.** |
| Global parameters breathing continuously, not one event per lyric | refrain | The lean is continuous and is not keyed to any cue. |
| 0:00–0:20 first minimal response; 4:25–4:37 the same, diminished; 4:37–4:40 none | outer frame | The room does not lean outside the film, so none of these is active. |

### 6. Section-specific accents

| Note | Source | This pass |
| --- | --- | --- |
| 0:58.6 second "stump": subtle accent | film map | **Not done.** |
| 1:00.0 back-wall surfaces wake | film map | **Not done.** |
| 1:20–1:30 fine surface activity, no low-frequency light | film map | **Not done.** |
| 3:20–3:30 less low-frequency light, selective edge response bordering the lane | network | The lean falls with the bass by itself. Nothing else. |
| 4:15.0 the whole layer withdrawing | film map | The cut does it. |
| Raised runs need a visible means of support | climax | Checked in the stills: see the report. No geometry added. |

### 7. Forbidden or deliberately absent

- The lane is never drawn or lit; no light, signal or response enters or crosses it.
- Any response path follows surviving infrastructure.
- No neon, no glowing circuit board, no science-fiction computer.
- No logo, text, wafer, package or real die layout.
- No readable writing (the one exception, added 2026-10-21, is the sung lyric in Chinese: see
  the lyric section); no one event per repetition of the lyric.
- No audio-reactive change during the final silence.
- The opening is not a visualiser.

Nothing in this pass does any of these.

## Materials

Nine classes of opaque surface, chosen by what an object is. They differ in roughness and in
how metallic they are; base colour is always the object's own.

| Class | What | Roughness | Metallic |
| --- | --- | --- | --- |
| wall | Room shell, ribs, anything unclassified | 0.72 | 0 |
| floor | Floors, plinth, rear panels, station platforms, level ground | 0.50 | 0 |
| trunk | Trunks, junction blocks, fine runs | 0.46 | 0.55 |
| main | Mains | 0.36 | 0.65 |
| station | Station bodies, bays, cells, spurs | 0.40 | 0 |
| machinery | Station machinery, cabinets, lamp, towers, rotors | 0.34 | 0.60 |
| debris | Refuse, strata, waste, discarded limbs, chutes | 0.90 | 0 |
| body | Everything belonging to the figure | 0.52 | 0 |
| scrawl / bar | The two conditions | 0.95 / 0.28 | 0 / 0.35 |
| shell | Room walls, ribs, ceiling: the wall class with the A2 surface (below) | 0.72 | 0 |
| display | The 15 rear-wall panels, reserved for the CRT / display pass | 0.50 | 0 |
| chamber_floor | The room floor and the plinth's lower step, with the F1-LARGE surface (below) | 0.50 | 0 |
| fixture | The cabinets and carriages and the lamp housing, with the X3 prop surface (below) | 0.34 | 0.6 |
| body_shell | The figure's pale shell (pelvis, torso slabs, head, arm and leg segments), with B1 (below) | 0.52 | 0 |

Edges are rounded in shading only (a bevel in the shader); every box keeps its exact shape.
Energy, translucent and plane materials are the film's own and are unchanged.

## Light

| Light | Where | Strength |
| --- | --- | --- |
| Level key | A distant, low, cold source over the station level, from the side | 2.2 W/m² |
| Level ambient | Everywhere above ground | 0.012 |
| Pit fill | One broad source under the pit's ceiling | 90 kW over 420 m square |
| Pit lamp | Over the heap our chute feeds (as before) | 60 kW |
| Room fills | Above the ceiling, front and back | 220 W each |
| Room lamp | Over the plinth | 1300 W, when the film has it on (see below) |
| Practical | Ceiling panels, lamp face, cells, conduits, chute mouths | The film's own emission |

The black shell that stands in for distance is made invisible to light, so it does not shade
the level; the camera still sees it as black.

Energy surfaces (cells, conduits, chute mouths) emit at strength 4; the room's practical
sources (ceiling panels, the lamp's face) at 1.8, so that when the film dims them they are seen
to dim. An energy surface the film has idle emits nothing.

## Render settings used for the stills

| | |
| --- | --- |
| Engine, device | Cycles, CPU (4 threads; no supported GPU on the development machine) |
| Resolution | 1920 × 1080 |
| Samples | 32, adaptive (threshold 0.03) |
| Bounces | 4 total: diffuse 2, glossy 3, transmission 2, transparent 8, volume 0 |
| Clamp | Indirect 4.0; no caustics |
| Denoiser | OpenImageDenoise, guided by albedo and normals, prefilter accurate |
| Pixel filter | Box, 1 px (from 2026-10-19; before that Cycles' default 1.5 px Blackman-Harris) |
| Geometry | The preview's: no bevels, no added pipes, two realities |
| Render time | 67 s to 302 s a frame: about 2 min on the level, 4 to 5 min in the room and the pit |
| Build time | About 80 s a frame, since each still is built on its own |

Stills are in `renders/lookdev/stills/`; `contact_lookdev.png` is the sheet.

## Second pass: the hinge and the scrawls (done)

Both layers are approved and finished. Do not revisit them when later layers are added.

**The level's key is kept off the waste.** Light linking: the key has a receiver collection in
which every object of the pit (refuse, strata, terrain, discarded limbs, chutes, the pit's floor
and walls: 9,212 objects) is excluded. They keep the pit's own light and all indirect light.
From 1:57.5 to 2:15 the waste is a dark irregular ground under the routing.

**What stands on a station is not there until the film reveals it.** Station machinery,
platforms, cells and bars stand in the scene, black, from the start; the hinge was approved
before they existed. In the look, each such object's visibility to every kind of ray follows
its own colour channel, the very function the film animates it with: off while that is black,
on the moment it is not. Nothing is timed here. Station bodies, routing, cells of the level,
the pit and the room are not affected.

**Scrawls.** Still the film's boxes, on the film's paths, with the film's colour and timing.
In the look:

- only the face of each box that lies in the surface is drawn, so a trace has no sides, ends
  or thickness;
- a trace is seen by the camera and by nothing else. Where two of its boxes overlap their faces
  lie in one plane and each shaded the other black: that was the "dark joints";
- across its width the normal tips as the two lips of a shallow cut (20 degrees);
- its edges are frayed by a fine grain fixed in the world, running unbroken from box to box;
- no highlight, no shadow, no emission;
- its tone is the film's, lifted 18% in the material only (about 10% in the displayed image),
  so that a line this thin survives motion and compression. The object's colour is untouched.

Stills: `renders/lookdev/hinge/` and `renders/lookdev/scrawl/`.

## Network emission, 3:00–3:20 (approved)

Code: `procedural_disagreement/presentation/emission.py` (the rule; pure, no Blender) and
`scene/look.py` (how it is drawn).

**Rule.** The state starts at the junction of the heavy trunk and the heavy main at 3:00.0 and
goes outward along the routing. A piece's ring is its distance from the junction measured along
the routing, in steps of 40 m, as the film's own rings; ring *n* is reached *n* bars after
3:00.0 (eight rings, the last at 3:17.5). A response comes up in half a second and settles to
50% of its peak. A station's cell confirms on the film's own ring for that station. From 3:20
everything holds: nothing later is designed.

**What responds.** Trunks, mains, junction blocks and fine runs only. Never a station body, a
bay or a holding cell, and never anything that lies in the lane.

| Kind | Peak strength | Share that responds |
| --- | --- | --- |
| The source (where the two heavy runs cross) | 1.5 | one |
| Heavy main, heavy trunk; junction block; station cell | 1.0 | all |
| Main | 0.825 | all |
| Trunk | 0.675 | all |
| Fine run | 0.45 | about one in eight |

**How it is drawn.** As emission in the piece's own material, on its upward face only.

- The source is a square frame, 3.4 m across and 0.45 m thick, with no inlay within 7 m of it:
  a different kind of mark from an inlay.
- A run lights only at short inlays: 0.9 m long; 0.8 m wide on a trunk and 1.0 m on a main,
  whatever the width of the run; spaced 6 to 11 m apart, each run with its own spacing and offset.
- A junction block carries an inset a quarter of its top.
- A response is turned down near the camera: 30% within 10 m, full from 45 m.
- A response is never brighter than the film has the piece lit.

The value is a custom property on the object; it is not its colour, place or visibility.

**Also fixed here.** The eleven junction blocks on the heavy trunk are exactly as high as it, so
their tops lay in one plane and shaded each other black. They are now seen by the camera only.

Stills: `renders/lookdev/emission/` (`look_emit4_*`, `contact_emission_v4.png`).

## Network emission, 3:20–3:30 (approved)

The bass goes and the network turns to the lane. The state it acquired does not go on
building. Nothing new lights anywhere in this passage: every response only goes down.

- **The field eases back.** From 3:20.0, over one bar, every response settles to 70% of the
  level it had.
- **Routing beside the lane goes quiet.** Within 16 m of the lane's axis a response falls to
  8% of its level; beyond 42 m it is untouched; between, it is graded. It does so band by band
  along the lane, in the order the lane is cleared, starting 0.6 s before each band begins to
  go down and done 1.2 s after.
- **Stations facing the lane keep their cells** (at the field's 70%). They are the only lights
  bordering it.
- **The source goes quiet with the rest**: the lane starts about 12 m from the junction.
- Nothing is lit in the lane, at its edge or across it.

It is acceptable for this to read as the network broadly withdrawing; the viewer is not asked
to decode a lane-specific rule. From 3:30 the levels hold until the next passage is designed.

Stills: `renders/lookdev/emission/` (`look_lane_*`, `contact_lane_emission.png`,
`diagnostic_lane_emission_overhead.png`).

## The prosthesis passage, 3:30–4:00 (approved, locked)

Function is routed round the lane, station by station. No new mark, colour or timing: the two
marks the network already has, a station's cell and the inset on the junction block where its
spur meets its trunk, say what each station is doing, on the film's own stroke clock for it
(`prosthesis.turn`).

- **3:30 is a change of state for the whole field.** From 3:30.0, over 1.25 s, every
  station's cell goes down to rest: 12% of its emission, which displays at about 73% of a full
  cell. Every station, on the route or not. It reads as the field settling, not powering down.
- **Full = gives.** A donor's cell returns to full during its stroke.
- **Rest = available.** Every other cell, and a carrier's.
- **Dark = takes.** A receiver's cell goes out (to 3% of its rest) during its stroke.
- **Infrastructure pulse = carries.** A carrier's junction block pulses (+1.2) while its
  carriage runs.
- **The relay**, 224, has no cell: only its junction block answers, when it indexes.
- **The route accumulates.** When a station is recruited its junction block comes back up
  (peak 1.0, settling to half) and stays, in the order the film recruits.
- **What has just joined owns the picture.** A station's first stroke, the one it makes as it
  is recruited, is its full response; every repeat is 45% of it.
- Nothing is lit in the lane or across it; nothing changes at or before 3:30.0.

Measured in the stills (blue channel, 0–255): a full cell about 236, a resting cell about 173,
a receiver at the depth of its stroke about 42. A donor's repeat at 45% displays at about 222:
visibly above rest, only a little below full, because a cell is near the top of the picture's
range either way.

Across the passage the field does not build up: frame mean luminance stays between 11 and 18
and lit pixels under 0.3% from 3:30 to 4:00.

**Validation.** 174 unit tests pass (five for this passage pin its rule: nothing changes at or
before 3:30; one rest for the whole field; donor to full, receiver out, carrier at rest; the
route lit in recruitment order and never in the lane; first strokes 100%, repeats 45%). Parity:
zero deviation. All twelve locks pass on both the preview and lookdev builds. The whole-passage
still review (sixteen frames, 3:30 to 4:00) passed; the frame at 4:00 is consistent with the
passage, with no brightness jump (mean luminance 16.9 against 16.7 at 3:59.5), no build-up, no
new role ambiguity and nothing that prepares the climax.

Do not alter any parameter of 3:00–4:00.

Stills: `renders/lookdev/prosthesis/` (`look_pros3_*` diagnostics; `passage/` for the whole
passage, `contact_prosthesis_passage.png` and `compare_3m59p5_vs_4m00.png`).

## The climax, 4:00–4:15 (approved, locked: treatment v4)

The established system driven past its operating state. Nothing new is drawn: the marks the
network already has are driven by the climax's own authored clock instead of standing still.

- **Stations.** Every station with machinery keeps the 3:30 grammar exactly (full gives, rest is
  available, out takes, a carrier's junction block pulses), on the climax's clock; the 28
  stations recruited after 4:00 take part from their own recruitment. First strokes 100%,
  repeats 45%. The climax's accumulation is never applied to cells: a donor at 4:13 means what
  a donor meant at 3:42.9.
- **Routing.** An inlay responds when the authored spread reaches it: distance from the lane,
  16 m/s on the beat, so the first new marks are at the ends the lane cut. Nothing in the lane
  is lit; no mark stands within 2 m of a cut face; both sides of a cut answer independently.
  Reach: the climax's authored 150 m from the lane.
- **Structure refreshes, never boosts.** When a bus or trunk run makes its authored rise its
  response returns toward the peak it already had, never above it.
- **Occupancy, not brightness.** Settled level 50% → 65% from the coupling → 85% at the peak;
  the field keeps 0.7 → 0.85 → 1.0. Routing only.
- **Denser instrumentation.** The original marks never move. One more mark per period of each
  run's own spacing is admitted from the coupling (spacing about 4–7 m), one more from
  saturation (about 2.5–4.5 m), each run's admitted only when its wave reaches it. Each added
  mark has its own place along the period and across the run (within the middle 55% of the
  usable width), from a hash of (run, tier, period); at least 0.6 m from any other mark.
- **Fine runs** stay about one in eight until saturation, then about one in three, each when the
  saturation wave reaches it.
- **Hold.** From 4:14.375 to 4:15 everything holds; no flourish, no decay.

Measured (1920×1080; lit = cold-blue pixels): 4:00 0.07%, 4:05 0.27%, 4:08.5 0.42%, 4:11.2
0.43%, 4:12.0 0.61%, peak 4:14.375 0.91%, mean 20.0 against 19.4 with the layer off. No mark
brighter than a full donor cell. Zero lit pixels in the lane in every frame.

**Validation.** 181 unit tests pass (seven for this passage: no step at 4:00; the cell grammar
identical to 3:30-4:00; spread order, the lane and the cut ends; structure never above its
peak; added marks admitted by their wave and never before 4:00; fine runs widening only from
saturation; accumulation and the hold). Parity: zero deviation. All twelve locks pass on both
the preview and lookdev builds. 4:00 and 4:02.9 re-rendered with v4 are pixel-identical to the
first climax pass, and 4:00 matches the approved prosthesis 4:00 (largest difference 1/255).
From 4:14.375 to 4:14.967 the routing response changes by 1.4% and lit coverage by 0.01 points:
it holds. Zero lit pixels in the lane at the peak and the last frame.

Do not alter any parameter of 4:00–4:15.

Stills: `renders/lookdev/climax/` (`look_clx4_*` final; `contact_climax_v2.png`,
`compare_peak_v3_vs_v4_transverse.png` and the other comparisons).

## The room lamp outside the film: opening and ending (locked)

The preview has no lamps, so authored light is a factor on each object's colour. The look's
lamp over the plinth used to burn at full strength from the first frame to the last, which put a
lit pool on the plinth, the legs and the tray while the film had the lamp off: the room was lit
twice, once by the colours and once by a lamp that is not on. The rule now is one sentence: **the
lamp spot is the authored lamp.** Its strength follows the lamp's authored state and it moves
with the lamp. The ceiling fills are unchanged everywhere: they do not follow the authored room
level, which is already in every object's colour (dimming them too darkens the room twice; tried
and reverted at 4:25).

- **Opening (0:00–0:35).** The lamp is off until READY: its strength is the lamp pool's own
  authored level (0 until 0:30.0, 63% at 0:30.2, full by 0:30.5). It hangs at its authored
  0.4 m raised position until READY and docks with it (by about 0:30.9).
- **Inside the film (0:35–4:15).** Full strength, docked: exactly as approved.
- **Ending (4:15–4:40).** Its strength is the larger of the room's authored level and the
  plinth and lamp pools' levels, so it is at the room's level until the film lights the lamp
  (4:35.7), and then it is the light that arrives. It moves with the lamp's undocking.

Measured, opening (frame mean / plinth and legs, 0–255):

| | 0:12.5 | 0:17.5 | 0:29.9 | 0:30.3 | 0:31.5 |
| --- | --- | --- | --- | --- | --- |
| Before | 7.0 / 16.2 | 6.2 / 28.6 | 31.7 / 63.0 | – | 78.1 / 96.3 |
| After | 4.6 / 9.7 | 3.8 / 16.6 | 28.9 / 41.8 | 34.7 / 63.0 | 78.1 / 96.3 |

At 0:30.3 the pool reaches the plinth and the body while the walls barely move (22.1 → 26.3);
the room follows by 0:31.5. READY reads as the lamp's light arriving. Nothing is shown before
its authored reveal: compared with the locked preview at 0:12.5 and 0:17.5, the corrected frames
show the same things, slightly darker. (The torso at 0:12.5 is authored: the plinth pool reaches
it.)

Measured, ending (fills reverted, lamp rule kept): 4:14.967 mean 19.8 → 4:15.033 44.8; 4:25.0
mean 22.4 (base 24.8), plinth top 39 (base 54, no longer pre-lit); at 4:31.5 the head and the
carriage are lit; at 4:36.3 the plinth reaches 74, the light arriving.

The spot is the look's own light object, `LampSpot`, a copy of the stage's `Lamp`. The stage's
light object is part of the locked picture (the locks compare every object's transform), so it
stays where the preview has it, with no strength; moving it instead failed the lookdev lock
comparison at 4:22.8–4:40 by up to 0.2 m.

Validation: 181 unit tests, profile parity, the twelve preview locks and the lookdev lock
comparison all pass (zero deviation).

Stills: `renders/lookdev/opening/` (`look_open_before_*`, `look_open_after_*`,
`compare_opening_before_after.png`, `compare_preview_vs_after.png`, `contact_ready_after.png`)
and `renders/lookdev/ending/`.

## The room shell: A2 (approved 2026-10-19)

The room's walls, ribs and ceiling take a deliberately low-resolution grey surface in the manner
of late-PS1-era textures. The aim was not realism: it is to make the box geometry read as
intentionally synthetic rather than unfinished.

**The rule.** A 64 × 64 grey map is box-projected in each object's own space, scaled to metres,
and sampled nearest-neighbour. It only multiplies the object's own colour, about a mean of 1, so
black stays black and every authored reveal, light and colour state is kept. Roughness, metal,
bevel and specular are the wall class's own and unchanged; specular still follows the
unmultiplied colour. It never emits. The rear-wall display panels are their own class
(`display`) and never take it.

| Parameter | Value |
| --- | --- |
| Objects | Wall, WallBack, WallFront, Ceiling, Rib (33 in all) |
| Map | `assets/textures/room_shell/retro_ps1_01/modulation.png`: 64 × 64, grey, seamless; mottling at 6–24 texels plus per-texel grain, 8 levels through a 4 × 4 ordered dither. Made by `tools/make_retro_maps.py` (deterministic). |
| Texel | 10 cm (one tile 6.4 m) |
| Sampling | Closest (nearest-neighbour), box projection, no blend |
| Contrast | Walls and ribs ±20% on colour; ceiling ±11% (its darker blue-grey read the full contrast as stains) |
| Pixel filter | 1 px box for the whole film, with OIDN guided by albedo and normals: keeps texel boundaries hard. Approved knowing it also slightly hardens every geometric edge. |

**How it reads.** Nearby, crisp square texels; at distance a finer grain, as on hardware of that
era. Frame brightness moves by at most 0.3 levels. Tested at 0:31.5 (READY), 1:18.5 (nearest
wall), 4:19.1 (coda, dim) and in motion during the approach, 0:44–0:46 at 15 fps: the texels ride
with the surface, with no crawling or block flicker.

**What was tried first, and why it was not kept** (stills under `renders/lookdev/materials/room_shell/`):

| Test | Parameters | Result |
| --- | --- | --- |
| Orange-peel micro texture (`orange_peel_01`, CC0) | 0.40 m tile (≈4 mm droplets); height as bump, 5.8° / 11.6° flank tilt; roughness ±0.04 | Invisible at 1080p and in 4K crops: below the film's useful scale. Not to be enlarged. |
| Roller / paint roughness | Procedural, 0.25 × 1 m bands and 1.5 m patches; ±0.03 / 0.06 / 0.10 | Indistinguishable from the baseline under the room's soft light. |
| Shallow waviness | Procedural bump, 0.8 m and 2.5 m; 0.15° / 0.35° / 0.7° RMS tilt | Indistinguishable from the baseline. |
| RETRO_A (PS1) | The A2 map with 5 cm texels, ±15% | Visible but read as dirty concrete; texels too small to read as deliberate. |
| RETRO_B (N64) | Bilinear, broad mottling, colour ±12% and roughness ±0.08 | Barely visible: soft variation vanishes under soft light. |
| **A2** | **10 cm texels, ±20%** | **Approved (ceiling at ±11%).** |
| A3 | 20 cm texels, ±20% | Upper bound: reads as a block pattern laid on the wall. |

Validation: unit tests, profile parity, the twelve preview locks and the lookdev lock comparison
pass; the production material renders 0:31.5 and 4:19.1 pixel-for-pixel as the approved test
candidate. The `lookdev` profile is the only one that applies the look so far; the final
profile does not yet.

## The chamber floor: F1-LARGE (approved 2026-10-19)

The room shell's language carried onto the floor. Its own class (`chamber_floor`: the floor and
the plinth's lower step only), so it cannot reach the plinth top, the floor trim, the station
aprons, the level ground or the pit ceiling, which keep the floor class's plain values.

| Parameter | Value |
| --- | --- |
| Objects | Floor, PlinthStep |
| Map | `assets/textures/room_shell/retro_floor_01/modulation.png`: the shell map's recipe (64 × 64, 8 levels through a 4 × 4 ordered dither) with its own seeds, so the floor does not repeat the walls |
| Texel | 20 cm (one tile 12.8 m): twice the walls'. The floor is seen at a grazing angle, where 10 cm texels fall below a pixel in depth; matching apparent size on screen matters more than matching metres |
| Sampling | Closest (nearest-neighbour), box projection, no blend |
| Contrast | ±20% on colour, mean 1: colour only, no roughness or other channel |

It reads as calm, clearly blocky retro structure even at the floor's grazing angle; the lamp
pool keeps its authored shape at 0:30.3, 0:32.0 and 4:36.3; the 4:36.3 composition is unchanged.
Motion: 1:35.6–1:36.8 at 15 fps (the fastest camera move over the floor, 1.0–1.4 m/s, floor 15–22% of the frame), against the baseline over the same frames: the blocks ride with the floor; frame-to-frame change 6.11 levels with the texture against 5.90 without, so no crawl, shimmer or extra denoiser flicker; the lamp pool stays one coherent shape with no block pattern inside the light beyond the floor's own colour steps.

**Test history** (`renders/lookdev/materials/chamber_floor/`):

| Test | Parameters | Result |
| --- | --- | --- |
| F1 | 10 cm, ±12%, colour | Under one level of change: invisible (dark floor, grazing view). |
| F2 | F1 + roughness ±0.05 in the map's steps | Same; the pool unchanged. |
| F1+ | 10 cm, ±25%, colour | Visible, but a busy small-grained mottle that reads slightly dirty. |
| **F1-LARGE** | **20 cm, ±20%, colour** | **Approved.** Amplitude was not the limit; projected texel size was. |
| F1-LARGE + roughness | ±0.15 in the map's steps | Lighter texels also rougher: cancels the blocks at 0:32.0 and adds smudgy sheen on the lit step. The pool stays coherent, but nothing is gained. |

Validation: unit tests, profile parity (zero deviation), the twelve preview locks and the lookdev
lock comparison pass; the production material renders 0:30.3, 0:32.0 and 4:36.3 pixel-for-pixel
as the approved test frames, and 1:36.5 within one level on 666 pixels scattered evenly over the
whole frame (run-to-run render noise, not the floor).

## The room's props: X3 (approved 2026-10-19)

The room's pale moving fixtures read as props in an early-3D world, not as room material on
smaller objects. Where the architecture tiles its texture in metres, each prop takes one small
texture stretched once over each face, as props were textured on hardware of that era.

| Parameter | Value |
| --- | --- |
| Objects | Cabinets and carriages (16), the lamp housing; class `fixture` (the machinery class's values) |
| Map | `assets/textures/room_shell/retro_prop_01/modulation.png`: 16 × 16, 4 grey levels, no dither (`tools/make_retro_maps.py`) |
| Mapping | Once per face, stretched: the box's own coordinates, nearest-neighbour. Texel size differs from prop to prop and face to face; the same texture is reused on every prop, deliberately |
| Per-face tone | One flat tone per face (and per facet of the lamp housing), ±6%, from a hash of the object and the face's direction |
| Contrast | Map ±14% plus face ±6%: within about ±20% on colour, mean 1. Colour only |
| The carriage | Its texture stretches with it as it extends (1:15.6–1:18, and 4:32–4:33.5), as on hardware of the era |

Not textured, by decision: the plinth top (the film's focal surface; the ending's light arrives
on it empty) and the dark trim and tray (at 3–6% colour a colour multiply cannot show, and a
roughness channel only smudged on the floor).

Motion, 15 fps, clean against X3: the carriage across 1:15.5–1:18.0 and 4:32–4:35 deforms
continuously with no pop (frame-to-frame change 0.38 against 0.29 clean, and 0.08 against 0.07);
the lamp housing during the approach, 0:44–0:46, keeps a steady banded rim with no temporal
aliasing (1.84 against 1.80). The props stay distinct from the walls throughout.

**Test history** (`renders/lookdev/materials/fixtures/`):

| Test | Parameters | Result |
| --- | --- | --- |
| Clean | — | Too modern and neutral for an early-3D world. |
| X1 | The architecture's language: 10 cm metric texels, ±12% | Read as miniature wall texture. |
| X2 | 5 cm metric texels, ±12% | Generic grain, barely visible. |
| **X3** | **Per-face stretched 16 × 16, 4 levels, face tone ±6%** | **Approved.** |

Validation: unit tests, profile parity (zero deviation), the twelve preview locks and the lookdev
lock comparison pass; the production material renders 0:39.5 pixel-for-pixel as the approved X3
test frame and 1:16.5 within one level on 1,080 pixels scattered evenly over the frame (run-to-run
render noise); the approved shell and floor render pixel-for-pixel as before (0:32.0).

## The figure: B1 (approved 2026-10-20)

The figure's pale shell takes the props' logic, as a texture-mapped character model of the era:
the 16 × 16 prop map stretched once per face plus a flat tone per face, softer because it is
the focal human object (texture ±8.4%, face ±3.6%: about ±12%), colour only. Joints, neck,
sensor bands, spine, tanks and risers stay clean. The ghost copies (the amber body included) have
the translucent ghost material, which the look never touches.

Chosen over B2 (a flat tone per face only, ±8%: clean but closer to modern low-poly than to PS1)
at 0:31.5, 1:17.0 and 1:31.0. Checks: the reveal at 0:12.5 and 0:17.5 is unchanged (frame means
identical); the ghosts at 0:50.0 are intact; production renders 1:17.0 as the test frame (628
pixels within one level: render noise). Stills: `renders/lookdev/materials/figure/`.

## The CRT panels (2026-10-20)

**CRT physical treatment and display pipeline: APPROVED / LOCKED.
CRT screen content: the lyric is approved and locked (2026-10-21, see the next section); the real
footage is approved and locked (2026-10-22) as independent monitors, Stage B light (below).**

Locked: the authored pale bezel (10 cm) and box sides; dark glass on the inner front face (the
authored colour × 0.25, roughness 0.15); a 64 × 48 virtual-pixel raster with visible scanlines;
emission in a cold pale near-monochrome cyan, below the cyan cells in brightness, seen by camera
rays only (it lights nothing and appears in no reflection); tied to each panel's authored light
and to the screens' wake (the opening's panel at 0:09.5, the rest row by row from 0:20); and the
pipeline that carries animated imagery to the screens (per-panel animated values from
`presentation/screens.py`, drawn by the `display` class's material in `scene/look.py`).

**Revised 2026-10-21 (director): the 4:15 shutdown.** The screens were dark from 4:15 so that the
coda's marks read against dark glass. Now, while the refrain is sung at full voice (4:15–4:25),
the screens that carry its words are lit with them, and on those panels the lyric takes priority
over the coda's scrawls and bars; then they go dark again. Every other screen stays dark, and all
other coda lighting, geometry and marks (the floor, the other panels, the lamp, the room light,
the final marks) are unchanged. Details in the next section.

Provisional, until footage arrives: single stepping blocks from 1:00, traces from 1:20 with the
attractor's held block, sparse high-band flicker. Tried and dropped: rows of bars (read as lines
of text); a brighter idle raster (read as a lit wall, competing with the cells). Stills and clips:
`renders/lookdev/materials/crt/`.

## The lyric: CRT and world-space text (2026-10-21)

**The one exception to "no written language".** The sung lyric, in the director's final
Traditional Chinese translation, is the only writing in the film. It appears on the rear wall's
CRTs or, where they cannot be read in the shot, as text standing in the scene; never as
screen-space subtitles, and never both at once. This exception is the lyric only. It is no
permission for labels, interface text, numbers, logos or any other writing, on the screens or
anywhere else.

| | Line (final; do not rewrite) | Sung (first syllable) |
| --- | --- | --- |
| A1 | 捨棄那冒犯性的軀幹 | 0:40.0, 0:50.0 |
| A2 | 卻將它封聖於殘肢 | 0:44.97, 0:54.97 |
| C1 | 這些潦草的土地致謝聲明 | 1:20.1; 2:20.1–2:55.1 every 5 s; 4:15.1, 4:20.1 |
| C2 | 這些強人胸前的勳表 | 1:22.55; 2:22.55–2:57.55 every 5 s; 4:17.55, 4:22.55 |
| B1 | 我寧願它從未存在 | 1:30.1, 1:40.1 |
| B2 | 也想知道它在哪座垃圾掩埋場 | 1:34.85, 1:44.85 |

**Timing** comes from `docs/lyric_alignment.md` (authoritative): each line from its first
syllable; held through a pause of less than 0.8 s into the next line, so a couplet does not blink
between its lines; the last line of a statement held 0.3 s past its last syllable. A line sung
across one of the film's cuts (1:36.9, 2:15, 4:15) is shown in two parts, one on each side.
Text, phrase groups and timing: `presentation/lyrics.py`.

**The font** is GNU Unifont 17.0.05 (`assets/fonts/unifont/`, OFL 1.1 or GPL with the font
embedding exception), read from its .hex file pixel for pixel by `presentation/glyphs.py`: a true
bitmap font, so the text can only be hard square pixels. Nothing is smoothed, boxed or animated:
text switches on and off on the frame.

**Where each line goes** is measured, not chosen by hand. `tools/lyric_layout.py` builds the final
profile's scene and steps the film's own cameras through every line. For each of the 15 screens
it tests, frame by frame, whether the part of the glass the text would occupy is in the picture,
faces the camera, is crossed by nothing opaque (rays against every object's posed box, 17 × 9
points a screen), is large enough to read (at least 45 lines of a 1080-line frame tall for one
or two characters a screen, 100 for three or four) and is lit and awake in the film. A screen
that passes for at least 85% of the line can carry it. Lines sung together in one shot (a couplet,
the refrain's repetitions) form a block, and a block is shown one way throughout: on the CRTs if
every line of it fits on its readable screens, otherwise as world-space text. So the two systems
never alternate within a shot; a change happens only at a cut. Results:
`assets/lyrics/layout.json`.

*CRT mode.* The wall is one 320 × 144 canvas, each screen a 64 × 48 section of it. While a line is
up the whole wall is in lyric mode: the screens with text show it, the rest show only the idle
raster, and no footage, blocks, traces or flicker run underneath. The line is split at its phrase
boundaries into rows, one per wall row from the top, each on the widest run of readable screens in
that row (a row of text may step over one hidden screen, never more), centred on it. One or two
characters a screen, drawn two screen pixels to a font pixel (32 × 32), if the block fits that
way; otherwise three or four at one pixel (16 × 16). One size for the whole block. Within a row
the text is divided between screens at whole words (director, 2026-10-21: 「土地」 / 「致謝聲明」,
never 「土地致」 / 「謝聲明」): a screen whose glass is clear for it takes one character more than
the line's usual number rather than split a word; meaningful grouping comes before an even count.
The words are listed in `presentation/lyrics.py` (WORDS). The glyphs are
the screens' own light (the lyric at full, footage below it), so they take the raster, scanlines,
panel light and wake like everything else the screens show.

*World-space mode.* The line in rows of at most eight characters, centred, on a flat sheet fixed
in the world: placed where the camera sees it in the upper part or a side of the frame, 5–60 m
away, facing the camera as it is at one moment of the line, and left there, so the camera's own
movement gives it parallax. The place is chosen from candidates followed through the whole line:
the text must stay inside the frame, keep its glyphs within 0.55–1.8 times their size when
placed, be hidden by nothing (the ghosts and planes included), and be seen against empty space:
the void, or a plain surface of the place (wall, ceiling, floor, the pit) not so close behind it
that it would read as written there, never against an object (the figure, a ghost, a panel, a
conduit), however far; with a slight preference for the upper half and for about 10 m. Consecutive lines in one shot keep the
same place (as their own camera sees it) for as long as one place is usable for all of them:
holding as long as each line's own best place and scoring within 0.2 of it; the text moves only
where staying would put it somewhere clearly worse. If no place holds for the whole line (the camera falls
after the 1:36.9 cut), the text appears from when one does hold, for at least a second, and never
later than a second before the line's last syllable: a line is not put up once it has been sung.
Checked against the alignment (2026-10-21): after the cut B2 appears at 1:38.1, while "it is in"
is still to come (1:38.15–1:39.4); every other line appears on its first syllable. The glyphs are
one font pixel to a texel, nearest-pixel, 3.6% of the frame's height when placed; a pale, cold,
nearly grey light (0.80, 0.86, 0.90 × 0.55), held below the CRTs' cyan; seen by the camera only:
it lights nothing, casts nothing and is in no reflection.

*The coda (4:15–4:25).* The refrain's four lines go on the CRTs (the room camera sees the wall
well). The lyric goes round the three panels with ranked bars where it can (the bars are what its
second line names, and the last of them goes inside the last sung word); on the panels it does
use, the coda's scrawls give way to it for the whole coda, so no mark appears and vanishes as the
lines change. The screens without words stay dark.

**Where the lines went** (final profile, measured 10 times a second through every line; locked
2026-10-21):

| Lines | Shown | Why |
| --- | --- | --- |
| A, 0:40–1:00 | CRTs: one row along the top of the wall, three characters a screen, stepping over the top-centre screen the lamp hides (捨棄那 / 冒犯性 / 的軀幹; 卻將它 / 封聖 / 於殘肢); the last line in two rows (於殘肢 on the middle row) | The figure, the plinth, the side towers and the conduit risers hide every other screen; the top row is too short for one or two characters a screen as the camera nears, so the block is at one pixel a font pixel (glyphs 37–52 lines of 1080 tall) |
| C, 1:20 | World text, right, 8 m, both lines in one place | Close on the figure: no line fits on the screens that stay readable |
| B, 1:30–1:36.9 | World text, right, 5 m, both lines in one place | Only the right-hand column stays readable; B2 cannot fit, so the couplet is in the world |
| B2 after the cut | World text, upper left, 12 m, from 1:38.1 | The camera falls 16 m and tilts 30° through 1:36.9–1:38.4; nothing fixed stays in frame until it settles. "It is in" is still sung (1:38.15–1:39.4) |
| B, 1:40–1:50 | World text, upper centre, 26 m, both lines in one place | The flyover: the camera's travel gives the parallax |
| C ×8, 2:20–3:00 | World text, upper left, 12 m, all sixteen lines in one place | The station level: the room is not in the shot |
| C ×2, 4:15–4:25 | CRTs: 這些 top left, the second phrase in the middle row, the rest on the bottom row (土地 / 致謝聲明; 胸前的 / 勳表); three characters a screen, four for 致謝聲明 | The lyric goes round the bars; the scrawls on these four panels give way |

**Footage (approved and locked 2026-10-22).** Real video for the screens goes in
`assets/video/crt/` (the director's clips 01–08); `tools/make_crt_video.py` makes it into one clean
stream (`assets/video/crt/canvas/stream.mp4`, 960 × 540, the film's 30 fps by dropping frames,
never sped up) and a manifest. Every CRT is its own monitor: it plays the stream from the start of
its own clip and cuts to the next when that ends, so the eight clips run side by side on different
screens and none loops within the 36.9 s the wall carries footage (1:00 to the cut at 1:36.9). The
bank starts on the clips in the pattern 1 2 3 4 5 / 6 7 8 1 2 / 3 4 5 6 7 (top row first): no two
screens side by side, above one another or corner to corner on the same clip, and the seven repeats
start half-way through their clip. The lyric takes priority while it is on the CRTs; the footage
runs on underneath. Before 1:00, in the coda and in the ending there is none.

Each picture fills its screen's height, its own aspect kept, the width that does not fit cut off
evenly left and right; it is sampled smoothly (no virtual-pixel grid, no quantisation, no noise) and
taken toward the CRT in two approved steps, from a clean full-colour baseline (approved first, so
that the footage reads as real video before anything is taken away):

| Step | What | Approved |
| --- | --- | --- |
| Baseline | Full colour, height-filled, smooth, at 60% of the screens' light, camera rays only | 2026-10-22, the reference |
| A, tint | The picture's own luminance carried in the screens' cyan, scaled to a luminance of one: colder, not brighter or darker | 2026-10-22 |
| B, scanlines | The screens' 48-row raster over the picture at half the lyric's depth (the lower 35% of each row to about 67%) | 2026-10-22, light (the full depth cost fine detail); steady in motion (about 4 image pixels a row at 1080, 8 at 4K) |

No further steps (fewer pixels, fewer levels): recognisability first, and the cold monochrome,
scanlines, dark glass and the PS1 room already make them old monitors. The steps are
`VIDEO_STAGES` in `presentation/screens.py` (empty gives the clean baseline back). Tried and
dropped on the way: one picture across the whole wall at 64 × 48 a screen (also at twice that),
and the same picture on every screen: all too abstract to read as video.

## The pull-out and the level's distance (approved, locked 2026-10-20)

The station level ends nowhere the camera can see. Three look-only devices, in the early-3D
language rather than realistic atmosphere:

| Device | What it is |
| --- | --- |
| Distance fog | Linear, 110 m to 700 m, into a very dark blue-grey (0.010, 0.012, 0.016) that goes to black above the horizon. Camera rays only: it lights nothing and is in no reflection. The level's structure, ground, pit ceiling and walls take it; the network's cyan emission is split out of the routing's material and added after the fog, unchanged |
| No shell | The black distance shell is invisible to the camera (its transform and colour are untouched). The camera sees the world as the fog's gradient instead; lighting still takes the world's ambient only |
| Echo network | Eight look-only tiles of the network's structure at rest (runs, junction blocks, station bodies), merged into one simplified mesh and instanced round the real network at 420 m spacing, each turned a further quarter. They carry the level's tiled surface, no emission. Black before the climax (4:00), up over 8 s, black from 4:15 |

At 4:14.37 the network continues into the dark with no wall, edge or seam; at 4:08.5 it recedes
into the horizon; 2:25 is visually unchanged. The climax's cyan inlays match the frames before the
fog (20,831 of about 20,900 pixels; brightness 108.2 against 107.9); the level key still keeps off
the same 9212 pit objects. Stills: `renders/lookdev/materials/pullout/stage4/`.

## Integration and the final profile (2026-10-21)

**Integration review.** Fourteen frames across the film (`renders/lookdev/integration/`,
`integration_contact_sheet.png`). One failure found and fixed: the echo tiles, black before the
climax, could stand as a dark skyline against the horizon; they are now invisible to every ray
while black (the same mechanism as unrevealed station machinery). The horizon band at 3:51.5 is
the real network's own far edge, visible through the longer fog, and is left as continuation.

**Tests.** Unit tests, profile parity (zero deviation), the twelve preview locks and the
lookdev lock comparison pass. The lookdev comparison now runs one reference window per process
(`tests/blender_locked.py -- --profile lookdev --only NAME`): the whole film in one lit build no
longer fits in this machine's 11.8 GB.

**The final profile carries the look.** `final` now has `look=True`, with its volumetric haze
off (it would scatter light into the locked lighting; depth is the camera-only fog) and motion
blur off (early real-time 3D had none). Prop and screen mapping read the bounding-box
("Generated") coordinates, the same on a stretched unit box and on the final profile's true-size
bevelled meshes; on the lookdev scene the change renders within 2 levels on 968 pixels at 1:17
(texel-boundary rounding). Visual confirmation on the final meshes is part of the GPU review.

**Still open:** the CRT footage (the pipeline is built; see the lyric section). Everything else is production.

## Known problems

- **Raised routing** at the peak sits on visible shadow; where a raised run meets one held down
  under a station there is a hard step.
- No atmosphere and no section accents; no network emission after 4:15 yet: see the tables above.
- The plinth event at 4:35.7 reads stronger than the head and the carriage at 4:31.5: the lamp is
  the only real light in the ending. The ceiling panels and the lamp face are the brightest things
  in the room at 4:25. Left as they are.
- At the peak a few marks render as short slivers: a mark on a held-down heavy-trunk run is cut
  where the run ends beside a raised one, and one near the junction is clipped by the source's
  7 m clearance. Both follow from existing rules; left as they are.
- Narrow (1.6 m) trunks still read as rows of marks at the peak: their width leaves an added mark
  little room to stand off the centre line. Accepted.
