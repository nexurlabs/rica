"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const WORKERS = [
    { key: "db_manager", name: "Database Manager", icon: "📁", desc: "Stores, organizes, and retrieves data from Markdown files" },
    { key: "moderator", name: "Moderator", icon: "🛡️", desc: "Auto-moderation + web search decisions" },
    { key: "responder", name: "Responder", icon: "💬", desc: "Main chatbot that responds to trigger word" },
    { key: "agent", name: "Agent", icon: "🤖", desc: "Advanced AI for designated users — code execution + creative tools" },
];

export default function WorkersPage() {
    const [config, setConfig] = useState<any>(null);
    const [prompts, setPrompts] = useState<any>({});
    const [defaultPrompts, setDefaultPrompts] = useState<any>({});
    const [saving, setSaving] = useState("");
    const [msg, setMsg] = useState("");

    useEffect(() => {
        api.getServer().then((c) => {
            setConfig(c);
            setPrompts(c.prompts || {});
        });
        api.getDefaultPrompts().then(setDefaultPrompts).catch(() => { });
    }, []);

    async function toggleWorker(workerKey: string) {
        const current = config.workers?.[workerKey]?.enabled || false;
        const update = { [workerKey]: { enabled: !current } };
        try {
            await api.updateWorkers(update);
            setConfig((prev: any) => ({
                ...prev,
                workers: { ...prev.workers, [workerKey]: { enabled: !current } },
            }));
            setMsg(`${workerKey} ${!current ? "enabled" : "disabled"}`);
            setTimeout(() => setMsg(""), 2000);
        } catch (e: any) {
            setMsg(`Error: ${e.message}`);
        }
    }

    async function savePrompt(workerKey: string) {
        setSaving(workerKey);
        try {
            await api.updatePrompts({ [workerKey]: prompts[workerKey] });
            setMsg(`${workerKey} prompt saved!`);
            setTimeout(() => setMsg(""), 2000);
        } catch (e: any) {
            setMsg(`Error: ${e.message}`);
        }
        setSaving("");
    }

    function resetPrompt(workerKey: string) {
        setPrompts((prev: any) => ({ ...prev, [workerKey]: defaultPrompts[workerKey] || "" }));
    }

    if (!config) return <div className="loading-container"><div className="loading-spinner" /><p style={{ color: "var(--text-secondary)" }}>Loading workers...</p></div>;

    return (
        <div className="fade-in max-w-3xl">
            <h1 className="text-3xl font-bold mb-2">Workers Configuration</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>Enable/disable workers and customize their prompts</p>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm" style={{ borderColor: "var(--success)" }}>✅ {msg}</div>}

            <div className="space-y-6">
                {WORKERS.map((w) => {
                    const enabled = config.workers?.[w.key]?.enabled || false;
                    return (
                        <div key={w.key} className="glass-card">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <span className="text-2xl">{w.icon}</span>
                                    <div>
                                        <h3 className="font-semibold text-lg">{w.name}</h3>
                                        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{w.desc}</p>
                                    </div>
                                </div>
                                <div className={`toggle-switch ${enabled ? "active" : ""}`} onClick={() => toggleWorker(w.key)} />
                            </div>

                            {enabled && (
                                <div>
                                    <div className="flex items-center justify-between mb-2">
                                        <label className="text-sm font-medium">System Prompt</label>
                                        <button className="text-xs" style={{ color: "var(--accent)" }} onClick={() => resetPrompt(w.key)}>
                                            Reset to default
                                        </button>
                                    </div>
                                    <textarea
                                        className="textarea-field"
                                        style={{ minHeight: "160px" }}
                                        value={prompts[w.key] || ""}
                                        onChange={(e) => setPrompts((p: any) => ({ ...p, [w.key]: e.target.value }))}
                                        placeholder={defaultPrompts[w.key]?.slice(0, 100) + "..."}
                                    />
                                    <button
                                        className="btn-primary mt-3 text-sm"
                                        onClick={() => savePrompt(w.key)}
                                        disabled={saving === w.key}
                                    >
                                        {saving === w.key ? "Saving..." : "Save Prompt"}
                                    </button>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
