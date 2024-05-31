import { Composition } from 'remotion';
import { ArxflixComposition } from './ArxflixComp/Main';
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
				calculateMetadata={({ props }) => {
					return {
						durationInFrames: props.durationInSeconds * VIDEO_FPS,
						props,
					};
				}}
			/>
		</>
	);
};
