# Material and texture inventory

MINOR_CONTROVERSIES_IN_AMPUTATION 截肢中的小爭議 · final look development · for sourcing, before any material work

Status: inventory for approval. Nothing has been implemented, downloaded, generated or altered.

## How this was measured

- Every object in the scene was sorted into families by name and owner (112 families, about 13,600 objects).
- The whole film, 0:00–4:40, was sampled every 0.5 s (560 frames) through the locked cameras. Each frame was rendered as a flat ID pass, one colour per object, so what is counted is what is actually on screen, with occlusion.
- For each family: when it is lit and visible; the largest share of the frame it takes; the nearest it comes to the camera; and the texel density that nearest view needs. Densities are given for the final 3840×2160 render (twice the 1080p figure).
- The authored colour of every family was read at eleven moments, because colour carries the film's light and visibility and must not change.
- Nothing in the project was changed. No material was created, downloaded or altered.

## Rules every texture must obey

- **Colour stays the film's.** Every object's base colour is its authored colour, and it carries the film's darkness, energy and translucency over time. An albedo map can only be a grey variation multiplied in (mean 1.0, no hue). Photographic colour textures are out. The approved room shell (A2) multiplies by up to ±20%; other families set their own strength when tested.
- **Specular is tied to colour.** What the film makes dark takes no highlight. Roughness and normal maps can redistribute a highlight; they cannot create one on a surface the film has darkened.
- **Every object is a scaled box with no UVs.** Image textures must be seamless, tileable in both directions, and projected box-wise (triplanar) in the object's own space, corrected for its scale. Textures with a unique layout (a one-off panel, a decal sheet) cannot be used.
- **Moving things carry their texture.** Projection is locked to the object, never to the world, so nothing swims as the body, towers, carriages, station machinery and falling arms move. The scrawls' world-fixed grain is the one approved exception.
- **Edges are already rounded in the shader.** Any normal map has to be combined with that bevel, not replace it.
- **Emission is untouched.** Routing inlays, cells, conduits, ceiling panels, the lamp face, chute mouths and the planes keep their approved emission. No texture may modulate it or put specular competition beside it.
- **Translucency stays the film's.** The ghost copies (including the amber body) and unrevealed station machinery get their translucency from colour alpha and from baked ray visibility. A texture may add roughness or normal detail only, never opacity or albedo.
- **Large repeated surfaces need breakup.** The floor, walls, routing runs and the landfill's 30 m tiles will show tiling. Each tileable map needs a second, larger, very low-contrast variation (procedural, about 5–30 m) and a per-object random offset.

## A. Master inventory

| ID | Family | Priority | Visible | Largest / nearest | Density (4K) | Approach | Maps | Scale | Tiling visible | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Room shell paint | HERO (approved) | 0:21–1:36.5 and 4:15.5–4:40 (dark before 0:21) | Walls 22.6% at 1:18.5; ribs 19.7% at 1:03.5; ceiling 15.4% at 0:21; rear wall 6.4% at 4:28; nearest 8.5 m (ribs, 1:17) | 430 px/m | Done. Direction: a deliberately low-resolution, late-PS1-era material language, chosen over realism. Realistic micro (orange peel) and mesoscale (roller roughness, waviness) tests were invisible under the room's soft light; RETRO_A (5 cm) read as dirty concrete; RETRO_B (N64) vanished; A3 (20 cm) read as a pattern laid on the wall. Details and parameters in docs/look.md. | One generated grey map (tools/make_retro_maps.py), colour multiply only. No roughness, normal, height or metallic maps. | 10 cm texels, 6.4 m tile | Not visible in any tested frame (6.4 m tile at ±20%). | 64 x 64 by design |
| R2 | Chamber floor | HERO (approved) | 0:21.5–1:36.5, 4:15.5–4:40 | Floor 27.0% at 0:32.0; nearest 8.1 m (1:36.5) | 480 px/m | Done. 10 cm texels (F1 +-12%, F1+ +-25%) were invisible or read as dirty mottle at the grazing angle; stepped roughness (+-0.05, +-0.15) added nothing and smudged the lit step. Details in docs/look.md. | One generated grey map, colour multiply only. | 20 cm texels, 12.8 m tile | Not visible in any tested frame. | 64 x 64 by design |
| R3 | Pale fixtures | HERO (approved) | Cabinets from 0:05; plinth from 0:12.5; lamp 0:21–0:56.5; all again 4:15.5–4:40 | Cabinets 6.3% at 0:39.5; plinth 4.8% at 1:36.5; nearest 6.9 m (plinth, 1:36.5); cabinets 7.8 m | 530 px/m | Done. Clean read too modern; X1 (10 cm metric) read as miniature wall; X2 (5 cm) as generic grain. Details in docs/look.md. | One generated 16 x 16 grey map, colour multiply only. | One texture per face (texel size varies by prop) | The same texture recurs on every prop, deliberately. | 16 x 16 by design |
| R4 | Dark trim and tray | MID (clean by decision) | Trim 0:30.5–1:36.5 and 4:15.5–4:22; tray 0:07.5–1:36.5 | Tray 0.9% at 1:12; channels 0.8%; nearest 5.2 m (tray, 1:17) | 700 px/m | None, by decision. | Roughness (scratch and wipe marks), normal (fine scratches). No albedo map at this darkness. | Tile about 0.5–1 m | No: small, few objects | 1K–2K |
| R5 | Body shell (and tower casings) | HERO (approved) | Body 0:12.5–1:40.5 (it falls with the cut to 1:40.5); towers 0:02.5–1:36.5 and 4:15.5–4:40 | Arm and leg segments 8.4% at 1:31; torso 3.3% at 1:18.5; tower columns 2.6% at 0:58; nearest 3.6 m (1:40.5); 5.0 m at 1:17 | 980 px/m | Done. B2 (flat tone per face only) read as modern low-poly; B1 as a texture-mapped character of the era. | Roughness (handling, slight sheen variation), normal (very fine moulded texture), grey variation at most ±5%. Optional faint subsurface-like softness is a shader decision, not a texture. | Tile about 0.3–0.5 m | Low: small parts, but 64 segments side by side. Per-object offset. | 2K tileable; 2K masks |
| R6 | Joints and elastomer | MID | 0:12.5–1:40.5 | Joints 1.2% at 1:13; nearest 3.6 m (1:40.5) | 850 px/m | None, by decision. | Roughness (matte with soft sheen on the rounded faces), normal (fine elastomer grain). No albedo map. | Tile about 0.2–0.3 m | No | 1K |
| R7 | Dark machined metal | MID | Body parts 0:12.5–1:36.5; risers also 4:15.5–4:40; towers 0:02.5–1:36.5 and the ending | Tower bases 1.6% at 1:06.5; risers 1.1% at 0:55; nearest 5.0–5.5 m (body tanks and risers, 1:17) | 700 px/m | Image (roughness, normal) with direction; procedural cavity grime | Roughness (directional), normal (machining marks), metallic (solid), grey variation. | Tile about 0.5 m; brushing runs along each part's long axis | Low | 2K tileable |
| R8 | Practicals and energy surfaces | MID (no sourcing) | Panels 0:21–1:35.5 and the ending; conduits 0:17.5–1:36.5 and 4:15.5–4:22 | Conduits 5.4% at 1:05.5; panels 1.7% at 0:26; nearest 5.8 m (conduits, 1:17) | 630 px/m | None by default. At most, a procedural diffuser texture on the light panels and a roughness on the idle conduit sleeve. | None required. Optional: roughness for the idle conduit sleeve. | n/a | n/a | none |
| R9 | Planes A and B | Not to be textured | From 0:40, when they appear, until 1:36.5 (the ID pass counts them earlier while they are fully transparent) | 4.5% at 1:20.5; nearest 5.0 m (1:17) | 730 px/m | None | None | n/a | n/a | none |
| R10 | Scrawls and bars | Not to be textured | Level 2:21–4:15; coda 4:15.5–4:24.5 | Scrawls 1.9% at 2:22.5; bars 1.1% at 3:54.5; coda scrawls 1.2% at 4:16.5; nearest 5.1 m (scrawls, 2:21) | 450 px/m | None. Approved appearance must not be disturbed. | None | n/a | n/a | none |
| R11 | Rear-wall display panels (CRT wall) | HERO (pipeline locked; lyric built; footage pending) | 0:10–1:36.5 and 4:15.5–4:40 (one panel is lit and slides into place at 0:09.5) | 22.8% of the frame at 1:00; nearest 14.3 m (1:34) | 256 px/m | Three separable layers: (1) the physical screen (locked); (2) screen emission and response (locked); (3) content: the lyric canvas while a line is up, footage where there is footage, the provisional content elsewhere. | GNU Unifont 17.0.05 (assets/fonts/unifont/), pixel for pixel. Footage, when supplied, as 320 x 144 canvas frames (assets/video/crt/canvas/). | One 320 x 144 canvas for the wall; a 64 x 48 section a screen | n/a | 320 x 144 canvas, nearest-pixel |
| N1 | Routing metal | HERO | 1:58.5–2:14.5 (from above) and 2:23–4:15 | Mains 26.3% at 2:27.5; trunks 14.7% at 3:13.5; fine runs 9.2% at 3:39.5; junction blocks 2.4% at 2:53; nearest 4.6 m (mains, 2:28.5); trunks 5.8 m | 500 px/m | Image (directional roughness, normal) plus procedural breakup along each run | Roughness (directional), normal (rolled or brushed grain), metallic (solid), grey variation (very low). | Tile about 2 m along × run width; breakup 10–30 m along runs | Yes: 24 m runs in long rows, seen down their length. Per-run offset and breakup are essential. | 2K tileable (anisotropic) |
| N2 | Station bodies | HERO | 1:58.5–2:14.5 and 2:23–4:15 | Units 25.7% at 3:32.5; cells 16.7% at 3:59; bays 6.6% at 2:43.5; nearest 6.0 m (units, 2:42) | 385 px/m | Image (roughness, normal) plus procedural top-face dust and edge mask | Roughness (satin with a dusty top), normal (very fine aggregate), grey variation. | Tile 2–4 m; breakup 15 m | Yes: 258 identical 8 m units in grids, from above and at grazing angles. Per-object offset and rotation. | 2K tileable |
| N3 | Station machinery | HERO (nearby stations) | 2:23.5–4:15 | Posts 2.8% at 2:45.5; carriages 2.7% at 2:47.5; head blocks 2.1% at 2:46; nearest 4.4 m (head blocks, 2:46.5) | 525 px/m | Reuse R7 (and R3 where painted) at network scale | As R7: roughness (directional), normal, metallic. | As R7, about 0.5 m | Low | Shared with R7 (2K) |
| N4 | Station platforms and aprons | MID | Platforms 2:23.5–4:15; aprons 2:22–2:53.5 and 3:52–4:03.5 | Aprons 8.7% at 2:22; platforms 1.6% at 2:46; nearest 5.2 m (apron, 2:22) | 440 px/m | Image roughness and normal; reuse R2 for platforms | Roughness, normal, grey variation. | Tile 2 m | Low | 2K (shared with R2) |
| N5 | Ground, pit ceiling and distance shell | DISTANT (environment) | All of the level and the pit, as near-black | Pit ceiling 20–49% of level frames; shell 7–46%; ground up to 14% (4:15); nearest n/a | n/a | No texture sourcing. This is the environment task (below). | None: at 1% albedo with colour-tied specular, a texture would not show. | n/a | n/a | none |
| L1 | Waste ground | HERO | 1:37–2:14.5 | 63% of the frame at 1:42.5; nearest 1.26 m at 1:39 (the landing) | 1840 px/m | Image (scanned ground) plus true displacement near the landing only, normal elsewhere; procedural macro variation at 30 m and above | Height / displacement (16-bit), normal, roughness, grey variation. No metallic. | Tile 2–4 m; macro 30–60 m (must hide the 30 m tile grid) | Yes, badly: 149 identical tiles of 30 m and a 63% share of the frame. Strong breakup required. | 4K tileable minimum; 8K if the tile is 4 m |
| L2 | Strata | MID | 1:37–2:00 and 2:11–2:14.5 | Strata sheets 14.6% at 1:42; nearest 6.9 m (1:40) | 335 px/m | Image (roughness, normal) plus the shared dust overlay | Normal (compressed layering), roughness, grey variation. | Tile about 1–2 m | Yes: 1,178 similar sheets. Per-object offset. | 2K tileable |
| L3 | Refuse (dulled room and station parts) | HERO (near the landing) / DISTANT beyond | 1:37–2:14.5 | Refuse platform 8% at 1:39.5; blocks 3.7% at 1:40; housings 2.2%; nearest 3.7–3.9 m (1:39–1:40) | 620 px/m | Reuse the source family's maps (R1, R3, R5, R7) plus one shared disposal-wear overlay (procedural masks driven by image grunge) | Shared overlay: dust (top-facing), abraded edges, scratches, roughness lift. Base maps borrowed from the family each piece came from. | As the source family; overlay masks about 1 m | Yes: thousands of instances. Per-object random offset and seed. | 2K grunge and dust masks (tileable) |
| L4 | Discarded arms and disposed parts | MID | 1:37–1:59.5; the live disposals 1:45.5–1:52 | Upper arms 0.2% at 1:42; nearest 5.9 m (1:38.5) | 400 px/m | Reuse R5 and R6 plus the L3 disposal-wear overlay | As R5 and R6, plus the dust and scuff overlay. | As R5 | Low | Shared with R5 |
| L5 | Chutes | MID | 1:37–2:14.5 (mouths to 1:58.5) | Chute walls 10% at 1:43.5; nearest 5.7 m (1:44) | 405 px/m | Image roughness and normal with a downward-streak mask | Roughness (vertical abrasion streaks), normal (sheet and weld seams kept faint), no albedo at this darkness. | Tile about 2 m (streaks run vertically) | Moderate: 384 walls. Per-object offset. | 2K tileable |

## Families in detail

### Room / inner frame

#### R1 Room shell paint

- **1. Objects:** Long walls ×2, rear wall, ceiling, structural ribs ×32 (and the front wall, which is never seen)
- **Authored colour:** Wall grey 0.35 (WALL)
- **2. Visible:** 0:21–1:36.5 and 4:15.5–4:40 (dark before 0:21)
- **3. Largest on screen:** Walls 22.6% at 1:18.5; ribs 19.7% at 1:03.5; ceiling 15.4% at 0:21; rear wall 6.4% at 4:28
- **3. Nearest to camera:** 8.5 m (ribs, 1:17)
- **3. Texel density needed (4K):** 430 px/m
- **4. Current material and what is missing:** APPROVED 2026-10-19: A2. A 64 x 64 grey map (retro_ps1_01, 8 levels, ordered dither), 10 cm texels, nearest-neighbour, box-projected in object space in metres, multiplying the authored colour about a mean of 1: walls and ribs ±20%, ceiling ±11%. Wall-class roughness 0.72, no metal, shader bevel, unchanged. The whole film uses a 1 px box pixel filter with albedo- and normal-guided OIDN to keep texel edges hard.
- **5. Approach:** Done. Direction: a deliberately low-resolution, late-PS1-era material language, chosen over realism. Realistic micro (orange peel) and mesoscale (roller roughness, waviness) tests were invisible under the room's soft light; RETRO_A (5 cm) read as dirty concrete; RETRO_B (N64) vanished; A3 (20 cm) read as a pattern laid on the wall. Details and parameters in docs/look.md.
- **6. Useful maps:** One generated grey map (tools/make_retro_maps.py), colour multiply only. No roughness, normal, height or metallic maps.
- **7. Physical identity:** An intentionally synthetic painted shell: coarse quantised grey variation, crisp texels near, fine grain far.
- **8. Texture scale:** 10 cm texels, 6.4 m tile
- **9. Repetition visible?:** Not visible in any tested frame (6.4 m tile at ±20%).
- **10. Priority:** HERO (approved)
- **11. Source resolution:** 64 x 64 by design
- **12. Constraints:** Room darkness comes from colour (0:00–0:21 and the ending). Grime must stay subtle enough not to read as narrative dirt.
- **13. Diagnostic frames:** 0:32.0, 1:03.5, 1:17.0, 4:28.0

#### R2 Chamber floor

- **1. Objects:** Floor, plinth step (the lower riser)
- **Authored colour:** Floor grey 0.20 (FLOOR)
- **2. Visible:** 0:21.5–1:36.5, 4:15.5–4:40
- **3. Largest on screen:** Floor 27.0% at 0:32.0
- **3. Nearest to camera:** 8.1 m (1:36.5)
- **3. Texel density needed (4K):** 480 px/m
- **4. Current material and what is missing:** APPROVED 2026-10-19: F1-LARGE. Own class chamber_floor (Floor, PlinthStep). A 64 x 64 grey map (retro_floor_01: the shell recipe, own seeds), 20 cm texels, nearest-neighbour, box-projected in object space in metres, multiplying the authored colour about a mean of 1 by +-20%. Colour only; floor-class roughness 0.50 and bevel unchanged.
- **5. Approach:** Done. 10 cm texels (F1 +-12%, F1+ +-25%) were invisible or read as dirty mottle at the grazing angle; stepped roughness (+-0.05, +-0.15) added nothing and smudged the lit step. Details in docs/look.md.
- **6. Useful maps:** One generated grey map, colour multiply only.
- **7. Physical identity:** The shell's synthetic low-resolution language, with texels sized for the floor's grazing view.
- **8. Texture scale:** 20 cm texels, 12.8 m tile
- **9. Repetition visible?:** Not visible in any tested frame.
- **10. Priority:** HERO (approved)
- **11. Source resolution:** 64 x 64 by design
- **12. Constraints:** The lamp pool on the floor is now locked light; roughness changes how wide it reads. Test against 0:30.3 and 4:36.3.
- **13. Diagnostic frames:** 0:30.3, 0:32.0, 1:36.5, 4:36.3

#### R3 Pale fixtures

- **1. Objects:** Plinth (top block), carriages / wall cabinets ×16, lamp housing. (The rear-wall panels are now their own family, R11.)
- **Authored colour:** Fixture grey 0.44 (FIXTURE)
- **2. Visible:** Cabinets from 0:05; plinth from 0:12.5; lamp 0:21–0:56.5; all again 4:15.5–4:40
- **3. Largest on screen:** Cabinets 6.3% at 0:39.5; plinth 4.8% at 1:36.5
- **3. Nearest to camera:** 6.9 m (plinth, 1:36.5); cabinets 7.8 m
- **3. Texel density needed (4K):** 530 px/m
- **4. Current material and what is missing:** APPROVED 2026-10-19 for the cabinets, carriages and lamp housing: X3, PS1-style prop texturing. Class fixture (machinery values). One 16 x 16 grey map (retro_prop_01, 4 levels, no dither) stretched once over each face, plus a flat tone per face (+-6%); colour only, within about +-20%, mean 1. The carriage's texture stretches as it extends. The plinth top stays clean by decision.
- **5. Approach:** Done. Clean read too modern; X1 (10 cm metric) read as miniature wall; X2 (5 cm) as generic grain. Details in docs/look.md.
- **6. Useful maps:** One generated 16 x 16 grey map, colour multiply only.
- **7. Physical identity:** Props in an early-3D world: a distinct, cruder, per-face texture logic from the architecture.
- **8. Texture scale:** One texture per face (texel size varies by prop)
- **9. Repetition visible?:** The same texture recurs on every prop, deliberately.
- **10. Priority:** HERO (approved)
- **11. Source resolution:** 16 x 16 by design
- **12. Constraints:** Cabinets move (carriage, re-indexing). Unrevealed cabinets must stay unlit.
- **13. Diagnostic frames:** 0:39.5, 1:16.5, 4:36.3

#### R4 Dark trim and tray

- **1. Objects:** Floor channels and bands, the aperture, lamp stem, the tray
- **Authored colour:** Trim 0.06; tray 0.03
- **2. Visible:** Trim 0:30.5–1:36.5 and 4:15.5–4:22; tray 0:07.5–1:36.5
- **3. Largest on screen:** Tray 0.9% at 1:12; channels 0.8%
- **3. Nearest to camera:** 5.2 m (tray, 1:17)
- **3. Texel density needed (4K):** 700 px/m
- **4. Current material and what is missing:** CLEAN BY DECISION (2026-10-19): channels, bands, aperture, lamp stem and tray keep their plain values. At 3-6% colour a colour multiply cannot show, and a roughness channel only smudged on the floor.
- **5. Approach:** None, by decision.
- **6. Useful maps:** Roughness (scratch and wipe marks), normal (fine scratches). No albedo map at this darkness.
- **7. Physical identity:** Black anodised or black-oxide steel. The tray is a handled object: fine wipe marks and a few hairline scratches across its working face.
- **8. Texture scale:** Tile about 0.5–1 m
- **9. Repetition visible?:** No: small, few objects
- **10. Priority:** MID (clean by decision)
- **11. Source resolution:** 1K–2K
- **12. Constraints:** At 3–6% albedo the detail lives in the highlight, so test in the frames where the tray catches the lamp.
- **13. Diagnostic frames:** 0:31.5, 1:12.0, 1:17.0

#### R5 Body shell (and tower casings)

- **1. Objects:** Figure: torso slabs, pelvis, head, arm and leg segments (slices). Tower columns and head caps share the colour and the family. The ghost copies, including the amber body, carry the same surface.
- **Authored colour:** Body 0.58 / 0.56 / 0.51, warm pale (BODY); ghosts tinted, alpha 0.71–0.8
- **2. Visible:** Body 0:12.5–1:40.5 (it falls with the cut to 1:40.5); towers 0:02.5–1:36.5 and 4:15.5–4:40
- **3. Largest on screen:** Arm and leg segments 8.4% at 1:31; torso 3.3% at 1:18.5; tower columns 2.6% at 0:58
- **3. Nearest to camera:** 3.6 m (1:40.5); 5.0 m at 1:17
- **3. Texel density needed (4K):** 980 px/m
- **4. Current material and what is missing:** APPROVED 2026-10-20: B1. Class body_shell (Pelvis, TorsoSlab, Head, Slice). The props' 16 x 16 map stretched once per face (+-8.4%) plus a flat tone per face (+-3.6%), colour only. Ghost copies untouched (ghost material).
- **5. Approach:** Done. B2 (flat tone per face only) read as modern low-poly; B1 as a texture-mapped character of the era.
- **6. Useful maps:** Roughness (handling, slight sheen variation), normal (very fine moulded texture), grey variation at most ±5%. Optional faint subsurface-like softness is a shader decision, not a texture.
- **7. Physical identity:** Matte moulded polymer or bisque ceramic, like a prosthetic or mannequin shell. Fine mould texture, a soft polish where segments are handled, faint fingerprints near joints. Nothing medical-sci-fi.
- **8. Texture scale:** Tile about 0.3–0.5 m
- **9. Repetition visible?:** Low: small parts, but 64 segments side by side. Per-object offset.
- **10. Priority:** HERO (approved)
- **11. Source resolution:** 2K tileable; 2K masks
- **12. Constraints:** Rigid parts that move (no deformation). Its reveal is authored light (0:12.5–0:17.5). Ghost copies must take no albedo and no opacity from the texture. The amber forearm is the orange ghost copy of 0:45–1:00, not a separate object.
- **13. Diagnostic frames:** 0:31.5, 0:50.0 (ghosts), 1:17.0, 1:31.0

#### R6 Joints and elastomer

- **1. Objects:** Figure joints ×20, neck, sensor bands, spine
- **Authored colour:** Joint 0.03 (JOINT); tinted in ghosts
- **2. Visible:** 0:12.5–1:40.5
- **3. Largest on screen:** Joints 1.2% at 1:13
- **3. Nearest to camera:** 3.6 m (1:40.5)
- **3. Texel density needed (4K):** 850 px/m
- **4. Current material and what is missing:** CLEAN BY DECISION (2026-10-20): near-black joints, neck, sensor bands, spine.
- **5. Approach:** None, by decision.
- **6. Useful maps:** Roughness (matte with soft sheen on the rounded faces), normal (fine elastomer grain). No albedo map.
- **7. Physical identity:** Black silicone rubber or a matte elastomer: slightly softer and less reflective than the shell, a faint dusty bloom in recesses.
- **8. Texture scale:** Tile about 0.2–0.3 m
- **9. Repetition visible?:** No
- **10. Priority:** MID
- **11. Source resolution:** 1K
- **12. Constraints:** Detail lives in the highlight; check it doesn't sparkle under the lamp.
- **13. Diagnostic frames:** 1:13.0, 1:17.0

#### R7 Dark machined metal

- **1. Objects:** Body tanks, the four risers (the rods from the lamp to the body), receiver post and foot, tower bases, head blocks, hubs and rotor blades
- **Authored colour:** Structure 0.13 (STRUCTURE); tower parts up to 0.38
- **2. Visible:** Body parts 0:12.5–1:36.5; risers also 4:15.5–4:40; towers 0:02.5–1:36.5 and the ending
- **3. Largest on screen:** Tower bases 1.6% at 1:06.5; risers 1.1% at 0:55
- **3. Nearest to camera:** 5.0–5.5 m (body tanks and risers, 1:17)
- **3. Texel density needed (4K):** 700 px/m
- **4. Current material and what is missing:** Restrained metal, roughness 0.34, metallic 0.6, or body class for the tanks and risers.
- **5. Approach:** Image (roughness, normal) with direction; procedural cavity grime
- **6. Useful maps:** Roughness (directional), normal (machining marks), metallic (solid), grey variation.
- **7. Physical identity:** Machined or bead-blasted dark steel and anodised aluminium; turned finish on the round risers, brushed along the blades; a little grime where parts meet.
- **8. Texture scale:** Tile about 0.5 m; brushing runs along each part's long axis
- **9. Repetition visible?:** Low
- **10. Priority:** MID
- **11. Source resolution:** 2K tileable
- **12. Constraints:** Blades spin and heads turn, so anisotropy must follow the object, not the world. The opening's lamp spot catches the risers.
- **13. Diagnostic frames:** 0:55.0, 1:02.5, 1:06.5, 1:17.0

#### R8 Practicals and energy surfaces

- **1. Objects:** Ceiling light panels ×14, lamp face, wall conduits (segments ×176, elbows ×20), tower cells and head cells. Station head cells on the level behave the same way.
- **Authored colour:** Emissive whites and the cold accent (ENERGY 0.22 / 0.78 / 1.0); idle cells and conduits 0.27–0.38
- **2. Visible:** Panels 0:21–1:35.5 and the ending; conduits 0:17.5–1:36.5 and 4:15.5–4:22
- **3. Largest on screen:** Conduits 5.4% at 1:05.5; panels 1.7% at 0:26
- **3. Nearest to camera:** 5.8 m (conduits, 1:17)
- **3. Texel density needed (4K):** 630 px/m
- **4. Current material and what is missing:** The film's own emission, approved.
- **5. Approach:** None by default. At most, a procedural diffuser texture on the light panels and a roughness on the idle conduit sleeve.
- **6. Useful maps:** None required. Optional: roughness for the idle conduit sleeve.
- **7. Physical identity:** Opal acrylic diffusers, glass-sleeved conduits. Keep them uniform: they are the film's language.
- **8. Texture scale:** n/a
- **9. Repetition visible?:** n/a
- **10. Priority:** MID (no sourcing)
- **11. Source resolution:** none
- **12. Constraints:** Emission must not change. The light panels' brightness is locked lighting.
- **13. Diagnostic frames:** 0:26.0, 1:05.5 (no-change check only)

#### R9 Planes A and B

- **1. Objects:** The two translucent planes and their edges
- **Authored colour:** PLANE_A blue, PLANE_B orange; translucent and emissive (PD_Plane)
- **2. Visible:** From 0:40, when they appear, until 1:36.5 (the ID pass counts them earlier while they are fully transparent)
- **3. Largest on screen:** 4.5% at 1:20.5
- **3. Nearest to camera:** 5.0 m (1:17)
- **3. Texel density needed (4K):** 730 px/m
- **4. Current material and what is missing:** Their own translucent emissive material, unchanged by the look.
- **5. Approach:** None
- **6. Useful maps:** None
- **7. Physical identity:** Authored language. Leave as it is.
- **8. Texture scale:** n/a
- **9. Repetition visible?:** n/a
- **10. Priority:** Not to be textured
- **11. Source resolution:** none
- **12. Constraints:** Translucent and emissive. Untouched.
- **13. Diagnostic frames:** 1:20.5 (no-change check only)

#### R10 Scrawls and bars

- **1. Objects:** Level scrawls ×633, bars ×430; coda scrawls ×97, coda bars ×25
- **Authored colour:** Bars up to 0.40; scrawls up to 0.22; coda pieces 0.44
- **2. Visible:** Level 2:21–4:15; coda 4:15.5–4:24.5
- **3. Largest on screen:** Scrawls 1.9% at 2:22.5; bars 1.1% at 3:54.5; coda scrawls 1.2% at 4:16.5
- **3. Nearest to camera:** 5.1 m (scrawls, 2:21)
- **3. Texel density needed (4K):** 450 px/m
- **4. Current material and what is missing:** Approved: scrawl shader (shallow-cut normal, world-fixed grain, +18% tone); bars smoother and slightly metallic.
- **5. Approach:** None. Approved appearance must not be disturbed.
- **6. Useful maps:** None
- **7. Physical identity:** Authored language.
- **8. Texture scale:** n/a
- **9. Repetition visible?:** n/a
- **10. Priority:** Not to be textured
- **11. Source resolution:** none
- **12. Constraints:** Coda pieces scale from zero. Any texture on a neighbouring surface must not make the scrawls harder to read; check that in every test that includes them.
- **13. Diagnostic frames:** 2:22.5, 3:54.5, 4:16.5 (do-not-disturb checks)

#### R11 Rear-wall display panels (CRT wall)

- **1. Objects:** The 15 rear-wall panels (3 rows × 5, each 2.35 × 2.0 m, seeded depth 0.05–0.18 m), named Panel
- **Authored colour:** Fixture grey 0.44 (FIXTURE), with the film's reveal and darkness in colour as everywhere
- **2. Visible:** 0:10–1:36.5 and 4:15.5–4:40 (one panel is lit and slides into place at 0:09.5)
- **3. Largest on screen:** 22.8% of the frame at 1:00
- **3. Nearest to camera:** 14.3 m (1:34)
- **3. Texel density needed (4K):** 256 px/m
- **4. Current material and what is missing:** CRT physical treatment and display pipeline: APPROVED / LOCKED (2026-10-20): pale bezel, dark glass, 64 x 48 scanline raster, camera-only cyan emission below the cells, tied to authored panel light and wake. Content (2026-10-21): the sung lyric in its final Chinese translation, laid out on the screens measured readable in each shot (docs/look.md, the lyric section); the footage pipeline (tools/make_crt_video.py) is built and waits for footage; until then the provisional blocks and traces. 4:15 rule revised: the screens carrying the refrain's words are lit with them 4:15–4:25.
- **5. Approach:** Three separable layers: (1) the physical screen (locked); (2) screen emission and response (locked); (3) content: the lyric canvas while a line is up, footage where there is footage, the provisional content elsewhere.
- **6. Useful maps:** GNU Unifont 17.0.05 (assets/fonts/unifont/), pixel for pixel. Footage, when supplied, as 320 x 144 canvas frames (assets/video/crt/canvas/).
- **7. Physical identity:** Decision (director, 2026-10-18): these are not room-wall surfaces. They are CRT-like display screens set into the rear wall, a separate CRT / display family. The room-wall treatment excludes their screen faces.
- **8. Texture scale:** One 320 x 144 canvas for the wall; a 64 x 48 section a screen
- **9. Repetition visible?:** n/a
- **10. Priority:** HERO (pipeline locked; lyric built; footage pending)
- **11. Source resolution:** 320 x 144 canvas, nearest-pixel
- **12. Constraints:** Keep the existing geometry and authored timing; any change alters locked transforms and needs its own approval and a new lock reference. The top-centre panel (row 2, column 2) is animated: it slides into place at 0:09.5 and turns to face the phantom from 1:27.5, so the screen treatment is attached to the object. In the coda the lyric takes priority over the scrawls on the panels that carry it and goes round the three panels with ranked bars; every other mark stays. Text on the screens is the sung lyric only (the one exception to the no-writing rule, 2026-10-21): no labels, interface text, numbers or logos. Deterministic, the same in every profile, not a spectrum visualiser.
- **13. Diagnostic frames:** 0:09.5, 0:45, 1:00.0, 1:27.5, 4:16

### Network / outer field

#### N1 Routing metal

- **1. Objects:** Trunks ×289, mains and heavy mains ×66, fine runs ×176, junction blocks ×243
- **Authored colour:** Trunks up to 0.20; mains up to 0.27; fine runs 0.15; junction blocks up to 0.31
- **2. Visible:** 1:58.5–2:14.5 (from above) and 2:23–4:15
- **3. Largest on screen:** Mains 26.3% at 2:27.5; trunks 14.7% at 3:13.5; fine runs 9.2% at 3:39.5; junction blocks 2.4% at 2:53
- **3. Nearest to camera:** 4.6 m (mains, 2:28.5); trunks 5.8 m
- **3. Texel density needed (4K):** 500 px/m
- **4. Current material and what is missing:** PROVISIONALLY ACCEPTED 2026-10-20 (N1): structure takes the architecture's tiled retro map (40 cm texels, +-20%, colour only, emission untouched); station machinery takes the props' X3 logic.
- **5. Approach:** Image (directional roughness, normal) plus procedural breakup along each run
- **6. Useful maps:** Roughness (directional), normal (rolled or brushed grain), metallic (solid), grey variation (very low).
- **7. Physical identity:** Rolled or brushed aluminium and steel, grain running along the run. Mains a touch smoother than trunks (as now). Slight dulling on top faces; a little grime where runs meet junction blocks.
- **8. Texture scale:** Tile about 2 m along × run width; breakup 10–30 m along runs
- **9. Repetition visible?:** Yes: 24 m runs in long rows, seen down their length. Per-run offset and breakup are essential.
- **10. Priority:** HERO
- **11. Source resolution:** 2K tileable (anisotropic)
- **12. Constraints:** The emission inlays are drawn in this same material and are locked: the texture must stay out of the inlay slots, must not add highlights that compete with them, and must not touch the lane. The grain axis follows each run's own axis, the same one the inlays use.
- **13. Diagnostic frames:** 2:27.5, 3:13.5, 3:39.5, 4:14.37

#### N2 Station bodies

- **1. Objects:** Units ×258, bays ×190, cell arrays ×113, spurs ×258
- **Authored colour:** Units and bays up to 0.13; cells 0.11; spurs up to 0.17
- **2. Visible:** 1:58.5–2:14.5 and 2:23–4:15
- **3. Largest on screen:** Units 25.7% at 3:32.5; cells 16.7% at 3:59; bays 6.6% at 2:43.5
- **3. Nearest to camera:** 6.0 m (units, 2:42)
- **3. Texel density needed (4K):** 385 px/m
- **4. Current material and what is missing:** Dark, smooth, not metal (roughness 0.40): the hinge's "dark silicon-like" note.
- **5. Approach:** Image (roughness, normal) plus procedural top-face dust and edge mask
- **6. Useful maps:** Roughness (satin with a dusty top), normal (very fine aggregate), grey variation.
- **7. Physical identity:** Dark cast composite: black polymer concrete or cast resin with a very fine aggregate, satin; dust settled on the top faces, edges barely worn.
- **8. Texture scale:** Tile 2–4 m; breakup 15 m
- **9. Repetition visible?:** Yes: 258 identical 8 m units in grids, from above and at grazing angles. Per-object offset and rotation.
- **10. Priority:** HERO
- **11. Source resolution:** 2K tileable
- **12. Constraints:** Cell arrays carry emission (3:00 onward). Stations beyond sight stay dark through colour and must stay unlit.
- **13. Diagnostic frames:** 2:42.0, 3:32.5, 3:59.0

#### N3 Station machinery

- **1. Objects:** Posts, beams, rails, columns, carriages, head blocks, rotor blades, yoke bars and faces (40 stations)
- **Authored colour:** 0.16–0.32
- **2. Visible:** 2:23.5–4:15
- **3. Largest on screen:** Posts 2.8% at 2:45.5; carriages 2.7% at 2:47.5; head blocks 2.1% at 2:46
- **3. Nearest to camera:** 4.4 m (head blocks, 2:46.5)
- **3. Texel density needed (4K):** 525 px/m
- **4. Current material and what is missing:** Restrained metal (0.34, metallic 0.6), the same class as the room's machinery.
- **5. Approach:** Reuse R7 (and R3 where painted) at network scale
- **6. Useful maps:** As R7: roughness (directional), normal, metallic.
- **7. Physical identity:** The room's machinery at network scale: machined and painted steel, so the stations read as kin to the towers and carriages.
- **8. Texture scale:** As R7, about 0.5 m
- **9. Repetition visible?:** Low
- **10. Priority:** HERO (nearby stations)
- **11. Source resolution:** Shared with R7 (2K)
- **12. Constraints:** Heavily animated (donor, relay, receiver, carrier). Unrevealed machinery is kept invisible by baked ray visibility, which must survive any material change.
- **13. Diagnostic frames:** 2:46.5, 3:36.5

#### N4 Station platforms and aprons

- **1. Objects:** Station platforms ×40, mark aprons ×6
- **Authored colour:** Platforms up to 0.25; aprons 0.02–0.06
- **2. Visible:** Platforms 2:23.5–4:15; aprons 2:22–2:53.5 and 3:52–4:03.5
- **3. Largest on screen:** Aprons 8.7% at 2:22; platforms 1.6% at 2:46
- **3. Nearest to camera:** 5.2 m (apron, 2:22)
- **3. Texel density needed (4K):** 440 px/m
- **4. Current material and what is missing:** Floor class (0.50).
- **5. Approach:** Image roughness and normal; reuse R2 for platforms
- **6. Useful maps:** Roughness, normal, grey variation.
- **7. Physical identity:** Platforms: the room floor's concrete at network scale. Aprons: a dark, matte, slightly resilient mat, the ground the scrawls and bars sit on.
- **8. Texture scale:** Tile 2 m
- **9. Repetition visible?:** Low
- **10. Priority:** MID
- **11. Source resolution:** 2K (shared with R2)
- **12. Constraints:** Scrawls and bars sit directly on the aprons: their legibility comes first.
- **13. Diagnostic frames:** 2:22.0, 2:46.5

#### N5 Ground, pit ceiling and distance shell

- **1. Objects:** Level ground ×4, the pit's ceiling (seen between the routing from above), pit floor and walls, the black distance shell
- **Authored colour:** 0.010–0.013; the shell is 0.0
- **2. Visible:** All of the level and the pit, as near-black
- **3. Largest on screen:** Pit ceiling 20–49% of level frames; shell 7–46%; ground up to 14% (4:15)
- **3. Nearest to camera:** n/a
- **3. Texel density needed (4K):** n/a
- **4. Current material and what is missing:** Authored near-black. Never lit enough to count as visible.
- **5. Approach:** No texture sourcing. This is the environment task (below).
- **6. Useful maps:** None: at 1% albedo with colour-tied specular, a texture would not show.
- **7. Physical identity:** Darkness, as authored.
- **8. Texture scale:** n/a
- **9. Repetition visible?:** n/a
- **10. Priority:** DISTANT (environment)
- **11. Source resolution:** none
- **12. Constraints:** Brightening these would change the locked picture. Any change belongs to the environment proposal and needs approval.
- **13. Diagnostic frames:** See the environment audit

### Landfill / waste

#### L1 Waste ground

- **1. Objects:** The continuous waste surface: 149 tiles of 30 m, 6–10 m of relief
- **Authored colour:** 0.027–0.096 (dulled)
- **2. Visible:** 1:37–2:14.5
- **3. Largest on screen:** 63% of the frame at 1:42.5
- **3. Nearest to camera:** 1.26 m at 1:39 (the landing)
- **3. Texel density needed (4K):** 1840 px/m
- **4. Current material and what is missing:** PROVISIONALLY ACCEPTED 2026-10-20 (L1): the floor's tiled logic, own map, 20 cm texels, +-25%, colour only.
- **5. Approach:** Image (scanned ground) plus true displacement near the landing only, normal elsewhere; procedural macro variation at 30 m and above
- **6. Useful maps:** Height / displacement (16-bit), normal, roughness, grey variation. No metallic.
- **7. Physical identity:** Compacted grey rubble and ash: crushed composite, grit and dust, a few flat fragments. Low colour, no organic matter, no rust, no recognisable rubbish.
- **8. Texture scale:** Tile 2–4 m; macro 30–60 m (must hide the 30 m tile grid)
- **9. Repetition visible?:** Yes, badly: 149 identical tiles of 30 m and a 63% share of the frame. Strong breakup required.
- **10. Priority:** HERO
- **11. Source resolution:** 4K tileable minimum; 8K if the tile is 4 m
- **12. Constraints:** The landing's camera path is locked: displacement must not push the surface into the camera or change the silhouette the debris sits on. Render cost: displacement only where the camera is near.
- **13. Diagnostic frames:** 1:39.0, 1:42.5, 1:48.1, 2:13.0

#### L2 Strata

- **1. Objects:** Strata sheets ×1,178, ribs ×232, bodies ×190, ducts ×200
- **Authored colour:** Up to 0.18 (bodies up to 0.58)
- **2. Visible:** 1:37–2:00 and 2:11–2:14.5
- **3. Largest on screen:** Strata sheets 14.6% at 1:42
- **3. Nearest to camera:** 6.9 m (1:40)
- **3. Texel density needed (4K):** 335 px/m
- **4. Current material and what is missing:** Debris class, roughness 0.90.
- **5. Approach:** Image (roughness, normal) plus the shared dust overlay
- **6. Useful maps:** Normal (compressed layering), roughness, grey variation.
- **7. Physical identity:** Compressed laminated debris: pressed sheets with a dust skin. Reads as layers by light, not colour.
- **8. Texture scale:** Tile about 1–2 m
- **9. Repetition visible?:** Yes: 1,178 similar sheets. Per-object offset.
- **10. Priority:** MID
- **11. Source resolution:** 2K tileable
- **12. Constraints:** None beyond the general rules.
- **13. Diagnostic frames:** 1:40.0, 1:42.0

#### L3 Refuse (dulled room and station parts)

- **1. Objects:** Refuse blocks, housings, panels (discarded rear-wall panels: they follow whatever R11 becomes), cabinets, columns, shafts, beams, ribs, stubs, sheets, shards, lumps, blades, ducts, heads, joints, slices, torsos, machines, decks, bases, platforms (about 7,000 pieces)
- **Authored colour:** 0.04–0.43, the upper world's colours dulled
- **2. Visible:** 1:37–2:14.5
- **3. Largest on screen:** Refuse platform 8% at 1:39.5; blocks 3.7% at 1:40; housings 2.2%
- **3. Nearest to camera:** 3.7–3.9 m (1:39–1:40)
- **3. Texel density needed (4K):** 620 px/m
- **4. Current material and what is missing:** PROVISIONALLY ACCEPTED 2026-10-20 (L1): refuse, strata, discarded parts and chutes take the props' X3 logic.
- **5. Approach:** Reuse the source family's maps (R1, R3, R5, R7) plus one shared disposal-wear overlay (procedural masks driven by image grunge)
- **6. Useful maps:** Shared overlay: dust (top-facing), abraded edges, scratches, roughness lift. Base maps borrowed from the family each piece came from.
- **7. Physical identity:** The same objects as above, after disposal: dust-caked, edges abraded, scratched, slightly dulled. No rust, no stains, no labels.
- **8. Texture scale:** As the source family; overlay masks about 1 m
- **9. Repetition visible?:** Yes: thousands of instances. Per-object random offset and seed.
- **10. Priority:** HERO (near the landing) / DISTANT beyond
- **11. Source resolution:** 2K grunge and dust masks (tileable)
- **12. Constraints:** Instances share one mesh (every box is the one shared cube), so variation has to come from the per-object seed.
- **13. Diagnostic frames:** 1:39.5, 1:40.5, 1:44.0

#### L4 Discarded arms and disposed parts

- **1. Objects:** Discarded arms ×272 (upper arm, forearm, elbow, hand); the disposed body's parts (slab, spine, thigh, shin, foot, knee)
- **Authored colour:** Body palette dulled: 0.30 grey, pale parts up to 0.73
- **2. Visible:** 1:37–1:59.5; the live disposals 1:45.5–1:52
- **3. Largest on screen:** Upper arms 0.2% at 1:42
- **3. Nearest to camera:** 5.9 m (1:38.5)
- **3. Texel density needed (4K):** 400 px/m
- **4. Current material and what is missing:** Debris class (0.90).
- **5. Approach:** Reuse R5 and R6 plus the L3 disposal-wear overlay
- **6. Useful maps:** As R5 and R6, plus the dust and scuff overlay.
- **7. Physical identity:** The body's moulded polymer, discarded: dusty, scuffed, matte. These are the film's prosthetic arms; they should read as the same material as the body in the room.
- **8. Texture scale:** As R5
- **9. Repetition visible?:** Low
- **10. Priority:** MID
- **11. Source resolution:** Shared with R5
- **12. Constraints:** The live disposals fall (rigid motion): object-locked projection.
- **13. Diagnostic frames:** 1:38.5, 1:42.0, 1:48.1

#### L5 Chutes

- **1. Objects:** Chute walls ×384, chute blocks ×167, chute mouths ×263 (emissive)
- **Authored colour:** Walls 0.05–0.08; blocks 0.02–0.04; mouths emissive
- **2. Visible:** 1:37–2:14.5 (mouths to 1:58.5)
- **3. Largest on screen:** Chute walls 10% at 1:43.5
- **3. Nearest to camera:** 5.7 m (1:44)
- **3. Texel density needed (4K):** 405 px/m
- **4. Current material and what is missing:** Debris class (0.90); mouths emissive and light what is under them.
- **5. Approach:** Image roughness and normal with a downward-streak mask
- **6. Useful maps:** Roughness (vertical abrasion streaks), normal (sheet and weld seams kept faint), no albedo at this darkness.
- **7. Physical identity:** Dark sheet steel worn by what has passed down it: faint vertical abrasion, no rust.
- **8. Texture scale:** Tile about 2 m (streaks run vertically)
- **9. Repetition visible?:** Moderate: 384 walls. Per-object offset.
- **10. Priority:** MID
- **11. Source resolution:** 2K tileable
- **12. Constraints:** Chute mouth emission and the pools under it are locked lighting.
- **13. Diagnostic frames:** 1:37.0, 1:44.0

## Rear-wall display panels: where the pipeline groups them with other geometry

Recorded so the panels are not textured as wall or floor by accident.

| Where | What |
| --- | --- |
| scene/look.py, _PREFIXES | Fixed 2026-10-18. Panel was in the floor class, sharing PD_Look_floor with the floor, plinth, aprons, level ground, pit ceiling and floor trim, so a floor texture would have reached the screens. It is now its own class, display, with identical response values: nothing renders differently. |
| scene/look.py, classify() | Classification is by name prefix. Only the 15 rear panels start with Panel (LightPanel and RefusePanel do not), so a separate class can be keyed on that prefix safely. |
| Room shell (approved A2) | Applies only to Wall, WallBack, WallFront, Ceiling and Rib, so it does not touch the panels. WallBack stands directly behind them and shows in the 0.25 m seams, so the screens will be read against the A2 wall: grey, non-emissive, low-contrast, 10 cm texels, much coarser than any screen imagery should be. |
| Inventory, family R3 | The panels were grouped with the plinth, carriages and lamp as pale fixtures. Now split out as R11. |
| Landfill, RefusePanel x164 | Discarded copies of the rear panels (same 2.35 x 2.0 m, same colour), currently debris class. Whether they become discarded dead screens is a decision for the screen-look proposal. |
| Coda (scene/coda.py) | Coda scrawls and bars are placed on the panels' faces (layout.back_panel_center). A screen surface must keep them legible. |
| Opening and attractor (scene/chamber.py) | The attractor panel's location and rotation are animated; any screen layer must ride with it. |

## Background and environment audit

Share of frame that is empty: the world, the black distance shell, or near-black authored surfaces.

| Time | Shot | Empty share | Recommendation | Why |
| --- | --- | --- | --- | --- |
| 0:00–0:21 | Room, opening | 89–100% black | Leave black | The darkness is authored: the reveal is the content. |
| 0:21–1:36.5 | Room | 0–1% | Nothing to do | The room fills the frame. |
| 1:37–1:57 | Landfill, low flyover | 17–33% near-black pit walls and ceiling (70% at the landing) | Leave black; test a faint absorption-only haze | Underground: no sky. A little depth haze could separate the debris planes from the pit's black. It must not add light that shows what the film keeps dark. |
| 1:57.5–2:02.5 | Rising through the level | Shell 5–22% | Leave black | Transition; the black reads as the level's underside. |
| 2:00–2:14.5 | Overhead, to 170 m | 17–38% near-black (the pit seen through the lattice) | Leave black; optional haze between level and pit | Looking down, so no horizon. Atmospheric separation between the level and the refuse is an open note from the hinge. |
| 2:15–2:22.5 | Breakdown | 83–94% | Leave black | Authored darkness. |
| 2:22.5–4:05 | Level travel (low camera) | Shell 28–46% above the horizon; near-black ground 15–40% | Ground continuation + absorption-only haze + camera-only background gradient | Here the geometry stops at a hard line against black and can read as floating. Sight (what is visible when) is locked, so nothing added may show stations beyond it: low-information ground only. |
| 4:05–4:15 | The pull-out | Shell 28% → 7%; near-black ground 7–14%; pit ceiling 37–49% | Ground continuation + distant haze band + very low-contrast camera-only dome gradient | The clearest case: at 4:14 the ground ends in a visible edge. This is the environment task's main target. |
| 4:15–4:40 | Room, coda and ending | 1–3% | Nothing to do | The room fills the frame. |

Rules for any environment work:

- Default to no lighting contribution. Any world image or gradient is set to be seen by camera rays only: no diffuse, glossy, transmission or volume-scatter visibility. Lighting, reflections and exposure then stay exactly as locked.
- Reflections are a separate decision. The routing and machinery are partly metallic and currently reflect black. Letting them reflect a background would change their look and needs its own approval and test.
- Using an image as a light source would change the locked lighting. It is not proposed.
- No city, landscape, stars, mountains or planet. A dark ground continuation, a faint haze band and a very slight gradient at the horizon are the full vocabulary.

## B. Textures to hunt for

| Search for | For | Maps | Resolution |
| --- | --- | --- | --- |
| (Done: the room shell uses a generated retro map; no sourcing needed) | R1 room shell | - | - |
| (Done: the chamber floor uses a generated retro map; N4 platforms still to decide) | R2 floor | - | - |
| Fine textured powder coat / satin powder-coated steel | R3 fixtures | roughness, normal | 2K |
| Black anodised aluminium with fine scratches | R4 trim and tray | roughness, normal | 1K–2K |
| Matte moulded plastic / bisque porcelain / mannequin surface | R5 body, L4 arms | roughness, normal (albedo only as grey variation) | 2K |
| Black silicone rubber / matte elastomer | R6 joints | roughness, normal | 1K |
| Bead-blasted and brushed aluminium; machined steel | R7 machinery, N3 station machinery | roughness (anisotropic), normal, metallic | 2K |
| Brushed or rolled aluminium sheet, long directional grain | N1 routing | roughness, normal, metallic | 2K |
| Black polymer concrete / dark cast resin, very fine aggregate | N2 station bodies | roughness, normal | 2K |
| Dark rubber matting, fine texture, plain | N4 aprons | roughness, normal | 1K–2K |
| Compacted gravel and ash ground / crushed rubble surface (photoscan) | L1 waste ground | height (16-bit), normal, roughness, albedo | 4K–8K |
| Compressed laminated board / pressed layered debris | L2 strata | normal, roughness | 2K |
| Dark sheet steel with vertical abrasion streaks | L5 chutes | roughness, normal | 2K |
| Greyscale grunge masks: edge wear, cavity dust, top dust, fingerprints, fine scratches | Shared overlay (R1, R3, R5, L3, L4) | masks only | 2K |

- Prefer PBR sets that state their real-world size and include roughness and normal; 16-bit height where relief matters.
- Prefer neutral, desaturated albedo: it is used as grey variation only.
- Seamless in both directions; no unique layouts.
- CC0 libraries (for example ambientCG, Poly Haven) are a good first stop because licensing is not a question.
- Avoid: rust, stains, graffiti, labels, stickers, warning stripes, hazard paint, sci-fi panelling, greebles, circuit patterns, visible text, strong colour.

## C. Order of look-development tests

| Step | Families | Why here | Frames |
| --- | --- | --- | --- |
| 1 | R1 room shell and R2 chamber floor: DONE (A2 and F1-LARGE, approved 2026-10-19) | Largest share of frame in the room; the shell set the film's material language (retro, low-resolution). | - |
| 2 | R3 + R4: DONE (props X3 approved 2026-10-19; plinth top, trim and tray clean by decision) | Props took a per-face, early-3D texture logic distinct from the architecture. | - |
| 3 | R5 + R6: body shell and joints (with ghosts) | The closest surface in the film (about 980 px/m at 4K). | 0:31.5, 0:50.0, 1:17.0, 1:31.0 |
| 4 | R7: dark machined metal | Towers, risers, receiver; defines the metal shared with the stations. | 0:55.0, 1:02.5, 1:17.0 |
| 5 | N1: routing metal, with an emission check | The network's dominant surface; the inlays must be unchanged. | 2:27.5, 3:13.5, 3:39.5, 4:14.37 |
| 6 | N2 + N4: station bodies, platforms, aprons | The other dominant network surface; scrawl legibility on aprons. | 2:22.0, 2:42.0, 3:32.5, 3:59.0 |
| 7 | N3: station machinery (R7 at network scale) | Confirms the kinship with the room. | 2:46.5, 3:36.5 |
| 8 | L1 + L2: waste ground and strata | Needs the heaviest maps and displacement; isolated sequence. | 1:39.0, 1:42.5, 1:48.1, 2:13.0 |
| 9 | L3 + L4 + L5: disposal wear, arms, chutes | Reuses approved families plus one overlay. | 1:38.5, 1:40.5, 1:44.0 |
| 10 | No-change checks: R8, R9, R10 | Confirms practicals, planes, scrawls and bars are untouched after all of the above. | 1:05.5, 1:20.5, 2:22.5, 3:54.5, 4:16.5 |
| then | Environment (separate task) | Ground continuation, haze, camera-only gradient. | 2:25.0, 3:20.0, 4:08.5, 4:14.37 |

## D. Representative still set

One set, reused for every family so that each approval is seen against the same frames. Each test renders only the frames listed for its family in C; the full set is rendered once at the end.

| Time | What it shows | Families |
| --- | --- | --- |
| 0:31.5 | Room just after READY: floor, fixtures, body, lamp pool | R1 R2 R3 R4 R5 |
| 0:32.0 | Floor at its largest (27%) | R2 |
| 0:39.5 | Carriages at their largest | R3 |
| 0:50.0 | Ghost copies, including the amber body | R5 (ghost rule) |
| 0:55.0 | Risers at their largest | R7 |
| 1:00.0 | Rear-wall panels at their largest | R1 (seams); R11 reserved, must stay untextured |
| 1:03.5 | Ribs at their largest | R1 |
| 1:12.0 | Tray at its largest | R4 |
| 1:17.0 | Nearest room view: walls, ribs, body, tray, risers | R1 R3 R4 R5 R6 R7 |
| 1:31.0 | Body at its largest | R5 |
| 1:39.0 | The landing: waste ground at 1.3 m | L1 L3 |
| 1:42.5 | Waste ground at 63% of frame | L1 L2 |
| 1:44.0 | Chute walls nearest | L5 L3 |
| 1:48.1 | Flyover with disposals | L1 L4 |
| 2:13.0 | Overhead: routing over the pit | N1 N2 L1 |
| 2:22.0 | Apron with scrawls | N4 R10 |
| 2:27.5 | Mains at their largest (26%) | N1 |
| 2:42.0 | Units nearest | N2 |
| 2:46.5 | Station machinery nearest | N3 N4 |
| 3:13.5 | Trunks at their largest, ring emission | N1 (emission check) |
| 3:32.5 | Units at their largest | N2 |
| 3:39.5 | Fine runs at their largest, prosthesis emission | N1 (emission check) |
| 3:54.5 | Bars at their largest | R10 (no-change) |
| 4:14.37 | Climax peak: inlays at saturation; pull-out | N1 N2 (emission check), environment |
| 4:16.5 | Coda scrawls | R10 (no-change) |
| 4:28.0 | Ending: rear wall | R1 R3 |
| 4:36.3 | The lamp arriving on the plinth | R2 R3 |
