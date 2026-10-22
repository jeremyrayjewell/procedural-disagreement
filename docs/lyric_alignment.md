# Lyric alignment

Where every sung word in the track falls, and what it means for the picture.
A planning document: no cue time and nothing in the scene was changed to produce it.

## The lyric

Confirmed by the songwriter. This is the whole of what is sung.

| | Text | Heard at |
| --- | --- | --- |
| **A**, verse 1 | Gave up the offensive trunk, / canonized it in the stump | 0:40.0, 0:50.0 |
| **B**, verse 2 | I'd like if it'd never been, / to know what landfill it is in | 1:30.0, 1:40.0 |
| **C**, refrain | These land-acknowledgement scrawls / these strongman's chest medal bars | Filtered: 1:20.0, and 2:20.0–2:55.0 every 5 s (eight times). Full voice: 4:15.0, 4:20.0 |

## Findings in brief

- **Three couplets, about 25 s of distinct singing, placed fifteen times.** Each is a recording dropped onto the bar grid and repeated as a literal copy.
- **The "thin voice" is the refrain, filtered.** The quiet, bright voice at 1:20 and all through 2:20–3:00 says the two lines that are sung in full voice at 4:15. The song says its last line nine times before letting it be heard plainly.
- **Verse 1 is never sung again.** Over the reprise of its music the second half has only the refrain, looped.
- **The song names the film's own objects.** *Trunk* and *stump* are in the first couplet; *landfill* in the second. The refrain names two kinds of official mark: scrawls and medals.
- **More was written than is in the song.** A raw take runs through a longer lyric; the extra lines are listed at the end as context.

## How the timing was found

1. **Each region's source was found by signal matching**, which does not depend on recognising words. Every 2.5 s bar of the isolated vocal `onlyvox1.wav` (itself sample-aligned with the master) was matched against the raw takes in the song's folder. The matches are exact in time (offset 0.0000 s), with correlations of 0.71–0.92:

   | Track | Source | How it is used |
   | --- | --- | --- |
   | 0:40.0–0:50.0 and 0:50.0–1:00.0 | `voxampunew.wav`, 0–10 s | The same 10 s, twice |
   | 1:20.0–1:24.6 | `intervox1.wav` (5 s) | Once |
   | 1:30.0–1:40.0 and 1:40.0–1:50.0 | `voxampusecondverse.wav`, 0–10 s | The same 10 s, twice |
   | 2:20.0–2:59.6 | `intervox1.wav` | The same 5 s, eight times, on every second bar line |
   | 4:15.0–4:24.6 | Not any of these files | A 5 s unit, twice; the refrain's words and rhythm, in full voice |

2. **Words were timed acoustically on the sources**: syllable nuclei from vowel-band energy, consonant bursts from 4–11 kHz energy, pauses from level. Because the sources sit on the track with zero offset, source time plus the region's start is track time.

Automatic speech recognition was used only as one witness among several, and it was wrong about each couplet in some way: it heard "scrolls" for "scrawls", "stock" for "stump", "truck" for "trunk", and "how I wish" for "I'd like if". The words below are the songwriter's; only the timing is measured.

Timing uncertainty, unless a row says otherwise: phrase starts and ends ±0.03 s; stressed syllables and consonant bursts ±0.05 s; other word onsets ±0.15 s.

## Region by region

### 0:40.0–1:00.0: verse 1 (couplet A, twice)

Full voice, moderate level, no pause anywhere in the 10 s. Add 10.0 s to every time for the second statement.

| Word | Time | Evidence |
| --- | --- | --- |
| Gave | 0:40.1 | First nucleus; consonant burst at 0:40.01 |
| up | 0:40.4 | |
| the | 0:40.65 | |
| of– | 0:41.1 | |
| –fen– | 0:41.3 – 0:42.0 | Held |
| –sive | 0:42.5 | **Stressed**: the strongest syllable of the line |
| **trunk** | 0:43.0 – 0:44.6 | "tr" burst at 0:43.02–0:43.15; vowel from 0:43.2. **Stressed**, then held and carried down through two or three weaker pulses to the end of the line |
| Can– | 0:45.0 | Burst at 0:44.97–0:45.05; vowel 0:45.2 |
| –on– | 0:45.4 | |
| –ized | 0:45.8 – 0:46.8 | **Stressed**, pitch rises; final "z" at 0:46.70–0:46.78 |
| it | 0:46.9 | ±0.15 s |
| in | 0:47.1 | ±0.15 s |
| the | 0:47.3 – 0:48.5 | Held, with a swell at 0:47.7 that is the loudest moment of the couplet: the line leans on the word before "stump" |
| **stump** | 0:48.6 – 0:49.4 | "st" burst at 0:48.57–0:48.75; vowel 0:48.9. **Stressed.** The voice runs on to 0:50.2 and into the repeat |

- **Pauses:** none.
- **Repeats:** the whole couplet, verbatim, at 0:50.0. So "trunk" is at 0:43.0 and 0:53.0; "stump" at 0:48.6 and 0:58.6.
- **Images and concepts:**
  - *Gave up*: surrender, relinquishing, handing over.
  - *The offensive trunk*: the trunk offends one's sensibilities (the songwriter's reading). "Offensive" is distaste, not a campaign: the body itself is the thing found objectionable, and it is given up.
  - *Canonized*: made official, made sacred, entered in a canon; a relic.
  - *In the stump*: what remains after an amputation, named outright; also the stump a speech is given from.

### 1:20.0–1:24.6: the refrain, filtered (couplet C, once)

Quiet (about 15 dB below verse 2), with almost no energy below 1 kHz: a voice through a small speaker or a telephone.

| Word | Time | Evidence |
| --- | --- | --- |
| These | 1:20.1 | **Stressed** |
| land– | 1:20.4 | **Stressed** |
| –ac–know–ledge–ment | 1:20.65 – 1:21.5 | Four quick syllables; bursts at 1:20.65 and 1:20.93 |
| **scrawls** | 1:21.65 – 1:22.1 | **Stressed**, the highest pitch of the line |
| *(pause)* | **1:22.1 – 1:22.5** | The only real pause in the lyric: 0.4 s, just before the bar line |
| These | 1:22.55 | |
| strong– | 1:22.85 | "str" burst at 1:22.80–1:22.91 |
| –man's | 1:23.15 | |
| chest | 1:23.5 | **Stressed**; burst at 1:23.42–1:23.50 |
| medal | 1:23.8 – 1:23.95 | |
| **bars** | 1:24.1 – 1:24.6 | **Stressed**; final "s" at 1:24.07–1:24.19 |

- **Images and concepts:**
  - *Land acknowledgement*: a formal statement recognising that something was taken, which changes nothing about who holds it.
  - *Scrawls*: writing that is hasty, careless, barely legible. The acknowledgement is not even a document; it is a scribble.
  - *Strongman's chest medal bars*: the rows of ribbon on a uniform. Decoration as a record of what was done, worn on the trunk.
  - Together: two kinds of official mark, one made on paper and one worn on a body.

### 1:30.0–1:49.4: verse 2 (couplet B, twice)

Full voice, the loudest singing in the track, no pause in the 10 s. Add 10.0 s for the second statement.

| Word | Time | Evidence |
| --- | --- | --- |
| I'd | 1:30.1 | |
| like | 1:30.65 | |
| if | 1:30.95 | Weak; the "f" shows as a small burst at about 1:30.96 |
| it'd | 1:31.2 – 1:31.9 | Consonant release at 1:31.76–1:31.89 |
| never | 1:32.0 – 1:32.9 | **Stressed** on the first syllable |
| been | 1:33.25 – 1:34.5 | Held |
| to | 1:34.85 | Line 1 runs into line 2 with only a dip in level at 1:34.6 |
| know | 1:35.0 | |
| what | 1:35.45 | |
| **land–** | **1:36.15** | **Stressed.** The heaviest low hit of the phrase is at 1:36.25 |
| **–fill** | **1:36.9 – 1:38.0** | **Stressed**, the strongest and longest syllable of the couplet |
| it | 1:38.15 | |
| is | 1:38.4 – 1:38.8 | ±0.15 s |
| in | 1:38.85 – 1:39.4 | The repeat begins at 1:40.0 |

- **Repeats:** the whole couplet, verbatim, at 1:40.0. "Landfill" is sung twice: 1:36.15 and **1:46.15**.
- **Images and concepts:** a mild, almost bureaucratic regret ("I'd like if", not a cry); the wish that the thing had never existed; unwanted knowledge; "it" having a location; the landfill.
- **Note:** "land" is in both the refrain and this verse: *land*-acknowledgement, *land*fill. One acknowledges it, the other fills it.

### 2:20.0–2:59.6: the refrain, filtered, eight times

The same 5 s recording as 1:20, starting on every second bar line. Add 60 s, then 5 s per repeat, to the 1:20 table: "scrawls" at 2:21.65, 2:26.65, …, 2:56.65; "bars" at 2:24.1, 2:29.1, …, 2:59.1; the 0.4 s pause before each of 2:22.5, 2:27.5, …, 2:57.5.

**Compared with the first half**

| | First half | Second half |
| --- | --- | --- |
| Music | 0:20–0:40 build, 0:40–1:00 verse bed | The same music, 2:20–3:00 |
| Words over the build | None | Refrain C, four times |
| Words over the verse bed | Verse 1 (couplet A), twice | Refrain C, four more times |
| Voice | Full | Filtered, quiet |

- **Repetition:** the 1:20 interjection, one bar pair long, becomes the entire content of 40 seconds.
- **Transformation:** verse 1 is not sung again. Where the first half had a first-person account of an act ("gave up", "canonized"), the second half has only the list of marks, on a loop.
- **Answer:** verse 1 says what was done to the body; the refrain says what the body got for it: a scrawl and a medal.
- **Contradiction:** an acknowledgement is supposed to be said once and meant. Said eight times through a filter it stops being a statement at all. "Scrawls" already says as much.
- **Register:** the filtered refrain is meant as background noise, as conditions (the songwriter's description). It is not a speaker addressing anyone and not an event: it is part of what the room is like while things happen in it. The acknowledgement and the medals are ambient.

### 4:15.0–4:24.6: the refrain, in full voice, twice

A 5 s unit at 4:15.0 and again at 4:20.0, over the dropout. Full voice (energy centred near 330 Hz, like the verses) but quiet: about 13 dB below verse 2.

Syllable timing matches the filtered refrain within 0.02–0.06 s, so add 175.0 s to the 1:20 table ("scrawls" at 4:16.65 and 4:21.65; "bars" at 4:19.1 and 4:24.1). It is either the same performance without the filter or a second take sung to the same rhythm.

- **Repetition:** the tenth and eleventh statements of the same two lines.
- **Transformation:** the filter is gone and the music is gone. For the first time the words can simply be heard.
- **Answer:** it answers the 75 s of voiceless music before it. After the system has run at full strength with nobody singing, what is left is the scrawl and the medals.
- **Register:** the verses' voice. What has been background conditions since 1:20 is, for the first time, in the foreground and sung by someone. That contrast is measured (filter off, music gone); what it means is not something the songwriter has stated.

## Recorded but not in the track

`voxampu.wav` performs a longer lyric in one pass. The songwriter confirms that the lines below are deliberately absent from the song. A matched-filter search of the whole master and of the isolated vocal finds no trace of the lines below (they score 9–20, against 32–159 for lines that are present). The wording here is from speech recognition on that take and has not been checked by the songwriter; it is context, not timing material, and nothing in the film should be built on it.

| Order in the take | Text (unconfirmed) | In the track? |
| --- | --- | --- |
| 1–2 | Couplet A | Yes |
| 3–4 | Two lines, roughly "…that I have got / some … above the old slot" | No |
| 5–6 | Couplet C | Yes |
| 7–8 | **There never was a presence / quite like this absence** | No |
| 9–10 | **There never was compulsion / quite like this prohibition** | No |
| 11–12 | Two lines ending "…email sign-off" and "…-off" (very uncertain) | No |
| 13–14 | Couplet B | Yes |
| 15–17 | **But for now it seems worthy / of minor controversy / [and / in] amputation** | No |

- "There never was a presence quite like this absence" is very nearly a description of the phantom-load and absent-attractor passages, which were designed without knowing it.
- The title exists as a lyric and is not sung.

## Existing cues against the lyric, 0:35–1:30

No cue was changed. Every relationship here is accidental: the cues were chosen from the instrumental analysis before any vocal file was found.

| Cue | Time | What is being sung | Relationship |
| --- | --- | --- | --- |
| Plane A appears | 0:40.0 | "Gave" (the first word of the song) | **Meaningful.** The intervention begins on "gave up the offensive trunk": the trunk offends, and the plane arrives as it is given up. |
| Plane B appears; plane A locks on | 0:42.5 | "–sive", then "trunk" at 0:43.0 | **Meaningful.** The second plane arrives on the stressed end of "offensive", and half a second later the song names the body. Both planes are at the shoulder, where the limb meets the trunk. |
| Disagreement begins; plane B in place | 0:45.0 | "Can–" (start of line 2) | Neutral: a line boundary. |
| Alternate fully split | 0:47.5 | "the", held and swelling, into "stump" at 0:48.6 | **Meaningful, and unmarked.** The first "stump" is sung while the alternate reality, the one that will be left with a stump, has just finished separating. No stump exists yet: the word arrives before the thing. Nothing happens on it. |
| **Primary cut** | 0:50.0 | "Gave" (the repeat) | **Especially meaningful.** The limb is removed on "gave up". And this is the cut at the shoulder, flush with the trunk, which is named three seconds later at 0:53.0. |
| Primary tower fails | 0:52.5 | "–sive", then "trunk" at 0:53.0 | Meaningful: the consequence lands on "offensive". |
| **Alternate cut** | 0:55.0 | "Can–[onized]" | **Especially meaningful.** Of the two cuts, this is the one that leaves a stump, and it happens on "canonized it in the stump". The stump recoils at 0:55.0–0:55.5; the word "stump" follows at 0:58.6. |
| Primary arm at rest on the tray | 0:56.25 | The end of "canonized" (0:55.8–0:56.8) | **Especially meaningful.** The removed arm is laid out on the tray as the song says "canonized": set apart, kept, a relic. |
| Alternate tower fails; plane A withdraws | 0:57.5 | "the" swelling (0:57.7), then "stump" at 0:58.6 | **A gap.** The second "stump" is sung with the stump on screen (translucent, in the alternate), and no event marks the word. The nearest event is 1.1 s earlier and concerns the tower. |
| System branches | 1:00.0 | Nothing (the voice has just stopped) | No relationship. |
| Phantom load | 1:06.25 | Nothing | No relationship in the track, though it is the stump that moves here, eight seconds after the song last named it. (The unsung line "there never was a presence quite like this absence" would have described it.) |
| Re-indexing (four actions) | 1:10.0, 1:12.5, 1:15.0, 1:17.5 | Nothing | No relationship: an instrumental phrase. It ends at rest 0.7 s before the refrain begins. |
| **Absent attractor** | 1:20.0 | "These land-acknowledgement scrawls" (filtered), 1:20.1–1:22.1 | **Especially meaningful.** The room begins to orient itself toward a place where something used to be as a land acknowledgement is heard in the background. The refrain is conditions, not an event, and the absent attractor is likewise a slow change in the room, not an action. |
| (no cue) | 1:22.5 – 1:24.6 | "These strongman's chest medal bars" | Neutral. The refrain's second line, and the lyric's only pause (1:22.1–1:22.5), have no visual event of their own. Since the refrain is background, this is not a missed word. The tower head begins to turn at 1:22.5, on the pause's end, by coincidence. |
| Prosthetic recruitment | 1:30.0 | "I'd" (first word of verse 2); "never been" at 1:32.0–1:34.5 | Neutral to meaningful. The stump makes its deliberate movement, and the rib answers, under "I'd like if it'd never been". |

Potentially problematic or worth a decision:

- **"Stump" is sung twice (0:48.6, 0:58.6) and marked neither time.** The second falls on a visible stump. This is the clearest unmarked word in the locked section.
- **The film's central object is in the song.** The stump drives the phantom load (1:06.25) and the recruitment (1:30.0). Both were designed as ideas about body schema; the lyric gives them a name and a prior claim, "canonized it in the stump", that neither currently acknowledges.
- **The second "landfill" is now marked.** "–fill" is held from 1:46.9 to 1:48.0, and the disposal at 1:47.5, which already fell inside it, is now a grey arm from another station. The first "landfill" shows where this limb goes; the second shows another going there too. No cue time changed.
- **"Scrawls" and the no-written-language rule.** The refrain names writing that is barely writing. If the back-wall surfaces ever show marks, scrawl is the one kind of mark the song licenses, and it is by definition not legible language.

## Answered by the songwriter

1. The filtered voice is meant as background noise, as conditions. It is not a different speaker.
2. The unused lines (presence/absence, compulsion/prohibition, the title line) are deliberately absent from the song.
3. "The offensive trunk": the trunk offends one's sensibilities.
