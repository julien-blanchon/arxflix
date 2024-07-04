import { Easing } from 'remotion';
import { interpolate } from 'remotion';
import React from 'react';
import { SubtitleItem } from 'parse-srt';
import { InlineMath } from 'react-katex';

export const Word: React.FC<{
	item: SubtitleItem;
	frame: number;
}> = ({ item, frame, }) => {
	if (item.text.startsWith('*') && item.text.endsWith('*')) {
		return <BoldWord stroke={true} item={item} frame={frame} />;
	} else if (item.text.startsWith('$') && item.text.endsWith('$')) {
		return <LatexWord stroke={true} item={item} frame={frame} />;
	} else {
		return <ClassicalWord item={item} frame={frame} />;
	}
}

export const ClassicalWord: React.FC<{
	item: SubtitleItem;
	frame: number;
}> = ({ item, frame }) => {
	const opacity = interpolate(frame, [item.start, item.start + 15], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const shiftY = interpolate(
		frame,
		[item.start, item.start + 10],
		[0.25, 0],
		{
			easing: Easing.out(Easing.quad),
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		},
	);

	return (
		<span
			style={{
				opacity,
				translate: `0 ${shiftY}em`,
				paintOrder: 'stroke fill',
			}}
			className="text-black inline-block will-change-transform transform-gpu"
		>
			{item.text}
		</span>
	);
};


export const BoldWord: React.FC<{
	item: SubtitleItem;
	frame: number;
	stroke?: boolean;
}> = ({ item, frame, stroke = false }) => {
	const opacity = interpolate(frame, [item.start, item.start + 15], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const shiftY = interpolate(
		frame,
		[item.start, item.start + 10],
		[0.25, 0],
		{
			easing: Easing.out(Easing.quad),
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		},
	);

	return (
		<span
			style={{
				opacity,
				translate: `0 ${shiftY}em`,
				WebkitTextStroke: stroke ? '15px black' : undefined,
				stroke: stroke ? '15px black' : undefined,
				paintOrder: 'stroke fill',
			}}
			className="text-blue-400 inline-block will-change-transform transform-gpu font-bold"
		>
			{item.text.slice(1, -1)}
		</span>
	);
};

export const LatexWord: React.FC<{
	item: SubtitleItem;
	frame: number;
	stroke?: boolean;
}> = ({ item, frame, stroke = false }) => {
	const opacity = interpolate(frame, [item.start, item.start + 15], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	const shiftY = interpolate(
		frame,
		[item.start, item.start + 10],
		[0.25, 0],
		{
			easing: Easing.out(Easing.quad),
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		},
	);

	return (
		<span
			style={{
				opacity,
				translate: `0 ${shiftY}em`,
				WebkitTextStroke: stroke ? '15px black' : undefined,
				stroke: stroke ? '15px black' : undefined,
				paintOrder: 'stroke fill',
			}}
			className="text-black inline-block will-change-transform transform-gpu font-bold"
		>
			<InlineMath math={item.text.slice(1, -1)} />
		</span>
	);
}