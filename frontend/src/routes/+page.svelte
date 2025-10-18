<script lang="ts">
	import ChatInput from '$lib/components/ChatInput.svelte';
	import MessageList from '$lib/components/MessageList.svelte';
	import { messages, isLoading, error } from '$lib/stores';
	import { sendMessage } from '$lib/api';
	import type { Message } from '$lib/stores';

	async function handleSend(message: string) {
		// Add user message
		const userMessage: Message = {
			id: crypto.randomUUID(),
			role: 'user',
			content: message,
			timestamp: new Date()
		};
		messages.update((m) => [...m, userMessage]);

		// Set loading state
		isLoading.set(true);
		error.set(null);

		try {
			// Send to backend
			const response = await sendMessage(message);

			// Add assistant response
			const assistantMessage: Message = {
				id: crypto.randomUUID(),
				role: 'assistant',
				content: response.response,
				timestamp: new Date(),
				sources: response.sources
			};
			messages.update((m) => [...m, assistantMessage]);
		} catch (err) {
			console.error('Failed to send message:', err);
			error.set('Failed to get response. Make sure the backend is running.');

			// Add error message to chat
			const errorMessage: Message = {
				id: crypto.randomUUID(),
				role: 'assistant',
				content: 'Sorry, I encountered an error. Please make sure the backend server is running.',
				timestamp: new Date()
			};
			messages.update((m) => [...m, errorMessage]);
		} finally {
			isLoading.set(false);
		}
	}
</script>

<svelte:head>
	<title>AI Mentor - Computer Science Tutor</title>
</svelte:head>

<div class="app-container">
	<header>
		<h1>AI Mentor</h1>
		<p>Your intelligent computer science tutor</p>
	</header>

	{#if $error}
		<div class="error-banner">
			{$error}
		</div>
	{/if}

	<main>
		<MessageList />
		<ChatInput onSend={handleSend} />
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu,
			Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
	}

	.app-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #fafafa;
	}

	header {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem 2rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	header h1 {
		margin: 0 0 0.25rem 0;
		font-size: 1.75rem;
		font-weight: 600;
	}

	header p {
		margin: 0;
		opacity: 0.9;
		font-size: 0.95rem;
	}

	.error-banner {
		background: #fee;
		color: #c33;
		padding: 1rem 2rem;
		border-bottom: 1px solid #fcc;
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		max-width: 1200px;
		width: 100%;
		margin: 0 auto;
		background: white;
		box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
	}
</style>
