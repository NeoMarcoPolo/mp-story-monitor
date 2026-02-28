import React from 'react';
import { Composition } from 'remotion';
import { StitchComposition } from './StitchComposition';
import { defaultInputProps } from './types';

const FPS = 30;
const SCENE_DURATION_FRAMES = 120; // 4 seconds per scene

// Default to 60s; the component fetches actual data at runtime
// and the Studio allows scrubbing beyond this if needed.
const DEFAULT_DURATION_FRAMES = FPS * 60;

export const RemotionRoot: React.FC = () => {
    return (
        <>
            <Composition
                id="StitchPreview"
                component={StitchComposition}
                durationInFrames={DEFAULT_DURATION_FRAMES}
                fps={FPS}
                width={1920}
                height={1080}
                defaultProps={defaultInputProps}
            />
        </>
    );
};
