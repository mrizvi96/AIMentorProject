<script lang="ts">
	import { isPedagogicalMode } from '../stores';

	function toggleMode() {
		isPedagogicalMode.update(m => !m);
	}
</script>

<div class="mode-toggle">
	<button
		class="toggle-button"
		class:pedagogical={$isPedagogicalMode}
		on:click={toggleMode}
		title={$isPedagogicalMode ? 'Switch to Q&A mode' : 'Switch to tutoring mode'}
	>
		{#if $isPedagogicalMode}
			🎓 Tutoring
		{:else}
			❓ Q&A
		{/if}
	</button>
	<div class="mode-description">
		{#if $isPedagogicalMode}
			Socratic guidance with phase-based tutoring
		{:else}
			Direct answers with source citations
		{/if}
	</div>
</div>

<style>
	.mode-toggle {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 12px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		border: 1px solid #333;
	}

	.toggle-button {
		background: #001100;
		color: #00ff00;
		border: 1px solid #00ff00;
		padding: 8px 16px;
		border-radius: 6px;
		cursor: pointer;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		font-weight: bold;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 1px;
		min-width: 100px;
	}

	.toggle-button:hover {
		background: #002200;
		transform: scale(1.05);
		box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
	}

	.toggle-button.pedagogical {
		background: #1a0033;
		color: #ffff00;
		border-color: #ffff00;
	}

	.toggle-button.pedagogical:hover {
		background: #220044;
		box-shadow: 0 0 10px rgba(255, 255, 0, 0.3);
	}

	.mode-description {
		font-size: 0.75rem;
		color: #888;
		text-align: center;
		line-height: 1.2;
		max-width: 150px;
	}
</style>