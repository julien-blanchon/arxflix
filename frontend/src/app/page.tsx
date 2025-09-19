"use client"
import { useState } from "react";
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { MDEditor } from "@/components/markdown"
import { Textarea } from "@/components/ui/textarea"
import { Step, type StepItem, Stepper, useStepper } from "@/components/stepper";
import { ScrollText } from 'lucide-react';
import { Captions } from 'lucide-react';
import { AudioLines } from 'lucide-react';
import { Video } from 'lucide-react';
import { Player } from "@remotion/player";
import { ArxflixComposition } from "@/remotion/ArxflixComp/Main";
import { useEffect } from "react";
import {
  client,
  generatePaperGeneratePaperGet,
  generateAssetsGenerateAssetsPost,
  generateScriptGenerateScriptPost,
  generateVideoGenerateVideoPost
} from '@/lib/client'
import { SmartInput, type InputType } from "@/components/ui/smart-input";
import { ContentTypeIndicator, type ContentType, type ProcessingMethod } from "@/components/ui/content-type-indicator";
import { processUrl, generateOverview, generatePaperFromUrl } from "@/lib/client/url-processing";

client.setConfig({
  baseURL: "http://127.0.0.1:8000/",
  headers: {
    "Content-Type": "application/json",
  },
});

type ScriptProvider = 'openai' | 'local' | 'gemini' | 'openrouter' | 'groq';

function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(defaultValue);

  useEffect(() => {
    const item = localStorage.getItem(key);
    //  Handle the case where the item is null or "undefined" string
    if (item === null || item === "undefined") {
      setValue(defaultValue);
      localStorage.setItem(key, JSON.stringify(defaultValue));
    } else {
      try {
        setValue(JSON.parse(item));
      } catch (error) {
        console.error("Error parsing localStorage item:", error);
        setValue(defaultValue);
        localStorage.setItem(key, JSON.stringify(defaultValue));
      }
    }


    const handler = (e: StorageEvent) => {
      if (e.key !== key) return;

      const lsi = localStorage.getItem(key);
      try {
         // added try/catch here as well to prevent parsing error.
        setValue(lsi ? JSON.parse(lsi) : defaultValue );
      } catch (error) {
        console.error("Error parsing localStorage item in event handler:", error);
        setValue(defaultValue);
        localStorage.setItem(key, JSON.stringify(defaultValue));
      }

    };

    window.addEventListener("storage", handler);

    return () => window.removeEventListener("storage", handler);
    // Added defaultValue to the dependency array
  }, [key, defaultValue]);

  const setValueWrap = (value: T) => {
    setValue(value);

      localStorage.setItem(key, JSON.stringify(value));


    if (typeof window !== "undefined") {
      window.dispatchEvent(new StorageEvent("storage", { key }));
    }

  };

  return [value, setValueWrap];
}

import {
  VIDEO_WIDTH,
  VIDEO_HEIGHT,
  VIDEO_FPS,
  CompositionProps,
  CompositionPropsType,
  defaultCompositionProps
} from "@/types/constants";

export default function Home() {
  const [mdContent, setMdContent] = useLocalStorage<string | undefined>("md", undefined);
  const [inputValue, setInputValue] = useLocalStorage<string | undefined>("input", undefined);
  const [script, setScript] = useLocalStorage<string | undefined>("script", undefined);
  const [folder, setFolder] = useLocalStorage<string | undefined>("folder", "3wbcwc");
  const [totalDuration, setTotalDuration] = useLocalStorage<number | undefined>("total_duration", undefined);
  const [state, setState] = useState<"loading" | "error" | undefined>(undefined);
  const [scriptProvider, setScriptProvider] = useLocalStorage<ScriptProvider>("script_provider", "openrouter");
  const [openrouterModel, setOpenrouterModel] = useLocalStorage<string | undefined>("openrouter_model", "google/gemini-2.0-flash-001");
  
  // New state for URL processing
  const [contentType, setContentType] = useLocalStorage<ContentType | undefined>("content_type", undefined);
  const [processingMethod, setProcessingMethod] = useLocalStorage<ProcessingMethod | undefined>("processing_method", undefined);
  const [confidenceScore, setConfidenceScore] = useLocalStorage<number | undefined>("confidence_score", undefined);
  const [sourceUrl, setSourceUrl] = useLocalStorage<string | undefined>("source_url", undefined);
  const [paperId, setPaperId] = useLocalStorage<string | undefined>("paper_id", undefined);

  const callGeneratePaper = async (input: string) => {
    setState("loading");
    
    try {
      // Detect if input is arXiv ID or URL
      const arxivIdPattern = /^\d{4}\.\d{4,5}(v\d+)?$/;
      const isArxivId = arxivIdPattern.test(input.trim());
      const isUrl = input.trim().startsWith('http');
      
      if (isUrl) {
        // Process URL using new endpoint
        console.log("Processing URL:", input);
        const urlResult = await processUrl(input);
        
        if (!urlResult.success) {
          setState("error");
          console.error("URL processing failed:", urlResult.error_message);
          return "error";
        }
        
        // Update state with URL processing results
        setMdContent(urlResult.markdown_content);
        setContentType(urlResult.content_type);
        setProcessingMethod(urlResult.source_type);
        setConfidenceScore(urlResult.confidence_score);
        setSourceUrl(urlResult.source_url);
        setPaperId(urlResult.paper_id);
        
        console.log("URL processed successfully:", {
          contentType: urlResult.content_type,
          processingMethod: urlResult.source_type,
          confidence: urlResult.confidence_score
        });
        
      } else if (isArxivId) {
        // Use existing arXiv processing
        console.log("Processing arXiv ID:", input);
        const response = await generatePaperGeneratePaperGet({
          client: client,
          query: { method: "arxiv_html", paper_id: input },
        });

        if (response.error) {
          setState("error");
          console.error("arXiv processing failed:", response.error);
          return "error";
        }

        setMdContent(response.data);
        // Set defaults for arXiv content
        setContentType("research");
        setProcessingMethod("arxiv");
        setConfidenceScore(1.0);
        setSourceUrl(`https://arxiv.org/abs/${input}`);
        setPaperId(input);
        
      } else {
        setState("error");
        console.error("Invalid input format:", input);
        return "error";
      }
      
      setState(undefined);
      
    } catch (error) {
      setState("error");
      console.error("Error processing input:", error);
      return "error";
    }
  }

  const callGenerateScript = async (mdContent: string, sourceIdentifier: string) => {
    console.log("Calling generate script with mdContent:", mdContent);
    setState("loading");
    
    try {
      // Use content-type-aware script generation if we have content type info
      if (contentType && (contentType === 'tutorial' || contentType === 'general')) {
        console.log("Using content-type-aware generation for:", contentType);
        const response = await generateOverview(
          mdContent,
          contentType,
          sourceIdentifier,
          scriptProvider as any
        );
        
        if (!response.success) {
          setState("error");
          console.error("Overview generation failed:", response.error_message);
          return "error";
        }
        
        setScript(response.script);
      } else {
        // Use existing script generation for research content or fallback
        console.log("Using traditional script generation");
        const response = await generateScriptGenerateScriptPost({ 
          client: client,
          query: { 
            method: scriptProvider, 
            paper_markdown: mdContent, 
            paper_id: sourceIdentifier
          },
        });

        if (response.error) {
          setState("error");
          console.error("Script generation failed:", response.error);
          return "error";
        }
        
        setScript(response.data);
      }
      
      setState(undefined);
      
    } catch (error) {
      setState("error");
      console.error("Error generating script:", error);
      return "error";
    }
  }

  const callGenerateAssets = async (script: string) => {
    setState("loading");
    // Generate a random folder uuid
    const _folder = Math.random().toString(36).substring(7);

    const response = await generateAssetsGenerateAssetsPost({
      client: client,
      query: { 
        method: "elevenlabs", 
        script: script,
        mp3_output: `../frontend/public/${_folder}/audio.wav`,
        rich_output: `../frontend/public/${_folder}/rich.json`,
        srt_output: `../frontend/public/${_folder}/subtitles.srt`,
      },
    });

    if (response.error) {
      console.error("Error in response:", response.error);
      setState("error");
      return "error";
    }

    setFolder(_folder);
    setTotalDuration(response.data || 60 * 4);
    setState(undefined);
  }

  const steps: StepItem[] = [
    { label: "Process Content", description: "Extract content from arXiv paper or URL", icon: ScrollText },
    { label: "Generate Script", description: "Generate script from the content", icon: Captions },
    { label: "Generate Assets", description: "Generate assets for the video", icon: AudioLines },
    { label: "Generate Video", description: "Generate the video", icon: Video },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="flex w-full flex-col gap-4">
        <Stepper orientation="horizontal" initialStep={3} steps={steps} state={state}>
          <Step label="Process Content" description="Extract content from arXiv paper or URL" icon={ScrollText}>
            <div className="m-3 h-96 flex flex-col items-center justify-center my-4 border bg-secondary text-primary rounded-md space-y-4">
              <div className="w-2/3 max-w-md">
                <SmartInput
                  value={inputValue || ""}
                  onChange={setInputValue}
                  placeholder="Enter arXiv ID (e.g., 2404.02905) or URL"
                  disabled={state === "loading"}
                />
              </div>
              
              {/* Content type indicator */}
              {state === "loading" && inputValue && (
                <div className="w-2/3 max-w-md">
                  <div className="p-4 bg-gray-50 border rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-gray-600">Processing content...</span>
                    </div>
                  </div>
                </div>
              )}
              
              {contentType && processingMethod && sourceUrl && state !== "loading" && (
                <div className="w-2/3 max-w-md">
                  <ContentTypeIndicator
                    contentType={contentType}
                    processingMethod={processingMethod}
                    confidenceScore={confidenceScore}
                    sourceUrl={sourceUrl}
                  />
                </div>
              )}
            </div>
            <StepButtons
              disabled={!inputValue || !inputValue.trim()}
              onClick={async (state) => {
                if (!inputValue?.trim()) return;
                await callGeneratePaper(inputValue.trim())
                return state;
              }} />
          </Step>

          <Step label="Generate Script" description="Generate script from the content" icon={Captions}>
            <div className="m-3 h-96 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
              <MDEditor height={384} value={mdContent || undefined}
                onChange={(md) => setMdContent(md)} />
            </div>
            <div className="flex gap-2 mb-4">
              <select className="border rounded px-2 py-1" value={scriptProvider || "openrouter"} onChange={(e) => setScriptProvider(e.target.value as ScriptProvider)}>
                <option value="openai">OpenAI</option>
                <option value="gemini">Gemini</option>
                <option value="local">Local (OpenAI-compatible)</option>
                <option value="openrouter">OpenRouter</option>
                <option value="groq">Groq</option>
              </select>
              {scriptProvider === "openrouter" && (
                <input className="border rounded px-2 py-1" placeholder="OpenRouter model (optional)" value={openrouterModel ?? ""} onChange={(e) => setOpenrouterModel(e.target.value)} />
              )}
            </div>
            <StepButtons onClick={async (state) => {
              if (!mdContent) return;
              const sourceIdentifier = paperId || inputValue || 'unknown_source';
              await callGenerateScript(mdContent, sourceIdentifier)
              return state;
            }} />
          </Step>

          <Step label="Generate Assets" description="Generate assets for the video" icon={AudioLines}>
            <div className="m-3 h-96 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
              <Textarea
                className="w-full h-full p-6"
                value={script || undefined}
                onChange={(e) => setScript(e.target.value)}
              />
            </div>
            <StepButtons onClick={async (state) => {
              if (!script) return;
              await callGenerateAssets(script)
              return state;
            }} />
          </Step>

          <Step label="Generate Video" description="Generate the video" icon={Video}>
            <div className="m-3 h-96 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
              {folder && totalDuration && (
                <Player
                  component={ArxflixComposition}
                  inputProps={{
                    audioFileName: `${folder}/audio.wav`,
                    richContentFileName: `${folder}/rich.json`,
                    subtitlesFileName: `${folder}/subtitles.srt`,
                    onlyDisplayCurrentSentence: true,
                    subtitlesLinePerPage: 2,
                    subtitlesZoomMeasurerSize: 10,
                    subtitlesLineHeight: 98,
                    waveColor: "#a3a5ae",
                    waveFreqRangeStartIndex: 5,
                    waveLinesToDisplay: 300,
                    waveNumberOfSamples: "512",
                    mirrorWave: false,
                    audioOffsetInSeconds: 0,
                  }}
                  // Ceil the total duration to the nearest frame
                  durationInFrames={Math.ceil(totalDuration * VIDEO_FPS)}
                  compositionWidth={1920}
                  compositionHeight={1080}
                  fps={30}
                  style={{ width: "100%", height: "100%" }}
                  controls
                />
              )}
            </div>
            <StepButtons />
          </Step>
          <FinalStep />
        </Stepper>
      </div>
    </main>
  );
}

const StepButtons = ({ onClick, disabled }: { onClick?: (state: 'loading' | 'error' | undefined) => Promise<void | 'loading' | 'error' | undefined>, disabled?: boolean }) => {
  const { nextStep, prevStep, isLastStep, isOptionalStep, isDisabledStep, state } =
    useStepper();
  return (
    <div className="w-full flex gap-2 mb-4">
      <Button
        disabled={isDisabledStep}
        onClick={prevStep}
        size="sm"
        variant="secondary"
      >
        Prev
      </Button>
      <Button size="sm" onClick={async () => {
        if (onClick) {
          onClick(state).then((r) => {
            if (r !== "error") {
              nextStep();
            }
          })
        } else {
          nextStep();
        }
      }} disabled={state === "loading" || disabled}>
        {isLastStep ? "Finish" : isOptionalStep ? "Skip" : state === "loading" ? "Loading..." : "Next"}
      </Button>
    </div>
  );
};

const FinalStep = () => {
  const { hasCompletedAllSteps, resetSteps, nextStep, prevStep, isLastStep, isOptionalStep, isDisabledStep, state } =
    useStepper();

  if (!hasCompletedAllSteps) {
    return null;
  }

  return (
    <>
      <div className="h-40 flex items-center justify-center border bg-secondary text-primary rounded-md">
        <h1 className="text-xl">Woohoo! All steps completed! 🎉</h1>
      </div>
      <Button
        disabled={isDisabledStep}
        onClick={prevStep}
        size="sm"
        variant="secondary"
      >
        Prev
      </Button>
      <Button size="sm" onClick={() => {
        nextStep();
      }} disabled={state === "loading"}>
        {isLastStep ? "Finish" : isOptionalStep ? "Skip" : state === "loading" ? "Loading..." : "Next"}
      </Button>
      <div className="w-full flex justify-end gap-2">
        <Button size="sm" onClick={resetSteps}>
          Reset
        </Button>
      </div>
    </>
  );
};
