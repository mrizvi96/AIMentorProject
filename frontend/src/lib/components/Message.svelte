<script lang="ts">
	import type { Message } from '$lib/stores';
	import WorkflowVisualization from './WorkflowVisualization.svelte';

	export let message: Message;

	function formatTime(date: Date): string {
		return new Date(date).toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
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
			<div class="sources">
				<div class="sources-header">📚 Sources</div>
				<div class="sources-list">
					{#each message.sources as source}
						<div class="source-item">{source}</div>
					{/each}
				</div>
			</div>
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
		color: #555;
	}

	.message.user .role-badge {
		color: #667eea;
	}

	.timestamp {
		font-size: 0.75rem;
		color: #999;
	}

	.message-content {
		background: #f8f9fa;
		padding: 1rem 1.25rem;
		border-radius: 12px;
		border-left: 3px solid #ddd;
	}

	.message.user .message-content {
		background: #f0f3ff;
		border-left-color: #667eea;
	}

	.message.assistant .message-content {
		background: #f8faf8;
		border-left-color: #4caf50;
	}

	.content-text {
		line-height: 1.6;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.content-placeholder {
		color: #999;
		font-style: italic;
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

	.sources {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
	}

	.sources-header {
		font-weight: 600;
		font-size: 0.875rem;
		color: #666;
		margin-bottom: 0.5rem;
	}

	.sources-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.source-item {
		font-size: 0.85rem;
		color: #555;
		background: white;
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
	}
</style>
