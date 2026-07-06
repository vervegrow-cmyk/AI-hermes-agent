# Solar Fan Hat Viral Clone Execution Plan

## Goal

Recreate the uploaded 15-second viral reference structure for the solar fan hat using:

- product refs in `assets/products/solar_fan_hat/`
- model ref: `08_model_stadium.png`
- reference video: `tmp/reference_analysis/reference.mp4`

The target is **all-dynamic UGC-style video**, not a slideshow.

## Runtime Choice

- `Remotion`: recommended for this sample because the output is mainly generated video clips stitched into a clean short-form cut with light subtitle/CTA support.
- `HyperFrames`: valid alternative if we later want more aggressive HTML kinetic text, richer animated overlays, or a bespoke landing-page feel.

For this sample run, the recommended runtime is `remotion`.

## Product Identity Notes

Every motion prompt should preserve these product traits:

- beige / khaki wide-brim outdoor sun hat
- two black side-mounted mini fans
- small solar panels mounted near the fan housings
- casual outdoor use, breathable crown band
- cooling + shade are the primary promise

Model identity notes:

- brunette woman
- warm tan skin tone
- fitted black T-shirt
- casual stadium spectator styling
- friendly expressive face, realistic lifestyle feel

## Viral Structure To Replicate

1. Heat pain point
2. First-person product reveal
3. Put on + activate
4. Immediate emotional payoff
5. Hero CTA while staying in the same environment

## Shot-by-Shot Provider Plan

All five shots should route to `seedance_ark_video`.

- `shot_01_stadium_heat_hook`: motion pain point
- `shot_02_first_person_reveal`: motion product reveal with dynamic closeup
- `shot_03_put_on_and_power`: motion demo + product proof
- `shot_04_relief_reaction`: motion payoff
- `shot_05_game_on_cta`: motion CTA

## Frame-by-Frame / Beat-by-Beat Prompting Guide

These are the canonical prompts to reuse if a shot needs regeneration.

### Shot 1: Stadium Heat Hook

**Seedance prompt**

```text
Vertical TikTok UGC in a crowded sunny soccer stadium. A brunette female sports fan in a fitted black T-shirt sits in the stands under harsh afternoon sun, sweaty and uncomfortable, fanning herself with one hand and squinting from the heat. Real handheld phone camera energy, high relatability, photorealistic, no text overlay, no hat yet.
0-1s: she wipes sweat and exhales.
1-2s: she shades her eyes and looks frustrated.
2-3s: she fans herself faster and looks like she cannot enjoy the game.
```

### Shot 2: First-Person Product Reveal

**Seedance prompt**

```text
First-person handheld UGC shot in the same sunny soccer stadium. Two hands lift a beige wide-brim solar fan hat into frame toward the brunette female fan. The hat must clearly show dual black side fans and small solar panels mounted near the brim. The woman reacts with curiosity and relief as the product enters frame. Photorealistic stadium background, realistic public setting, no text overlay.
0-1s: product rises into frame.
1-2s: close reveal of brim and dual fans.
2-3s: woman reaches for it with an interested expression.
```

### Shot 3: Put On And Power

**Seedance prompt**

```text
Vertical realistic UGC close-up in stadium seating. The brunette female fan quickly puts on the beige solar fan hat, adjusts it comfortably, and presses the power control to activate the dual fans. The black fan housings visibly spin and a light breeze moves strands of her hair near her cheeks. Strong product fidelity: beige brim, dual black fans, solar panels visible, athletic stadium background. No text overlay.
0-1s: she pulls the hat on.
1-2s: she adjusts the brim and chin cord.
2-3s: finger presses the power control and fans begin spinning.
3-4s: hair moves slightly from airflow and her face starts relaxing.
```

### Shot 4: Relief Reaction

**Seedance prompt**

```text
Same female fan wearing the beige solar fan hat in a bright crowded soccer stadium. She visibly relaxes, smiles with relief, and enjoys the cooling airflow while the sun still beats down around her. Her posture softens and she looks refreshed instead of overheated. Handheld phone-camera realism, photorealistic face, subtle hair movement from the fans, no text overlay.
0-1s: relief hits her face.
1-2s: she smiles and takes a calm breath.
2-3s: she looks back toward the field feeling comfortable.
```

### Shot 5: Game-On CTA

**Seedance prompt**

```text
Final hero UGC shot in a sunny packed soccer stadium. The brunette female fan is now happy and confident while wearing the beige solar fan hat, smiling at the camera and pointing toward one of the built-in fans as if recommending it. The scene should still feel like a real live game day, not a studio ad. Product remains clearly visible and flattering, photorealistic, no text overlay.
0-1s: she faces the camera and points to the fan.
1-2s: she smiles naturally and keeps watching the game.
```

## Negative Prompt Guidance

Use these constraints mentally across all shots:

- no futuristic sci-fi styling
- no studio backdrop
- no extra accessories added to the hat
- no purple lighting or nightclub mood
- no unreadable embedded text
- no cartoon faces
- no plastic skin
- no unrealistic oversized fans

## Recommended Subtitle Lines

- `Too hot to enjoy the game?`
- `Here is the fix`
- `Turn on the breeze`
- `Instant relief`
- `Stay cool all game long`

## Recommended 15s Voiceover

```text
Too hot to enjoy the game? This solar fan hat gives you shade plus dual cooling fans. Put it on, switch it on, and feel instant airflow while you stay cool in the sun.
```

## Run Command

```powershell
python scripts\run_workflow.py --pipeline exaggerated_viral_ad --product assets\products\solar_fan_hat\product.json
```

## Expected Output

- all motion-led clips, no static product-image cards
- a 15-second stadium-focused viral-clone sample
- output under `runs/exaggerated_viral_ad/solar-fan-hat_<timestamp>/final/final.mp4`
