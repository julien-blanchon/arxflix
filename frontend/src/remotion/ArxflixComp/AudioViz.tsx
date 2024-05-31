import { useAudioData, visualizeAudio } from '@remotion/media-utils';
import { linearPath } from "./waveform-path/waveform-path";
import React from 'react';
import {
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import { extendViewBox } from "@remotion/paths";

export const fps = 30;

export const AudioViz: React.FC<{
	waveColor: string;
	numberOfSamples: number;
	freqRangeStartIndex: number;
	waveLinesToDisplay: number;
	mirrorWave: boolean;
	audioSrc: string;
	vizType?: 'bars' | 'waveform' | 'circle' | 'radialBars' | 'customWaveform';
}> = ({
	waveColor,
	numberOfSamples,
	freqRangeStartIndex,
	waveLinesToDisplay,
	mirrorWave,
	audioSrc,
	vizType = 'customWaveform',
}) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();

	const audioData = useAudioData(audioSrc);

	if (!audioData) {
		return null;
	}

	const frequencyData = visualizeAudio({
		fps,
		frame,
		audioData,
		numberOfSamples,
	});

	const frequencyDataSubset = frequencyData.slice(
		freqRangeStartIndex,
		freqRangeStartIndex +
			(mirrorWave ? Math.round(waveLinesToDisplay / 2) : waveLinesToDisplay),
	);

	const frequenciesToDisplay = mirrorWave
		? [...frequencyDataSubset.slice(1).reverse(), ...frequencyDataSubset]
		: frequencyDataSubset;

	const pathLogo = linearPath(frequenciesToDisplay, {
		type: 'steps',
		paths: [
			{d:'V', sy: 0, x: 50, ey: 100 }
		],
		height: 75,
		normalizeFactor: 40,
	});

	// const pathLogo = polarPath(frequenciesToDisplay, {
	// 	type: 'bars',
  //   left: 200, top: 50, distance: 30, length: 1000,
  //   paths: [
	// 		{d: 'L', sdeg:50, sr:0, edeg: 50, er:100 },
  //   ]
	// });

	const barViz = (
		<div className="flex flex-row h-48 items-center justify-center gap-2 mt-12">
			{frequenciesToDisplay.map((v, i) => (
				<div
					key={i}
					className="w-3 border rounded-lg"
					style={{
						minWidth: '1px',
						backgroundColor: waveColor,
						height: `${500 * Math.sqrt(v)}%`,
					}}
				/>
			))}
		</div>
	);

	const waveformViz = (
		<svg className="css-audio-viz" viewBox={extendViewBox("0 0 500 100", 1)} preserveAspectRatio="none">
			<polyline
				fill="none"
				stroke={waveColor}
				strokeWidth="2"
				points={frequenciesToDisplay
					.map((v, i) => `${(i / frequenciesToDisplay.length) * 500}, ${100 - (100 * Math.sqrt(v))*2}`)
					.join(' ')}
			/>
		</svg>
	);

	const circleViz = (
		<div className="css-audio-viz" style={{ position: 'relative', width: '500px', height: '500px' }}>
			{frequenciesToDisplay.map((v, i) => {
				const angle = (i / frequenciesToDisplay.length) * 2 * Math.PI;
				const x = 250 + 200 * Math.cos(angle);
				const y = 250 + 200 * Math.sin(angle);
				return (
					<div
						key={i}
						className="css-bar"
						style={{
							position: 'absolute',
							left: `${x}px`,
							top: `${y}px`,
							width: '2px',
							height: `${100 * Math.sqrt(v)}px`,
							backgroundColor: waveColor,
							transform: `rotate(${angle}rad)`,
						}}
					/>
				);
			})}
		</div>
	);

	const radialBarsViz = (
		<svg className="css-audio-viz" viewBox="0 0 500 500">
			{frequenciesToDisplay.map((v, i) => {
				const angle = (i / frequenciesToDisplay.length) * 2 * Math.PI;
				const x1 = 250 + 100 * Math.cos(angle);
				const y1 = 250 + 100 * Math.sin(angle);
				const x2 = 250 + (100 + 100 * Math.sqrt(v)) * Math.cos(angle);
				const y2 = 250 + (100 + 100 * Math.sqrt(v)) * Math.sin(angle);
				return (
					<line
						key={i}
						x1={x1}
						y1={y1}
						x2={x2}
						y2={y2}
						stroke={waveColor}
						strokeWidth="2"
					/>
				);
			})}
		</svg>
	);

	// https://jerosoler.github.io/waveform-path/
	const customWaveform = (
		<svg className="css-audio-viz" viewBox={extendViewBox("0 0 700 75", 1)} preserveAspectRatio="none">
			<defs>
				<linearGradient id="lgrad" x1="0%" y1="50%" x2="100%" y2="50%">
					<stop offset="0%" style={{stopColor: '#ff8d33', stopOpacity: 0.4}}/>
					<stop offset="50%" style={{stopColor: '#ff8d33', stopOpacity: 1}}/>
					<stop offset="100%" style={{stopColor: '#ff8d33', stopOpacity: 0.4}}/>
				</linearGradient>
			</defs>
			<path
				d={pathLogo}
				fill="none"
				stroke="url(#lgrad)"
				strokeWidth="5px"
				strokeLinecap='round'
			/>
		</svg>
	);

	return vizType === 'bars' ? barViz :
		vizType === 'waveform' ? waveformViz :
		vizType === 'circle' ? circleViz :
		vizType === 'radialBars' ? radialBarsViz :
		vizType === 'customWaveform' ? customWaveform : null;
};