"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function AgentsPage() {
    const [agents, setAgents] = useState<string[]>([]);
    const [newId, setNewId] = useState("");
    const [msg, setMsg] = useState("");
    const [ownerId, setOwnerId] = useState("");

    useEffect(() => {
        api.getServer().then((c) => {
            setAgents(c.agent_users || []);
            setOwnerId(c.owner_id || "");
        });
    }, []);

    async function save() {
        try {
            const data = await api.updateAgentUsers(agents);
            setAgents(data.agent_users);
            setMsg("✅ Agent users updated!");
        } catch (e: any) {
            setMsg(`❌ ${e.message}`);
        }
    }

    function addUser() {
        if (newId && agents.length < 5 && !agents.includes(newId)) {
            setAgents([...agents, newId]);
            setNewId("");
        }
    }

    function removeUser(id: string) {
        if (id !== ownerId) setAgents(agents.filter((a) => a !== id));
    }

    return (
        <div className="fade-in max-w-2xl">
            <h1 className="text-3xl font-bold mb-2">Agent Users</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
                Designate up to 5 users who can access the Agent pipeline (code execution + creative tools)
            </p>

            {msg && <div className="glass-card mb-4 py-2 text-center text-sm">{msg}</div>}

            <div className="glass-card">
                <div className="space-y-3 mb-6">
                    {agents.map((id, i) => (
                        <div key={id} className="flex items-center justify-between p-3 rounded-xl" style={{ background: "var(--bg-secondary)" }}>
                            <div className="flex items-center gap-3">
                                <span className="text-xl">{id === ownerId ? "👑" : "👤"}</span>
                                <div>
                                    <span className="font-mono text-sm">{id}</span>
                                    {id === ownerId && <span className="text-xs ml-2" style={{ color: "var(--accent)" }}>Owner</span>}
                                </div>
                            </div>
                            {id !== ownerId && (
                                <button className="text-sm" style={{ color: "var(--error)" }} onClick={() => removeUser(id)}>Remove</button>
                            )}
                        </div>
                    ))}
                </div>

                {agents.length < 5 && (
                    <div className="flex gap-2">
                        <input className="input-field flex-1 font-mono" value={newId}
                            onChange={(e) => setNewId(e.target.value)} placeholder="Discord User ID" />
                        <button className="btn-primary" onClick={addUser}>Add</button>
                    </div>
                )}
                <p className="text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
                    {agents.length}/5 slots used. Right-click a user in Discord → Copy User ID
                </p>

                <button className="btn-primary mt-4 w-full" onClick={save}>Save Agent Users</button>
            </div>
        </div>
    );
}
