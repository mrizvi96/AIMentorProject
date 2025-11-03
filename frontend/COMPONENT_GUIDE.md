# Frontend Component Guide

Comprehensive guide to the AI Mentor frontend components.

---

## Overview

The frontend is built with **SvelteKit** and TypeScript, featuring a modular component architecture optimized for displaying RAG-powered chat interactions with rich source citations and workflow visualization.

### Technology Stack
- **Framework**: SvelteKit
- **Language**: TypeScript
- **State Management**: Svelte stores (native)
- **Styling**: Scoped CSS (component-level)
- **API Communication**: Fetch API + WebSocket

---

## Component Architecture

```
src/
├── routes/
│   └── +page.svelte          # Main chat page
├── lib/
│   ├── stores.ts              # Global state management
│   ├── api.ts                 # Backend API service
│   └── components/
│       ├── ChatInput.svelte           # User input component
│       ├── MessageList.svelte         # Message container
│       ├── Message.svelte             # Individual message display
│       ├── SourceViewer.svelte        # Source document viewer (NEW)
│       └── WorkflowVisualization.svelte  # Agent workflow display
```

---

## Core Components

### 1. SourceViewer.svelte ⭐ NEW

**Purpose**: Display retrieved source documents with rich metadata and expandable details.

**Features**:
- Displays detailed source information from RAG retrieval
- Expandable/collapsible cards for each source
- Relevance scoring with color-coded badges
- Document metadata (file name, page, size, type)
- Text excerpts with scrollable full content
- Sorted by relevance score (highest first)
- Backward compatible with simple string sources

**Props**:
```typescript
export let sources: string[] | SourceDocument[];
```

**Data Structure**:
```typescript
interface SourceDocument {
  text: string;            // Document excerpt
  score: number;           // Relevance score (0-1)
  metadata: {
    page_label?: string;          // Page number
    file_name: string;            // Document filename
    file_path?: string;           // Full file path
    file_type?: string;           // MIME type
    file_size?: number;           // Size in bytes
    creation_date?: string;
    last_modified_date?: string;
  };
}
```

**Usage**:
```svelte
<script>
  import SourceViewer from '$lib/components/SourceViewer.svelte';

  let sources = [
    {
      text: "Chapter 7. Loops\nLoops are compound statements that let us execute code over and over...",
      score: 0.85,
      metadata: {
        file_name: "The Self-Taught Programmer.pdf",
        page_label: "75",
        file_size: 42017852
      }
    }
  ];
</script>

<SourceViewer {sources} />
```

**Relevance Scoring**:
- **Green** (≥70%): Highly Relevant
- **Orange** (50-69%): Moderately Relevant
- **Red** (<50%): Weakly Relevant

**Styling**: Fully self-contained with scoped styles. No external CSS needed.

---

### 2. WorkflowVisualization.svelte

**Purpose**: Visualize the agentic RAG workflow steps in real-time.

**Features**:
- Shows each node in the LangGraph agent
- Status indicators (pending/running/completed)
- Animated transitions between states
- Node descriptions for clarity

**Props**:
```typescript
export let steps: WorkflowStep[];
```

**Data Structure**:
```typescript
interface WorkflowStep {
  node: string;              // Node name (retrieve, grade, rewrite, generate)
  status: 'pending' | 'running' | 'completed';
  timestamp?: Date;
}
```

**Supported Nodes**:
- `retrieve`: 🔍 Retrieve - Searching knowledge base
- `grade_documents`: ✅ Grade - Evaluating relevance
- `rewrite_query`: ✏️ Rewrite - Rephrasing query
- `generate`: 💬 Generate - Generating answer

**Usage**:
```svelte
<WorkflowVisualization steps={[
  { node: 'retrieve', status: 'completed' },
  { node: 'grade_documents', status: 'completed' },
  { node: 'generate', status: 'running' }
]} />
```

---

### 3. Message.svelte

**Purpose**: Display individual chat messages with sources and workflow.

**Features**:
- Role-based styling (user vs assistant)
- Timestamp formatting
- Loading indicator while thinking
- Integrates SourceViewer and WorkflowVisualization
- Smooth slide-in animation

**Props**:
```typescript
export let message: Message;
```

**Data Structure**:
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[] | SourceDocument[];
  workflow?: WorkflowStep[];
}
```

**Usage**:
```svelte
<Message {message} />
```

---

### 4. ChatInput.svelte

**Purpose**: Text input for user questions with UX enhancements.

**Features**:
- Auto-disable while loading
- Loading spinner in send button
- Enter to send, Shift+Enter for new line
- Disabled state when loading
- SVG send icon
- Gradient button styling

**Props**:
```typescript
export let onSend: (message: string) => void;
```

**Usage**:
```svelte
<ChatInput onSend={handleSendMessage} />
```

**UX Details**:
- Button disabled when input is empty or loading
- Textarea disabled during loading
- Visual feedback with spinner
- Keyboard shortcuts supported

---

### 5. MessageList.svelte

**Purpose**: Container for all chat messages with auto-scroll.

**Features**:
- Scrollable message container
- Auto-scroll to bottom on new messages
- Empty state placeholder
- Responsive layout

**Usage**:
```svelte
<MessageList />
```

---

## State Management (stores.ts)

### Stores

```typescript
// Message history
export const messages = writable<Message[]>([]);

// Loading state (API request in progress)
export const isLoading = writable(false);

// Error message (if any)
export const error = writable<string | null>(null);

// Current workflow steps (for real-time visualization)
export const currentWorkflow = writable<WorkflowStep[]>([]);
```

### Usage

```typescript
import { messages, isLoading, error } from '$lib/stores';

// Subscribe to changes
$: console.log($messages);

// Update values
messages.update(m => [...m, newMessage]);
isLoading.set(true);
error.set('Something went wrong');
```

---

## API Service (api.ts)

### Functions

#### `sendMessageHTTP(message: string)`
Send message via REST API (non-streaming).

**Behavior**:
1. Adds user message to store
2. Sets loading state
3. Calls `/api/chat` endpoint
4. Adds assistant response with sources
5. Clears loading state

**Error Handling**: Sets error store on failure

#### `sendMessageWebSocket(message: string)`
Send message via WebSocket (streaming).

**Behavior**:
1. Opens WebSocket connection
2. Streams tokens as they arrive
3. Updates workflow in real-time
4. Adds sources on completion

**Message Types**:
- `workflow`: Update workflow step
- `token`: Append content token
- `complete`: Response finished with sources
- `error`: Error occurred

#### `closeWebSocket()`
Close active WebSocket connection.

---

## Styling Conventions

### Colors

**Primary Gradient**:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**Status Colors**:
- Success/Active: `#4caf50` (green)
- Running/Primary: `#667eea` (purple-blue)
- Warning: `#ff9800` (orange)
- Error: `#f44336` (red)

**Neutrals**:
- Text: `#333` (dark), `#666` (medium), `#999` (light)
- Backgrounds: `#fafafa` (page), `#f8f9fa` (cards)
- Borders: `#e0e0e0` (light), `#ddd` (medium)

### Typography

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, ...
```

**Sizes**:
- Headers: `1.75rem` (h1), `1.25rem` (h2)
- Body: `1rem` (default), `0.95rem` (input)
- Small: `0.875rem` (labels), `0.8rem` (meta)
- Tiny: `0.75rem` (badges)

### Animations

**Slide In** (messages):
```css
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
```

**Spin** (loading):
```css
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

**Pulse** (indicators):
```css
@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}
```

---

## Integration Examples

### Basic Chat Page

```svelte
<script lang="ts">
  import ChatInput from '$lib/components/ChatInput.svelte';
  import MessageList from '$lib/components/MessageList.svelte';
  import { sendMessageHTTP } from '$lib/api';
  import { error } from '$lib/stores';

  async function handleSend(message: string) {
    try {
      await sendMessageHTTP(message);
    } catch (err) {
      error.set('Failed to connect to backend');
    }
  }
</script>

{#if $error}
  <div class="error-banner">{$error}</div>
{/if}

<MessageList />
<ChatInput onSend={handleSend} />
```

### Streaming Chat with Workflow

```svelte
<script lang="ts">
  import { sendMessageWebSocket } from '$lib/api';

  function handleSend(message: string) {
    sendMessageWebSocket(message); // Enables real-time workflow
  }
</script>

<ChatInput onSend={handleSend} />
```

---

## Testing

### Component Testing

```bash
# Run tests (when configured)
npm run test

# Type checking
npm run check
```

### Manual Testing Checklist

**SourceViewer**:
- [ ] Displays sources sorted by relevance
- [ ] Expand/collapse functionality works
- [ ] Relevance badges show correct colors
- [ ] Metadata displays correctly
- [ ] Scrollable text content
- [ ] Handles both detailed and simple sources

**ChatInput**:
- [ ] Disabled while loading
- [ ] Enter sends message
- [ ] Shift+Enter adds new line
- [ ] Button disabled when empty
- [ ] Loading spinner appears

**WorkflowVisualization**:
- [ ] Shows all workflow steps
- [ ] Status indicators update correctly
- [ ] Animations are smooth

**Message**:
- [ ] User/assistant styling differs
- [ ] Timestamps format correctly
- [ ] Sources display via SourceViewer
- [ ] Workflow displays correctly

---

## Performance Considerations

### Optimizations

1. **Component Splitting**: Each component is self-contained
2. **Lazy Loading**: Sources/workflow only render when present
3. **Reactive Updates**: Svelte's compiler optimizes re-renders
4. **CSS Scoping**: Prevents style conflicts and reduces bundle size

### Bundle Size

Estimated sizes (production build):
- Base framework: ~15KB gzipped
- Components: ~8KB gzipped
- Total: ~23KB gzipped

---

## Accessibility

### Features

- Semantic HTML (`<button>`, `<textarea>`, etc.)
- ARIA labels where needed
- Keyboard navigation support
- Focus indicators
- Color contrast ratios meet WCAG AA

### Future Improvements

- [ ] Add ARIA live regions for dynamic updates
- [ ] Screen reader announcements for new messages
- [ ] Keyboard shortcuts documentation
- [ ] High contrast mode

---

## Deployment

### Environment Configuration

```typescript
// src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';
```

**Production**:
```bash
# .env.production
VITE_API_BASE=https://your-backend-url.com
VITE_WS_BASE=wss://your-backend-url.com
```

### Build

```bash
# Install dependencies
npm install

# Development
npm run dev

# Production build
npm run build

# Preview production
npm run preview
```

### Deployment Platforms

**Recommended: Vercel** (Free tier)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Alternatives**:
- Netlify (automatic from Git)
- GitHub Pages (static)
- AWS S3 + CloudFront

---

## Troubleshooting

### "Cannot find module" errors

**Solution**: Run `npm install` in frontend directory

### TypeScript errors in IDE

**Solution**: Expected without npm install. Run:
```bash
cd frontend
npm install
```

### Sources not displaying

**Check**:
1. Backend returns `sources` array in response
2. API service passes sources to Message component
3. Browser console for errors

### Workflow not showing

**Check**:
1. Using WebSocket mode (`sendMessageWebSocket`)
2. Backend emits workflow events
3. `WorkflowStep` status is valid

---

## Future Enhancements

### Planned Features

1. **Code Syntax Highlighting**: For code examples in responses
2. **Markdown Rendering**: Rich text formatting
3. **Image Support**: Display images from PDFs
4. **Dark Mode**: Theme switching
5. **Export Chat**: Download conversation history
6. **Search History**: Find previous conversations
7. **Source Preview**: Inline PDF viewer
8. **Voice Input**: Speech-to-text

### Component Wishlist

- `CodeBlock.svelte`: Syntax highlighted code
- `MarkdownRenderer.svelte`: Rich text display
- `ThemeToggle.svelte`: Dark/light mode switch
- `ChatHistory.svelte`: Sidebar with past conversations
- `SettingsPanel.svelte`: User preferences

---

## Contributing

### Adding New Components

1. Create component in `src/lib/components/`
2. Follow naming convention: `ComponentName.svelte`
3. Use TypeScript for props
4. Include scoped styles
5. Export relevant types in `stores.ts`
6. Update this guide

### Style Guidelines

- Use Svelte's scoped `<style>` tags
- Follow existing color scheme
- Include animations for state changes
- Mobile-first responsive design
- Test in Chrome, Firefox, Safari

---

## Resources

- [Svelte Docs](https://svelte.dev/docs)
- [SvelteKit Docs](https://kit.svelte.dev/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Project CLAUDE.md](../CLAUDE.md) - Architecture overview

---

**Last Updated**: 2025-11-03
**Version**: 2.0.0 (SourceViewer update)
