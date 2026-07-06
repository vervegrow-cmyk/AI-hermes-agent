# Dynamic Generation Plan V2

## Principle

Do **not** generate the whole ad from text prompts first.

Use this order:

1. lock `KF1` through `KF4`
2. approve the 4 target frames
3. animate each frame into a short clip
4. stitch into the 15-second clone cut

## Phase 1: Keyframe Lock

Primary tool: `comfyui_image`

Goal:

- preserve model identity more tightly than free-form video generation
- preserve hat geometry and fan placement
- preserve the packed sunny stadium setting

## Phase 2: Motion Conversion

Primary tool: `seedance_ark_video`

Use each approved keyframe as the first frame for the matching shot:

- `KF1_pain` -> `clone_01_pain`
- `KF2_reveal` -> `clone_02_reveal`
- `KF3_activate` -> `clone_03_activate`
- `KF4_relief_finish` -> `clone_04_relief_finish`

Recommended durations:

- `clone_01_pain`: 4-5s
- `clone_02_reveal`: 4s generated, trimmed to ~1.3s
- `clone_03_activate`: 4s
- `clone_04_relief_finish`: 6s generated, trimmed to ~5.5s

## Phase 3: Edit

The final cut should preserve the reference order:

1. pain
2. reveal
3. activate
4. relief finish

No static cards.

No eBay infographic inserts.

No separate CTA slate at the end.

## Why This Will Match Better

- the first frame of every dynamic clip is intentionally designed
- the model’s face and outfit are better anchored
- the hat silhouette is better anchored
- the environment is no longer left to model improvisation

## Recommended Review Gate

Do not proceed from Phase 1 to Phase 2 until all four keyframes are approved for:

- face likeness
- hat accuracy
- stadium continuity
- shot grammar match to the reference
