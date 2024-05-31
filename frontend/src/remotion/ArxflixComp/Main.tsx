import React, { useEffect, useRef, useState } from 'react';
import {
	AbsoluteFill,
	Audio,
	continueRender,
	delayRender,
	Sequence,
	useVideoConfig,
} from 'remotion';
import { z } from 'zod';
import { zColor } from '@remotion/zod-types';
import { PaginatedSubtitles } from './Subtitles';
import { AudioViz } from './AudioViz';
import { CurrentFigure, RichContent } from './RichContent';
import { loadFont, fontFamily } from "@remotion/google-fonts/Inter";

loadFont();

export const ArxflixSchema = z.object({
	durationInSeconds: z.number().positive(),
	audioOffsetInSeconds: z.number().min(0),
	subtitlesFileName: z.string().refine((s) => s.endsWith('.srt'), {
		message: 'Subtitles file must be a .srt file',
	}),
	audioFileName: z.string().refine((s) => s.endsWith('.mp3'), {
		message: 'Audio file must be a .mp3 file',
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
});

export type ArxflixCompositionSchemaType = z.infer<typeof ArxflixSchema>;

export const ArxflixComposition: React.FC<ArxflixCompositionSchemaType> = ({
	subtitlesFileName,
	audioFileName,
	richContentFileName,
	subtitlesLinePerPage,
	waveColor,
	waveNumberOfSamples,
	waveFreqRangeStartIndex,
	waveLinesToDisplay,
	subtitlesZoomMeasurerSize,
	subtitlesLineHeight,
	onlyDisplayCurrentSentence,
	mirrorWave,
	audioOffsetInSeconds,
}) => {
	const { durationInFrames, fps } = useVideoConfig();

	const [handle] = useState(() => delayRender());
	const [subtitles, setSubtitles] = useState<string | null>(null);
	const [richContent, setRichContent] = useState<RichContent[]>([]);
	const ref = useRef<HTMLDivElement>(null);

	useEffect(() => {
		fetch(subtitlesFileName)
			.then((res) => res.text())
			.then((text) => {
				setSubtitles(text);
				continueRender(handle);
			})
			.catch((err) => {
				console.log('Error fetching subtitles', err);
			});
	}, [handle, subtitlesFileName]);

	useEffect(() => {
		fetch(richContentFileName)
			.then((res) => res.json())
			.then((data) => {
				setRichContent(data);
				continueRender(handle);
			})
			.catch((err) => {
				console.log('Error fetching rich content', err);
			});
	}, [handle, richContentFileName]);

	if (!subtitles) {
		return null;
	}

	const figures: RichContent[] = [];
	const audioOffsetInFrames = Math.round(audioOffsetInSeconds * fps);

	return (
		<div ref={ref}>
			<AbsoluteFill>
				<Sequence from={-audioOffsetInFrames}>
					<Audio src={audioFileName} />

					<div
						className="grid grid-cols-1 grid-rows-5 w-full h-full text-white p-5 bg-orange-50"
						style={{
							fontFamily
						}}
					>
						<div className="row-span-3 flex justify-center items-center">
							<CurrentFigure
								richContent={richContent}
								transitionFrames={2}
								key={figures.map((f) => f.content).join('')}
							/>
						</div>
						
						<div className='row-span-1'>
							<div
								style={{ lineHeight: `${subtitlesLineHeight}px` }}
								className="font-semibold text-7xl pt-24"
							>
								<PaginatedSubtitles
									subtitles={subtitles}
									startFrame={audioOffsetInFrames}
									endFrame={audioOffsetInFrames + durationInFrames}
									linesPerPage={subtitlesLinePerPage}
									subtitlesZoomMeasurerSize={subtitlesZoomMeasurerSize}
									subtitlesLineHeight={subtitlesLineHeight}
									onlyDisplayCurrentSentence={onlyDisplayCurrentSentence}
								/>
							</div>
						</div>
						<div className='row-span-1 max-h-[100px] content-end self-end'>
							<AudioViz
								audioSrc={audioFileName}
								mirrorWave={mirrorWave}
								waveColor={waveColor}
								numberOfSamples={Number(waveNumberOfSamples)}
								freqRangeStartIndex={waveFreqRangeStartIndex}
								waveLinesToDisplay={waveLinesToDisplay}
								vizType='customWaveform'
							/>
						</div>
					</div>
				</Sequence>
			</AbsoluteFill>
		</div>
	);
};
