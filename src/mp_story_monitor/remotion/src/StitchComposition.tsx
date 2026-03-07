import React from 'react';
import {
    AbsoluteFill,
    Series,
    Video,
    staticFile,
    useCurrentFrame,
} from 'remotion';
import { SceneBlock } from './types';

const SCENE_DURATION_FRAMES = 120; // 4 seconds at 30 fps

// ─── Scene Label Overlay (minimal, top-left) ────────────────────────────────

const SceneLabel: React.FC<{ scene: SceneBlock; sceneIdx: number; totalScenes: number }> = ({
    scene,
    sceneIdx,
    totalScenes,
}) => {
    return (
        <div
            style={{
                position: 'absolute',
                top: '16px',
                left: '16px',
                zIndex: 2,
                fontFamily: 'monospace',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                background: 'rgba(0,0,0,0.6)',
                padding: '6px 14px',
                borderRadius: '6px',
            }}
        >
            <span style={{ color: '#00ecff', fontSize: '16px', fontWeight: 'bold' }}>
                {scene.chapter_name
                    ? `${scene.chapter_name} — ${scene.scene_name ?? `S${sceneIdx}`}`
                    : scene.scene_index ?? `Scene ${sceneIdx + 1}`}
            </span>
            <span style={{ color: '#666', fontSize: '13px' }}>
                {sceneIdx + 1}/{totalScenes}
            </span>
        </div>
    );
};

// ─── Main Composition ────────────────────────────────────────────────────────

export const StitchComposition: React.FC<{
    method: string;
    scenes: SceneBlock[];
}> = ({ method, scenes }) => {
    const frame = useCurrentFrame();
    const totalFrames = scenes.length * SCENE_DURATION_FRAMES;

    const clampedFrame = Math.min(frame, totalFrames > 0 ? totalFrames - 1 : 0);
    const sceneIdx = Math.min(
        Math.floor(clampedFrame / SCENE_DURATION_FRAMES),
        Math.max(scenes.length - 1, 0),
    );
    const currentScene = scenes[sceneIdx];

    if (!currentScene) {
        return (
            <AbsoluteFill
                style={{
                    backgroundColor: '#000',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <h1 style={{ color: '#888', fontFamily: 'monospace' }}>
                    No scenes for {method}
                </h1>
            </AbsoluteFill>
        );
    }

    return (
        <AbsoluteFill style={{ backgroundColor: '#000' }}>
            <Series>
                {scenes.map((s, idx) => (
                    <Series.Sequence
                        key={`${method}-${idx}`}
                        durationInFrames={SCENE_DURATION_FRAMES}
                        name={
                            s.scene_index
                                ? `${s.scene_index}${s.chapter_name ? ` — ${s.chapter_name}` : ''}`
                                : `Scene ${idx + 1}`
                        }
                    >
                        <AbsoluteFill>
                            <Video
                                src={staticFile(s.video_file)}
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'contain',
                                }}
                            />
                        </AbsoluteFill>
                    </Series.Sequence>
                ))}
            </Series>

            {/* Minimal label overlay */}
            <SceneLabel
                scene={currentScene}
                sceneIdx={sceneIdx}
                totalScenes={scenes.length}
            />
        </AbsoluteFill>
    );
};
