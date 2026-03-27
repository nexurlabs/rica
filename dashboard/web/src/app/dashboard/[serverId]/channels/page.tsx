"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Dropdown } from "@/components/Dropdown";

const PROVIDERS = [
    { id: "google_ai", name: "Google AI" },
    { id: "openrouter", name: "OpenRouter" },
    { id: "openai", name: "OpenAI" },
    { id: "anthropic", name: "Anthropic" },
    { id: "groq", name: "Groq (Fast)" },
];

export default function ChannelsPage() {
    const [channelId, setChannelId] = useState("");
    const [channelConfig, setChannelConfig] = useState<any>(null);
    const [msg, setMsg] = useState("");
    const [fetchedModels, setFetchedModels] = useState<Record<string, string[]>>({});
    const [fetchingModels, setFetchingModels] = useState<Record<string, boolean>>({});

    async function loadChannel() {
        if (!channelId) return;
        try {
            const data = await api.getChannelConfig(channelId);
            setChannelConfig(data || {});
            setMsg("");
        } catch (e) {
            setChannelConfig({});
        }
    }

    async function saveChannel() {
        try {
            await api.setChannelConfig(channelId, channelConfig);
            setMsg("✅ Channel config saved!");
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
    }

    async function fetchModels(worker: string, provider: string, apiKey: string) {
        if (!apiKey) {
            setMsg("❌ Please enter an API key to fetch models");
            return;
        }
        setFetchingModels(prev => ({ ...prev, [worker]: true }));
        try {
            const data = await api.getModels(provider || "google_ai", apiKey);
            setFetchedModels(prev => ({ ...prev, [worker]: data.models || [] }));
            setMsg(`✅ Models fetched for ${worker.replace("_", " ")}`);
        } catch (e: any) {
            setMsg(`❌ Failed to fetch models: ${e.message}`);
        }
        setFetchingModels(prev => ({ ...prev, [worker]: false }));
    }

    return (
        <div className="fade-in max-w-2xl pb-10">
            <h1 className="text-3xl font-bold mb-2">Channel Configuration</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
                Set per-channel overrides for workers, keys, and prompts
            </p>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm">{msg}</div>}

            {/* Channel selector */}
            <div className="glass-card mb-6">
                <h3 className="font-semibold mb-3">Select Channel</h3>
                <div className="flex gap-2">
                    <input className="input-field flex-1 font-mono" value={channelId}
                        onChange={(e) => setChannelId(e.target.value)}
                        placeholder="Paste Channel ID (right-click channel → Copy Channel ID)" />
                    <button className="btn-primary" onClick={loadChannel}>Load</button>
                </div>
            </div>

            {/* Channel config editor */}
            {channelConfig !== null && (
                <div className="glass-card">
                    <h3 className="font-semibold mb-4">Channel Overrides</h3>

                    {/* Worker overrides */}
                    <div className="space-y-3 mb-6">
                        <h4 className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Workers (override global settings)</h4>
                        {["db_manager", "moderator", "responder", "agent"].map((w, idx) => {
                            const enabled = channelConfig?.workers?.[w]?.enabled;
                            const apiKey = channelConfig?.workers?.[w]?.api_key || "";
                            const provider = channelConfig?.workers?.[w]?.provider || "google_ai";
                            const model = channelConfig?.workers?.[w]?.model || "";
                            const prompt = channelConfig?.workers?.[w]?.prompt || "";

                            return (
                                <div key={w} className="flex flex-col gap-2 p-4 rounded-xl mb-4" style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", position: "relative", zIndex: 10 - idx }}>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-semibold uppercase tracking-wider">{w.replace("_", " ")}</span>
                                        <div className="flex items-center gap-3">
                                            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                                                {enabled === undefined ? "Using global" : enabled ? "Enabled" : "Disabled"}
                                            </span>
                                            <Dropdown
                                                value={enabled === undefined ? "global" : enabled ? "on" : "off"}
                                                options={[
                                                    { label: "Use Global", value: "global" },
                                                    { label: "On", value: "on" },
                                                    { label: "Off", value: "off" }
                                                ]}
                                                onChange={(val) => {
                                                    setChannelConfig((prev: any) => ({
                                                        ...prev,
                                                        workers: {
                                                            ...prev.workers,
                                                            [w]: val === "global" ? undefined : { ...prev.workers?.[w], enabled: val === "on" },
                                                        },
                                                    }));
                                                }}
                                            />
                                        </div>
                                    </div>

                                    {w !== "agent" && (
                                        <div className="mt-4 space-y-4 pt-4 border-t" style={{ borderColor: "var(--border)" }}>
                                            {/* Provider Selection */}
                                            <div>
                                                <label className="text-xs mb-1.5 block font-medium" style={{ color: "var(--text-secondary)" }}>Provider Override</label>
                                                <div className="flex flex-wrap gap-2">
                                                    {PROVIDERS.map((p) => (
                                                        <button
                                                            key={p.id}
                                                            type="button"
                                                            className="text-xs py-1.5 px-3 rounded-lg transition-all"
                                                            style={{
                                                                border: "1px solid",
                                                                borderColor: provider === p.id ? "var(--accent)" : "var(--border)",
                                                                background: provider === p.id ? "rgba(108, 92, 231, 0.18)" : "transparent",
                                                                color: provider === p.id ? "var(--text)" : "var(--text-secondary)"
                                                            }}
                                                            onClick={() => {
                                                                setChannelConfig((prev: any) => ({
                                                                    ...prev,
                                                                    workers: {
                                                                        ...prev.workers,
                                                                        [w]: { ...prev.workers?.[w], provider: p.id },
                                                                    },
                                                                }));
                                                            }}
                                                        >
                                                            {p.name}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* API Key */}
                                            <div>
                                                <label className="text-xs mb-1.5 block font-medium" style={{ color: "var(--text-secondary)" }}>Channel API Key Override</label>
                                                <div className="flex gap-2">
                                                    <input
                                                        type="password"
                                                        className="input-field text-xs font-mono flex-1"
                                                        placeholder="Leave empty to use global key..."
                                                        value={apiKey}
                                                        onChange={(e) => {
                                                            const val = e.target.value;
                                                            setChannelConfig((prev: any) => ({
                                                                ...prev,
                                                                workers: {
                                                                    ...prev.workers,
                                                                    [w]: { ...prev.workers?.[w], api_key: val },
                                                                },
                                                            }));
                                                        }}
                                                        autoComplete="new-password"
                                                        autoCorrect="off"
                                                        autoCapitalize="none"
                                                        spellCheck={false}
                                                        data-lpignore="true"
                                                        data-1p-ignore="true"
                                                        data-bwignore="true"
                                                    />
                                                    <button
                                                        className="btn-primary text-xs whitespace-nowrap px-4"
                                                        onClick={() => fetchModels(w, provider, apiKey)}
                                                        disabled={fetchingModels[w] || !apiKey}
                                                        style={{ opacity: (!apiKey || fetchingModels[w]) ? 0.5 : 1 }}
                                                    >
                                                        {fetchingModels[w] ? "Fetching..." : "Fetch Models"}
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Model Selection */}
                                            {fetchedModels[w] && fetchedModels[w].length > 0 && (
                                                <div className="fade-in">
                                                    <label className="text-xs mb-1.5 block font-medium" style={{ color: "var(--text-secondary)" }}>Model Override</label>
                                                    <Dropdown
                                                        className="w-full text-xs"
                                                        value={model}
                                                        options={[
                                                            { label: "-- Default for Provider --", value: "" },
                                                            ...fetchedModels[w].map((m) => ({ label: m, value: m }))
                                                        ]}
                                                        onChange={(val) => {
                                                            setChannelConfig((prev: any) => ({
                                                                ...prev,
                                                                workers: {
                                                                    ...prev.workers,
                                                                    [w]: { ...prev.workers?.[w], model: val },
                                                                },
                                                            }));
                                                        }}
                                                    />
                                                </div>
                                            )}

                                            {/* System Prompt Override */}
                                            <div>
                                                <label className="text-xs mb-1.5 block font-medium" style={{ color: "var(--text-secondary)" }}>System Prompt Override</label>
                                                <textarea
                                                    className="input-field text-xs w-full min-h-[80px]"
                                                    placeholder="Leave empty to use the standard worker prompt..."
                                                    value={prompt}
                                                    onChange={(e) => {
                                                        const val = e.target.value;
                                                        setChannelConfig((prev: any) => ({
                                                            ...prev,
                                                            workers: {
                                                                ...prev.workers,
                                                                [w]: { ...prev.workers?.[w], prompt: val },
                                                            },
                                                        }));
                                                    }}
                                                />
                                            </div>

                                            {/* Save Button for this specific worker override layout */}
                                            <div className="flex justify-end pt-2">
                                                <button
                                                    className="btn-secondary text-xs"
                                                    onClick={saveChannel}
                                                >
                                                    Save Overrides for {w.replace("_", " ")}
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    <button className="btn-primary w-full py-3 text-sm font-semibold" onClick={saveChannel}>Save All Channel Configs</button>
                </div>
            )}

            <div className="glass-card mt-6">
                <h3 className="font-semibold mb-3">💡 How it works</h3>
                <div className="text-sm space-y-2" style={{ color: "var(--text-secondary)" }}>
                    <p>• Channel overrides take priority over global settings.</p>
                    <p>• You can set a unique System Prompt per channel for distinct personas.</p>
                    <p>• Fetching models requires a valid API key for that provider.</p>
                </div>
            </div>
        </div>
    );
}
