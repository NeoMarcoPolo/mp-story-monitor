import React, { useCallback, useEffect, useState } from 'react';
import { Composition, delayRender, continueRender } from 'remotion';
import { StitchComposition } from './StitchComposition';
import { defaultInputProps, TimelinesInputProps } from './types';

const FPS = 30;
const SCENE_DURATION_FRAMES = 120; // 4 seconds per scene

export const RemotionRoot: React.FC = () => {
    const [handle] = useState(() => delayRender('Loading remotion_input.json'));
    const [data, setData] = useState<TimelinesInputProps | null>(null);

    const load = useCallback(async () => {
        try {
            const res = await fetch(
                new URL('/public/remotion_input.json', window.location.origin).href,
            );
            if (res.ok) {
                const json: TimelinesInputProps = await res.json();
                setData(json);
            } else {
                setData(defaultInputProps);
            }
        } catch {
            setData(defaultInputProps);
        }
        continueRender(handle);
    }, [handle]);

    useEffect(() => {
        load();
    }, [load]);

    if (!data) return null;

    const methodEntries = Object.entries(data.methods);

    // If no methods exist, register a single placeholder composition
    if (methodEntries.length === 0) {
        return (
            <Composition
                id="StitchPreview"
                component={StitchComposition}
                fps={FPS}
                width={1920}
                height={1080}
                durationInFrames={SCENE_DURATION_FRAMES}
                defaultProps={{ method: 'none', scenes: [] }}
            />
        );
    }

    return (
        <>
            {methodEntries.map(([method, scenes]) => {
                const duration = Math.max(
                    scenes.length * SCENE_DURATION_FRAMES,
                    SCENE_DURATION_FRAMES,
                );
                return (
                    <Composition
                        key={method}
                        id={method}
                        component={StitchComposition}
                        fps={FPS}
                        width={1920}
                        height={1080}
                        durationInFrames={duration}
                        defaultProps={{ method, scenes }}
                    />
                );
            })}
        </>
    );
};
