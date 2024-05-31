import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const url = searchParams.get('url');
  console.log("URL:", url);
  if (!url) {
    return NextResponse.json({ error: 'URL parameter is required' }, { status: 400 });
  }

  try {
    const response = await axios.get('http://127.0.0.1:8000/generate_paper/', {
      params: { url },
      headers: {
        'accept': 'application/json'
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
