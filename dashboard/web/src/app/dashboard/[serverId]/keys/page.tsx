"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Dropdown } from "@/components/Dropdown";

const KEY_NAMES = [
    { key: "global_key", label: "Global AI Key", desc: "Shared key for all workers (fallback)" },
    { key: "db_manager", label: "Database Manager", desc: "Worker override key for DB Manager" },
    { key: "moderator", label: "Moderator", desc: "Worker override key for Moderator" },
    { key: "responder", label: "Responder", desc: "Worker override key for Responder" },
    { key: "agent", label: "Agent", desc: "Worker override key for Agent" },
];

const PROVIDERS = [
    { id: "google_ai", name: "Google AI" },
    { id: "openrouter", name: "OpenRouter" },
    { id: "openai", name: "OpenAI" },
    { id: "anthropic", name: "Anthropic" },
    { id: "groq", name: "Groq (Fast)" },
];

export default function KeysPage() {
    const [keysInfo, setKeysInfo] = useState<any>(null);
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [newKey, setNewKey] = useState("");
    const [saving, setSaving] = useState(false);
    const [validating, setValidating] = useState(false);
    const [msg, setMsg] = useState("");

    // Model Selection State
    const [selectedProvider, setSelectedProvider] = useState("google_ai");
    const [selectedModel, setSelectedModel] = useState("");
    const [fetchedModels, setFetchedModels] = useState<Record<string, string[]>>({});

    useEffect(() => { loadKeys(); }, []);

    async function loadKeys() {
        const data = await api.getKeys();
        setKeysInfo(data);
    }

    // Handles the first step: Validate Key & Fetch Models
    async function validateAndFetchModels(keyName: string, isConfigured: boolean) {
        setValidating(true);
        setMsg("");
        try {
            if (newKey) {
                // Validate new key
                const isValid = await api.validateKey({ api_key: newKey, provider: selectedProvider });
                if (!isValid.valid) {
                    throw new Error(isValid.message);
                }
                setMsg("✅ Key validated. Fetching models...");

                // Fetch models dynamically
                const mRes = await api.getModels(selectedProvider, newKey);
                setFetchedModels(prev => ({ ...prev, [keyName]: mRes.models || [] }));
                setMsg("✅ Models fetched!");
            } else if (isConfigured) {
                setMsg("Fetching models from saved key...");
                const mRes = await api.getSavedModels(keyName);
                setFetchedModels(prev => ({ ...prev, [keyName]: mRes.models || [] }));
                setMsg("✅ Models fetched!");
            } else {
                setMsg("❌ Please enter an API key first.");
            }
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
        setValidating(false);
    }

    // Handles the final step: Saving the entire config (provider, key, model)
    async function saveKeyConfig(keyName: string) {
        setSaving(true);
        setMsg("");
        try {
            await api.setKey({
                key_name: keyName,
                api_key: newKey.trim(),
                provider: selectedProvider,
                model: selectedModel
            });
            setMsg(`✅ ${keyName} completed and saved!`);
            setEditingKey(null);
            setNewKey("");
            setSelectedModel("");
            loadKeys();
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
        setSaving(false);
    }

    async function deleteKey(keyName: string) {
        try {
            await api.deleteKey(keyName);
            setMsg(`🗑️ ${keyName} removed`);
            loadKeys();
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
    }

    if (!keysInfo) return <div className="loading-container"><div className="loading-spinner" /><p style={{ color: "var(--text-secondary)" }}>Loading keys...</p></div>;

    return (
        <div className="fade-in max-w-3xl pb-10">
            <h1 className="text-3xl font-bold mb-2">API Keys</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>Manage your BYOK API keys. Keys are encrypted at rest.</p>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm">{msg}</div>}

            <div className="space-y-4">
                {KEY_NAMES.map((k) => {
                    const info = keysInfo.keys?.[k.key] || {};
                    const isConfigured = info.configured;
                    const hasFetchedModels = fetchedModels[k.key] && fetchedModels[k.key].length > 0;

                    return (
                        <div key={k.key} className="glass-card" style={{ position: "relative", zIndex: editingKey === k.key ? 10 : 1 }}>
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="font-semibold">{k.label}</h3>
                                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{k.desc}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                    {isConfigured ? (
                                        <>
                                            <div className="flex flex-col items-end">
                                                <span className="text-sm font-mono" style={{ color: "var(--text-secondary)" }}>{info.masked}</span>
                                                <span className="text-xs mt-1" style={{ background: "rgba(108,92,231,0.1)", color: "var(--accent)", padding: "2px 6px", borderRadius: "4px" }}>
                                                    {info.model || info.provider || "Default"}
                                                </span>
                                            </div>
                                            <span className="status-dot active"></span>
                                        </>
                                    ) : (
                                        <span className="text-sm" style={{ color: "var(--text-secondary)" }}>Not set</span>
                                    )}
                                </div>
                            </div>

                            {editingKey === k.key ? (
                                <div className="mt-4 pt-4 border-t" style={{ borderColor: "var(--border)" }}>
                                    <label className="text-xs block mb-2" style={{ color: "var(--text-secondary)" }}>Provider</label>
                                    <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 mb-4">
                                        {PROVIDERS.map((p) => (
                                            <button
                                                key={p.id}
                                                type="button"
                                                className="btn-secondary text-xs py-1.5"
                                                style={{
                                                    borderColor: selectedProvider === p.id ? "var(--accent)" : "var(--border)",
                                                    background: selectedProvider === p.id ? "rgba(108, 92, 231, 0.18)" : "transparent",
                                                    color: selectedProvider === p.id ? "var(--text)" : "var(--text-secondary)"
                                                }}
                                                onClick={() => {
                                                    setSelectedProvider(p.id);
                                                    setFetchedModels(prev => ({ ...prev, [k.key]: [] }));
                                                }}
                                            >
                                                {p.name}
                                            </button>
                                        ))}
                                    </div>

                                    <label className="text-xs block mb-2" style={{ color: "var(--text-secondary)" }}>API Key</label>
                                    <div className="flex gap-2 mb-4">
                                        <input
                                            className="input-field font-mono text-sm flex-1"
                                            type="password"
                                            value={newKey}
                                            onChange={(e) => {
                                                setNewKey(e.target.value);
                                                setFetchedModels(prev => ({ ...prev, [k.key]: [] }));
                                            }}
                                            placeholder={isConfigured ? "Leave empty to keep existing key..." : "Paste new API key..."}
                                            autoComplete="new-password"
                                            autoCorrect="off"
                                            autoCapitalize="none"
                                            spellCheck={false}
                                            data-lpignore="true"
                                            data-1p-ignore="true"
                                            data-bwignore="true"
                                        />
                                        <button
                                            className="btn-primary text-sm whitespace-nowrap"
                                            onClick={() => validateAndFetchModels(k.key, isConfigured)}
                                            disabled={validating || (!newKey && !isConfigured)}
                                            style={{ opacity: validating || (!newKey && !isConfigured) ? 0.5 : 1 }}
                                        >
                                            {validating ? "Validating & Fetching..." : "Validate & Fetch Models"}
                                        </button>
                                    </div>

                                    {/* Models Selection */}
                                    {hasFetchedModels && (
                                        <div className="mb-4 fade-in">
                                            <label className="text-xs block mb-2" style={{ color: "var(--text-secondary)" }}>Select Default Model</label>
                                            <Dropdown
                                                className="w-full"
                                                value={selectedModel}
                                                options={[
                                                    { label: "-- Default Provider Model --", value: "" },
                                                    ...fetchedModels[k.key].map(m => ({ label: m, value: m }))
                                                ]}
                                                onChange={setSelectedModel}
                                            />
                                        </div>
                                    )}

                                    {/* Action Buttons */}
                                    <div className="flex gap-2 mt-4 pt-4 border-t" style={{ borderColor: "var(--border)" }}>
                                        <button
                                            className="btn-primary flex-1 text-sm font-semibold py-2"
                                            onClick={() => saveKeyConfig(k.key)}
                                            disabled={saving}
                                        >
                                            {saving ? "Saving..." : "Save Configuration"}
                                        </button>
                                        <button
                                            className="btn-secondary text-sm px-6"
                                            onClick={() => {
                                                setEditingKey(null);
                                                setNewKey("");
                                                setSelectedModel("");
                                            }}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex gap-2 mt-3">
                                    <button
                                        className="btn-secondary text-sm"
                                        onClick={() => {
                                            setEditingKey(k.key);
                                            setSelectedProvider(info.provider || "google_ai");
                                            setSelectedModel(info.model || "");
                                        }}
                                    >
                                        {isConfigured ? "Edit Config" : "Set Key"}
                                    </button>
                                    {isConfigured && (
                                        <button className="text-sm px-3 py-2 rounded-lg transition-all hover:bg-[rgba(255,82,82,0.15)]" style={{ color: "var(--error)", cursor: "pointer" }} onClick={() => deleteKey(k.key)}>Remove</button>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
