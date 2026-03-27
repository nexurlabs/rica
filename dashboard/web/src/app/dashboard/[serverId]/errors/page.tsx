"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ErrorsPage() {
    const [errors, setErrors] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [msg, setMsg] = useState("");

    useEffect(() => { loadErrors(); }, []);

    async function loadErrors() {
        setLoading(true);
        try {
            const data = await api.getErrors();
            setErrors(data.errors || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    }

    async function clearAll() {
        try {
            await api.clearErrors();
            setErrors([]);
            setMsg("✅ Errors cleared");
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
    }

    const workerColors: Record<string, string> = {
        db_manager: "#3498db",
        moderator: "#f39c12",
        responder: "#2ecc71",
        agent: "#e74c3c",
    };

    return (
        <div className="fade-in max-w-3xl">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-3xl font-bold">Error Logs</h1>
                    <p style={{ color: "var(--text-secondary)" }}>{errors.length} errors recorded</p>
                </div>
                {errors.length > 0 && (
                    <button className="btn-danger text-sm" onClick={clearAll}>Clear All</button>
                )}
            </div>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm">{msg}</div>}

            {errors.length === 0 ? (
                <div className="glass-card text-center py-12">
                    <p className="text-4xl mb-3">✨</p>
                    <p className="text-lg">No errors!</p>
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Everything is running smoothly</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {errors.map((err, i) => (
                        <div key={i} className="glass-card">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs font-mono px-2 py-1 rounded-lg"
                                    style={{ background: `${workerColors[err.worker] || "gray"}22`, color: workerColors[err.worker] || "gray" }}>
                                    {err.worker?.replace("_", " ")}
                                </span>
                                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{err.timestamp}</span>
                            </div>
                            <p className="text-sm font-mono" style={{ color: "var(--error)", wordBreak: "break-all" }}>
                                {err.error}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
