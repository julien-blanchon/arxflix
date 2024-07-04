import React, { useEffect } from 'react';
import {
	Img,
	interpolate,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import { InlineMath } from 'react-katex';
import { preloadImage } from "@remotion/preload";

export type RichContent = {
	type: 'figure' | 'headline' | 'equation';
	content: string;
	start: number;
	end: number;
};

export const CurrentFigure: React.FC<{
	richContent: RichContent[];
	transitionFrames?: number;
}> = ({ richContent = [], transitionFrames = 10 }) => {
	const frame = useCurrentFrame();
	const config = useVideoConfig();
	const { fps } = config;

	// useEffect(() => {
	// 	richContent.forEach((f) => {
	// 		if (f.type === 'figure') {
	// 			preloadImage(f.content);
	// 		}
	// 	});
	// }, [richContent]);

	const currentFigure = richContent.find((f) => frame >= (f.start * fps) && frame <= (f.end * fps));
	if (!currentFigure) {
		return null;
	}



	const currentFigureDurationInFrame = (currentFigure.end * fps) - (currentFigure.start * fps);

	const scale = interpolate(frame - (currentFigure.start * fps), [0, transitionFrames, currentFigureDurationInFrame - transitionFrames, currentFigureDurationInFrame], [0.5, 1, 1, 0.5], {
		extrapolateRight: 'clamp',
	});
	const opacity = interpolate(frame - (currentFigure.start * fps), [0, transitionFrames, currentFigureDurationInFrame - transitionFrames, currentFigureDurationInFrame], [0, 1, 1, 0], {
		extrapolateRight: 'clamp',
	});

	const styleCombined = {
		transform: `scale(${scale})`,
		opacity,
	};

	if (!currentFigure) {
		return null;
	}
	if (currentFigure.type === 'headline') {
		return (
			<div className="text-8xl font-semibold text-black text-center" style={styleCombined}>
				{currentFigure.content}
			</div>
		);
	} else if (currentFigure.type === 'figure') {
		return <div className="flex w-full justify-center items-center">
			<Img className="object-fill min-h-[500px] max-h-[650px]" style={styleCombined} src={currentFigure.content} />
		</div>;
	} else if (currentFigure.type === 'equation') {
		return (
			<div className="text-5xl font-semibold text-black text-center" style={styleCombined}>
				<InlineMath math={currentFigure.content} />
			</div>
		);
	}
}
