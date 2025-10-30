import { messages, isLoading, currentWorkflow, error } from './stores';
import type { Message, WorkflowStep } from './stores';

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

let socket: WebSocket | null = null;
let currentConversationId = crypto.randomUUID();

export async function sendMessage(message: string): Promise<{ response: string; sources: string[] }> {
	const response = await fetch(`${API_BASE}/api/chat`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			message,
			conversation_id: currentConversationId
		})
	});

	if (!response.ok) {
		throw new Error(`HTTP ${response.status}`);
	}

	return response.json();
}

/**
 * Send a message using simple HTTP (non-streaming)
 * This integrates with Svelte stores for state management
 */
export async function sendMessageHTTP(userMessage: string) {
	// Add user message to chat
	const userMsg: Message = {
		id: crypto.randomUUID(),
		role: 'user',
		content: userMessage,
		timestamp: new Date()
	};
	messages.update(m => [...m, userMsg]);

	// Set loading state
	isLoading.set(true);
	error.set(null);

	try {
		// Call simple RAG endpoint
		const response = await fetch(`${API_BASE}/api/chat`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				message: userMessage,
				conversation_id: currentConversationId
			})
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const data = await response.json();

		// Add assistant message to chat
		const assistantMsg: Message = {
			id: crypto.randomUUID(),
			role: 'assistant',
			content: data.answer,
			timestamp: new Date(),
			sources: data.sources?.map((s: any, i: number) => {
				const fileName = s.metadata?.file_name || 'Unknown source';
				const page = s.metadata?.page_label ? ` (page ${s.metadata.page_label})` : '';
				return `${fileName}${page}`;
			}) || []
		};
		messages.update(m => [...m, assistantMsg]);

	} catch (err) {
		console.error('Failed to send message:', err);
		error.set(err instanceof Error ? err.message : 'Failed to connect to backend');
	} finally {
		isLoading.set(false);
	}
}

export function sendMessageWebSocket(userMessage: string) {
	// Add user message
	const msg: Message = {
		id: crypto.randomUUID(),
		role: 'user',
		content: userMessage,
		timestamp: new Date()
	};
	messages.update(m => [...m, msg]);

	// Set loading state
	isLoading.set(true);
	error.set(null);

	// Close existing socket if any
	if (socket) {
		socket.close();
	}

	// Create new WebSocket connection
	socket = new WebSocket(`${WS_BASE}/api/ws/chat`);

	let assistantMessageId = crypto.randomUUID();
	let assistantContent = '';
	let workflowSteps: WorkflowStep[] = [];

	socket.onopen = () => {
		// Send message as JSON (backend expects this format)
		socket?.send(JSON.stringify({
			message: userMessage,
			max_retries: 2
		}));

		// Add initial assistant message placeholder
		const assistantMsg: Message = {
			id: assistantMessageId,
			role: 'assistant',
			content: '',
			timestamp: new Date(),
			workflow: []
		};
		messages.update(m => [...m, assistantMsg]);
	};

	socket.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data);

			if (data.type === 'workflow') {
				// Backend sends: {"type": "workflow", "node": "...", "message": "..."}
				// Add as "running" status
				const existingStep = workflowSteps.find(s => s.node === data.node);
				if (!existingStep) {
					workflowSteps.push({
						node: data.node,
						status: 'completed', // Mark as completed immediately for simplicity
						timestamp: new Date()
					});
				}

				// Update current workflow for visualization
				currentWorkflow.set([...workflowSteps]);

				// Update message with workflow
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
							? { ...m, workflow: [...workflowSteps] }
							: m
					);
				});

			} else if (data.type === 'token') {
				// Append token to content
				assistantContent += data.content;

				// Update message content
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
							? { ...m, content: assistantContent }
							: m
					);
				});

			} else if (data.type === 'complete') {
				// Backend sends final completion with sources
				// Extract source filenames from source objects
				const sourceNames = data.sources?.map((s: any, i: number) =>
					`Source ${i + 1}: ${s.text.substring(0, 100)}...`
				) || [];

				// Add sources to message
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
							? { ...m, sources: sourceNames }
							: m
					);
				});

				// Response is complete - clear loading state
				isLoading.set(false);
				currentWorkflow.set([]);

				// Close the socket since we're done
				if (socket) {
					socket.close();
					socket = null;
				}
			} else if (data.type === 'error') {
				// Handle error events
				error.set(data.message || 'An error occurred');
				isLoading.set(false);
				currentWorkflow.set([]);
			}

		} catch (err) {
			console.error('Failed to parse WebSocket message:', err);
		}
	};

	socket.onerror = (err) => {
		console.error('WebSocket error:', err);
		error.set('Connection error. Please check if the backend is running.');
		isLoading.set(false);
	};

	socket.onclose = () => {
		isLoading.set(false);
		currentWorkflow.set([]);
		socket = null;
	};
}

export function closeWebSocket() {
	if (socket) {
		socket.close();
		socket = null;
	}
}
