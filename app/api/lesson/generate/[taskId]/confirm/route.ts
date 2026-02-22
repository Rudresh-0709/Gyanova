import { NextResponse } from 'next/server';

export async function POST(
    req: Request,
    { params }: { params: Promise<{ taskId: string }> }
) {
    try {
        const { taskId } = await params;
        const body = await req.json();

        // Call the Python FastAPI backend
        const pythonResponse = await fetch(`http://localhost:8000/api/generate/${taskId}/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!pythonResponse.ok) {
            const errorText = await pythonResponse.text();
            console.error("Python API Error:", pythonResponse.status, errorText);
            return NextResponse.json({ error: "Failed to confirm lesson plan" }, { status: pythonResponse.status });
        }

        const data = await pythonResponse.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error proxying to Python backend:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
