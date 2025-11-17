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
				<div class="project-info">
					<p class="project-title">CS 6460: Educational Technology Project</p>
					<p class="author">Built by Mohammad M. Rizvi</p>
					<p class="license">Creative Commons License</p>
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
		background: #000000;
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
		color: #00ff00;
		font-family: 'Courier New', monospace;
		text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
	}

	.welcome-content > p {
		font-size: 1.1rem;
		color: #00ff00;
		margin-bottom: 2rem;
		line-height: 1.6;
		font-family: 'Courier New', monospace;
		opacity: 0.8;
	}

	.project-info {
		margin: 2rem 0;
		padding: 1.5rem;
		background: rgba(0, 255, 0, 0.05);
		border-radius: 8px;
		border: 1px solid #00ff00;
		border-left: 3px solid #00ff00;
		box-shadow: 0 0 15px rgba(0, 255, 0, 0.1);
	}

	.project-title {
		color: #00ff00;
		font-size: 1.1rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		font-family: 'Courier New', monospace;
		text-shadow: 0 0 5px rgba(0, 255, 0, 0.3);
	}

	.author {
		color: #00ff00;
		font-size: 1rem;
		margin-bottom: 0.5rem;
		font-family: 'Courier New', monospace;
		opacity: 0.9;
	}

	.license {
		color: #00ff00;
		font-size: 0.9rem;
		font-family: 'Courier New', monospace;
		opacity: 0.8;
		font-style: italic;
	}

	.prompt {
		margin-top: 2rem;
		font-size: 1.1rem;
		font-weight: 600;
		color: #00ff00;
		font-family: 'Courier New', monospace;
		text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
	}
</style>
