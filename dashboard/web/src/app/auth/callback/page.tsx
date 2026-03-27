"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LOCAL_SERVER_ID } from "@/lib/api";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    // Self-hosted mode: no OAuth, redirect to dashboard
    router.replace(`/dashboard/${LOCAL_SERVER_ID}`);
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a0f 70%)" }}>
      <div className="text-center glass-card p-8 max-w-md">
        <h1 className="text-2xl font-bold gradient-text mb-4">Rica</h1>
        <p style={{ color: "var(--text-secondary)" }}>Redirecting to dashboard…</p>
      </div>
    </div>
  );
}
