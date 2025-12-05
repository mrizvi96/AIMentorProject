<script lang="ts">
  /**
   * FeedbackComponent - User rating component for AI responses
   *
   * Provides a simple UI for users to rate AI responses (1-5 stars)
   * and optionally provide detailed feedback text.
   *
   * Props:
   * - interactionId: Unique identifier for the interaction being rated
   * - onFeedback: Optional callback function called when feedback is submitted
   * - compact: If true, shows a compact version without text area
   */

  export let interactionId: string;
  export let onFeedback: (rating: number, comment: string) => void = () => {};
  export let compact: boolean = false;

  let rating = 0;
  let comment = '';
  let submitted = false;
  let submitting = false;
  let error = '';
  let hoverRating = 0;

  const starLabels = ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'];

  const submitFeedback = async () => {
    if (rating === 0) {
      error = 'Please select a rating before submitting';
      return;
    }

    submitting = true;
    error = '';

    try {
      const response = await fetch('/api/analytics/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          interaction_id: interactionId,
          rating: rating,
          feedback_text: comment.trim() || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit feedback');
      }

      submitted = true;
      onFeedback(rating, comment);

    } catch (err) {
      error = err.message || 'Failed to submit feedback. Please try again.';
      console.error('Feedback submission error:', err);
    } finally {
      submitting = false;
    }
  };

  const setRating = (value: number) => {
    if (!submitted) {
      rating = value;
      error = '';
    }
  };

  const resetFeedback = () => {
    rating = 0;
    comment = '';
    submitted = false;
    error = '';
    hoverRating = 0;
  };
</script>

<div class="feedback-container" class:compact class:submitted>
  {#if !submitted}
    <div class="feedback-header">
      <h4>Was this response helpful?</h4>
      <p class="feedback-subtitle">Your feedback helps improve the AI Mentor</p>
    </div>

    <div class="rating-section">
      <div class="rating-stars" role="radiogroup" aria-label="Rate this response">
        {#each [1, 2, 3, 4, 5] as star}
          <button
            type="button"
            class="star"
            class:active={star <= rating}
            class:hover={star <= hoverRating}
            on:click={() => setRating(star)}
            on:mouseenter={() => hoverRating = star}
            on:mouseleave={() => hoverRating = 0}
            disabled={submitted}
            aria-label={`${starLabels[star - 1]} - ${star} star${star !== 1 ? 's' : ''}`}
            aria-checked={star <= rating}
          >
            <span class="star-icon">★</span>
            {#if !compact && star === hoverRating && star > rating}
              <span class="star-label">{starLabels[star - 1]}</span>
            {/if}
          </button>
        {/each}
      </div>

      {#if rating > 0 && !compact}
        <div class="rating-text">
          <span class="selected-label">{starLabels[rating - 1]}</span>
        </div>
      {/if}
    </div>

    {#if !compact}
      <div class="comment-section">
        <textarea
          bind:value={comment}
          placeholder="Optional: Tell us more about your experience..."
          rows="3"
          class="comment-textarea"
          disabled={submitted || submitting}
          maxlength="1000"
        ></textarea>
        <div class="comment-char-count">
          {comment.length}/1000
        </div>
      </div>
    {/if}

    {#if error}
      <div class="error-message">
        <span class="error-icon">⚠️</span>
        {error}
      </div>
    {/if}

    <div class="actions">
      <button
        class="submit-btn"
        on:click={submitFeedback}
        disabled={rating === 0 || submitting}
        class:loading={submitting}
      >
        {#if submitting}
          <span class="spinner"></span>
          Submitting...
        {:else}
          Submit Feedback
        {/if}
      </button>

      {#if !compact && rating > 0}
        <button
          class="reset-btn"
          on:click={resetFeedback}
          disabled={submitting}
        >
          Clear
        </button>
      {/if}
    </div>

  {:else}
    <div class="success-message">
      <div class="success-icon">✅</div>
      <h5>Thank you for your feedback!</h5>
      <p>Your input helps us improve the AI Mentor experience.</p>
      {#if !compact}
        <button class="new-feedback-btn" on:click={resetFeedback}>
          Submit another rating
        </button>
      {/if}
    </div>
  {/if}
</div>

<style>
  .feedback-container {
    margin: 1rem 0;
    padding: 1rem;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    background-color: #f8f9fa;
    transition: all 0.2s ease;
    max-width: 500px;
  }

  .feedback-container:hover {
    border-color: #d1d5db;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  .feedback-container.compact {
    padding: 0.75rem;
    margin: 0.5rem 0;
  }

  .feedback-container.submitted {
    background-color: #f0fdf4;
    border-color: #bbf7d0;
  }

  .feedback-header {
    margin-bottom: 1rem;
  }

  .feedback-header h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
  }

  .feedback-subtitle {
    margin: 0;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .rating-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 1rem;
  }

  .compact .rating-section {
    margin-bottom: 0.5rem;
  }

  .rating-stars {
    display: flex;
    gap: 0.25rem;
    margin-bottom: 0.5rem;
  }

  .star {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #d1d5db;
    transition: all 0.2s ease;
    padding: 0.25rem;
    border-radius: 4px;
    position: relative;
    line-height: 1;
  }

  .star:hover {
    transform: scale(1.1);
  }

  .star.active,
  .star.hover {
    color: #fbbf24;
  }

  .star-icon {
    display: block;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
  }

  .star-label {
    position: absolute;
    top: -25px;
    left: 50%;
    transform: translateX(-50%);
    background: #374151;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    white-space: nowrap;
    z-index: 10;
  }

  .star-label::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: #374151;
  }

  .rating-text {
    margin-top: 0.5rem;
  }

  .selected-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #059669;
  }

  .comment-section {
    margin-bottom: 1rem;
    position: relative;
  }

  .comment-textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    resize: vertical;
    font-family: inherit;
    font-size: 0.875rem;
    line-height: 1.5;
    transition: border-color 0.2s ease;
  }

  .comment-textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .comment-textarea:disabled {
    background-color: #f3f4f6;
    color: #6b7280;
    cursor: not-allowed;
  }

  .comment-char-count {
    text-align: right;
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 0.25rem;
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    color: #dc2626;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  .error-icon {
    font-size: 1rem;
  }

  .actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .submit-btn {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .submit-btn:hover:not(:disabled) {
    background: #2563eb;
  }

  .submit-btn:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .submit-btn.loading {
    background: #3b82f6;
    opacity: 0.8;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid #ffffff;
    border-top: 2px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .reset-btn {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .reset-btn:hover:not(:disabled) {
    background: #e5e7eb;
  }

  .reset-btn:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .success-message {
    text-align: center;
    color: #059669;
  }

  .success-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .success-message h5 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .success-message p {
    margin: 0 0 1rem 0;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .new-feedback-btn {
    background: #059669;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .new-feedback-btn:hover {
    background: #047857;
  }

  /* Compact mode styles */
  .compact .feedback-header {
    margin-bottom: 0.5rem;
  }

  .compact .feedback-header h4 {
    font-size: 0.875rem;
  }

  .compact .feedback-subtitle {
    font-size: 0.75rem;
  }

  .compact .rating-stars {
    margin-bottom: 0;
  }

  .compact .star {
    font-size: 1.25rem;
    padding: 0.125rem;
  }

  .compact .actions {
    justify-content: center;
  }

  .compact .submit-btn {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  /* Responsive design */
  @media (max-width: 640px) {
    .feedback-container {
      margin: 0.75rem 0;
      padding: 0.75rem;
    }

    .rating-stars {
      gap: 0.125rem;
    }

    .star {
      font-size: 1.25rem;
    }

    .actions {
      flex-direction: column;
    }

    .submit-btn,
    .reset-btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>