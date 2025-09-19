import { Composition } from 'remotion';
import { TestArxflixComposition, calculateTestMetadata } from './ArxflixComp/TestMain';
import { CompositionProps, defaultCompositionProps, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH } from '../types/constants';

export const TestCompositions: React.FC = () => {
	return (
		<>
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