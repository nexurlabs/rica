"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function UsagePage() {
    const [usage, setUsage] = useState<any>({});

    useEffect(() => {
        api.getUsage().then((d) => setUsage(d.usage || {}));
    }, []);

    const workers = [
        { key: "db_manager", name: "Database Manager", icon: "📁", color: "#3498db" },
        { key: "moderator", name: "Moderator", icon: "🛡️", color: "#f39c12" },
        { key: "responder", name: "Responder", icon: "💬", color: "#2ecc71" },
        { key: "agent", name: "Agent", icon: "🤖", color: "#e74c3c" },
    ];

    const totalTokens = workers.reduce((s, w) => s + (usage[`${w.key}_tokens`] || 0), 0);
    const totalCalls = workers.reduce((s, w) => s + (usage[`${w.key}_calls`] || 0), 0);

    return (
        <div className="fade-in max-w-3xl">
            <h1 className="text-3xl font-bold mb-2">Usage Statistics</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
                Track token usage and API calls per worker
            </p>

            {/* Totals */}
            <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="glass-card text-center">
                    <p className="text-4xl font-bold gradient-text">{formatNum(totalTokens)}</p>
                    <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Total Tokens</p>
                </div>
                <div className="glass-card text-center">
                    <p className="text-4xl font-bold gradient-text">{formatNum(totalCalls)}</p>
                    <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Total API Calls</p>
                </div>
            </div>

            {/* Per-worker breakdown */}
            <div className="space-y-4">
                {workers.map((w) => {
                    const tokens = usage[`${w.key}_tokens`] || 0;
                    const calls = usage[`${w.key}_calls`] || 0;
                    const pct = totalTokens > 0 ? (tokens / totalTokens) * 100 : 0;

                    return (
                        <div key={w.key} className="glass-card">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    <span className="text-xl">{w.icon}</span>
                                    <span className="font-semibold">{w.name}</span>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold" style={{ color: w.color }}>{formatNum(tokens)} tokens</p>
                                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{formatNum(calls)} calls</p>
                                </div>
                            </div>
                            <div className="w-full h-2 rounded-full" style={{ background: "var(--bg-secondary)" }}>
                                <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: w.color }} />
                            </div>
                        </div>
                    );
                })}
            </div>

            {usage.last_updated && (
                <p className="text-xs mt-6 text-center" style={{ color: "var(--text-secondary)" }}>
                    Last updated: {usage.last_updated}
                </p>
            )}
        </div>
    );
}

function formatNum(n: number): string {
    if (!n) return "0";
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return String(n);
}
