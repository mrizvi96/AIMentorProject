<script lang="ts">
	import ChatInput from '$lib/components/ChatInput.svelte';
	import MessageList from '$lib/components/MessageList.svelte';
	import { error } from '$lib/stores';
	import { sendMessageHTTP } from '$lib/api';

	async function handleSend(message: string) {
		try {
			await sendMessageHTTP(message);
		} catch (err) {
			console.error('Failed to send message:', err);
			error.set('Failed to connect. Make sure the backend is running.');
		}
	}
</script>

<svelte:head>
	<title>AI Mentor - Computer Science Tutor</title>
</svelte:head>

<div class="app-container">
	<header>
		<div class="header-content">
			<div>
				<h1>AI Tutor</h1>
				<p>Intelligent CS tutor powered by RAG</p>
			</div>
			<div class="status-indicator">
				<span class="status-dot"></span>
				<span>Live</span>
			</div>
		</div>
	</header>

	{#if $error}
		<div class="error-banner">
			⚠️ {$error}
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

	.header-content {
		max-width: 1200px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
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

	.status-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: rgba(255, 255, 255, 0.2);
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		background: #4caf50;
		border-radius: 50%;
		animation: pulse-dot 2s ease-in-out infinite;
	}

	@keyframes pulse-dot {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	.error-banner {
		background: #fee;
		color: #c33;
		padding: 1rem 2rem;
		border-bottom: 1px solid #fcc;
		text-align: center;
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
