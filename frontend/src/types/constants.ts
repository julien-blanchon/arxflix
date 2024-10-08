import { zColor } from "@remotion/zod-types";
import { staticFile } from "remotion";
import { z } from "zod";
export const COMP_NAME = "MyComp";

export const CompositionProps = z.object({
	audioOffsetInSeconds: z.number().min(0),
	subtitlesFileName: z.string().refine((s) => s.endsWith('.srt'), {
		message: 'Subtitles file must be a .srt file',
	}),
	audioFileName: z.string().refine((s) => s.endsWith('.mp3') || s.endsWith('.wav'), {
		message: 'Audio file must be a .mp3 or .wav file',
	}),
	richContentFileName: z.string().refine((s) => s.endsWith('.json'), {
		message: 'Rich content file must be a .json file',
	}),
	waveColor: zColor(),
	subtitlesLinePerPage: z.number().int().min(0),
	subtitlesLineHeight: z.number().int().min(0),
	subtitlesZoomMeasurerSize: z.number().int().min(0),
	onlyDisplayCurrentSentence: z.boolean(),
	mirrorWave: z.boolean(),
	waveLinesToDisplay: z.number().int().min(0),
	waveFreqRangeStartIndex: z.number().int().min(0),
	waveNumberOfSamples: z.enum(['32', '64', '128', '256', '512']),
	duration: z.optional(z.number().int().min(0)),
});

export type CompositionPropsType = z.infer<typeof CompositionProps>;

export const defaultCompositionProps: CompositionPropsType = {
    // Audio settings
    audioOffsetInSeconds: 0,

    // Title settings
    audioFileName: staticFile('1512.03385/audio.wav'),
    richContentFileName: staticFile('1512.03385/rich.json'),

    // Subtitles settings
    subtitlesFileName: staticFile('1512.03385/subtitles.srt'),
    onlyDisplayCurrentSentence: true,
    subtitlesLinePerPage: 2,
    subtitlesZoomMeasurerSize: 10,
    subtitlesLineHeight: 98,

    // Wave settings
    waveColor: '#a3a5ae',
    waveFreqRangeStartIndex: 5,
    waveLinesToDisplay: 300,
    waveNumberOfSamples: '512', // This is string for Remotion controls and will be converted to a number
    mirrorWave: false,
};

export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;
export const VIDEO_FPS = 30;
