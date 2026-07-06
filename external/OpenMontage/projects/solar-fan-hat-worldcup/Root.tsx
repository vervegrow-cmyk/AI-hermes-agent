import { Composition } from "remotion";
import { Scene, calculateMetadata, SceneProps } from "./Composition";

export const Root: React.FC = () => (
  <Composition
    id="SolarFanHatWorldcup"
    component={Scene}
    durationInFrames={30 * 30}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={ { /* fill from artifacts/props.json at render time */ } as SceneProps }
    calculateMetadata={calculateMetadata}
  />
);
