<script lang="ts">
	import { onMount } from 'svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';
	import MessageList from '$lib/components/MessageList.svelte';
	import AuthButton from '$lib/components/AuthButton.svelte';
	import { error } from '$lib/stores';
	import { sendMessageHTTP } from '$lib/api';
	import { checkAuth } from '$lib/auth';

	// Check authentication status on mount (non-blocking)
	onMount(() => {
		checkAuth().catch(err => {
			console.warn('Auth check failed:', err);
		});
	});

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
				<h1>AI Mentor</h1>
				<p>CS 6460: Educational Technology Project</p>
			</div>
			<div class="header-right">
				<div class="status-indicator">
					<span class="status-dot"></span>
					<span>Live</span>
				</div>
				<AuthButton />
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
		font-family: 'Courier New', monospace;
		background: #000000;
	}

	.app-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #000000;
	}

	header {
		background: linear-gradient(135deg, #001100 0%, #003300 100%);
		color: #00ff00;
		padding: 1.5rem 2rem;
		box-shadow: 0 2px 8px rgba(0, 255, 0, 0.3);
		border-bottom: 2px solid #00ff00;
	}

	.header-content {
		max-width: 1200px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 1rem;
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
		background: rgba(0, 255, 0, 0.1);
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		border: 1px solid #00ff00;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		background: #00ff00;
		border-radius: 50%;
		animation: pulse-dot 2s ease-in-out infinite;
		box-shadow: 0 0 10px #00ff00;
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
		background: #1a0000;
		color: #ff0000;
		padding: 1rem 2rem;
		border-bottom: 1px solid #ff0000;
		text-align: center;
		font-family: 'Courier New', monospace;
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		max-width: 1200px;
		width: 100%;
		margin: 0 auto;
		background: #000000;
		box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
		border-left: 1px solid #00ff00;
		border-right: 1px solid #00ff00;
	}
</style>
