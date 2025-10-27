<script lang="ts">
	import type { WorkflowStep } from '$lib/stores';

	export let steps: WorkflowStep[];

	const nodeLabels: Record<string, string> = {
		retrieve: '🔍 Retrieve',
		grade_documents: '✅ Grade',
		rewrite_query: '✏️ Rewrite',
		generate: '💬 Generate'
	};

	const nodeDescriptions: Record<string, string> = {
		retrieve: 'Searching knowledge base for relevant documents',
		grade_documents: 'Evaluating relevance of retrieved documents',
		rewrite_query: 'Rephrasing query for better results',
		generate: 'Generating answer from validated context'
	};
</script>

<div class="workflow">
	<div class="workflow-header">
		<span class="workflow-icon">⚙️</span>
		<span class="workflow-title">Agentic RAG Workflow</span>
	</div>
	<div class="workflow-steps">
		{#each steps as step, index}
			<div class="step {step.status}">
				<div class="step-indicator">
					{#if step.status === 'completed'}
						<span class="checkmark">✓</span>
					{:else if step.status === 'running'}
						<span class="spinner"></span>
					{:else}
						<span class="dot"></span>
					{/if}
				</div>
				<div class="step-content">
					<div class="step-label">{nodeLabels[step.node] || step.node}</div>
					<div class="step-description">{nodeDescriptions[step.node] || ''}</div>
				</div>
			</div>
			{#if index < steps.length - 1}
				<div class="step-connector"></div>
			{/if}
		{/each}
	</div>
</div>

<style>
	.workflow {
		margin-top: 1rem;
		padding: 1rem;
		background: #fff;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
	}

	.workflow-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
		font-weight: 600;
		font-size: 0.875rem;
		color: #555;
	}

	.workflow-icon {
		font-size: 1rem;
	}

	.workflow-steps {
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.step {
		display: flex;
		gap: 1rem;
		padding: 0.75rem 0;
	}

	.step-indicator {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.checkmark {
		width: 24px;
		height: 24px;
		background: #4caf50;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid #e0e0e0;
		border-top-color: #667eea;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.dot {
		width: 12px;
		height: 12px;
		background: #ddd;
		border-radius: 50%;
		margin: 6px;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.step-content {
		flex: 1;
	}

	.step-label {
		font-weight: 600;
		font-size: 0.875rem;
		color: #333;
		margin-bottom: 0.25rem;
	}

	.step.completed .step-label {
		color: #4caf50;
	}

	.step.running .step-label {
		color: #667eea;
	}

	.step-description {
		font-size: 0.8rem;
		color: #777;
	}

	.step-connector {
		width: 2px;
		height: 12px;
		background: #e0e0e0;
		margin-left: 11px;
	}
</style>
