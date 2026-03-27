"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const TOOLS = [
    { key: "imagen", name: "Imagen 4", icon: "🖼️", desc: "Generate images from text prompts" },
    { key: "lyria", name: "Lyria", icon: "🎵", desc: "Generate music and audio" },
    { key: "veo", name: "Veo 3", icon: "🎬", desc: "Generate videos from text prompts" },
];

export default function CreativePage() {
    const [config, setConfig] = useState<any>({});
    const [keys, setKeys] = useState<any>({});
    const [msg, setMsg] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        api.getKeys().then((data) => {
            const creative = data.creative || {};
            setConfig(Object.fromEntries(TOOLS.map((t) => [t.key, creative[t.key]?.enabled || false])));
            setKeys({});
        });
    }, []);

    async function save() {
        setSaving(true);
        try {
            const payload: any = {};
            TOOLS.forEach((t) => {
                payload[t.key] = { enabled: config[t.key] || false };
                if (keys[t.key]) payload[t.key].api_key = keys[t.key];
            });
            await api.updateCreative(payload);
            setMsg("✅ Creative tools config saved!");
            setKeys({});
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
        setSaving(false);
    }

    return (
        <div className="fade-in max-w-2xl">
            <h1 className="text-3xl font-bold mb-2">Creative Tools</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
                Enable AI-powered creative generation for Agent users
            </p>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm">{msg}</div>}

            <div className="space-y-4">
                {TOOLS.map((tool) => (
                    <div key={tool.key} className="glass-card">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">{tool.icon}</span>
                                <div>
                                    <h3 className="font-semibold">{tool.name}</h3>
                                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{tool.desc}</p>
                                </div>
                            </div>
                            <div className={`toggle-switch ${config[tool.key] ? "active" : ""}`}
                                onClick={() => setConfig((prev: any) => ({ ...prev, [tool.key]: !prev[tool.key] }))} />
                        </div>

                        {config[tool.key] && (
                            <div>
                                <label className="text-sm font-medium block mb-2">API Key (Vertex AI)</label>
                                <input className="input-field font-mono" type="password" value={keys[tool.key] || ""}
                                    onChange={(e) => setKeys((prev: any) => ({ ...prev, [tool.key]: e.target.value }))}
                                    placeholder="Optional — uses default credentials if not set" />
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <button className="btn-primary mt-6" onClick={save} disabled={saving}>
                {saving ? "Saving..." : "Save Creative Config"}
            </button>
        </div>
    );
}
