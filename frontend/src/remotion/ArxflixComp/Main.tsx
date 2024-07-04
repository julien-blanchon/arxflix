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


export const ArxflixComposition: React.FC<CompositionPropsType> = ({
	introFileName,
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
		fetch(introFileName)
			.then((res) => res.text())
			.then((text) => {
				const [title, figure] = text.split('\n');
				setIntroData({
					title,
					figure,
				});
				continueRender(handle);
			})
			.catch((err) => {
				console.log('Error fetching intro', err);
			});
	}, [handle, introFileName]);

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

	if (!subtitles || !richContent || !introData) {
		return null;
	}

	const figures: RichContent[] = [];
	// Introduction takes 2 seconds at the beginning
	const introductionDurationInSeconds = Math.round(2 * fps);
	// Outro takes 5 seconds at the end
	const outroDurationInSeconds = Math.round(5 * fps);
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
						<div className="row-span-3 flex justify-center items-center relative"
						>
							<Img className="object-fill min-h-[500px] max-h-[650px]" src={introData.figure} />
							<div className="text-7xl text-black absolute top-0 right-0 justify-center items-center flex flex-col gap-5 p-5 will-change-transform transform-gpu"
								style={{ transform: `scale(${spring({ fps, frame, })}` }}
							>
								<div>
									Voice by
								</div>
								<div className="flex justify-center items-center max-h-40">
									<Img className="object-cover max-h-[150px]"
										src={staticFile("static/LMNT_Logo_Full.png")} />
								</div>
							</div>
						</div>

						<div className='row-span-3'>
							<div
								style={{
									lineHeight: `${subtitlesLineHeight}px`,
								}}
								className="font-semibold text-8xl pt-24 text-black text-center"
							>
								{introData.title}
							</div>
						</div>
					</div>
				</Sequence>
				<Sequence from={introductionDurationInSeconds} durationInFrames={durationInFrames - introductionDurationInSeconds - outroDurationInSeconds}>
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
				<Sequence from={durationInFrames - outroDurationInSeconds} durationInFrames={outroDurationInSeconds}>
					<div
						className="grid grid-cols-1 grid-rows-5 w-full h-full text-white p-5 bg-orange-50"
						style={{
							fontFamily
						}}
					>
						<Audio src={staticFile("static/LMNT.wav")} />
						<div className="row-span-3 h-full justify-center items-center flex">
							<div className="grid grid-cols-3 gap-20 self-center h-[600px] p-28">
								<Img className="object-fill self-center scale-110" src={staticFile("static/LMNT_Logo_Full.png")} />
								<div className="bg-transparent border-2 border-black rounded-3xl self-center h-full w-full"></div>
								<div className="bg-transparent border-2 border-black rounded-3xl self-center h-full w-full"></div>

							</div>
						</div>

						<div className='row-span-2 h-full flex w-full'>
							<div
								className="font-bold text-7xl text-black text-center self-end w-full pb-28"
							>
								Thank LMNT for supporting this channel !
							</div>
						</div>
					</div>
				</Sequence>
			</AbsoluteFill>
		</div>
	);
};

export const calculateMetadata: CalculateMetadataFunction<
	CompositionPropsType
> = async ({ props }) => {
	if (props.duration) {
		return {
			durationInFrames: props.duration,
			fps: VIDEO_FPS,
		};
	}
	const duration = await getAudioDurationInSeconds(props.audioFileName);
	const audioDurationInFrame = Math.floor(duration * VIDEO_FPS)
	
	return {
		durationInFrames: audioDurationInFrame,
		fps: VIDEO_FPS,
	};
};