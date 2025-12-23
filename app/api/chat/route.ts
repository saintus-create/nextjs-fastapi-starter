import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json();

    // Extract the last user message as the task
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage || lastMessage.role !== 'user') {
      return NextResponse.json({ error: 'No user message found' }, { status: 400 });
    }

    const task = typeof lastMessage.content === 'string'
      ? lastMessage.content.trim()
      : lastMessage.content.map((part: any) => part.text || '').join('').trim();

    if (!task) {
      return NextResponse.json({ error: 'Empty task' }, { status: 400 });
    }

    // Determine the backend URL (localhost for dev, Vercel URL for prod)
    const backendUrl = process.env.NODE_ENV === 'production'
      ? process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : 'http://localhost:8000'
      : 'http://localhost:8000';

    // Call the FastAPI backend
    const response = await fetch(`${backendUrl}/api/run-task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task,
        mode: 'plan_act'  // Use plan_act mode for better structured execution
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend error: ${response.status} ${errorText}`);
    }

    const result = await response.json();

    // Transform structured result into conversational message
    let content = '';
    if (result.success) {
      content = `✅ Task completed successfully!\n\n**Result:**\n${result.stdout || 'No output'}\n\n*Executed via autonomous agent with safety guardrails*`;
    } else {
      content = `❌ Task failed.\n\n**Error:** ${result.stderr || 'Unknown error'}\n\n*The agent encountered an issue while executing this task.*`;
    }

    return NextResponse.json({
      id: Date.now().toString(),
      role: 'assistant',
      content
    });

  } catch (error: any) {
    console.error('Chat API error:', error);
    return NextResponse.json({
      id: Date.now().toString(),
      role: 'assistant',
      content: `🚨 Error: ${error.message}\n\n*Please check the agent logs for more details.*`
    }, { status: 500 });
  }
}