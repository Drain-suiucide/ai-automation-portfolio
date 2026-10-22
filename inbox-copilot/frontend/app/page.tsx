"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { EmailListItem } from "@/lib/types";
import { categoryColor, formatDate, priorityColor } from "@/lib/ui";

export default function InboxPage() {
  const [items, setItems] = useState<EmailListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<string>("");
  const [priority, setPriority] = useState<string>("");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listEmails({
        category: category || undefined,
        priority: priority || undefined,
        limit: 50,
      });
      setItems(res.items);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [category, priority]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Inbox</h1>
        <div className="flex gap-3">
          <select
            className="border rounded px-3 py-1.5 text-sm"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All categories</option>
            <option value="billing">Billing</option>
            <option value="support">Support</option>
            <option value="sales">Sales</option>
            <option value="spam">Spam</option>
            <option value="partnership">Partnership</option>
            <option value="other">Other</option>
          </select>
          <select
            className="border rounded px-3 py-1.5 text-sm"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="">All priorities</option>
            <option value="P0">P0 — Critical</option>
            <option value="P1">P1 — High</option>
            <option value="P2">P2 — Normal</option>
            <option value="P3">P3 — Low</option>
          </select>
        </div>
      </div>

      {loading && <p className="text-gray-500">Loading…</p>}
      {error && <p className="text-red-600">Error: {error}</p>}
      {!loading && items.length === 0 && !error && (
        <p className="text-gray-500">No emails yet. Send one via POST /process.</p>
      )}

      <div className="space-y-2">
        {items.map((e) => (
          <Link
            key={e.id}
            href={`/emails/${e.id}`}
            className="block bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm text-gray-500 truncate">{e.from_address}</span>
                  <span className="text-xs text-gray-400">·</span>
                  <span className="text-xs text-gray-400">{formatDate(e.received_at)}</span>
                </div>
                <p className="font-medium truncate">{e.subject || "(no subject)"}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {e.category && (
                  <span className={`text-xs px-2 py-0.5 rounded ${categoryColor(e.category)}`}>
                    {e.category}
                  </span>
                )}
                {e.priority && (
                  <span className={`text-xs px-2 py-0.5 rounded border font-mono ${priorityColor(e.priority)}`}>
                    {e.priority}
                  </span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}