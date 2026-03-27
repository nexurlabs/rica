"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LOCAL_SERVER_ID } from "@/lib/api";

export default function DashboardHome() {
    const router = useRouter();

    useEffect(() => {
        // Single-instance mode: skip server selector, go straight to your dashboard
        router.replace(`/dashboard/${LOCAL_SERVER_ID}`);
    }, [router]);

    return (
        <div className="loading-container">
            <div className="loading-spinner" />
            <p style={{ color: "var(--text-secondary)" }}>Loading dashboard…</p>
        </div>
    );
}
