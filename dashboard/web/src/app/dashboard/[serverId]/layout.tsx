"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

const NAV_ITEMS = [
    { href: "", icon: "🏠", label: "Dashboard" },
    { href: "/workers", icon: "⚙️", label: "Workers" },
    { href: "/keys", icon: "🔑", label: "API Keys" },
    { href: "/search", icon: "🔍", label: "Search" },
    { href: "/creative", icon: "🎨", label: "Creative Tools" },
    { href: "/channels", icon: "📺", label: "Channels" },
    { href: "/agents", icon: "👤", label: "Agent Users" },
    { href: "/data", icon: "📁", label: "Data Browser" },
    { href: "/usage", icon: "📊", label: "Usage Stats" },
    { href: "/errors", icon: "⚠️", label: "Error Logs" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const serverId = "local";
    const [botName, setBotName] = useState("Rica");
    const [sidebarOpen, setSidebarOpen] = useState(false);

    useEffect(() => {
        api.getServer().then((s) => setBotName(s.server_name || "Rica")).catch(() => { });
    }, []);

    // Close sidebar on route change (mobile)
    useEffect(() => {
        setSidebarOpen(false);
    }, [pathname]);

    return (
        <div className="flex min-h-screen">
            {/* Mobile menu button */}
            <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
                {sidebarOpen ? "✕" : "☰"}
            </button>

            {/* Mobile overlay */}
            <div className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`} onClick={() => setSidebarOpen(false)} />

            {/* Sidebar */}
            <aside className={`sidebar flex flex-col ${sidebarOpen ? "open" : ""}`}>
                <div className="block mb-6">
                    <h2 className="text-2xl font-bold gradient-text brand-name">Rica</h2>
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Self-Hosted Dashboard</p>
                </div>

                <div className="glass-card p-3 mb-6">
                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Your Bot</p>
                    <p className="font-semibold text-sm truncate">{botName}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                        <span className="status-dot active" style={{ width: 6, height: 6 }}></span>
                        <span className="text-xs" style={{ color: "var(--success)" }}>Local Instance</span>
                    </div>
                </div>

                <nav className="flex-1 space-y-1">
                    {NAV_ITEMS.map((item) => {
                        const href = `/dashboard/${serverId}${item.href}`;
                        const isActive = pathname === href ||
                            (item.href === "" && pathname === `/dashboard/${serverId}`);
                        return (
                            <Link key={item.href} href={href} className={`sidebar-link ${isActive ? "active" : ""}`}>
                                <span>{item.icon}</span>
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border)" }}>
                    <p className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
                        Rica v0.1.0 · Open Source
                    </p>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8 overflow-auto">
                {children}
            </main>
        </div>
    );
}
