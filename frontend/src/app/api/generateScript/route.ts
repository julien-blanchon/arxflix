import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const { paper } = await request.json();
    console.log("Paper:", paper);
    if (!paper) {
      return NextResponse.json({ error: 'Paper parameter is required' }, { status: 400 });
    }
    
    const response = await axios.post('http://127.0.0.1:8000/generate_script/', {
      paper: paper,
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

    return NextResponse.json(response.data);
  } catch (error) {
    console.error("Error fetching the paper data:", error);
    return NextResponse.json({ error: 'Error fetching the paper data.' }, { status: 500 });
  }
}
