<script lang="ts">
	import type { Message } from '$lib/stores';
	import WorkflowVisualization from './WorkflowVisualization.svelte';
	import SourceViewer from './SourceViewer.svelte';
	import FeedbackComponent from './FeedbackComponent.svelte';

	export let message: Message;

	function formatTime(date: Date): string {
		return new Date(date).toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
	}

	function handleFeedback(rating: number, comment: string) {
		console.log(`Feedback submitted for interaction ${message.interactionId}:`, rating, comment);
	}
</script>

<div class="message {message.role}">
	<div class="message-header">
		<span class="role-badge">
			{message.role === 'user' ? '👤 You' : '🤖 AI Mentor'}
		</span>
		<span class="timestamp">{formatTime(message.timestamp)}</span>
	</div>

	<div class="message-content">
		{#if message.content}
			<div class="content-text">
				{message.content}
			</div>
		{:else}
			<div class="content-placeholder">
				<span class="thinking-indicator">Thinking...</span>
			</div>
		{/if}

		{#if message.workflow && message.workflow.length > 0}
			<WorkflowVisualization steps={message.workflow} />
		{/if}

		{#if message.sources && message.sources.length > 0}
			<SourceViewer sources={message.sources} />
		{/if}

		{#if message.role === 'assistant' && message.interactionId && message.content}
			<FeedbackComponent
				interactionId={message.interactionId}
				onFeedback={handleFeedback}
				compact={true}
			/>
		{/if}
	</div>
</div>

<style>
	.message {
		margin: 1.5rem;
		animation: slideIn 0.3s ease-out;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.message-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.role-badge {
		font-weight: 600;
		font-size: 0.875rem;
		color: #00ff00;
		font-family: 'Courier New', monospace;
	}

	.message.user .role-badge {
		color: #00ff00;
		text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
	}

	.timestamp {
		font-size: 0.75rem;
		color: #00ff00;
		opacity: 0.6;
		font-family: 'Courier New', monospace;
	}

	.message-content {
		background: rgba(0, 255, 0, 0.05);
		padding: 1rem 1.25rem;
		border-radius: 12px;
		border-left: 3px solid #00ff00;
		border: 1px solid #00ff00;
	}

	.message.user .message-content {
		background: rgba(0, 255, 0, 0.08);
		border-left-color: #00ff00;
		box-shadow: 0 0 10px rgba(0, 255, 0, 0.1);
	}

	.message.assistant .message-content {
		background: rgba(0, 255, 0, 0.05);
		border-left-color: #00ff00;
	}

	.content-text {
		line-height: 1.6;
		white-space: pre-wrap;
		word-wrap: break-word;
		color: #00ff00;
		font-family: 'Courier New', monospace;
	}

	.content-placeholder {
		color: #00ff00;
		font-style: italic;
		opacity: 0.7;
		font-family: 'Courier New', monospace;
	}

	.thinking-indicator {
		display: inline-block;
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% {
			opacity: 0.6;
		}
		50% {
			opacity: 1;
		}
	}

	/* Source styling moved to SourceViewer component */
</style>
