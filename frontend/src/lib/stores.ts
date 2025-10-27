import { writable } from 'svelte/store';

export interface Message {
	id: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: Date;
	sources?: string[];
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
