"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MetricsResponse } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMetrics().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading || !data) return <div className="text-gray-500 p-8">Loading metrics…</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Верхние карточки */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Total Emails" value={data.total_emails.toString()} />
        <MetricCard 
          title="P0 + P1 (Urgent)" 
          value={((data.priority_stats["P0"] || 0) + (data.priority_stats["P1"] || 0)).toString()} 
          color="text-orange-600"
        />
        <MetricCard title="Fallback Rate" value={`${data.fallback_rate}%`} color={data.fallback_rate > 50 ? "text-red-600" : "text-green-600"} />
        <MetricCard 
          title="Avg Total Latency" 
          value={`${Math.round((data.avg_latency_ms.classification + data.avg_latency_ms.extraction + data.avg_latency_ms.priority) / 1000)}s`} 
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Блок приоритетов */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="font-semibold mb-4 text-gray-800">Priority Distribution</h2>
          <div className="space-y-3">
            {["P0", "P1", "P2", "P3"].map((p) => {
              const count = data.priority_stats[p] || 0;
              const pct = data.total_emails ? (count / data.total_emails) * 100 : 0;
              return (
                <div key={p} className="flex items-center gap-3 text-sm">
                  <span className="w-8 font-mono font-bold">{p}</span>
                  <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                    <div className={`h-full ${p === "P0" ? "bg-red-500" : p === "P1" ? "bg-orange-400" : p === "P2" ? "bg-yellow-400" : "bg-gray-400"}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="w-8 text-right text-gray-600">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Блок категорий */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="font-semibold mb-4 text-gray-800">Category Distribution</h2>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(data.category_stats).map(([cat, count]) => (
              <div key={cat} className="flex justify-between items-center p-2 bg-gray-50 rounded text-sm border border-gray-100">
                <span className="capitalize">{cat}</span>
                <span className="font-bold">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, color = "text-gray-900" }: { title: string, value: string, color?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
      <p className="text-sm text-gray-500 font-medium mb-1">{title}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  );
}