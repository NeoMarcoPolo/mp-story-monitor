export type StoryMeta = {
    title: string;
    logline?: string;
    genre?: string;
    visual_style?: string;
    thematic_tags?: string[];
    cinema_style_tags?: string[];
};

export type SceneBlock = {
    method: string;
    video_file: string;
    chapter_name?: string;
    scene_name?: string;
    scene_index?: string;
    has_audio?: boolean;
    workflow?: string;
    prompt?: string;
    keyframe_file?: string;
    // Chapter-level metadata
    chapter_intent?: string;
    chapter_who?: string;
    chapter_where?: string;
    chapter_when?: string;
    chapter_what?: string;
    // Scene-level metadata
    narrative_beat?: string;
    emotional_state?: string;
    visual_requirement?: string;
    character_state?: Record<string, string>;
    must_show?: string[];
    dialogue_density?: string;
};

export type TimelinesInputProps = {
    story_id: string;
    story_meta?: StoryMeta;
    methods: Record<string, SceneBlock[]>;
};

export const defaultInputProps: TimelinesInputProps = {
    story_id: "preview_default",
    methods: {},
};
