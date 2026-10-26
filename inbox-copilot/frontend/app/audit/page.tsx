"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditEntry } from "@/lib/types";
import { formatDate } from "@/lib/ui";

const actionColors: Record<string, string> = {
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  sent: "bg-blue-100 text-blue-800 border-blue-200",
  regenerated: "bg-yellow-100 text-yellow-800 border-yellow-200",
  created: "bg-gray-100 text-gray-800 border-gray-200",
};

export default function AuditPage() {
  const [items, setItems] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listAudit({ limit: 100 }).then((res) => {
      setItems(res.items);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Audit Log</h1>
      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : items.length === 0 ? (
        <p className="text-gray-500">No actions recorded yet.</p>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-600">
              <tr>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Entity</th>
                <th className="px-4 py-3 font-medium">Actor</th>
                <th className="px-4 py-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {formatDate(a.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${actionColors[a.action] || "bg-gray-100"}`}>
                      {a.action.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">
                    {a.entity_type}:{a.entity_id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3">{a.actor}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs max-w-xs truncate">
                    {a.payload.reason ? `Reason: ${a.payload.reason}` : 
                     a.payload.instructions ? `Instructions: ${a.payload.instructions}` : 
                     JSON.stringify(a.payload)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}