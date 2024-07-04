import parseSRT, { SubtitleItem } from 'parse-srt';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { makeTransform, translateY } from "@remotion/animation-utils";
import {
	continueRender,
	delayRender,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import { Word } from './Word';

const useWindowedFrameSubs = (
	src: string,
	options: { windowStart: number; windowEnd: number },
) => {
	const { windowStart, windowEnd } = options;
	const config = useVideoConfig();
	const { fps } = config;

	const parsed = useMemo(() => parseSRT(src), [src]);

	return useMemo(() => {
		return parsed
			.map((item) => {
				const start = Math.floor(item.start * fps);
				const end = Math.floor(item.end * fps);
				return { item, start, end };
			})
			.filter(({ start }) => {
				return start >= windowStart && start <= windowEnd;
			})
			.map<SubtitleItem>(({ item, start, end }) => {
				return {
					...item,
					start,
					end,
				};
			}, []);
	}, [fps, parsed, windowEnd, windowStart]);
};

export const PaginatedSubtitles: React.FC<{
	subtitles: string;
	startFrame: number;
	endFrame: number;
	linesPerPage: number;
	subtitlesZoomMeasurerSize: number;
	subtitlesLineHeight: number;
	onlyDisplayCurrentSentence: boolean;
}> = ({
	startFrame,
	endFrame,
	subtitles,
	linesPerPage,
	subtitlesZoomMeasurerSize,
	subtitlesLineHeight,
	onlyDisplayCurrentSentence,
}) => {
		const frame = useCurrentFrame();
		const windowRef = useRef<HTMLDivElement>(null);
		const zoomMeasurer = useRef<HTMLDivElement>(null);
		const [handle] = useState(() => delayRender());
		const windowedFrameSubs = useWindowedFrameSubs(subtitles, {
			windowStart: startFrame,
			windowEnd: endFrame,
		});
		const [lineOffset, setLineOffset] = useState(0);
		const currentAndFollowingSentences = useMemo(() => {
			// If we don't want to only display the current sentence, return all the words
			if (!onlyDisplayCurrentSentence) return windowedFrameSubs;

			const indexOfCurrentSentence =
				windowedFrameSubs.findLastIndex((w, i) => {
					const nextWord = windowedFrameSubs[i + 1];

					return (
						nextWord &&
						(w.text.endsWith('?') ||
							w.text.endsWith('.') ||
							w.text.endsWith('!')) &&
						nextWord.start < frame
					);
				}) + 1;
			return windowedFrameSubs.slice(indexOfCurrentSentence)
		}, [frame, onlyDisplayCurrentSentence, windowedFrameSubs]);

		const currentAndFollowingSentencesFix = useMemo(() => {
			// If the last element end is ended for 20 frames, return an empty array
			if (currentAndFollowingSentences.length === 0) return [];
			const lastElement = currentAndFollowingSentences[currentAndFollowingSentences.length - 1];
			if (lastElement.end + 100 < frame) return [];
			return currentAndFollowingSentences;
		}, [currentAndFollowingSentences, frame]);

		useEffect(() => {
			const zoom =
				(zoomMeasurer.current?.getBoundingClientRect().height as number) /
				subtitlesZoomMeasurerSize;
			const linesRendered =
				(windowRef.current?.getBoundingClientRect().height as number) /
				(subtitlesLineHeight * zoom);
			const linesToOffset = Math.max(0, linesRendered - linesPerPage);
			setLineOffset(linesToOffset);
			continueRender(handle);
		}, [
			frame,
			handle,
			linesPerPage,
			subtitlesLineHeight,
			subtitlesZoomMeasurerSize,
		]);

		const currentFrameSentences = useMemo(() => {
			return currentAndFollowingSentencesFix.filter((word) => {
				return word.start < frame;
			});
		}, [currentAndFollowingSentencesFix, frame]);
		// const currentFrameSentences = currentAndFollowingSentencesFix.filter((word) => {
		// 	return word.start < frame;
		// });

		return (
			<div
				className="relative overflow-hidden px-10"
			>
				<div
					ref={windowRef}
					style={{
						transform: makeTransform([translateY(-lineOffset * subtitlesLineHeight)]),
					}}
				>
					{currentFrameSentences.map((item) => (
						<span key={item.id} id={String(item.id)}>
							{
								// If don't start with a - or a space, add a space
								item.text.startsWith('-') || item.text.startsWith(' ')
									? ''
									: ' '
							}
							<Word
								frame={frame}
								item={item}
							/>
						</span>
					))}
				</div>
				<div
					ref={zoomMeasurer}
					style={{
						height: subtitlesZoomMeasurerSize,
						width: subtitlesZoomMeasurerSize,
					}}
				/>
			</div>
		);
	};

declare global {
	interface Array<T> {
		findLastIndex(
			predicate: (value: T, index: number, obj: T[]) => unknown,
			thisArg?: unknown,
		): number;
	}
}
