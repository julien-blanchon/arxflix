import { Composition, delayRender } from 'remotion';
import { ArxflixComposition, calculateMetadata } from './ArxflixComp/Main';
import { TestArxflixComposition, calculateTestMetadata } from './ArxflixComp/TestMain';
import './style.css';
import 'katex/dist/katex.min.css';
import {
	VIDEO_WIDTH,
	VIDEO_HEIGHT,
	VIDEO_FPS,
	CompositionProps,
	CompositionPropsType,
	defaultCompositionProps
} from "../types/constants";
import { useEffect, useState } from 'react';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			<Composition
				id="Arxflix"
				component={ArxflixComposition}
				fps	={VIDEO_FPS}
				width={VIDEO_WIDTH}
				height={VIDEO_HEIGHT}
				schema={CompositionProps}
				defaultProps={defaultCompositionProps}
				// Determine the length of the video based on the duration of the audio file
				// durationInFrames={8000}
				calculateMetadata={calculateMetadata}
			/>
			<Composition
				id="TestCodeSnippet"
				component={TestArxflixComposition}
				durationInFrames={390} // 13 seconds at 30fps
				fps={VIDEO_FPS}
				width={VIDEO_WIDTH}
				height={VIDEO_HEIGHT}
				schema={CompositionProps}
				defaultProps={defaultCompositionProps}
				calculateMetadata={calculateTestMetadata}
			/>
		</>
	);
};
