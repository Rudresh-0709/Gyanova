import { NextResponse } from 'next/server';

function safeParseJson(text: string, fallback: unknown = null) {
    if (!text || !text.trim()) {
        return fallback;
    }
    try {
        return JSON.parse(text);
    } catch {
        return fallback;
    }
}

function extractErrorMessage(payload: any, fallback: string): string {
    if (!payload || typeof payload !== 'object') {
        return fallback;
    }

    if (typeof payload.error === 'string' && payload.error.trim()) {
        return payload.error;
    }

    if (typeof payload.detail === 'string' && payload.detail.trim()) {
        return payload.detail;
    }

    return fallback;
}

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
            const errorData = safeParseJson(errorText, null);
            console.error("Python API Error:", pythonResponse.status, errorText);
            return NextResponse.json(
                { error: extractErrorMessage(errorData, "Failed to confirm lesson plan") },
                { status: pythonResponse.status }
            );
        }

        const raw = await pythonResponse.text();
        const data = safeParseJson(raw, { task_id: taskId, status: 'processing' });
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error proxying to Python backend:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
