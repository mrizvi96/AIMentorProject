<script lang="ts">
	import { isLoading } from '$lib/stores';

	export let onSend: (message: string) => void;

	let inputValue = '';

	function handleSubmit() {
		if (inputValue.trim() && !$isLoading) {
			onSend(inputValue);
			inputValue = '';
		}
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit();
		}
	}
</script>

<div class="chat-input-container">
	<div class="input-wrapper">
		<textarea
			bind:value={inputValue}
			on:keypress={handleKeyPress}
			placeholder="Ask a computer science question..."
			disabled={$isLoading}
			rows="1"
		/>
		<button on:click={handleSubmit} disabled={$isLoading || !inputValue.trim()} class="send-btn">
			{#if $isLoading}
				<span class="loading-spinner"></span>
			{:else}
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			{/if}
		</button>
	</div>
</div>

<style>
	.chat-input-container {
		padding: 1.5rem;
		background: white;
		border-top: 1px solid #e0e0e0;
	}

	.input-wrapper {
		display: flex;
		gap: 0.75rem;
		max-width: 900px;
		margin: 0 auto;
	}

	textarea {
		flex: 1;
		padding: 0.875rem 1rem;
		border: 2px solid #e0e0e0;
		border-radius: 12px;
		font-size: 0.95rem;
		font-family: inherit;
		resize: none;
		outline: none;
		transition: border-color 0.2s;
		min-height: 48px;
		max-height: 200px;
	}

	textarea:focus {
		border-color: #667eea;
	}

	textarea:disabled {
		background: #f5f5f5;
		cursor: not-allowed;
	}

	.send-btn {
		padding: 0 1.25rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: transform 0.2s, opacity 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 48px;
	}

	.send-btn:hover:not(:disabled) {
		transform: scale(1.05);
	}

	.send-btn:active:not(:disabled) {
		transform: scale(0.95);
	}

	.send-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.loading-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
