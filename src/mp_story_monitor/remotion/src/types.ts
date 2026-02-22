export type SceneBlock = {
    method: string;
    video_file: string;
};

export type TimelinesInputProps = {
    story_id: string;
    methods: Record<string, SceneBlock[]>;
};

export const defaultInputProps: TimelinesInputProps = {
    story_id: "preview_default",
    methods: {}
};
