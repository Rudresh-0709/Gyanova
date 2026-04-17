import { NextResponse } from 'next/server';

export async function POST(req: Request) {
    try {
        const body = await req.json();

        const pythonResponse = await fetch('http://localhost:8000/api/qna/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!pythonResponse.ok) {
            const errorText = await pythonResponse.text();
            let errorData;
            try { errorData = JSON.parse(errorText); } catch { errorData = null; }
            console.error("Q&A API Error:", pythonResponse.status, errorText);
            return NextResponse.json(
                { error: errorData?.detail || "Failed to get answer from backend" },
                { status: pythonResponse.status }
            );
        }

        const data = await pythonResponse.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error proxying to Q&A backend:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
