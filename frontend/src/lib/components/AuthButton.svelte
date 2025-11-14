<script lang="ts">
	import { onMount } from 'svelte';
	import { currentUser, isAuthenticated } from '$lib/stores';
	import { checkAuth, login, logout } from '$lib/auth';

	let isLoading = $state(true);

	onMount(async () => {
		try {
			await checkAuth();
		} catch (error) {
			console.error('Failed to check auth status:', error);
		} finally {
			isLoading = false;
		}
	});

	async function handleLogin() {
		try {
			await login();
		} catch (error) {
			console.error('Login failed:', error);
		}
	}

	async function handleLogout() {
		try {
			await logout();
		} catch (error) {
			console.error('Logout failed:', error);
		}
	}
</script>

{#if isLoading}
	<div class="auth-loading">Loading...</div>
{:else if $isAuthenticated && $currentUser}
	<div class="user-info">
		{#if $currentUser.github_avatar_url}
			<img
				src={$currentUser.github_avatar_url}
				alt="GitHub Avatar"
				class="avatar"
			/>
		{/if}
		<span class="user-name">{$currentUser.github_name || $currentUser.github_login}</span>
		<button class="logout-btn" on:click={handleLogout}>Logout</button>
	</div>
{:else}
	<button class="login-btn" on:click={handleLogin}>
		<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
			<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
		</svg>
		Login with GitHub
	</button>
{/if}

<style>
	.auth-loading {
		padding: 0.5rem 1rem;
		color: #00ff00;
		font-family: 'Courier New', monospace;
		font-size: 0.875rem;
	}

	.user-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		background: rgba(0, 255, 0, 0.1);
		border: 1px solid #00ff00;
		border-radius: 20px;
	}

	.avatar {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		border: 1px solid #00ff00;
	}

	.user-name {
		color: #00ff00;
		font-size: 0.875rem;
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}

	.login-btn, .logout-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: transparent;
		color: #00ff00;
		border: 1px solid #00ff00;
		border-radius: 20px;
		cursor: pointer;
		font-family: 'Courier New', monospace;
		font-size: 0.875rem;
		transition: all 0.2s ease;
		text-decoration: none;
	}

	.login-btn:hover, .logout-btn:hover {
		background: #00ff00;
		color: #000000;
		box-shadow: 0 0 10px #00ff00;
		transform: translateY(-1px);
	}

	.logout-btn {
		background: rgba(255, 0, 0, 0.1);
		border-color: #ff0000;
		color: #ff0000;
	}

	.logout-btn:hover {
		background: #ff0000;
		color: #000000;
		box-shadow: 0 0 10px #ff0000;
	}

	svg {
		width: 16px;
		height: 16px;
	}
</style>