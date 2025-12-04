<script lang="ts">
	import { isPedagogicalMode, currentPhase, phaseSummary } from '../stores';

	// Phase color mapping
	const phaseColors = {
		initial: '#00ff00',      // Green
		explanation: '#ffff00',  // Yellow
		implementation: '#00ffff', // Cyan
		debugging: '#ff6600',    // Red
		reflection: '#9966ff'   // Purple
	};

	const phaseIcons = {
		initial: '🎯',
		explanation: '📋',
		implementation: '⚙️',
		debugging: '🐛',
		reflection: '💡'
	};
</script>

{#if $isPedagogicalMode}
	<div class="pedagogical-status">
		<div class="phase-indicator">
			<span class="phase-icon" style="color: {phaseColors[$currentPhase]}">
				{phaseIcons[$currentPhase]}
			</span>
			<span class="phase-text">
				{$currentPhase.toUpperCase()}
			</span>
		</div>
		<div class="phase-summary">
			{$phaseSummary}
		</div>
	</div>
{/if}

<style>
	.pedagogical-status {
		background: rgba(0, 255, 0, 0.1);
		border: 1px solid #00ff00;
		border-radius: 8px;
		padding: 12px 16px;
		margin-bottom: 16px;
		font-family: 'Courier New', monospace;
	}

	.phase-indicator {
		display: flex;
		align-items: center;
		gap: 8px;
		font-weight: bold;
		font-size: 0.9rem;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.phase-icon {
		font-size: 1.2rem;
		animation: pulse 2s ease-in-out infinite;
	}

	.phase-summary {
		font-size: 0.85rem;
		color: #00ff00;
		margin-top: 4px;
		opacity: 0.9;
	}

	@keyframes pulse {
		0%, 100% {
			opacity: 1;
			transform: scale(1);
		}
		50% {
			opacity: 0.7;
			transform: scale(1.1);
		}
	}
</style>