import React from 'react';
import { Composition } from 'remotion';
import { StitchComposition } from './StitchComposition';
import { defaultInputProps } from './types';

// The root registers the main compositions for the Studio.
export const RemotionRoot: React.FC = () => {
    return (
        <>
            <Composition
                id="StitchPreview"
                component={StitchComposition}
                durationInFrames={1200} // This is just an arbitrary default duration for preview
                fps={30}
                width={1920}
                height={1080}
                defaultProps={defaultInputProps}
            />
        </>
    );
};
