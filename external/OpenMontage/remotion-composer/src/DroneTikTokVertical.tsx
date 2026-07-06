import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";

const { fontFamily: spaceGrotesk } = loadSpaceGrotesk("normal", {
  weights: ["400", "500", "700"],
  subsets: ["latin"],
});

const resolveAsset = (src: string): string => {
  if (src.startsWith("http://") || src.startsWith("https://") || src.startsWith("data:")) {
    return src;
  }
  const clean = src.replace(/^file:\/\/\/?/, "");
  if (clean.startsWith("/") || /^[A-Za-z]:[\\/]/.test(clean)) {
    return `file:///${clean.replace(/\\/g, "/")}`;
  }
  return staticFile(clean);
};

export interface DroneTikTokScene {
  id: string;
  start: number;
  end: number;
  image: string;
  kicker?: string;
  headline: string;
  subhead?: string;
  badges?: string[];
  accentColor?: string;
  imageFit?: "contain" | "cover";
  imagePosition?: string;
  zoomFrom?: number;
  zoomTo?: number;
}

export interface DroneTikTokCaption {
  text: string;
  start: number;
  end: number;
}

export interface DroneTikTokAudio {
  narrationSrc?: string;
  musicSrc?: string;
  narrationVolume?: number;
  musicVolume?: number;
}

export interface DroneTikTokVerticalProps {
  productName: string;
  cta: string;
  scenes: DroneTikTokScene[];
  captions: DroneTikTokCaption[];
  audio?: DroneTikTokAudio;
}

export const calculateDroneTikTokVerticalMetadata = async ({
  props,
}: {
  props: DroneTikTokVerticalProps;
}) => {
  const scenes = props.scenes || [];
  if (scenes.length === 0) {
    return { durationInFrames: 30 * 24 };
  }
  const lastEnd = Math.max(...scenes.map((scene) => scene.end || 0));
  return { durationInFrames: Math.ceil((lastEnd + 0.5) * 30) };
};

const ProgressRail: React.FC<{ progress: number }> = ({ progress }) => {
  return (
    <div
      style={{
        position: "absolute",
        top: 30,
        left: 42,
        right: 42,
        height: 8,
        borderRadius: 999,
        background: "rgba(255,255,255,0.14)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${Math.max(0, Math.min(progress, 1)) * 100}%`,
          height: "100%",
          borderRadius: 999,
          background: "linear-gradient(90deg, #22D3EE 0%, #A855F7 50%, #F97316 100%)",
          boxShadow: "0 0 26px rgba(168,85,247,0.55)",
        }}
      />
    </div>
  );
};

const CaptionBand: React.FC<{ caption: DroneTikTokCaption }> = ({ caption }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inFrame = Math.floor(caption.start * fps);
  const outFrame = Math.floor(caption.end * fps);
  const opacity = interpolate(frame, [inFrame, inFrame + 6, outFrame - 5, outFrame], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(opacity, [0, 1], [20, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: 44,
        right: 44,
        bottom: 120,
        display: "flex",
        justifyContent: "center",
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          maxWidth: 920,
          padding: "20px 28px",
          borderRadius: 28,
          background: "rgba(15,23,42,0.82)",
          color: "#F8FAFC",
          fontFamily: spaceGrotesk,
          fontSize: 42,
          fontWeight: 700,
          lineHeight: 1.18,
          textAlign: "center",
          boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
          border: "1px solid rgba(255,255,255,0.10)",
        }}
      >
        {caption.text}
      </div>
    </div>
  );
};

const SceneLayer: React.FC<{
  scene: DroneTikTokScene;
  productName: string;
  cta: string;
  totalFrames: number;
}> = ({ scene, productName, cta, totalFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inFrame = Math.floor(scene.start * fps);
  const outFrame = Math.floor(scene.end * fps);
  const localFrame = frame - inFrame;
  const duration = Math.max(1, outFrame - inFrame);

  const fade = interpolate(frame, [inFrame, inFrame + 7, outFrame - 7, outFrame], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const scale = interpolate(
    localFrame,
    [0, duration],
    [scene.zoomFrom ?? 1.03, scene.zoomTo ?? 1.12],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    }
  );

  const headlineSpring = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 115, mass: 0.8 },
  });

  const kickerOpacity = interpolate(localFrame, [0, 8, duration - 10, duration], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Img
        src={resolveAsset(scene.image)}
        style={{
          position: "absolute",
          inset: -80,
          width: 1240,
          height: 2080,
          objectFit: scene.imageFit ?? "cover",
          objectPosition: scene.imagePosition ?? "center",
          transform: `scale(${scale})`,
          filter: "saturate(1.03) contrast(1.02)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(3,7,18,0.20) 0%, rgba(3,7,18,0.35) 30%, rgba(3,7,18,0.78) 72%, rgba(2,6,23,0.92) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 20%, rgba(34,211,238,0.14) 0%, rgba(0,0,0,0) 38%), radial-gradient(circle at 85% 10%, rgba(249,115,22,0.12) 0%, rgba(0,0,0,0) 28%)",
        }}
      />

      <div
        style={{
          position: "absolute",
          top: 72,
          left: 48,
          right: 48,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div
          style={{
            padding: "14px 20px",
            borderRadius: 999,
            background: "rgba(255,255,255,0.10)",
            color: "#E2E8F0",
            fontFamily: spaceGrotesk,
            fontSize: 26,
            fontWeight: 700,
            letterSpacing: "0.03em",
            textTransform: "uppercase",
            backdropFilter: "blur(14px)",
          }}
        >
          {productName}
        </div>
        <div
          style={{
            padding: "14px 22px",
            borderRadius: 999,
            background: "linear-gradient(135deg, #22D3EE 0%, #A855F7 100%)",
            color: "#F8FAFC",
            fontFamily: spaceGrotesk,
            fontSize: 24,
            fontWeight: 700,
            boxShadow: "0 16px 32px rgba(34,211,238,0.20)",
          }}
        >
          TikTok Ad
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 52,
          right: 52,
          top: 220,
          display: "flex",
          flexDirection: "column",
          gap: 18,
        }}
      >
        {scene.kicker ? (
          <div
            style={{
              alignSelf: "flex-start",
              padding: "12px 18px",
              borderRadius: 999,
              background: scene.accentColor ?? "rgba(34,211,238,0.18)",
              color: "#E0F2FE",
              fontFamily: spaceGrotesk,
              fontSize: 24,
              fontWeight: 700,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              opacity: kickerOpacity,
            }}
          >
            {scene.kicker}
          </div>
        ) : null}

        <div
          style={{
            color: "#F8FAFC",
            fontFamily: spaceGrotesk,
            fontSize: 94,
            fontWeight: 700,
            lineHeight: 0.95,
            letterSpacing: "-0.04em",
            transform: `translateY(${interpolate(headlineSpring, [0, 1], [44, 0])}px) scale(${interpolate(
              headlineSpring,
              [0, 1],
              [0.96, 1]
            )})`,
            opacity: headlineSpring,
            textShadow: "0 10px 36px rgba(0,0,0,0.30)",
          }}
        >
          {scene.headline}
        </div>

        {scene.subhead ? (
          <div
            style={{
              maxWidth: 820,
              color: "#CBD5E1",
              fontFamily: spaceGrotesk,
              fontSize: 32,
              fontWeight: 500,
              lineHeight: 1.18,
              opacity: interpolate(localFrame, [8, 18], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {scene.subhead}
          </div>
        ) : null}
      </div>

      <div
        style={{
          position: "absolute",
          left: 48,
          right: 48,
          bottom: 310,
          display: "flex",
          flexWrap: "wrap",
          gap: 14,
        }}
      >
        {(scene.badges || []).map((badge, index) => {
          const badgeSpring = spring({
            frame: localFrame - 10 - index * 3,
            fps,
            config: { damping: 16, stiffness: 150, mass: 0.8 },
          });
          return (
            <div
              key={badge}
              style={{
                padding: "14px 18px",
                borderRadius: 18,
                background: "rgba(15,23,42,0.68)",
                color: "#F8FAFC",
                border: "1px solid rgba(255,255,255,0.12)",
                fontFamily: spaceGrotesk,
                fontSize: 24,
                fontWeight: 700,
                transform: `translateY(${interpolate(badgeSpring, [0, 1], [18, 0])}px) scale(${interpolate(
                  badgeSpring,
                  [0, 1],
                  [0.92, 1]
                )})`,
                opacity: badgeSpring,
                boxShadow: "0 14px 28px rgba(2,6,23,0.22)",
              }}
            >
              {badge}
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          left: 48,
          right: 48,
          bottom: 42,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div
          style={{
            color: "#94A3B8",
            fontFamily: spaceGrotesk,
            fontSize: 24,
            fontWeight: 600,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
          }}
        >
          beginner-friendly product ad
        </div>
        <div
          style={{
            padding: "16px 24px",
            borderRadius: 999,
            background: "rgba(255,255,255,0.08)",
            color: "#F8FAFC",
            fontFamily: spaceGrotesk,
            fontSize: 28,
            fontWeight: 700,
          }}
        >
          {cta}
        </div>
      </div>

      <ProgressRail progress={frame / Math.max(1, totalFrames - 1)} />
    </AbsoluteFill>
  );
};

export const DroneTikTokVertical: React.FC<DroneTikTokVerticalProps> = ({
  productName,
  cta,
  scenes,
  captions,
  audio,
}) => {
  const { fps, durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#020617" }}>
      {audio?.musicSrc ? (
        <Audio src={resolveAsset(audio.musicSrc)} volume={audio.musicVolume ?? 0.16} />
      ) : null}
      {audio?.narrationSrc ? (
        <Audio src={resolveAsset(audio.narrationSrc)} volume={audio.narrationVolume ?? 1} />
      ) : null}

      {scenes.map((scene) => (
        <SceneLayer
          key={scene.id}
          scene={scene}
          productName={productName}
          cta={cta}
          totalFrames={durationInFrames}
        />
      ))}

      {captions.map((caption, index) => (
        <CaptionBand key={`${caption.text}-${index}`} caption={caption} />
      ))}
    </AbsoluteFill>
  );
};
