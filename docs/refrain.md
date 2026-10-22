# The refrain, 2:20.0–3:00.0

The system without a subject, seen from inside.

The filtered refrain ("These land-acknowledgement scrawls / these strongman's chest medal
bars") is sung eight times here, once every two bars. The songwriter defines it as background
conditions. Nothing in this passage is cued to a repetition of it. It describes what the place
is like.

Nothing after 3:00.0 is authored. This document states what is true at 3:00.0.

The code is in `procedural_disagreement/core/refrain.py` (camera, sight, coupling, stations,
procedure, marks) and `scene/refrain.py` (drawing).

## Cues

Two new cues. The passage starts on the hinge's own boundary cue.

| Time | Music | Used for |
| --- | --- | --- |
| 2:20.0 | The reprise of 0:20.0, where the bass entered and the chamber coupled around a body. | The level couples, around no one. The camera leaves rest. |
| 2:40.0 | The bed of the first verse returns (the reprise of 0:40.0), without the verse. | The stations begin their procedure. |
| 3:00.0 | The third big entrance. | A target boundary only. |

## What a station is, at standing height

The hinge showed a station as a square block on a spur. Thirty-one of them, in the part of the
level the camera moves through, are built out. On top of each unit:

- **A platform.** A low round plinth in the middle. Nothing is ever on it.
- **A yoke.** A bar and disc riding on two posts over the platform.
- **A head.** A block on a column at one corner, with a lit cell on its face and a rotor under it.
- **A carriage.** A block on a rail along one edge.

Each station has an **empty coordinate**: the point over its platform where a shoulder would
be, 2.7 m above the unit. Stations further off remain the plain units the hinge showed.

## Conditions

Both are physical geometry, a few centimetres proud of what they lie on, so they read in the
flat preview. Both are seeded and identical in every profile. Neither forms letters, numerals,
symbols or maps.

**Scrawls** (507 short segments). Crooked lines: each stroke is a walk of seven or eight short
segments that keeps turning by up to 48° either way and bounces off the edge of its surface.
- On the ground beside the trunk the camera travels: six dark plates, four strokes on each,
  14 cm wide.
- On the working faces of about half the built-out stations: three strokes low on the face,
  10 cm wide.

**Medal bars** (171 plates). Identical plates, 76 × 20 cm, in three or four rows high on a
station's working face. Every row is squared up at the same end and no row is longer than the
one above it. About three stations in five carry them. Some faces carry both conditions, bars
above and scrawl below.

The station the hinge left lit (131) carries neither, because its face is part of the locked
2:20 image.

**Strokes moved by hand.** As seeded, three of the six ground plates could be read as pictures:
one as a star or bird (strokes converging on a point), one as a branching figure seen at the
camera's angle, one as a closed loop with two ear-like peaks. Two strokes on each (plates 0, 3
and 6) were given a different starting place and heading; nothing else about any scrawl was
changed. The table is `_UNPICTURED` in `core/refrain.py`.

**The bars are as large as they will be made.** At 360p a ranked block is about 30 × 12 px and
a single plate about 5 × 2 px: the block reads, the plates barely. At 4K a plate is about
30 × 12 px. Their final visual strength is expected to come from the final profile's material
treatment (metal, specular, emissive), not from more geometry.

## The passage

| Time | What happens |
| --- | --- |
| 2:20.0 | Exactly the hinge's last frame: one trunk, station 131, its spur, darkness. Camera at rest. |
| 2:20–2:24 | **Coupling.** Every station's rotor runs up from rest to one blade a beat over four seconds, and the cells on the heads come on. This is true of all of them at once, but only what is in sight can be seen. |
| 2:20–2:30 | The camera eases to 2 m/s along the trunk. What can be seen opens outward from it at once and then more slowly, to 55 m: a scrawled plate at its feet (half out of the dark by 2:22.0), the cross-main (2:24), the first other station (2:24–2:25). While sight is short its soft edge is no wider than the sight itself, so the nearest things come fully out first. |
| 2:30–2:40 | It rises from standing height to 5.75 m and sight reaches 85 m. It approaches station 131 and moves aside to pass between two stations. Observation only: nothing but rotors moves. |
| 2:40.0 | **The procedure begins** at station 131, the nearest. |
| 2:40–2:55 | It passes outward from station to station, six metres a beat, each starting on a beat. All 31 are running by 2:54.4. The camera quickens to 3.6 m/s and rises to 7.75 m; sight widens to 135 m. |
| 2:46–3:00 | The camera turns from the trunk toward the heavy main ahead. |
| 3:00.0 | Still travelling, still turning, every station in mid-procedure. |

**Stations in sight** (more than faintly): none at 2:20; 5 at 2:30; 24 at 2:40; 41 at 2:50;
56 at 3:00. What the camera has passed goes dark again behind it: sight is a distance.

## The procedure

One run takes three bars (7.5 s) and returns exactly to rest, so it repeats without a seam. Each
station runs it continuously from its own starting beat.

| Seconds in | Action |
| --- | --- |
| 0.0 | The head turns 86.5° to face the empty coordinate. |
| 1.25 | The carriage runs 1.6 m along its rail toward the platform's line. |
| 2.5 | The yoke comes down 0.8 m toward the platform and stops 16 cm short of shoulder height. |
| 3.75 | The head turns from the empty coordinate to the carriage. |
| 4.2 | The carriage extends 0.5 m. |
| 5.0–7.3 | Yoke up, carriage retracted and returned, head back to rest. |

Nothing arrives. Nothing is cut. Nothing is disposed of.

**Rhymes with the first half** (three):

1. The head's turn is the 86.5° the chamber's tower head made at 0:02, toward a shoulder; here toward where one would be.
2. The carriage's run, then extension when the head turns to it, is the re-indexing cross-check of 1:12–1:17.
3. The yoke coming down over the platform is the lamp docking over the body at 0:30; here it stops short and goes back up.

## State at 3:00.0

| | State | Set by |
| --- | --- | --- |
| Camera | The hinge camera. Position (49.38, 179.78, 7.50) m, 7.75 m above the level. Travelling +y at 3.6 m/s. Looking 76.6° east of the trunk's direction and 4.4° down, turning east at 5.7°/s. 50° field of view. | `refrain.camera_pose` |
| Where it is | 11.5 m short of the heavy main (y = 191.3 m), which runs east out of frame with stations along both sides. | |
| Sight | 135 m. 56 stations in sight, 30 of them built out. | `refrain.sight` |
| Stations | All 31 built-out stations running the procedure, at different phases. | `refrain.kits` |
| Coupling | On: rotors at one blade a beat, cells lit. | `refrain.coupling` |
| Conditions | Scrawls and bars as placed. | `refrain.marks` |
| Body | None anywhere on the level. | |
| Pit ceiling | Present. No waste visible. | `hinge.ceiling_present` |

After 3:00.0 the camera and the procedure hold their 3:00.0 state; only the rotors go on turning.
That is a placeholder.

## Final-render annotations (not implemented)

This is one of the main places for material and detail in the final render. The geometry here
gives locations, density and scale; it is meant to be replaced or augmented.

- **Scrawls** can become fine scratches, etching, irregular emissive traces, surface abrasion,
  displacement, layered marks, and a subtle animated material response.
- **Medal bars** can become metallic rectangular inlays, ranked emissive strips, roughness and
  specular blocks, raised plates, ordered screen regions.
- **Audio response:** not one event per repetition of the lyric. Global parameters (scrawl
  visibility, bar reflectivity, local emissive intensity, fine surface activity) breathing
  continuously with the soundtrack.
- **Sight** is the preview's stand-in for atmosphere: a lit engine should replace it with real
  extinction and local light.
