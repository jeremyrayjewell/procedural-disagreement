# The field, 4:00.0–4:15.0

The mechanical climax. At 4:00 twelve stations and a block pass function round the lane's end,
one to the next. From 4:00 that stops being a route and becomes the network: the whole level
works as a prosthesis for something that is still not there.

**Locked.** Nothing after 4:15.0 is authored. This document states what is true at 4:15.0.

The code is in `procedural_disagreement/core/climax.py`. No object is added anywhere.

## What the music does

Measured in `analysis/audio_features.json`. The level is steady, about +11 to +12.6 dB, from
4:00 to 4:14.5; there is no sectional change inside the passage. What it has is accents.

| Time | Measured | Used for |
| --- | --- | --- |
| 4:02.5 | The loudest bar of the passage begins; a heavy low hit at 4:02.86. | The fine runs begin to pair. |
| 4:05.0 | A strong onset on the bar line. | Nothing of its own: the spread is passing the tenth station. |
| 4:06.22 | The only harmonic change inside the passage; at 4:06.93 the heaviest low hit. | **Coupling** (4:06.25): the level's own structure joins. |
| 4:08.44 | The strongest onset. | Nothing of its own: the heavy main is rising along its length. |
| 4:11.30 | A heavy low hit opens the last run of hits (4:11.3, 4:11.9, 4:13.8, 4:14.4). | **Saturation** (4:11.25): everything, at once. |
| 4:14.43 | The last heavy low hit. | **Peak** (4:14.375): every large stroke arrives. |
| 4:14.9 | The music gives way: about 20 dB down between 4:14.5 and 4:15.3. | Left unanswered, for what follows. |

Cues: `climax_lines` 4:02.5, `climax_coupling` 4:06.25, `climax_saturation` 4:11.25,
`climax_peak` 4:14.375, `climax_end` 4:15.0. The three stages are therefore 6.25 s, 5 s and
3.75 s long, not three equal parts: that is where the music puts them.

## The idea

One number organises everything: how far a thing stands from the lane.

- A station takes a part when the spread reaches it. The spread leaves the lane at 4:00 and
  covers 10 m a beat (16 m/s).
- From then on the station works on that same clock, so that what a nearer station finishes a
  further one begins.
- The route's own twelve stations, which were recruited one at a time while the camera
  watched, slip onto that clock between 4:03.75 and 4:11.25. None runs backward to get there.
- From 4:11.25 a station's place in its turn depends only on its distance from the lane. That
  is what makes it one machine.

The lane is the centre of all of it, and nothing happens there.

## Three scales

| Scale | What | Stroke | Time a stroke takes |
| --- | --- | --- | --- |
| Station | Donor, carrier, receiver: the route's verbs, unchanged | 1.2 m reach, 2.4 m run, 1.8 m drop | 1.4 s |
| Group | A plain block indexing along its trunk; a column of holding cells shearing; fine runs pairing | 2.0 m; 2.0 m each way (4.0 m between neighbouring columns); 1.0 m each way | 1.4 s; 2.5 s; 2.5 s |
| Network | The heavy main and heavy trunk rising; every trunk and main within 150 m rising | 2.0 m then 1.0 m more; 1.6 m | 2.5 s then 3.1 s; 1.25 s each, 3.1 s for the whole field |

## Populations

All forty stations that have machinery take part. The twelve on the route keep their parts.
Each of the other twenty-eight gets its part from where it stands on the grid, so that
neighbours differ, and its moment from its distance from the lane.

| By | Donors | Carriers | Receivers | Relays (plain blocks) |
| --- | --- | --- | --- | --- |
| 4:00.0 | 5 | 3 | 4 | 0 (and the route's block, 224) |
| 4:02.5 | 6 | 5 | 6 | 1 |
| 4:05.0 | 11 | 8 | 8 | 7 |
| 4:07.5 | 15 | 12 | 11 | 14 |
| 4:10.0 | 17 | 12 | 11 | 21 |

A new donor turns its head to the nearest station further from the lane than itself: function
is passed outward. A relay is a plain block that slides 2.0 m along its trunk and back, as
station 224 did; 21 of the 218 plain blocks do, chosen by a fixed hash from those that have no
bays, touch nothing in the stroke, and stay at least 4 m from the lane.

## Large structures

| Structure | Pieces | Movement | When |
| --- | --- | --- | --- |
| Fine runs | 172 | Every other run moves 1.0 m sideways toward its neighbour: they pair. At saturation they cross, 2.0 m, to pair with the neighbour on the other side. | From 4:02.5, outward over 2.5 s; crossing 4:11.25–4:14.375 |
| Holding cells | 85 | Every other column shears 2.0 m along itself: a square grid becomes a bond. At saturation they shear through, 4.0 m, to the opposite bond. | From 4:06.25, outward over three beats; through 4:11.25–4:14.375 |
| Heavy main and heavy trunk | 13 runs and 6 junction blocks | Rise 2.0 m, run after run outward, a beat apart; 1.0 m more at saturation. | From 4:06.25; the last run starts at 4:11.25 |
| Other trunks and mains | 78 runs and 60 junction blocks | Rise 1.6 m, outward from the lane. | 4:11.25–4:14.375 |

Nothing goes down. Every large stroke has arrived by 4:14.375 and stays.

**A run that passes through a station with machinery stays down** (18 trunk runs and 10 main
runs, among them five runs of the heavy trunk and five of the heavy main). Risen, it would
stand in the place the station keeps empty. So the heavy trunk and heavy main rise in lengths,
not as one line.

## Across the lane

The lane cut two trunks and the heavy main. Nothing replaces what was cut. But the two sides
of each cut respond at exactly the same moment, as if they were still one piece: the runs
either side of the heavy main's gap rise together at 4:06.875, and the runs either side of each
cut trunk rise together at 4:11.25 (for one of the two cut trunks; the other has a station on
one side of its cut, and that side stays down). That is the only relation across the lane, and it has no
geometry.

## Camera

No cut. It leaves 4:00 with the position, velocity and turning it arrived with. It bears left
and climbs, backing away from the lane it has just gone round, while its gaze goes on turning
right: over the stations to the west while the spread crosses them, then round to the lane as
the structure joins.

| Time | Position (m) | Height above the level | Looking (clockwise from +y) | Pitch down | Sight |
| --- | --- | --- | --- | --- | --- |
| 4:00.0 | (133.0, 133.0) | 12.0 m | 304° | 11.5° | 135 m |
| 4:02.5 | (126.5, 135.6) | 13.9 m | 319.5° | 12.7° | 141 m |
| 4:05.0 | (120.6, 135.6) | 19.0 m | 358.5° | 16.0° | 168 m |
| 4:07.5 | (114.9, 131.1) | 26.4 m | 24° | 20.9° | 207 m |
| 4:10.0 | (109.4, 123.4) | 35.0 m | 31.4° | 26.0° | 234 m |
| 4:12.5 | (103.8, 114.6) | 43.4 m | 33.1° | 29.8° | 240 m |
| 4:15.0 | (98.9, 105.6) | 50.0 m | 35.7° | 32.0° | 240 m |

64 m of travel; never above 5.5 m/s; the gaze never turns faster than 16.6° a second (at 4:04.05), is under 4° a second from 4:08.5 and under 2° a second through saturation, and neither its speed nor its acceleration steps; it only
climbs.

## The absence stays

Tests assert, through the passage:

- all 21 pieces in the lane are still below the ground, and nothing here moves them;
- nothing that moves comes inside the lane; whatever moves sideways stays at least 2.0 m from
  it, and a relaying block at least 4.0 m;
- the trunks and mains beside it only rise, so they cannot come nearer than they stand;
- no moving piece has parts on both sides of the lane;
- no station's carriage or head assembly comes within 0.5 m of the lane at any frame;
- the eight overhead frames are still turned 12° and the fifteen stations facing the lane are
  still held.

## State at 4:15.0

| | State | Set by |
| --- | --- | --- |
| Camera | Position (98.90, 105.60, 49.75) m. Velocity (−1.6, −3.2, 2.0) m/s. Looking 35.7° clockwise from +y, turning right at 3°/s; 32.0° down, tipping at 0.6°/s; 50° field of view. The middle of the lane is at the centre of the picture and its whole length is in it. | `climax.camera_pose` |
| Sight | 240 m | `refrain.sight` |
| Stations | All forty taking part, on one clock set by distance from the lane. | `climax.turn` |
| Relays | 21 plain blocks, on the same clock. | `climax.relay_offset` |
| Fine runs | 1.0 m across, paired with the other neighbour. | `climax.piece_offset` |
| Holding cells | 2.0 m across, in the opposite bond. | |
| Heavy main, heavy trunk | 3.0 m up, except where they pass through a station. | |
| Other trunks and mains within 150 m | 1.6 m up, except where they pass through a station. | |
| Station 224, the three trunk runs at the corner | As at 4:00.0. | `prosthesis.piece_offset` |
| The lane | Empty. All 21 pieces below the ground. Nothing has entered, crossed or marked it. | `network.piece_offset` |
| Body, waste, any marker or drawn connection | None. | |

From 4:15.0 to 4:25.0 the camera and the large structures hold their 4:15.0 state and the
stations go on running. That is a placeholder. From 4:25.0 the film's ending stands as it was
built, and nothing in this passage applies to it.

## Final-render annotations (not implemented)

- Emissive propagation outward from the lane's edge on the same clock as the spread, carried
  only by surviving structure.
- Reflected light from stations in motion onto the raised trunks and mains.
- A specular sweep along the heavy main and heavy trunk as each run rises.
- Heat or energy building in the routing through saturation, greatest at the peak.
- Material distinction between the three scales: station, group, network.
- Dense signal travel along trunks and fine runs, stopping at every cut end.
- Raised runs will need a visible means of support, or shadow alone will read as floating.

No light, signal or response may enter or cross the lane.
