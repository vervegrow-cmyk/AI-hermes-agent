import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface ShotSpec {
  id: string;
  start: number;
  end: number;
  mode: "video" | "product";
  source?: string;
  sources?: string[];
  subtitle: string;
  eyebrow: string;
  voiceover: string;
  purpose: string;
  qaNotes?: string;
  heatLevel?: number;
  coolLevel?: number;
  cta?: boolean;
}

export interface SceneProps {
  title: string;
  fps: number;
  width: number;
  height: number;
  totalDuration: number;
  soundtrackPath?: string;
  shots: ShotSpec[];
}

const palette = {
  heat: "#FF8A3D",
  cool: "#66E0FF",
  ink: "#08131C",
  surface: "rgba(6, 17, 26, 0.68)",
  line: "rgba(255,255,255,0.18)",
  white: "#F8FBFF",
};

const baseTextStyle: React.CSSProperties = {
  fontFamily: "Arial, sans-serif",
  color: palette.white,
  textShadow: "0 8px 30px rgba(0,0,0,0.45)",
};

const getLocalOpacity = (frame: number, durationInFrames: number) => {
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return Math.min(fadeIn, fadeOut);
};

const HeatRibbon: React.FC<{ heatLevel: number; coolLevel: number }> = ({ heatLevel, coolLevel }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const wave = Math.sin(frame / 8) * 10;
  const heatWidth = width * (0.18 + heatLevel * 0.48);
  const coolWidth = width * (0.12 + coolLevel * 0.38);

  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 88 + wave,
          left: -120,
          width: heatWidth,
          height: 18,
          transform: "rotate(-9deg)",
          background: `linear-gradient(90deg, rgba(255,138,61,0), ${palette.heat}, rgba(255,138,61,0.18))`,
          opacity: 0.92,
        }}
      />
      {coolLevel > 0 ? (
        <div
          style={{
            position: "absolute",
            top: 132 - wave,
            right: -120,
            width: coolWidth,
            height: 16,
            transform: "rotate(11deg)",
            background: `linear-gradient(90deg, rgba(102,224,255,0), ${palette.cool}, rgba(102,224,255,0.15))`,
            opacity: 0.96,
          }}
        />
      ) : null}
    </>
  );
};

const StadiumChrome: React.FC<{ shot: ShotSpec }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const chipPop = spring({
    frame,
    fps: 30,
    config: { damping: 14, stiffness: 160 },
  });
  const glowOffset = Math.sin(frame / 11) * 8;

  return (
    <>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(6,17,26,0.10) 0%, rgba(6,17,26,0.22) 52%, rgba(6,17,26,0.72) 100%)",
        }}
      />
      <HeatRibbon heatLevel={shot.heatLevel ?? 0.4} coolLevel={shot.coolLevel ?? 0} />
      <div
        style={{
          position: "absolute",
          inset: 28,
          border: `1px solid ${palette.line}`,
          borderRadius: 34,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 92,
          left: 72,
          padding: "12px 22px",
          borderRadius: 999,
          background: "rgba(6,17,26,0.58)",
          border: `1px solid ${shot.coolLevel ? "rgba(102,224,255,0.42)" : "rgba(255,138,61,0.38)"}`,
          transform: `scale(${0.9 + chipPop * 0.1})`,
          ...baseTextStyle,
          fontSize: 22,
          fontWeight: 800,
          letterSpacing: "0.12em",
        }}
      >
        {shot.eyebrow}
      </div>
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          bottom: 148,
          padding: "28px 30px 30px",
          borderRadius: 32,
          background: palette.surface,
          backdropFilter: "blur(16px)",
          border: `1px solid ${palette.line}`,
          boxShadow: "0 22px 80px rgba(0,0,0,0.35)",
        }}
      >
        <div
          style={{
            ...baseTextStyle,
            fontSize: 66,
            lineHeight: 1,
            fontWeight: 900,
            letterSpacing: "-0.04em",
            textTransform: "uppercase",
          }}
        >
          {shot.subtitle}
        </div>
        <div
          style={{
            ...baseTextStyle,
            marginTop: 14,
            fontSize: 24,
            lineHeight: 1.35,
            color: "rgba(248,251,255,0.84)",
          }}
        >
          {shot.voiceover}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          right: 90 + glowOffset,
          top: height * 0.16,
          width: 108,
          height: 108,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(255,255,255,0.25) 0%, ${
            shot.coolLevel ? "rgba(102,224,255,0.20)" : "rgba(255,138,61,0.18)"
          } 48%, rgba(255,255,255,0) 70%)`,
          filter: "blur(4px)",
        }}
      />
    </>
  );
};

const ProductStillScene: React.FC<{ shot: ShotSpec }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const images = shot.sources ?? [];
  const firstHalf = frame < fps * 2;
  const active = images[firstHalf ? 0 : Math.min(1, images.length - 1)] ?? images[0];
  const zoom = interpolate(frame, [0, 120], [1.02, 1.12], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const pulse = 0.94 + Math.sin(frame / 10) * 0.04;

  return (
    <AbsoluteFill style={{ background: "#F3EEE8" }}>
      {active ? (
        <Img
          src={staticFile(active)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${zoom})`,
          }}
        />
      ) : null}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(243,238,232,0.08) 0%, rgba(9,19,28,0.18) 56%, rgba(9,19,28,0.74) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 118,
          left: 70,
          padding: "16px 22px",
          borderRadius: 999,
          border: "1px solid rgba(102,224,255,0.42)",
          background: "rgba(6, 17, 26, 0.68)",
          ...baseTextStyle,
          fontSize: 24,
          fontWeight: 800,
          letterSpacing: "0.14em",
        }}
      >
        REAL PRODUCT CLOSE-UP
      </div>
      <div
        style={{
          position: "absolute",
          left: 74,
          bottom: 182,
          right: 74,
          padding: "30px 30px 34px",
          borderRadius: 34,
          background: "rgba(8,19,28,0.74)",
          border: `1px solid ${palette.line}`,
        }}
      >
        <div style={{ ...baseTextStyle, fontSize: 70, lineHeight: 1, fontWeight: 900 }}>
          {shot.subtitle}
        </div>
        <div
          style={{
            ...baseTextStyle,
            marginTop: 16,
            fontSize: 26,
            color: "rgba(248,251,255,0.84)",
            lineHeight: 1.36,
          }}
        >
          {shot.voiceover}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          right: 84,
          top: 228,
          width: 160,
          height: 160,
          borderRadius: "50%",
          border: `6px solid rgba(102,224,255,${pulse})`,
          boxShadow: "0 0 50px rgba(102,224,255,0.22)",
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 120,
          top: 406,
          width: 110,
          height: 8,
          borderRadius: 999,
          background: palette.cool,
          transform: "rotate(-24deg)",
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 154,
          top: 432,
          width: 72,
          height: 8,
          borderRadius: 999,
          background: palette.cool,
          transform: "rotate(-24deg)",
        }}
      />
    </AbsoluteFill>
  );
};

const CTAOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const pop = spring({
    frame,
    fps: 30,
    config: { damping: 12, stiffness: 140 },
  });

  return (
    <>
      <div
        style={{
          position: "absolute",
          right: 56,
          bottom: 286,
          width: 248,
          height: 248,
          borderRadius: 34,
          overflow: "hidden",
          border: "2px solid rgba(255,255,255,0.32)",
          boxShadow: "0 22px 60px rgba(0,0,0,0.36)",
          background: "#EFE8DE",
        }}
      >
        <Img src={staticFile("01_main_hat.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          bottom: 88,
          height: 122,
          borderRadius: 999,
          background: "linear-gradient(90deg, #00C2FF 0%, #1DE5A3 100%)",
          boxShadow: "0 18px 60px rgba(0,194,255,0.28)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${0.9 + pop * 0.1})`,
        }}
      >
        <div
          style={{
            ...baseTextStyle,
            color: "#031018",
            textShadow: "none",
            fontSize: 40,
            fontWeight: 900,
            letterSpacing: "-0.03em",
            textTransform: "uppercase",
          }}
        >
          Tap to check it out
        </div>
      </div>
    </>
  );
};

const ShotLayer: React.FC<{ shot: ShotSpec }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = Math.max(1, Math.round((shot.end - shot.start) * fps));
  const opacity = getLocalOpacity(frame, durationInFrames);
  const scale = interpolate(frame, [0, durationInFrames], [1.02, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity, transform: `scale(${scale})` }}>
      {shot.mode === "video" && shot.source ? (
        <OffthreadVideo src={staticFile(shot.source)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : null}
      {shot.mode === "product" ? <ProductStillScene shot={shot} /> : <StadiumChrome shot={shot} />}
      {shot.cta ? <CTAOverlay /> : null}
    </AbsoluteFill>
  );
};

export const Scene: React.FC<SceneProps> = (props) => {
  return (
    <AbsoluteFill style={{ background: palette.ink }}>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 20% 10%, rgba(255,138,61,0.14) 0%, rgba(255,138,61,0) 34%), radial-gradient(circle at 82% 84%, rgba(102,224,255,0.12) 0%, rgba(102,224,255,0) 28%), #08131C",
        }}
      />
      {props.shots.map((shot) => (
        <Sequence
          key={shot.id}
          from={Math.round(shot.start * props.fps)}
          durationInFrames={Math.max(1, Math.round((shot.end - shot.start) * props.fps))}
        >
          <ShotLayer shot={shot} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const calculateMetadata: CalculateMetadataFunction<SceneProps> = async ({ props }) => ({
  durationInFrames: Math.round((props.totalDuration || 30) * (props.fps || 30)),
  fps: props.fps || 30,
  width: props.width || 1080,
  height: props.height || 1920,
});
