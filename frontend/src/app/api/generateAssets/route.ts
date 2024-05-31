import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const { script, mp3_output, srt_output, rich_output } = await request.json();
    if (!script || !mp3_output || !srt_output || !rich_output) {
      return NextResponse.json({ error: 'Script, mp3_output, srt_output, and rich_output parameters are required' }, { status: 400 });
    }
    
    const response = await axios.post('http://127.0.0.1:8000/generate_assets/', {
      script: script,
      mp3_output: mp3_output,
      srt_output: srt_output,
      rich_output: rich_output,
      use_path: false,
    }, {
      headers: {
        'Accept': 'application/json'
      }
    });
    if (response.data.status === 'ERR') {
      console.error("Error in response:", response.data);
      return NextResponse.json({ error: 'Error fetching the paper data.' }, { status: 500 });
    }

    return NextResponse.json({
      mp3_output: mp3_output,
      srt_output: srt_output,
      rich_output: rich_output,
      total_duration: response.data.total_duration,
    });
  } catch (error) {
    console.error("Error fetching the paper data:", error);
    return NextResponse.json({ error: 'Error fetching the paper data.' }, { status: 500 });
  }
}
