<script lang="ts">
	import { messages } from '$lib/stores';
	import Message from './Message.svelte';
	import { onMount, afterUpdate } from 'svelte';

	let messagesContainer: HTMLElement;

	function scrollToBottom() {
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	afterUpdate(() => {
		scrollToBottom();
	});

	onMount(() => {
		scrollToBottom();
	});
</script>

<div class="messages-container" bind:this={messagesContainer}>
	{#if $messages.length === 0}
		<div class="welcome-screen">
			<div class="welcome-content">
				<h2>AI Mentor</h2>
				<p>AI Introductory CS Mentor</p>
				<div class="features">
					<div class="feature">
						<span class="feature-icon">🔍</span>
						<span>Retrieval-augmented answers from course materials</span>
					</div>
					<div class="feature">
						<span class="feature-icon">🧠</span>
						<span>Self-correcting agentic workflow</span>
					</div>
					<div class="feature">
						<span class="feature-icon">📚</span>
						<span>Source citations for every answer</span>
					</div>
					<div class="feature">
						<span class="feature-icon">⚡</span>
						<span>Real-time streaming responses</span>
					</div>
				</div>
				<p class="prompt">Ask me anything about computer science!</p>
			</div>
		</div>
	{:else}
		{#each $messages as message (message.id)}
			<Message {message} />
		{/each}
	{/if}
</div>

<style>
	.messages-container {
		flex: 1;
		overflow-y: auto;
		padding: 1rem 0;
		scroll-behavior: smooth;
	}

	.welcome-screen {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
		padding: 2rem;
	}

	.welcome-content {
		max-width: 600px;
		text-align: center;
	}

	.welcome-content h2 {
		font-size: 2rem;
		margin-bottom: 1rem;
		color: #333;
	}

	.welcome-content > p {
		font-size: 1.1rem;
		color: #666;
		margin-bottom: 2rem;
		line-height: 1.6;
	}

	.features {
		display: grid;
		gap: 1rem;
		margin: 2rem 0;
		text-align: left;
	}

	.feature {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 3px solid #667eea;
	}

	.feature-icon {
		font-size: 1.5rem;
	}

	.feature span:last-child {
		color: #555;
		font-size: 0.95rem;
	}

	.prompt {
		margin-top: 2rem;
		font-size: 1.1rem;
		font-weight: 600;
		color: #667eea;
	}
</style>
