import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton"

// import { commands } from "@uiw/react-md-editor";

export const MDEditor = dynamic(
  () => import("@uiw/react-md-editor"),
  {
    ssr: false,
    loading: () => <div className="flex w-full">
      <Skeleton className="h-[700px] w-full " />
    </div>,
  }
);
