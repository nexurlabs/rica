"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LOCAL_SERVER_ID } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Self-hosted mode: no login needed, go straight to dashboard
    router.replace(`/dashboard/${LOCAL_SERVER_ID}`);
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a0f 70%)" }}>
      <div className="text-center fade-in">
        <h1 className="text-6xl font-bold gradient-text brand-name mb-4">Rica</h1>
        <p className="text-lg mb-6" style={{ color: "var(--text-secondary)" }}>
          Loading your dashboard…
        </p>
        <div className="loading-spinner mx-auto" />
      </div>
    </div>
  );
}
