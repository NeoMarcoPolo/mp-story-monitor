import React, { useCallback, useEffect, useState } from 'react';
import {
    AbsoluteFill,
    Series,
    Video,
    staticFile,
    delayRender,
    continueRender,
} from 'remotion';
import { TimelinesInputProps } from './types';

const SCENE_DURATION_FRAMES = 120; // 4 seconds at 30 fps

export const StitchComposition: React.FC<TimelinesInputProps> = (fallbackProps) => {
    const [handle] = useState(() => delayRender());
    const [data, setData] = useState<TimelinesInputProps | null>(null);

    const load = useCallback(async () => {
        try {
            const res = await fetch(staticFile('remotion_input.json'));
            if (res.ok) {
                const json: TimelinesInputProps = await res.json();
                setData(json);
            } else {
                // Fall back to default props passed from Root.tsx
                setData(fallbackProps);
            }
        } catch {
            setData(fallbackProps);
        }
        continueRender(handle);
    }, [handle, fallbackProps]);

    useEffect(() => {
        load();
    }, [load]);

    if (!data) return null;

    const { methods } = data;
    const methodEntries = Object.entries(methods);

    if (methodEntries.length === 0) {
        return (
            <AbsoluteFill style={{ backgroundColor: '#111', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <h1 style={{ color: '#888', fontFamily: 'monospace' }}>No methods found in remotion_input.json</h1>
            </AbsoluteFill>
        );
    }

    return (
        <AbsoluteFill style={{ backgroundColor: '#111', display: 'flex', flexDirection: 'column' }}>
            <h1 style={{ color: 'white', textAlign: 'center', fontFamily: 'monospace' }}>
                Story Stitch Timeline — {data.story_id}
            </h1>

            <div style={{ display: 'flex', flex: 1, padding: '20px', gap: '20px' }}>
                {methodEntries.map(([method, scenes]) => (
                    <div key={method} style={{ flex: 1, border: '1px solid #333', background: '#222', padding: '10px' }}>
                        <h2 style={{ color: '#00ecff', margin: 0, paddingBottom: '10px', textTransform: 'uppercase' }}>
                            {method}
                        </h2>
                        <div style={{ height: '300px', width: '100%', position: 'relative' }}>
                            <Series>
                                {scenes.map((scene, idx) => (
                                    <Series.Sequence key={idx} durationInFrames={SCENE_DURATION_FRAMES}>
                                        <AbsoluteFill>
                                            <Video
                                                src={staticFile(scene.video_file)}
                                                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                            />
                                        </AbsoluteFill>
                                    </Series.Sequence>
                                ))}
                            </Series>
                        </div>
                        <div style={{ color: '#888', marginTop: '10px' }}>{scenes.length} Scenes</div>
                    </div>
                ))}
            </div>
        </AbsoluteFill>
    );
};
