// Rica Dashboard - API Client (Local Self-Hosted Mode)

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Single-instance: Rica always uses "local" as the server ID
export const LOCAL_SERVER_ID = 'local';

class ApiClient {
    private async request(path: string, options: RequestInit = {}) {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string> || {}),
        };

        const res = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers,
        });

        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${res.status}`);
        }

        return res.json();
    }

    // Auth (local mode — auto-authenticated)
    async getMe() { return this.request('/auth/me'); }

    // Server config (single-instance — always "local")
    async getServer() { return this.request(`/servers/${LOCAL_SERVER_ID}`); }
    async setupServer(data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/setup`, { method: 'POST', body: JSON.stringify(data) }); }
    async updateConfig(data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/config`, { method: 'PATCH', body: JSON.stringify(data) }); }
    async updateWorkers(data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/workers`, { method: 'PATCH', body: JSON.stringify(data) }); }
    async updatePrompts(data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/prompts`, { method: 'PATCH', body: JSON.stringify(data) }); }
    async getDefaultPrompts() { return this.request(`/servers/${LOCAL_SERVER_ID}/prompts/defaults`); }
    async updateAgentUsers(ids: string[]) { return this.request(`/servers/${LOCAL_SERVER_ID}/agent-users`, { method: 'PUT', body: JSON.stringify({ user_ids: ids }) }); }
    async updateSearch(data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/search`, { method: 'PATCH', body: JSON.stringify(data) }); }
    async updateCreative(data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/creative`, { method: 'PATCH', body: JSON.stringify(data) }); }

    // Channel config
    async getChannelConfig(channelId: string) { return this.request(`/servers/${LOCAL_SERVER_ID}/channels/${channelId}`); }
    async setChannelConfig(channelId: string, data: any) { return this.request(`/servers/${LOCAL_SERVER_ID}/channels/${channelId}`, { method: 'PUT', body: JSON.stringify(data) }); }

    // Keys
    async getKeys() { return this.request(`/keys/${LOCAL_SERVER_ID}`); }
    async setKey(data: any) { return this.request(`/keys/${LOCAL_SERVER_ID}/set`, { method: 'POST', body: JSON.stringify(data) }); }
    async setProvider(provider: string) { return this.request(`/keys/${LOCAL_SERVER_ID}/provider`, { method: 'PATCH', body: JSON.stringify({ provider }) }); }
    async validateKey(data: any) { return this.request('/keys/validate', { method: 'POST', body: JSON.stringify(data) }); }
    async deleteKey(keyName: string) { return this.request(`/keys/${LOCAL_SERVER_ID}/${keyName}`, { method: 'DELETE' }); }
    async getModels(provider: string, api_key: string) { return this.request('/keys/models', { method: 'POST', body: JSON.stringify({ provider, api_key }) }); }
    async getSavedModels(keyName: string) { return this.request(`/keys/${LOCAL_SERVER_ID}/models/${keyName}`); }

    // Data browser
    async listFiles(prefix = '') { return this.request(`/data/${LOCAL_SERVER_ID}/files?prefix=${encodeURIComponent(prefix)}`); }
    async readFile(path: string) { return this.request(`/data/${LOCAL_SERVER_ID}/file?path=${encodeURIComponent(path)}`); }

    // Stats
    async getUsage() { return this.request(`/stats/${LOCAL_SERVER_ID}/usage`); }
    async getErrors(limit = 50) { return this.request(`/stats/${LOCAL_SERVER_ID}/errors?limit=${limit}`); }
    async clearErrors() { return this.request(`/stats/${LOCAL_SERVER_ID}/errors`, { method: 'DELETE' }); }

    // System
    async getVersion() { return this.request(`/version`); }
}

export const api = new ApiClient();
