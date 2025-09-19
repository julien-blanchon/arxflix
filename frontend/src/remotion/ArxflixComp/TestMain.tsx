import React, { useEffect, useRef, useState } from 'react';
import {
	AbsoluteFill,
	Audio,
	continueRender,
	delayRender,
	Img,
	Sequence,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import { z } from 'zod';
import { zColor } from '@remotion/zod-types';
import { PaginatedSubtitles } from './Subtitles';
import { AudioViz } from './AudioViz';
import { CurrentFigure, RichContent } from './RichContent';
import { loadFont, fontFamily } from "@remotion/google-fonts/Inter";
import { CalculateMetadataFunction } from "remotion";
import { getAudioDurationInSeconds } from '@remotion/media-utils';
import { VIDEO_FPS, CompositionPropsType } from '../../types/constants';

loadFont();

// Embedded test data to bypass file loading issues
const TEST_RICH_CONTENT: RichContent[] = [
	{
		type: "headline",
		content: "FastAPI Tutorial: Building REST APIs",
		start: 0.0,
		end: 3.0
	},
	{
		type: "codesnippet",
		content: "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\ndef read_root():\n    return {\"Hello\": \"World\"}",
		language: "python",
		start: 3.0,
		end: 10.0
	},
	{
		type: "headline",
		content: "Key Features Demonstrated",
		start: 10.0,
		end: 13.0
	}
];

const TEST_SUBTITLES = `1
00:00:00,000 --> 00:00:03,000
Welcome to our FastAPI tutorial

2
00:00:03,000 --> 00:00:10,000
Let's start with a basic FastAPI application

3
00:00:10,000 --> 00:00:13,000
This demonstrates the key features of FastAPI`;

export const TestArxflixComposition: React.FC<CompositionPropsType> = ({
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
}) => {
	const { durationInFrames, fps } = useVideoConfig();
	const frame = useCurrentFrame();
	const [handle] = useState(() => delayRender());
	const [subtitles, setSubtitles] = useState<string | null>(null);
	const [introData, setIntroData] = useState<{ title: string; figure: string } | null>(null);
	const [richContent, setRichContent] = useState<RichContent[]>([]);
	const ref = useRef<HTMLDivElement>(null);

	useEffect(() => {
		// Use embedded test data instead of fetching
		setSubtitles(TEST_SUBTITLES);
		setRichContent(TEST_RICH_CONTENT);
		
		const firstFigure = TEST_RICH_CONTENT.find((f) => f.type === 'figure')?.content || '';
		const firstHeadline = TEST_RICH_CONTENT.find((f) => f.type === 'headline')?.content || 'FastAPI Tutorial';
		
		setIntroData({
			title: firstHeadline,
			figure: firstFigure,
		});
		
		continueRender(handle);
	}, [handle]);

	if (!subtitles || !richContent || !introData) {
		return null;
	}

	const figures: RichContent[] = [];
	// Introduction takes 2 seconds at the beginning
	const introductionDurationInSeconds = Math.round(2 * fps);
	// No outro section needed
	const outroDurationInSeconds = 0;
	
	return (
		<div ref={ref}>
			<AbsoluteFill>
				<Sequence from={0} durationInFrames={introductionDurationInSeconds}>
					<div
						className="grid grid-cols-1 grid-rows-5 w-full h-full text-white p-16 bg-orange-50 "
						style={{
							fontFamily
						}}
					>
						<div className="row-span-3 flex justify-center items-center relative">
							{/* Show first headline as intro */}
							<div className="text-8xl font-semibold text-black text-center">
								{introData.title}
							</div>
						</div>

						<div className='row-span-3'>
							<div
								style={{
									lineHeight: `${subtitlesLineHeight}px`,
								}}
								className="font-semibold text-6xl pt-24 text-black text-center"
							>
								Code Snippet Demo
							</div>
						</div>
					</div>
				</Sequence>
				<Sequence from={introductionDurationInSeconds} durationInFrames={durationInFrames - introductionDurationInSeconds - outroDurationInSeconds}>
					{/* <Audio src={audioFileName} /> */}

					<div
						className="grid grid-cols-1 grid-rows-5 w-full h-full text-white p-5 bg-orange-50"
						style={{
							fontFamily
						}}
					>
						<div className="row-span-3 flex justify-center items-center">
							<CurrentFigure
								richContent={richContent}
								transitionFrames={5}
								key={figures.map((f) => f.content).join('')}
							/>
						</div>

						<div className='row-span-1'>
							<div
								style={{
									lineHeight: `${subtitlesLineHeight}px`,
								}}
								className="font-semibold text-7xl pt-24"
							>
								<PaginatedSubtitles
									subtitles={subtitles}
									startFrame={0}
									endFrame={durationInFrames - introductionDurationInSeconds}
									linesPerPage={subtitlesLinePerPage}
									subtitlesZoomMeasurerSize={subtitlesZoomMeasurerSize}
									subtitlesLineHeight={subtitlesLineHeight}
									onlyDisplayCurrentSentence={onlyDisplayCurrentSentence}
								/>
							</div>
						</div>
						<div className='row-span-1 max-h-[100px] content-end self-end'>
							{/* <AudioViz
								audioSrc={audioFileName}
								mirrorWave={mirrorWave}
								waveColor={waveColor}
								numberOfSamples={Number(waveNumberOfSamples)}
								freqRangeStartIndex={waveFreqRangeStartIndex}
								waveLinesToDisplay={waveLinesToDisplay}
								vizType='customWaveform'
							/> */}
						</div>
					</div>
				</Sequence>

			</AbsoluteFill>
		</div>
	);
};

export const calculateTestMetadata: CalculateMetadataFunction<
	CompositionPropsType
> = async ({ props }) => {
	if (props.duration) {
		return {
			durationInFrames: props.duration,
			fps: VIDEO_FPS,
		};
	}
	
	// Use a fixed duration for testing
	return {
		durationInFrames: 390, // 13 seconds at 30fps
		fps: VIDEO_FPS,
	};
};