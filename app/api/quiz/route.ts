import { NextResponse } from 'next/server';

export async function POST(req: Request) {
    try {
        const body = await req.json();

        const pythonResponse = await fetch('http://localhost:8000/api/quiz/generate', {
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
            console.error("Quiz API Error:", pythonResponse.status, errorText);
            return NextResponse.json(
                { error: errorData?.detail || "Failed to generate quiz from backend" },
                { status: pythonResponse.status }
            );
        }

        const data = await pythonResponse.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error proxying to Quiz backend:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
