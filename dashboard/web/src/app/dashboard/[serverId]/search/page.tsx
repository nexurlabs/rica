"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SearchPage() {
    const [enabled, setEnabled] = useState(false);
    const [serperKey, setSerperKey] = useState("");
    const [configured, setConfigured] = useState(false);
    const [msg, setMsg] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        api.getKeys().then((data) => {
            setEnabled(data.search?.enabled || false);
            setConfigured(data.search?.configured || false);
        });
    }, []);

    async function save() {
        setSaving(true);
        try {
            await api.updateSearch({
                enabled,
                serper_api_key: serperKey || undefined,
            });
            setMsg("✅ Search config saved!");
            if (serperKey) setConfigured(true);
            setSerperKey("");
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
        setSaving(false);
    }

    return (
        <div className="fade-in max-w-2xl">
            <h1 className="text-3xl font-bold mb-2">Search Configuration</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
                Enable web search via Serper API. The Moderator decides when to search and results go directly to Responder.
            </p>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm">{msg}</div>}

            <div className="glass-card">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="font-semibold text-lg">🔍 Web Search</h3>
                        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                            Moderator auto-detects when search is needed for factual queries
                        </p>
                    </div>
                    <div className={`toggle-switch ${enabled ? "active" : ""}`} onClick={() => setEnabled(!enabled)} />
                </div>

                <div className="mb-4">
                    <label className="text-sm font-medium block mb-2">Serper API Key</label>
                    <input className="input-field font-mono" type="password" value={serperKey}
                        onChange={(e) => setSerperKey(e.target.value)}
                        placeholder={configured ? "••••••••(configured)" : "Paste your Serper API key..."} />
                    <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                        Get a key at <a href="https://serper.dev" target="_blank" className="underline" style={{ color: "var(--accent)" }}>serper.dev</a>
                    </p>
                </div>

                <button className="btn-primary" onClick={save} disabled={saving}>
                    {saving ? "Saving..." : "Save Search Config"}
                </button>
            </div>

            <div className="glass-card mt-6">
                <h3 className="font-semibold mb-3">How it works</h3>
                <div className="space-y-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                    <p>1. User sends a message asking about facts, news, or real-time data</p>
                    <p>2. Moderator detects the need for search and generates a query</p>
                    <p>3. Serper API returns top results</p>
                    <p>4. Results are passed directly to Responder (no double API call)</p>
                    <p>5. Responder uses the results to generate an informed answer</p>
                </div>
            </div>
        </div>
    );
}
