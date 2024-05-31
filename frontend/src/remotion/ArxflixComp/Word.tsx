import { Easing } from 'remotion';
import { interpolate } from 'remotion';
import React from 'react';
import { SubtitleItem } from 'parse-srt';
// import katex from 'katex';
import { InlineMath } from 'react-katex';
// import { makeTransform, translateY, translate } from "@remotion/animation-utils";

export const Word: React.FC<{
	item: SubtitleItem;
	frame: number;
}> = ({ item, frame, }) => {
	// if bold: *word* then use BoldWord
	// else use ClassicalWord
	if (item.text.startsWith('*') && item.text.endsWith('*')) {
		return <BoldWord stroke={true} item={item} frame={frame} />;
	} else if (item.text.startsWith('$') && item.text.endsWith('$')) {
		return <LatexWord stroke={true} item={item} frame={frame} />;
	}
	else {
		return <ClassicalWord stroke={true} item={item} frame={frame} />;
	}
}

export const ClassicalWord: React.FC<{
	item: SubtitleItem;
	frame: number;
	stroke?: boolean;
}> = ({ item, frame, stroke = true }) => {
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
				display: 'inline-block',
				opacity,
				translate: `0 ${shiftY}em`,
				paintOrder: 'stroke fill',
			}}
			className="text-black"
		>
			{item.text}
		</span>
	);
};


export const BoldWord: React.FC<{
	item: SubtitleItem;
	frame: number;
	stroke?: boolean;
}> = ({ item, frame, stroke=false }) => {
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
				display: 'inline-block',
				opacity,
				translate: `0 ${shiftY}em`,
				color: "blue",
				fontWeight: 'bold',
				WebkitTextStroke: stroke ? '15px black' : undefined,
				stroke: stroke ? '15px black' : undefined,
				paintOrder: 'stroke fill',
			}}
		>
			{item.text.slice(1, -1)}
		</span>
	);
};

export const LatexWord: React.FC<{
	item: SubtitleItem;
	frame: number;
	stroke?: boolean;
}> = ({ item, frame, stroke=false }) => {
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

	// return (
	// 	<span
	// 		style={{
	// 			display: 'inline-block',
	// 			opacity,
	// 			translate: `0 ${shiftY}em`,
	// 		}}
	// 		dangerouslySetInnerHTML={{ __html: katex.renderToString(item.text.slice(1, -1)) }}
	// 	/>
	// );

	// Using InlineMath
	return (
		<span style={{
			display: 'inline-block',
			opacity,
			translate: `0 ${shiftY}em`,
			WebkitTextStroke: stroke ? '15px black' : undefined,
			stroke: stroke ? '15px black' : undefined,
			paintOrder: 'stroke fill',
		}}>
			<InlineMath math={item.text.slice(1, -1)} />
		</span>
	);
}