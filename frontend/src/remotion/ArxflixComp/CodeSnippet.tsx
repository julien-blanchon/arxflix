import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

// We'll use a simpler approach without Prism.js for now to avoid import issues
// This can be enhanced later with proper syntax highlighting

export interface CodeSnippetProps {
  code: string;
  language: string;
  startFrame: number;
  endFrame: number;
  transitionFrames?: number;
}

export const CodeSnippet: React.FC<CodeSnippetProps> = ({
  code,
  language,
  startFrame,
  endFrame,
  transitionFrames = 10,
}) => {
  const frame = useCurrentFrame();

  // Calculate animation values
  const durationInFrames = endFrame - startFrame;
  const relativeFrame = frame - startFrame;

  const scale = interpolate(
    relativeFrame,
    [0, transitionFrames, durationInFrames - transitionFrames, durationInFrames],
    [0.8, 1, 1, 0.8],
    { extrapolateRight: 'clamp' }
  );

  const opacity = interpolate(
    relativeFrame,
    [0, transitionFrames, durationInFrames - transitionFrames, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateRight: 'clamp' }
  );

  // Typewriter effect for code appearance
  const codeLength = code.length;
  const typewriterProgress = interpolate(
    relativeFrame,
    [transitionFrames, transitionFrames + 30], // 1 second typewriter effect at 30fps
    [0, 1],
    { extrapolateRight: 'clamp' }
  );
  
  const visibleCharacters = Math.floor(codeLength * typewriterProgress);
  const visibleCode = code.substring(0, visibleCharacters);

  const styleCombined = {
    transform: `scale(${scale})`,
    opacity,
  };

  return (
    <div 
      className="bg-gray-900 rounded-2xl p-12 w-full max-w-7xl mx-auto shadow-2xl border-2 border-gray-600"
      style={{
        ...styleCombined,
        minHeight: '400px',
        width: '90%',
      }}
    >
      {/* Code header with language indicator */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b-2 border-gray-600">
        <div className="flex items-center space-x-4">
          <div className="flex space-x-2">
            <div className="w-6 h-6 bg-red-500 rounded-full"></div>
            <div className="w-6 h-6 bg-yellow-500 rounded-full"></div>
            <div className="w-6 h-6 bg-green-500 rounded-full"></div>
          </div>
          <span className="text-gray-300 text-2xl font-mono ml-8 font-semibold">
            {language.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Code content */}
      <div className="relative">
        <pre className="text-2xl font-mono text-gray-100 overflow-hidden leading-relaxed whitespace-pre-wrap">
          <code style={{ fontSize: '1.75rem', lineHeight: '2.5rem' }}>
            {typewriterProgress < 1 ? visibleCode : code}
          </code>
        </pre>
        
        {/* Blinking cursor for typewriter effect */}
        {typewriterProgress < 1 && (
          <span 
            className="inline-block w-1 h-8 bg-green-400 ml-2"
            style={{
              animation: 'blink 1s infinite'
            }}
          />
        )}
      </div>

      <style jsx>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
};