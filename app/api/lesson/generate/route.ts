export const maxDuration = 300; // 5 minutes (max for Vercel Hobby is 10s, Pro is 300s, Enterprise is 900s). For local dev, this helps Next.js know it's a long-running function.

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

export async function POST(req: Request) {
    try {
        const body = await req.json();

        // Call the Python FastAPI backend
        // Assumes the Python server is running on localhost:8000
        const pythonResponse = await fetch('http://localhost:8000/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!pythonResponse.ok) {
            const errorText = await pythonResponse.text();
            console.error("Python API Error:", pythonResponse.status, errorText);
            return NextResponse.json({ error: "Failed to generate lesson from backend" }, { status: pythonResponse.status });
        }

        const raw = await pythonResponse.text();
        const data = safeParseJson(raw, null);
        if (!data) {
            return NextResponse.json(
                { error: 'Backend returned invalid JSON' },
                { status: 502 }
            );
        }
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error proxying to Python backend:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

export async function GET(req: Request) {
    try {
        const { searchParams } = new URL(req.url);
        const taskId = searchParams.get('taskId');

        if (!taskId) {
            return NextResponse.json({ error: "Task ID is required" }, { status: 400 });
        }

        const pythonResponse = await fetch(`http://localhost:8000/api/generate/${taskId}`);

        if (!pythonResponse.ok) {
            const errorText = await pythonResponse.text();
            console.error("Python API Error:", pythonResponse.status, errorText);
            return NextResponse.json({ error: "Failed to get task status from backend" }, { status: pythonResponse.status });
        }

        const raw = await pythonResponse.text();
        const data = safeParseJson(raw, null);
        if (!data) {
            // Keep polling resilient during transient backend write/flush states.
            return NextResponse.json({
                task_id: taskId,
                status: 'planning',
                warning: 'Transient invalid backend payload',
            });
        }
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error getting task status:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
