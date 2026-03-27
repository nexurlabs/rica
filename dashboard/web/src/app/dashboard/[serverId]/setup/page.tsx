"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Dropdown } from "@/components/Dropdown";

const PROVIDERS = [
    { id: "google_ai", name: "Google AI (Gemini)", icon: "🔵" },
    { id: "openrouter", name: "OpenRouter (100+ models)", icon: "🌐" },
    { id: "openai", name: "OpenAI (GPT)", icon: "🟢" },
    { id: "anthropic", name: "Anthropic (Claude)", icon: "🟠" },
    { id: "groq", name: "Groq (Fast Llama)", icon: "⚡" },
];

export default function SetupWizard() {
    const router = useRouter();
    const serverId = "local";

    const [step, setStep] = useState(1);
    const [triggerWord, setTriggerWord] = useState("rica");
    const [provider, setProvider] = useState("google_ai");
    const [allKey, setAllKey] = useState("");
    const [workers, setWorkers] = useState({
        db_manager: true, moderator: true, responder: true, agent: false,
    });
    const [loading, setLoading] = useState(false);
    const [validating, setValidating] = useState(false);
    const [error, setError] = useState("");
    const [msg, setMsg] = useState("");

    const [fetchedModels, setFetchedModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState("");

    async function validateAndFetchModels() {
        setValidating(true);
        setError("");
        setMsg("");
        try {
            if (!allKey.trim()) {
                throw new Error("Please enter an API key first");
            }

            const isValid = await api.validateKey({ api_key: allKey.trim(), provider });
            if (!isValid.valid) {
                throw new Error(isValid.message || "Key validation failed");
            }

            const modelsRes = await api.getModels(provider, allKey.trim());
            setFetchedModels(modelsRes.models || []);
            setMsg("✅ Key validated and models fetched");
        } catch (e: any) {
            setFetchedModels([]);
            setSelectedModel("");
            setError(e.message || "Validation failed");
        }
        setValidating(false);
    }

    async function handleComplete() {
        setLoading(true);
        setError("");
        try {
            await api.setupServer({
                trigger_word: triggerWord,
                provider,
                all_key: allKey || undefined,
                model: selectedModel || undefined,
                db_manager_enabled: workers.db_manager,
                moderator_enabled: workers.moderator,
                responder_enabled: workers.responder,
                agent_enabled: workers.agent,
            });
            router.push(`/dashboard/${serverId}`);
        } catch (e: any) {
            setError(e.message || "Setup failed");
            setLoading(false);
        }
    }

    return (
        <div className="max-w-xl mx-auto py-12 fade-in">
            <h1 className="text-3xl font-bold gradient-text mb-2">Setup Wizard</h1>
            <p className="mb-8" style={{ color: "var(--text-secondary)" }}>Let&apos;s get Rica configured for your bot</p>

            {/* Progress */}
            <div className="flex gap-2 mb-8">
                {[1, 2, 3].map((s) => (
                    <div key={s} className="flex-1 h-1 rounded-full" style={{ background: s <= step ? "var(--accent)" : "var(--border)" }} />
                ))}
            </div>

            {/* Step 1: Trigger Word */}
            {step === 1 && (
                <div className="glass-card">
                    <h2 className="text-xl font-semibold mb-4">1. Set Your Trigger Word</h2>
                    <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
                        This is how users will call the bot. E.g., &quot;hey rica&quot; or &quot;jarvis help me&quot;
                    </p>
                    <input
                        className="input-field text-lg"
                        type="text"
                        value={triggerWord}
                        onChange={(e) => setTriggerWord(e.target.value.toLowerCase().slice(0, 20))}
                        placeholder="rica"
                    />
                    <button className="btn-primary mt-6 w-full" onClick={() => setStep(2)}>
                        Next →
                    </button>
                </div>
            )}

            {/* Step 2: API Provider + Key */}
            {step === 2 && (
                <div className="glass-card">
                    <h2 className="text-xl font-semibold mb-4">2. Connect Your AI Provider</h2>
                    <div className="space-y-3 mb-6">
                        {PROVIDERS.map((p) => (
                            <button
                                key={p.id}
                                onClick={() => {
                                    setProvider(p.id);
                                    setFetchedModels([]);
                                    setSelectedModel("");
                                    setMsg("");
                                    setError("");
                                }}
                                className={`w-full text-left p-4 rounded-xl border transition-all flex items-center ${provider === p.id ? "border-[var(--accent)]" : "border-[var(--border)]"}`}
                                style={{ background: provider === p.id ? "rgba(108,92,231,0.1)" : "var(--bg-secondary)" }}
                            >
                                <span className="text-xl mr-3">{p.icon}</span>
                                <span className="font-medium text-[var(--text-primary)]">{p.name}</span>
                            </button>
                        ))}
                    </div>
                    <p className="text-sm mb-2" style={{ color: "var(--text-secondary)" }}>
                        API Key (shared across all workers — can change per-worker later):
                    </p>
                    <div className="flex gap-2 mb-4">
                        <input
                            className="input-field font-mono flex-1"
                            type="password"
                            value={allKey}
                            onChange={(e) => {
                                setAllKey(e.target.value);
                                setFetchedModels([]);
                                setSelectedModel("");
                            }}
                            placeholder="Paste your API key here..."
                            autoComplete="new-password"
                            autoCorrect="off"
                            autoCapitalize="none"
                            spellCheck={false}
                            data-lpignore="true"
                            data-1p-ignore="true"
                            data-bwignore="true"
                        />
                        <button
                            className="btn-primary whitespace-nowrap"
                            onClick={validateAndFetchModels}
                            disabled={validating || !allKey.trim()}
                            style={{ opacity: validating || !allKey.trim() ? 0.6 : 1 }}
                        >
                            {validating ? "Validating..." : "Validate & Fetch Models"}
                        </button>
                    </div>

                    {fetchedModels.length > 0 && (
                        <div className="mb-2 fade-in">
                            <p className="text-sm mb-2" style={{ color: "var(--text-secondary)" }}>
                                Optional: choose default model
                            </p>
                            <Dropdown
                                className="w-full"
                                value={selectedModel}
                                options={[
                                    { label: "-- Provider default model --", value: "" },
                                    ...fetchedModels.map((m) => ({ label: m, value: m }))
                                ]}
                                onChange={setSelectedModel}
                            />
                        </div>
                    )}

                    {msg && <p className="text-sm mt-2" style={{ color: "var(--accent)" }}>{msg}</p>}
                    {error && <p className="text-sm mt-2" style={{ color: "var(--error)" }}>❌ {error}</p>}

                    <div className="flex gap-3 mt-6">
                        <button className="btn-secondary flex-1" onClick={() => setStep(1)}>← Back</button>
                        <button className="btn-primary flex-1" onClick={() => setStep(3)}>Next →</button>
                    </div>
                </div>
            )}

            {/* Step 3: Enable Workers */}
            {step === 3 && (
                <div className="glass-card">
                    <h2 className="text-xl font-semibold mb-4">3. Enable Workers</h2>
                    <div className="space-y-4 mb-6">
                        {[
                            { key: "db_manager", name: "Database Manager", desc: "Stores user data & server knowledge", icon: "📁" },
                            { key: "moderator", name: "Moderator", desc: "Auto-moderation & web search", icon: "🛡️" },
                            { key: "responder", name: "Responder", desc: "Main chatbot (activated by trigger word)", icon: "💬" },
                            { key: "agent", name: "Agent", desc: "Advanced AI for owner + designated users", icon: "🤖" },
                        ].map((w) => (
                            <div key={w.key} className="flex items-center justify-between p-4 rounded-xl" style={{ background: "var(--bg-secondary)" }}>
                                <div className="flex items-center gap-3">
                                    <span className="text-xl">{w.icon}</span>
                                    <div>
                                        <p className="font-medium">{w.name}</p>
                                        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{w.desc}</p>
                                    </div>
                                </div>
                                <div
                                    className={`toggle-switch ${workers[w.key as keyof typeof workers] ? "active" : ""}`}
                                    onClick={() => setWorkers((prev) => ({ ...prev, [w.key]: !prev[w.key as keyof typeof prev] }))}
                                />
                            </div>
                        ))}
                    </div>

                    {error && <p className="text-sm mb-4" style={{ color: "var(--error)" }}>❌ {error}</p>}

                    <div className="flex gap-3">
                        <button className="btn-secondary flex-1" onClick={() => setStep(2)}>← Back</button>
                        <button className="btn-primary flex-1" onClick={handleComplete} disabled={loading}>
                            {loading ? "Setting up..." : "Complete Setup ✨"}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
