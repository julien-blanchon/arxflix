"use client"
import { useState } from "react";
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { MDEditor } from "@/components/markdown"
import { Textarea } from "@/components/ui/textarea"
import axios from 'axios';
import { Step, type StepItem, Stepper, useStepper } from "@/components/stepper";
import { ScrollText } from 'lucide-react';
import { Captions } from 'lucide-react';
import { AudioLines } from 'lucide-react';
import { Video } from 'lucide-react';
import { Player } from "@remotion/player";
import { ArxflixComposition } from "@/remotion/ArxflixComp/Main";
import { useEffect } from "react";

function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
    const [value, setValue] = useState(defaultValue);
    
    useEffect(() => {
        const item = localStorage.getItem(key);
        
        if (!item) {
            localStorage.setItem(key, JSON.stringify(defaultValue))
        }

        setValue(item ? JSON.parse(item) : defaultValue)

        function handler(e: StorageEvent) {
            if (e.key !== key) return;

            const lsi = localStorage.getItem(key)
            setValue(JSON.parse(lsi ?? ""))
        }

        window.addEventListener("storage", handler)

        return () => {
            window.removeEventListener("storage", handler)
        };
    }, [])

    const setValueWrap = (value: T) => {
        try {
            setValue(value);

            localStorage.setItem(key, JSON.stringify(value));
            if (typeof window !== "undefined") {
                window.dispatchEvent(new StorageEvent("storage", { key }))
            }
        } catch (e) { console.error(e) }
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
  const [mdContent, setMdContent] = useLocalStorage<string | null>("md", null);
  const [loading, setLoading] = useState<boolean>(false);
  const [url, setUrl] = useLocalStorage<string | null>("url", null);
  const [script, setScript] = useLocalStorage<string | null>("script", null);
  const [folder, setFolder] = useLocalStorage<string | null>("folder", "3wbcwc");
  const [totalDuration, setTotalDuration] = useLocalStorage<number | null>("total_duration", null);

  // const [mp3Content, setMp3Content] = useState<string | undefined>(undefined);
  // const [srtContent, setSrtContent] = useState<string | undefined>(undefined);
  // const [richContent, setRichContent] = useState<string | undefined>(undefined);
  // const [currentAudio, setCurrentAudio] = useState<{ title: string; src: string }>({ title: "Advanced RAG: A new Method for training LLMS", src: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" });


  const [state, setState] = useState<"loading" | "error" | undefined>(undefined);

  const callGeneratePaper = async (url: string) => {
    console.log("Calling generate paper with url:", url);
    try {
      setLoading(true);
      setState("loading");
      const response = await axios.get('/api/generatePaper', {
        params: { url },
        headers: {
          'accept': 'application/json'
        }
      });
      console.log("Response:", response);
      console.log(response.data);

      if (response.data.error) {
        console.error("Error in response:", response.data.error);
        setMdContent("**Error fetching the paper data.**");
      } else {
        setMdContent(response.data); // Assuming the response data is the markdown content
      }
    } catch (error) {
      console.error("Error fetching the paper data:", error);
      setMdContent("**Error fetching the paper data.**");
    } finally {
      setLoading(false);
      setState(undefined);
    }
  }

  const callGenerateScript = async (mdContent: string) => {
    console.log("Calling generate script with mdContent:", mdContent);
    try {
      setLoading(true);
      setState("loading");
      console.log("Calling generate script with mdContent:", mdContent);
      const response = await axios.post('/api/generateScript', {
        paper: mdContent,
      }, {
        headers: {
          'Accept': 'application/json'
        }
      });

      console.log("Response:", response);
      console.log(response.data);

      if (response.data.error) {
        console.error("Error in response:", response.data.error);
        setScript("**Error generating the script.**");
      } else {
        setScript(response.data); // Assuming the response data is the script content
      }
    } catch (error) {
      console.error("Error generating the script:", error);
      setScript("**Error generating the script.**");
    } finally {
      setLoading(false);
      setState(undefined);
    }
  }

  const callGenerateAssets = async (script: string) => {
    console.log("Calling generate assets with script:", script);
    try {
      setLoading(true);
      setState("loading");
      // Generate a random folder uuid
      const _folder = Math.random().toString(36).substring(7);
      console.log("Calling generate assets with script:", script);
      const response = await axios.post('/api/generateAssets', {
        script: script,
        mp3_output: "frontend/public/" + _folder + "/audio.wav",
        srt_output: "frontend/public/" + _folder + "/subtitles.srt",
        rich_output: "frontend/public/" + _folder + "/rich.json",
      }, {
        headers: {
          'Accept': 'application/json'
        }
      });

      console.log("Response:", response);
      console.log(response.data);

      if (response.data.error) {
        console.error("Error in response:", response.data.error);
        setFolder(null);
      } else {
        setFolder(_folder);
        setTotalDuration(response.data.total_duration || 60*4);
      }
    } catch (error) {
      console.error("Error generating the assets:", error);
      setFolder(null);
    } finally {
      setLoading(false);
      setState(undefined);
    }
  }


  const steps: StepItem[] = [
    {
      label: "Generate Paper",
      description: "Extract content from the paper",
      icon: ScrollText,
    },
    { label: "Generate Script", description: "Generate script from the content", icon: Captions },
    { label: "Generate Assets", description: "Generate assets for the video", icon: AudioLines },
    { label: "Generate Video", description: "Generate the video", icon: Video },
  ];

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="flex w-full flex-col gap-4">
        <Stepper orientation="vertical" initialStep={3} steps={steps} state={state}>
          <Step label="Generate Paper" description="Extract content from the paper" icon={ScrollText}>
            <div className="m-3 h-96 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
              <Input className="w-1/3" type="url" placeholder="Arxiv URL" value={url || undefined}
              onChange={(e) => setUrl(e.target.value)} />
            </div>
            <StepButtons onClick={async (state) => {
              if (!url) {
                return;
              }
              await callGeneratePaper(url)
            }} />
          </Step>

          <Step label="Generate Script" description="Generate script from the content" icon={Captions}>
            <div className="m-3 h-96 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
              <MDEditor height={384} value={mdContent || undefined}
               onChange={(md) => setMdContent(md || null)} />
            </div>
            <StepButtons onClick={async (state) => {
              if (!mdContent) {
                return;
              }
              await callGenerateScript(mdContent)
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
              if (!script) {
                return;
              }
              await callGenerateAssets(script)
            }} />
          </Step>

          <Step label="Generate Video" description="Generate the video" icon={Video}>
            <div className="m-3 h-96 flex items-center justify-center my-4 border bg-secondary text-primary rounded-md">
              {/* <button onClick={() => {
                alert("Folder: " + folder)
                // setFolder(undefined)
                setFolder(folder ? null : "3wbcwc")
              }}><ArrowRightIcon /
                ></button> */}
              {folder && (
                <Player
                  component={ArxflixComposition}
                  inputProps={{
                    introFileName: `${folder}/intro.txt`,
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
                  durationInFrames={totalDuration || 60*4 * VIDEO_FPS}
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

const StepButtons = ({ onClick }: { onClick?: (state: 'loading' | 'error' | undefined) => Promise<void> }) => {
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
          onClick(state).then(() => {
            nextStep();
          });
        } else {
          nextStep();
        }
      }} disabled={state === "loading"}>
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
