import { writable } from 'svelte/store';

export interface SourceDocument {
	text: string;
	score: number;
	metadata: {
		page_label?: string;
		file_name: string;
		file_path?: string;
		file_type?: string;
		file_size?: number;
		creation_date?: string;
		last_modified_date?: string;
	};
}

export interface Message {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: Date;
	sources?: string[] | SourceDocument[]; // Support both formats
	workflow?: WorkflowStep[];
}

export interface WorkflowStep {
	node: string;
	status: 'pending' | 'running' | 'completed';
	timestamp?: Date;
}

export const messages = writable<Message[]>([]);
export const isLoading = writable(false);
export const error = writable<string | null>(null);
export const currentWorkflow = writable<WorkflowStep[]>([]);

// Authentication stores
export interface User {
	github_id: number;
	github_login: string;
	github_name?: string;
	github_avatar_url?: string;
	session_id: string;
}

export const currentUser = writable<User | null>(null);
export const isAuthenticated = writable(false);
