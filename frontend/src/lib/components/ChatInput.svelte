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
			onkeypress={handleKeyPress}
			placeholder="Ask a computer science question..."
			disabled={$isLoading}
			rows="1"
		></textarea>
		<button onclick={handleSubmit} disabled={$isLoading || !inputValue.trim()} class="send-btn">
			{#if $isLoading}
				<span class="loading-spinner"></span>
			{:else}
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			{/if}
		</button>
		<div class="mic-container">
			<button class="mic-btn" disabled title="Coming soon!">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" stroke-width="2"/>
					<path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" stroke-width="2" stroke-linecap="round"/>
				</svg>
			</button>
			<span class="coming-soon">Talk-to-text features are coming soon!</span>
		</div>
	</div>
</div>

<style>
	.chat-input-container {
		padding: 1.5rem;
		background: #000000;
		border-top: 2px solid #00ff00;
	}

	.input-wrapper {
		display: flex;
		gap: 0.75rem;
		max-width: 900px;
		margin: 0 auto;
		align-items: flex-start;
	}

	textarea {
		flex: 1;
		padding: 0.875rem 1rem;
		border: 2px solid #00ff00;
		border-radius: 12px;
		font-size: 0.95rem;
		font-family: 'Courier New', monospace;
		resize: none;
		outline: none;
		transition: border-color 0.2s, box-shadow 0.2s;
		min-height: 48px;
		max-height: 200px;
		background: #001100;
		color: #00ff00;
	}

	textarea::placeholder {
		color: #00ff0080;
	}

	textarea:focus {
		border-color: #00ff00;
		box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
	}

	textarea:disabled {
		background: #001100;
		cursor: not-allowed;
		opacity: 0.5;
	}

	.send-btn {
		padding: 0 1.25rem;
		background: #00ff00;
		color: #000000;
		border: 2px solid #00ff00;
		border-radius: 12px;
		cursor: pointer;
		transition: transform 0.2s, opacity 0.2s, box-shadow 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 48px;
		font-weight: bold;
	}

	.send-btn:hover:not(:disabled) {
		transform: scale(1.05);
		box-shadow: 0 0 15px rgba(0, 255, 0, 0.5);
	}

	.send-btn:active:not(:disabled) {
		transform: scale(0.95);
	}

	.send-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.mic-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.mic-btn {
		padding: 0.75rem;
		background: rgba(0, 255, 0, 0.1);
		color: #00ff00;
		border: 2px solid #00ff00;
		border-radius: 12px;
		cursor: not-allowed;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 48px;
		min-height: 48px;
		opacity: 0.5;
	}

	.coming-soon {
		font-size: 0.7rem;
		color: #00ff00;
		text-align: center;
		max-width: 120px;
		line-height: 1.2;
		font-family: 'Courier New', monospace;
		opacity: 0.7;
	}

	.loading-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(0, 0, 0, 0.3);
		border-top-color: #000000;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
