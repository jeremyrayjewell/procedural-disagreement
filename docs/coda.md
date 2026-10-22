# The coda, 4:15.0–4:25.0

The withdrawal. 4:00–4:15 was the system at its largest. Straight after it the film cuts back
to the room, and nobody is there. What the room has instead is a record, in the two conditions
the station level has carried in the background since 2:20: scrawls and ranked bars. The
refrain is sung twice: the first time sets them out, the second takes them away.

**Locked.**

The code is in `procedural_disagreement/core/coda.py` (the marks) and
`procedural_disagreement/core/outer.py` (the room). The only objects added are the marks
themselves: 122 small boxes that have no size outside the coda.

## The cut

One hard cut, on frame 7651 (4:15.033), the first frame after the locked frame at 4:15.0. From
the network at its widest to the room, seen from the outer frame: the position, aim and lens
of the opening's first image and of the whole ending. The camera does not move again in the
film.

The body is not removed on screen. It was on the plinth when the film left this room at 1:36;
on the other side of the cut it is not. No translucent reality survives the cut either.

## The room at 4:15.033

| | State |
| --- | --- |
| Body, translucent realities, system branch | Absent. |
| Tray and removed arms | Gone, below the floor since 1:36. |
| Tower head, carriage, rear panel, recruited rib | As the locked film left them at 1:20: already where the ending needs them. They do not move. |
| Conduit ends | Closed, pointing at where the shoulders were. They do not move. |
| Lamp | Docked on the risers, as it has been since 0:30. |
| Circulation | Half of what it was: pulses still run in the conduits, the rotors still turn, the cells are lit. Nobody is being served. |
| Light | Room at 0.55; no pool lit. |

## Lyric and timing

| Time | Sung | What happens |
| --- | --- | --- |
| 4:15.03 | (cut) | The room. Scrawls are already faintly on its surfaces. |
| 4:15.1–4:16.5 | "These land-acknowledgement" | The scrawls come up, trace by trace, piece after piece. |
| 4:16.65 | "scrawls" | All of them are there. |
| 4:17.5 | "These strongman's chest medal" | Ranked bars begin to appear, on other panels, row by row. The scrawls do not change. |
| 4:19.1 | "bars" | All of them are there. Both conditions stand side by side. |
| 4:20.0 | the couplet again | The scrawls stay whole. The circulation begins to die and the room begins to go down. |
| 4:21.55–4:22.2 | "scrawls" (sung 4:21.65–4:22.10) | The scrawls go inside the word that names them: branches first, then each trace from its ends inward. 98% is still there at 4:21.65, 63% at 4:21.85, under 1% at 4:22.10, none at 4:22.2. |
| 4:22.5 | "These strongman's chest medal" | The bars begin to go, panel by panel, longest row first, each bar drawing back into its squared end. The lamp lets go of the risers. |
| 4:24.1–4:24.6 | "bars" | Only the last group is left. It goes row by row inside the word; the last bar ends with it. |
| 4:24.6–4:25.0 | | Nothing explicit is left. Everything stands exactly as the ending finds it. |

Cues: `coda_scrawls` 4:16.65, `coda_order` 4:17.5, `coda_bars` 4:19.1, `coda_again` 4:20.0,
`coda_unscrawled` 4:21.65, `coda_withdraw` 4:22.5, `coda_last` 4:24.1, `coda_silent` 4:24.6.

## Scrawls

- **Rear wall:** three long traces, each a crooked walk of short straight pieces that runs on
  across several panels and is broken wherever it meets a seam: along the bottom row (three
  panels), along the middle row (three panels), and up the right-hand column (two panels).
  Short branches come off them, alternately to either side.
- **Floor:** five wavering runs lying flat either side of the plinth.
- 97 pieces (56 on the wall, 41 on the floor), 42.6 m in all. 30.7 m of it is already faintly
  there on the first frame; a mark's tone rises out of the tone of the surface it is on.

A trace cannot come within 0.45 m of any earlier part of itself, so it cannot close a loop or
cross: nothing box-shaped, nothing the size or build of a character.

## Bars

Plain rectangles, 0.46 × 0.24 m, in rows that are squared up at the left and get shorter going
down. Three rear panels carry them:

| Panel (row, column) | Rows | Comes | Goes |
| --- | --- | --- | --- |
| Top row, second from left | 4, 3, 1 | 4:17.5 | 4:22.5–4:23.0 |
| Bottom row, right | 4, 2, 1 | 4:17.9 | 4:23.1–4:23.6 |
| Middle row, second from right | 4, 3, 2, 1 | 4:18.4 | 4:24.0–4:24.6 |

25 bars, 11.5 m in all. The last panel is the one the outer frame sees directly behind the
place the chest was, between the two risers.

## What else changes

Three things, each once and each in one direction:

1. **Circulation dies**, 4:20.0–4:23.0: pulses fade, rotors run down and stop, cells go dark.
2. **The room goes down**, 4:20.0–4:24.6: from 0.55 to the ending's 0.26.
3. **The lamp lets go of the risers**, 4:22.5–4:23.9: it rises 0.2 m, to where the ending
   finds it. At 4:35.7 it docks again, over nothing.

Nothing else in the room moves.

## The 4:25.0 boundary

From 4:24.6 every value the ending depends on is exactly its value at 4:25.0: camera, absence,
coupling 0, clock 265.0, lamp 0.2 m, room 0.26, no pool lit, tower head, carriage, conduits,
tray. No mark has any size. Tests assert it, and the ending's lock reference is unchanged.

## Final-render annotations (not implemented)

- Scrawls as shallow scratches and surface relief, not applied lines.
- A controlled specular or emissive response in place of flat bright marks.
- Small variations in roughness along a trace.
- Bars told apart by material, not by more geometry.
- Residual network light dying through the room.
- Subtle atmospheric separation between the plinth and the rear wall.
- The last bars keeping local light a fraction longer than their surroundings.
