import { AbsoluteFill, Series, Video } from 'remotion';
import { TimelinesInputProps } from './types';

// Assuming each method generates scenes of average ~4 seconds for visualization purposes natively.
// If exact frame durations are needed, they should be extracted dynamically via @remotion/media-utils or passed in JSON.
const SCENE_DURATION_FRAMES = 120; // 4 seconds at 30 fps

export const StitchComposition: React.FC<TimelinesInputProps> = ({ methods }) => {
    return (
        <AbsoluteFill style={{ backgroundColor: '#111', display: 'flex', flexDirection: 'column' }}>
            <h1 style={{ color: 'white', textAlign: 'center', fontFamily: 'monospace' }}>Story Stitch Timeline</h1>

            <div style={{ display: 'flex', flex: 1, padding: '20px', gap: '20px' }}>
                {Object.entries(methods).map(([method, scenes], i) => (
                    <div key={method} style={{ flex: 1, border: '1px solid #333', background: '#222', padding: '10px' }}>
                        <h2 style={{ color: '#00ecff', margin: 0, paddingBottom: '10px', textTransform: 'uppercase' }}>{method}</h2>
                        <div style={{ height: '300px', width: '100%', position: 'relative' }}>
                            <Series>
                                {scenes.map((scene, idx) => (
                                    <Series.Sequence key={idx} durationInFrames={SCENE_DURATION_FRAMES}>
                                        <AbsoluteFill>
                                            {/* Instead of loading local file explicitly which remotion might block, we assume they are served statically or pass valid file:/// paths */}
                                            <Video src={scene.video_file} />
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
