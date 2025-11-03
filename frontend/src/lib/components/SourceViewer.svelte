<script lang="ts">
	import type { SourceDocument } from '$lib/stores';

	export let sources: string[] | SourceDocument[];

	// Type guard to check if sources are detailed objects
	function isDetailedSource(source: string | SourceDocument): source is SourceDocument {
		return typeof source === 'object' && 'metadata' in source;
	}

	// Convert sources to uniform format
	const detailedSources: SourceDocument[] = sources
		.filter(isDetailedSource)
		.sort((a, b) => b.score - a.score); // Sort by relevance score

	// Simple string sources (legacy support)
	const simpleSources: string[] = sources.filter((s): s is string => typeof s === 'string');

	let expandedIndex: number | null = null;

	function toggleExpand(index: number) {
		expandedIndex = expandedIndex === index ? null : index;
	}

	function formatFileSize(bytes?: number): string {
		if (!bytes) return 'Unknown size';
		const mb = bytes / (1024 * 1024);
		return mb < 1 ? `${(bytes / 1024).toFixed(1)} KB` : `${mb.toFixed(1)} MB`;
	}

	function getRelevanceColor(score: number): string {
		if (score >= 0.7) return '#4caf50'; // Green - highly relevant
		if (score >= 0.5) return '#ff9800'; // Orange - moderately relevant
		return '#f44336'; // Red - weakly relevant
	}

	function getRelevanceLabel(score: number): string {
		if (score >= 0.7) return 'Highly Relevant';
		if (score >= 0.5) return 'Moderately Relevant';
		return 'Weakly Relevant';
	}

	function truncateText(text: string, maxLength: number = 200): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<div class="source-viewer">
	<div class="source-header">
		<span class="header-icon">📚</span>
		<span class="header-title">Retrieved Sources</span>
		<span class="source-count">{detailedSources.length + simpleSources.length}</span>
	</div>

	{#if detailedSources.length > 0}
		<div class="detailed-sources">
			{#each detailedSources as source, index}
				<div class="source-card" class:expanded={expandedIndex === index}>
					<button class="source-card-header" on:click={() => toggleExpand(index)}>
						<div class="source-info">
							<div class="source-title">
								<span class="file-icon">📄</span>
								<span class="file-name">{source.metadata.file_name}</span>
							</div>
							<div class="source-meta">
								{#if source.metadata.page_label}
									<span class="meta-item">
										<span class="meta-icon">📖</span>
										Page {source.metadata.page_label}
									</span>
								{/if}
								<span
									class="relevance-badge"
									style="background-color: {getRelevanceColor(source.score)}"
								>
									{getRelevanceLabel(source.score)} ({Math.round(source.score * 100)}%)
								</span>
							</div>
						</div>
						<div class="expand-icon">
							{expandedIndex === index ? '▼' : '▶'}
						</div>
					</button>

					{#if expandedIndex === index}
						<div class="source-card-content">
							<div class="source-text">
								<div class="content-label">Excerpt:</div>
								<div class="content-text">{source.text}</div>
							</div>

							<div class="source-metadata">
								<div class="metadata-label">Document Details:</div>
								<div class="metadata-grid">
									<div class="metadata-item">
										<span class="metadata-key">File:</span>
										<span class="metadata-value">{source.metadata.file_name}</span>
									</div>
									{#if source.metadata.page_label}
										<div class="metadata-item">
											<span class="metadata-key">Page:</span>
											<span class="metadata-value">{source.metadata.page_label}</span>
										</div>
									{/if}
									{#if source.metadata.file_size}
										<div class="metadata-item">
											<span class="metadata-key">Size:</span>
											<span class="metadata-value"
												>{formatFileSize(source.metadata.file_size)}</span
											>
										</div>
									{/if}
									{#if source.metadata.file_type}
										<div class="metadata-item">
											<span class="metadata-key">Type:</span>
											<span class="metadata-value">{source.metadata.file_type}</span>
										</div>
									{/if}
									<div class="metadata-item">
										<span class="metadata-key">Relevance:</span>
										<span class="metadata-value">{Math.round(source.score * 100)}%</span>
									</div>
								</div>
							</div>
						</div>
					{:else}
						<div class="source-preview">
							{truncateText(source.text)}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	{#if simpleSources.length > 0}
		<div class="simple-sources">
			<div class="simple-sources-label">Additional Sources:</div>
			{#each simpleSources as source}
				<div class="simple-source-item">
					<span class="simple-source-icon">📄</span>
					{source}
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.source-viewer {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
	}

	.source-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
		font-weight: 600;
		font-size: 0.875rem;
		color: #555;
	}

	.header-icon {
		font-size: 1rem;
	}

	.header-title {
		flex: 1;
	}

	.source-count {
		background: #667eea;
		color: white;
		padding: 0.125rem 0.5rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
	}

	/* Detailed Sources */
	.detailed-sources {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.source-card {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		overflow: hidden;
		transition: all 0.2s ease;
	}

	.source-card:hover {
		border-color: #667eea;
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
	}

	.source-card.expanded {
		border-color: #667eea;
	}

	.source-card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 0.75rem 1rem;
		background: transparent;
		border: none;
		cursor: pointer;
		text-align: left;
		transition: background 0.2s ease;
	}

	.source-card-header:hover {
		background: #f8f9fa;
	}

	.source-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.source-title {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
		font-size: 0.875rem;
		color: #333;
	}

	.file-icon {
		font-size: 1rem;
	}

	.file-name {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: 400px;
	}

	.source-meta {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.meta-item {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
		color: #777;
	}

	.meta-icon {
		font-size: 0.875rem;
	}

	.relevance-badge {
		display: inline-block;
		padding: 0.125rem 0.5rem;
		border-radius: 12px;
		font-size: 0.7rem;
		font-weight: 600;
		color: white;
	}

	.expand-icon {
		font-size: 0.75rem;
		color: #999;
		margin-left: 0.5rem;
		flex-shrink: 0;
	}

	.source-preview {
		padding: 0 1rem 0.75rem 1rem;
		font-size: 0.8rem;
		color: #666;
		line-height: 1.5;
		font-style: italic;
	}

	.source-card-content {
		padding: 0 1rem 1rem 1rem;
		border-top: 1px solid #f0f0f0;
		animation: expandContent 0.2s ease-out;
	}

	@keyframes expandContent {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.source-text {
		margin-top: 1rem;
	}

	.content-label {
		font-weight: 600;
		font-size: 0.8rem;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.content-text {
		font-size: 0.85rem;
		line-height: 1.6;
		color: #333;
		background: #f8f9fa;
		padding: 0.75rem;
		border-radius: 6px;
		border-left: 3px solid #667eea;
		white-space: pre-wrap;
		word-wrap: break-word;
		max-height: 300px;
		overflow-y: auto;
	}

	.source-metadata {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #f0f0f0;
	}

	.metadata-label {
		font-weight: 600;
		font-size: 0.8rem;
		color: #555;
		margin-bottom: 0.75rem;
	}

	.metadata-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 0.5rem;
	}

	.metadata-item {
		display: flex;
		gap: 0.5rem;
		font-size: 0.8rem;
	}

	.metadata-key {
		color: #777;
		font-weight: 500;
	}

	.metadata-value {
		color: #333;
		font-weight: 400;
	}

	/* Simple Sources (Legacy) */
	.simple-sources {
		margin-top: 1rem;
	}

	.simple-sources-label {
		font-weight: 600;
		font-size: 0.8rem;
		color: #666;
		margin-bottom: 0.5rem;
	}

	.simple-source-item {
		font-size: 0.85rem;
		color: #555;
		background: white;
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		border: 1px solid #e0e0e0;
		margin-bottom: 0.5rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.simple-source-icon {
		font-size: 1rem;
	}

	/* Scrollbar styling for content text */
	.content-text::-webkit-scrollbar {
		width: 6px;
	}

	.content-text::-webkit-scrollbar-track {
		background: #f1f1f1;
		border-radius: 3px;
	}

	.content-text::-webkit-scrollbar-thumb {
		background: #888;
		border-radius: 3px;
	}

	.content-text::-webkit-scrollbar-thumb:hover {
		background: #555;
	}
</style>
