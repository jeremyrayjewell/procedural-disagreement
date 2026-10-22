# The outer frame

The film's first 35 seconds and its last 15, designed as a pair.

- **Opening, 0:00.0–0:35.0.** The system exists before the case: capacity, preparation.
- **Ending, 4:25.0–4:40.0.** The system persists after the case: residue, persistence.

Nothing between 1:52.5 and 4:25.0 is authored. The ending is a target: this document states
what must be true at 4:25.0 for it to connect.

The code is in `procedural_disagreement/core/outer.py`. Every time below is a cue in
`cues/poc_0035_0105.json`, taken from a transient measured in `analysis/audio_features.json`.

## How darkness works in the preview

The preview engine has no lamps to dim. Light is therefore a factor on each object's colour,
between 0 (unlit) and 1 (the film's ordinary look): a level for the whole room, and seven local
pools that each come on with one hit. Inside the locked film the factor is exactly 1 and colours
pass through untouched. A lit engine can drive real lamps from the same curves; that belongs to
the final-render layer and is not built.

## Opening

The first twenty seconds are a near-silent bed with one heavy low transient per bar. They fall a
little after two seconds into each bar: 2.020, 4.528, 7.024, 9.520, 12.028, none at 14.5, then
17.032 and 19.528. These are the loudest events before the bass, and each gets one
acknowledgement. Sharper but much quieter transients between them are left alone.

| Time | Transient | What happens |
| --- | --- | --- |
| 0:00.0–0:02.0 | | Black. |
| 0:02.020 | Low hit 1 | **Tower head.** The head of the tower on the body's right is lit, alone, and turns 86.5° from where it was parked to face a place that is still dark. |
| 0:04.528 | Low hit 2 | **Carriage.** The cabinet on the right wall is lit and runs 0.6 m along the wall rail into its station. |
| 0:07.024 | Low hit 3 | **Tray.** The tray beside the plinth is lit and slides 0.8 m into place. |
| 0:09.520 | Low hit 4 | **Rear panel.** One panel of the rear wall is lit and slides 0.5 m into its place in the wall. |
| 0:12.028 | Low hit 5 | **Plinth and legs.** Light reaches the plinth and what stands on it. Nothing moves. |
| 0:14.5 | (no transient) | Nothing. |
| 0:17.032 | Low hit 6 | **Shoulders and torso.** The place the tower head has faced since 0:02 has a body in it. Nothing moves. |
| 0:19.528 | Low hit 7 | The conduit ends, standing 24° open, start to swing in toward the shoulders. |
| 0:20.004 | **Bass entry** | **Coupled.** The conduit ends close on the shoulders on the hit. Pulses begin to leave the body, both rotors run up evenly over four seconds, the cells come on, and the whole room becomes dimly visible as one space. |
| 0:26.250 | Heaviest low hit of the phrase | The tower head turns from the body to its working heading and lowers 0.25 m onto its seat. |
| 0:30.000 | Strong hit | **Ready.** The overhead lamp comes down 0.4 m and docks on the risers above the body, and the room comes up to full light over 1.5 s. |
| 0:31.5–0:35.0 | | Nothing new. Everything is in the state the locked film starts in. |

**Body visibility.** Unlit until 0:12.0. Plinth and legs from 0:12.0. Shoulders, torso and head
from 0:17.0. The whole figure in a dim room from 0:20, in full light from 0:31.5. It never moves
and nothing is done to it; the two reveals of the body are the only hits with no mechanical
action.

**Camera.** Still for the first six seconds, in the outer frame (below). Then one move, back
down the room and onto the line of the approach, arriving at 0:35.0 with the approach's own
position, aim, lens and velocity.

**The 0:35.0 boundary.** For 0:35.0 and later the code path is the locked film's own, so the
first locked frame is exactly what it was; tests assert equality, and all four lock references
pass. Every stroke of the opening has been at rest since 0:31.5. The camera's speed just before
the boundary is 0.14214 m/s and just after is 0.14214 m/s (they differ by 0.000004 m/s); its
rotation changes by 0.0028° per frame on both sides.

## Ending

The coda's transients come quickly at first and then thin out. Three are used, further and
further apart; the level falls 40 dB between 4:36.0 and 4:36.5 and the track is silent to 4:40.0.

| Time | Transient | What happens |
| --- | --- | --- |
| 4:25.0 | | The required state (below). Dim, still, nobody on the plinth. |
| 4:27.006 | The hardest transient in the track | **Tower head.** It is lit and turns 52.4° from the carriage it was last checked against to face the empty coordinate. |
| 4:30.710 | 3.7 s later | **Carriage.** It is lit, runs to the body's line again and extends, as it did at 1:15, against nothing. It stays extended. |
| 4:35.714 | 5.0 s later, the last strong transient | **Lamp.** It comes down 0.2 m and docks on the risers, over the empty plinth. Plinth and lamp are lit. The last motion in the film ends at 4:36.21. |
| 4:36.3–4:40.0 | Silence | Nothing moves and nothing changes. The image holds; it does not fade. |

**The empty coordinate** is the shoulder the arm was removed from: `layout.arm_origin(1)`, at
(0.53, 0.00, 3.22) m. It is the point the tower head faced at 0:02, when there was about to be a
shoulder there, and again at 1:10, when it re-indexed the amputated body. Nothing is drawn at it.

**Relationships that only make sense if someone were there** (four):

1. The tower head faces the empty coordinate.
2. The carriage is run to the body's line and extended.
3. The lamp is docked on two risers that hang from it and end in mid-air at shoulder height.
4. The conduit ends on both sides still point at where the shoulders were. (Static: they do not move in the ending.)

**Final camera state.** Position (−2.2, −10.5, 2.5) m, aimed at (1.2, 0.5, 3.0) m, 36° vertical
field of view. It does not move at any time in the ending.

## Required state at 4:25.0

Whatever is authored for 4:15–4:25 has to arrive here. Each line names where it is set.

| | State at 4:25.0 | Set by |
| --- | --- | --- |
| Body | Absent: torso, head, arms, pelvis and legs gone. Risers and conduits remain. | `outer.subject_presence` |
| Translucent realities, system branch | Absent. | `outer.alternates_presence` |
| Coupling | Uncoupled: no pulses in any conduit, rotors standing, cells dark. | `outer.coupling`, `outer.clock` |
| Light | Room at 0.26; no pool lit. | `outer.room_light`, `outer.zone_levels` |
| Tower head (right) | As accepted at 1:20: level, 0.42 m above its seat, turned 17.9° toward the carriage. | `choreography.reindex_head` |
| Carriage | As accepted at 1:20: 0.2 m along the wall, 0.12 m extended. | `choreography.reindex_carriage` |
| Lamp | Undocked, 0.2 m above the risers. | `outer.lamp_height` |
| Conduit ends | Closed, pointing at the shoulders' positions. | `outer.conduit_open` |
| Tray and removed arms | Gone: below the floor since 1:36, aperture closed. | (the locked film) |
| Rear panel, recruited rib | As the locked film left them. | (the locked film) |
| Camera | The upper camera, at rest in the outer frame. | `choreography.camera_pose` |

Until 4:15–4:25 exists, each of these is a step at 4:25.0. The frames before it show whatever
the unauthored interval gives and are a placeholder.

## Rhymes

| | Opening | Ending |
| --- | --- | --- |
| **Frame** | The first image is seen from the outer frame: plinth under its lamp on the left, tower and carriage to the right. A body is revealed in it. | The whole ending is seen from exactly that position, aim and lens. The same place is empty. |
| **Tower head** | At 0:02 it turns to face the shoulder, before the shoulder can be seen. | At 4:27 it turns to exactly the same heading (−34.5°). Nothing is there. |
| **Carriage** | At 0:04.5 it runs along the wall rail into its station. | At 4:30.7 it runs along the same rail to the body's line and extends. |
| **Lamp** | At 0:30 it docks on the risers over the body: READY. | At 4:35.7 it docks on the same risers over the empty plinth: the last motion. |
| **Hit and response** | A low transient lights one more component and it moves once. Seven in twenty seconds. | A transient lights one component and it moves once. Three in eleven seconds, further apart each time. |
| **Coupling** | Uncoupled until the bass enters at 0:20. | Uncoupled again. |

The tower head makes the same turn three times: toward a body about to be revealed (0:02),
toward the amputated shoulder (1:10), toward nothing (4:27).

## Final-render annotations (not implemented)

- **0:00–0:20:** the first, minimal appearance of soundtrack-responsive rendering. Possibilities:
  one rear panel's emissive activation, a small specular change, a sparse secondary light, subtle
  atmospheric visibility. One or a few responses only; the opening is not a visualiser.
- **4:25–4:37:** the same rendering grammar returns, diminished.
- **4:37–4:40:** no audio-reactive change of any kind during the silence.
- The high-power version can use real darkness, indirect light, specular edges, emissive
  surfaces and volumetric depth in place of the colour factor described above. The structural
  preview must work without them, and does.
