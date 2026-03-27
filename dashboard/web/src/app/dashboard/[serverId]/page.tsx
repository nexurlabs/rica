"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ServerDashboard() {
    const [config, setConfig] = useState<any>(null);
    const [usage, setUsage] = useState<any>({});
    const [errors, setErrors] = useState<any[]>([]);

    useEffect(() => {
        api.getServer().then(setConfig).catch(() => { });
        api.getUsage().then((d) => setUsage(d.usage || {})).catch(() => { });
        api.getErrors(5).then((d) => setErrors(d.errors || [])).catch(() => { });
    }, []);

    if (!config) return <div className="loading-container"><div className="loading-spinner" /><p style={{ color: "var(--text-secondary)" }}>Loading dashboard...</p></div>;

    const workers = config.workers || {};
    const activeCount = Object.values(workers).filter((w: any) => w.enabled).length;

    return (
        <div className="fade-in">
            <h1 className="text-3xl font-bold mb-1">{config.server_name || "Rica"}</h1>
            <p className="mb-8" style={{ color: "var(--text-secondary)" }}>
                Trigger: <span className="font-mono" style={{ color: "var(--accent-light)" }}>{config.trigger_word}</span>
            </p>

            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4 mb-8">
                {[
                    { label: "Active Workers", value: `${activeCount}/4`, color: "var(--success)" },
                    { label: "Total API Calls", value: formatNumber(sumCalls(usage)), color: "var(--accent)" },
                    { label: "Tokens Used", value: formatNumber(sumTokens(usage)), color: "var(--info)" },
                    { label: "Recent Errors", value: errors.length, color: errors.length > 0 ? "var(--error)" : "var(--success)" },
                ].map((stat) => (
                    <div key={stat.label} className="glass-card text-center">
                        <p className="text-3xl font-bold" style={{ color: stat.color }}>{stat.value}</p>
                        <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{stat.label}</p>
                    </div>
                ))}
            </div>

            {/* Workers Overview */}
            <h2 className="text-xl font-semibold mb-4">Workers</h2>
            <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                    { key: "db_manager", name: "Database Manager", icon: "📁", desc: "Stores & retrieves data" },
                    { key: "moderator", name: "Moderator", icon: "🛡️", desc: "Auto-moderation + search" },
                    { key: "responder", name: "Responder", icon: "💬", desc: "Main chatbot" },
                    { key: "agent", name: "Agent", icon: "🤖", desc: "Advanced AI + tools" },
                ].map((w) => {
                    const enabled = workers[w.key]?.enabled;
                    return (
                        <div key={w.key} className="glass-card">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="text-xl">{w.icon}</span>
                                    <span className="font-semibold">{w.name}</span>
                                </div>
                                <span className={`status-dot ${enabled ? "active" : "inactive"}`}></span>
                            </div>
                            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{w.desc}</p>
                            <div className="flex justify-between mt-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                                <span>{formatNumber(usage[`${w.key}_calls`] || 0)} calls</span>
                                <span>{formatNumber(usage[`${w.key}_tokens`] || 0)} tokens</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Recent Errors */}
            {errors.length > 0 && (
                <>
                    <h2 className="text-xl font-semibold mb-4">Recent Errors</h2>
                    <div className="space-y-2">
                        {errors.slice(0, 5).map((err, i) => (
                            <div key={i} className="glass-card py-3 flex items-center justify-between">
                                <div>
                                    <span className="text-xs font-mono px-2 py-1 rounded" style={{ background: "rgba(255,82,82,0.15)", color: "var(--error)" }}>
                                        {err.worker}
                                    </span>
                                    <span className="text-sm ml-3">{err.error}</span>
                                </div>
                                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{err.timestamp}</span>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

function formatNumber(n: number): string {
    if (!n) return "0";
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return String(n);
}

function sumCalls(usage: any): number {
    return (usage.db_manager_calls || 0) + (usage.moderator_calls || 0) +
        (usage.responder_calls || 0) + (usage.agent_calls || 0);
}

function sumTokens(usage: any): number {
    return (usage.db_manager_tokens || 0) + (usage.moderator_tokens || 0) +
        (usage.responder_tokens || 0) + (usage.agent_tokens || 0);
}
