import { messages, isLoading, currentWorkflow, error } from './stores';
import type { Message, WorkflowStep } from './stores';

// Detect if we're running on Runpod proxy or localhost
const isRunpodProxy = typeof window !== 'undefined' && window.location.hostname.includes('proxy.runpod.net');

// Use Runpod proxy URLs if detected, otherwise use localhost
const API_BASE = isRunpodProxy
	? window.location.origin.replace('-5173.', '-8000.')  // Replace frontend port with backend port
	: 'http://localhost:8000';

const WS_BASE = isRunpodProxy
	? API_BASE.replace('https://', 'wss://').replace('http://', 'ws://')
	: 'ws://localhost:8000';

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
			content: data.answer || data.response, // Support both 'answer' and 'response' keys
			timestamp: new Date(),
			sources: data.sources || [] // Pass through detailed source objects
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
				// Pass through detailed source objects for SourceViewer
				const sources = data.sources || [];

				// Add sources to message
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
							? { ...m, sources: sources }
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

// PEDAGOGICAL CHAT FUNCTIONS

/**
 * Send a message using pedagogical tutoring (phase-based guidance)
 */
export async function sendMessagePedagogicalHTTP(userMessage: string) {
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
		// Call pedagogical endpoint
		const response = await fetch(`${API_BASE}/api/chat/pedagogical`, {
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

		// Add assistant message with pedagogical context
		const assistantMsg: Message = {
			id: crypto.randomUUID(),
			role: 'assistant',
			content: data.answer,
			timestamp: new Date(),
			sources: [], // Pedagogical mode focuses on guidance, not sources
			workflow: data.phase_history ? data.phase_history.map(phase => ({
				node: phase.toUpperCase(),
				status: 'completed' as const,
				timestamp: new Date()
			})) : [],
			// Add pedagogical metadata
			pedagogicalPhase: data.current_phase,
			phaseSummary: data.phase_summary,
			problemStatement: data.problem_statement
		};

		messages.update(m => [...m, assistantMsg]);

	} catch (err) {
		console.error('Failed to send pedagogical message:', err);
		error.set(err instanceof Error ? err.message : 'Failed to connect to pedagogical backend');
	} finally {
		isLoading.set(false);
	}
}

let pedagogicalSocket: WebSocket | null = null;

/**
 * Send a message using pedagogical tutoring with WebSocket streaming
 */
export function sendMessagePedagogicalWebSocket(userMessage: string) {
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

	// Close existing pedagogical socket if any
	if (pedagogicalSocket) {
		pedagogicalSocket.close();
	}

	// Create new WebSocket connection for pedagogical chat
	pedagogicalSocket = new WebSocket(`${WS_BASE}/api/ws/chat-pedagogical/${currentConversationId}`);

	let assistantMessageId = crypto.randomUUID();
	let assistantContent = '';
	let currentPhase = '';
	let phaseSummary = '';
	let problemStatement = '';

	pedagogicalSocket.onopen = () => {
		// Send message as JSON
		pedagogicalSocket?.send(JSON.stringify({
			message: userMessage
		}));

		// Add initial assistant message placeholder
		const assistantMsg: Message = {
			id: assistantMessageId,
			role: 'assistant',
			content: '',
			timestamp: new Date(),
			workflow: [],
			pedagogicalPhase: 'initial'
		};
		messages.update(m => [...m, assistantMsg]);
	};

	pedagogicalSocket.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data);

			if (data.type === 'phase_change') {
				// Phase change notification
				currentPhase = data.phase;
				phaseSummary = data.message;

				// Update message with phase info
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
							? {
								...m,
								pedagogicalPhase: data.phase,
								phaseSummary: data.message
							}
							: m
					);
				});

			} else if (data.type === 'workflow') {
				// Workflow step notification
				const workflowStep: WorkflowStep = {
					node: data.node,
					status: 'completed',
					timestamp: new Date()
				};

				// Add to current workflow
				currentWorkflow.update(workflow => [...workflow, workflowStep]);

				// Update message with workflow
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
								? { ...m, workflow: [...(m.workflow || []), workflowStep] }
								: m
					);
				});

			} else if (data.type === 'token') {
				// Stream token content
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
				// Final completion event
				assistantContent = data.answer;
				currentPhase = data.current_phase;
				phaseSummary = data.phase_summary;
				problemStatement = data.problem_statement;

				// Update final message with all context
				messages.update(msgs => {
					return msgs.map(m =>
						m.id === assistantMessageId
								? {
									...m,
									content: data.answer,
									pedagogicalPhase: data.current_phase,
									phaseSummary: data.phase_summary,
									problemStatement: data.problem_statement,
									workflow: data.phase_history ? data.phase_history.map(phase => ({
										node: phase.toUpperCase(),
										status: 'completed' as const,
										timestamp: new Date()
									})) : (m.workflow || [])
								}
								: m
					);
				});

				// Clear loading and workflow state
				isLoading.set(false);
				currentWorkflow.set([]);

				// Close the socket since we're done
				if (pedagogicalSocket) {
					pedagogicalSocket.close();
					pedagogicalSocket = null;
				}

			} else if (data.type === 'error') {
				// Handle error events
				error.set(data.message || 'An error occurred in pedagogical mode');
				isLoading.set(false);
				currentWorkflow.set([]);
			}

		} catch (err) {
			console.error('Failed to parse pedagogical WebSocket message:', err);
		}
	};

	pedagogicalSocket.onerror = (err) => {
		console.error('Pedagogical WebSocket error:', err);
		error.set('Connection error in pedagogical mode. Please check if the backend is running.');
		isLoading.set(false);
	};

	pedagogicalSocket.onclose = () => {
		isLoading.set(false);
		currentWorkflow.set([]);
		pedagogicalSocket = null;
	};
}

/**
 * Get the current pedagogical state for a conversation
 */
export async function getPedagogicalState(conversationId: string = currentConversationId) {
	try {
		const response = await fetch(`${API_BASE}/api/chat/pedagogical/state/${conversationId}`);

		if (!response.ok) {
			if (response.status === 404) {
				return null; // No state exists yet
			}
			throw new Error(`HTTP ${response.status}`);
		}

		return await response.json();
	} catch (err) {
		console.error('Failed to get pedagogical state:', err);
		return null;
	}
}

/**
 * Clear the pedagogical state for a conversation
 */
export async function clearPedagogicalState(conversationId: string = currentConversationId) {
	try {
		const response = await fetch(`${API_BASE}/api/chat/pedagogical/state/${conversationId}`, {
			method: 'DELETE'
		});

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}`);
		}

		return await response.json();
	} catch (err) {
		console.error('Failed to clear pedagogical state:', err);
		throw err;
	}
}

export function closePedagogicalWebSocket() {
	if (pedagogicalSocket) {
		pedagogicalSocket.close();
		pedagogicalSocket = null;
	}
}
