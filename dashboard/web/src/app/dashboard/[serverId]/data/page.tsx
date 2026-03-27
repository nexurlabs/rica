"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function DataBrowserPage() {
    const [prefix, setPrefix] = useState("");
    const [folders, setFolders] = useState<string[]>([]);
    const [files, setFiles] = useState<any[]>([]);
    const [content, setContent] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => { loadDirectory(""); }, []);

    async function loadDirectory(newPrefix: string) {
        setLoading(true);
        setContent(null);
        setSelectedFile("");
        try {
            const data = await api.listFiles(newPrefix);
            setPrefix(newPrefix);
            setFolders(data.folders || []);
            setFiles(data.files || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    }

    async function openFile(path: string) {
        setSelectedFile(path);
        try {
            const data = await api.readFile(path);
            setContent(data.content);
        } catch (e: any) {
            setContent(`Error loading file: ${e.message}`);
        }
    }

    function goUp() {
        const parts = prefix.split("/").filter(Boolean);
        parts.pop();
        loadDirectory(parts.join("/"));
    }

    return (
        <div className="fade-in">
            <h1 className="text-3xl font-bold mb-2">Data Browser</h1>
            <p className="mb-6" style={{ color: "var(--text-secondary)" }}>
                View DB Manager&apos;s files (read-only)
            </p>

            {/* Breadcrumb */}
            <div className="flex items-center gap-2 mb-4 text-sm">
                <button onClick={() => loadDirectory("")} style={{ color: "var(--accent)" }}>root</button>
                {prefix.split("/").filter(Boolean).map((part, i, arr) => (
                    <span key={i} className="flex items-center gap-2">
                        <span style={{ color: "var(--text-secondary)" }}>/</span>
                        <button onClick={() => loadDirectory(arr.slice(0, i + 1).join("/"))} style={{ color: "var(--accent)" }}>
                            {part}
                        </button>
                    </span>
                ))}
            </div>

            <div className="flex gap-4" style={{ height: "calc(100vh - 250px)" }}>
                {/* File list */}
                <div className="glass-card flex-1 overflow-auto" style={{ minWidth: "300px" }}>
                    {prefix && (
                        <button onClick={goUp} className="w-full text-left p-3 rounded-lg hover:bg-[var(--bg-card-hover)] flex items-center gap-2 mb-1">
                            <span>📂</span> <span style={{ color: "var(--text-secondary)" }}>..</span>
                        </button>
                    )}

                    {folders.map((folder) => (
                        <button key={folder} onClick={() => loadDirectory(folder)}
                            className="w-full text-left p-3 rounded-lg hover:bg-[var(--bg-card-hover)] flex items-center gap-2 mb-1">
                            <span>📁</span> <span className="font-medium">{folder.split("/").pop()}</span>
                        </button>
                    ))}

                    {files.filter((f) => !f.path.endsWith(".keep")).map((file) => (
                        <button key={file.path} onClick={() => openFile(file.path)}
                            className={`w-full text-left p-3 rounded-lg flex items-center justify-between mb-1 ${selectedFile === file.path ? "bg-[var(--bg-card-hover)]" : "hover:bg-[var(--bg-card-hover)]"}`}>
                            <div className="flex items-center gap-2">
                                <span>📄</span> <span className="text-sm">{file.path.split("/").pop()}</span>
                            </div>
                            <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{formatSize(file.size)}</span>
                        </button>
                    ))}

                    {!loading && folders.length === 0 && files.filter((f) => !f.path.endsWith(".keep")).length === 0 && (
                        <p className="text-sm text-center py-8" style={{ color: "var(--text-secondary)" }}>Empty directory</p>
                    )}
                </div>

                {/* File content */}
                {content !== null && (
                    <div className="glass-card flex-1 overflow-auto">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-mono text-sm" style={{ color: "var(--accent)" }}>{selectedFile}</h3>
                            <button className="text-sm" style={{ color: "var(--text-secondary)" }} onClick={() => setContent(null)}>✕</button>
                        </div>
                        <pre className="text-sm whitespace-pre-wrap" style={{ fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.6 }}>
                            {content}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    );
}

function formatSize(bytes: number): string {
    if (!bytes) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
