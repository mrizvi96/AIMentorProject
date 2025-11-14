import { currentUser, isAuthenticated } from './stores';
import type { User } from './stores';

const API_BASE = typeof window !== 'undefined' && window.location.hostname.includes('proxy.runpod.net')
	? window.location.origin.replace('-5173.', '-8000.')
	: 'http://localhost:8000';

export async function checkAuth(): Promise<void> {
	try {
		const response = await fetch(`${API_BASE}/api/auth/me`, {
			credentials: 'include', // Important for cookies
		});

		if (response.ok) {
			const data = await response.json();
			const user = data.user; // Extract user from response

			if (user) {
				currentUser.set(user);
				isAuthenticated.set(true);
			} else {
				currentUser.set(null);
				isAuthenticated.set(false);
			}
		} else {
			currentUser.set(null);
			isAuthenticated.set(false);
		}
	} catch (error) {
		console.error('Failed to check auth status:', error);
		currentUser.set(null);
		isAuthenticated.set(false);
	}
}

export async function login(): Promise<void> {
	try {
		// Redirect to GitHub OAuth login
		window.location.href = `${API_BASE}/api/auth/github`;
	} catch (error) {
		console.error('Login failed:', error);
		throw error;
	}
}

export async function logout(): Promise<void> {
	try {
		const response = await fetch(`${API_BASE}/api/auth/logout`, {
			method: 'POST',
			credentials: 'include', // Important for cookies
		});

		if (response.ok) {
			currentUser.set(null);
			isAuthenticated.set(false);
		} else {
			throw new Error('Logout failed');
		}
	} catch (error) {
		console.error('Logout failed:', error);
		throw error;
	}
}