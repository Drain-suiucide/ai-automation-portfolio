"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DraftResponse, EmailDetail } from "@/lib/types";
import { categoryColor, draftStatusColor, formatDate, priorityColor } from "@/lib/ui";

export function EmailDetailClient({ id }: { id: string }) {
  const [email, setEmail] = useState<EmailDetail | null>(null);
  const [drafts, setDrafts] = useState<DraftResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Состояния для действий
  const [generating, setGenerating] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [emailData, draftsData] = await Promise.all([
        api.getEmail(id),
        api.listDrafts(id),
      ]);
      setEmail(emailData);
      setDrafts(draftsData);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  async function handleGenerate() {
    setGenerating(true);
    try {
      await api.createDraft(id);
      await load(); // перезагружаем черновики
    } catch (e: any) {
      alert("Error generating draft: " + e.message);
    } finally {
      setGenerating(false);
    }
  }

  async function handleAction(action: "approve" | "send" | "reject") {
    if (!drafts[0]) return;
    setActionLoading(true);
    try {
      if (action === "approve") await api.approve(drafts[0].draft_id);
      if (action === "send") await api.send(drafts[0].draft_id);
      if (action === "reject") {
        await api.reject(drafts[0].draft_id, rejectReason);
        setShowReject(false);
      }
      await load();
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) return <div className="p-8 text-gray-500">Loading email…</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;
  if (!email) return <div className="p-8">Email not found</div>;

  const latestDraft = drafts[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/" className="hover:underline">Inbox</Link>
        <span>/</span>
        <span className="truncate">{email.subject || "(no subject)"}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ЛЕВАЯ КОЛОНКА: Оригинал письма */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h1 className="text-xl font-bold">{email.subject || "(no subject)"}</h1>
                <p className="text-sm text-gray-600 mt-1">
                  From: <span className="font-medium">{email.from_address}</span>
                </p>
                <p className="text-xs text-gray-400 mt-0.5">{formatDate(email.received_at)}</p>
              </div>
              <div className="flex gap-2">
                {email.classification && (
                  <span className={`text-xs px-2 py-1 rounded ${categoryColor(email.classification.category)}`}>
                    {email.classification.category} ({Math.round(email.classification.confidence * 100)}%)
                  </span>
                )}
                {email.priority && (
                  <span className={`text-xs px-2 py-1 rounded border font-mono ${priorityColor(email.priority.priority)}`}>
                    {email.priority.priority}
                  </span>
                )}
              </div>
            </div>
            <hr className="my-4 border-gray-100" />
            <div className="whitespace-pre-wrap text-gray-800 text-sm leading-relaxed">
              {email.body_text}
            </div>
          </div>
        </div>

        {/* ПРАВАЯ КОЛОНКА: Инсайты и Draft */}
        <div className="space-y-6">
          {/* Сущности и приоритет */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-sm">
            <h3 className="font-semibold mb-3 text-gray-700">AI Insights</h3>
            {email.extraction && (
              <div className="space-y-2 mb-4">
                <p><span className="text-gray-500">Contact:</span> {email.extraction.contact_name || "—"}</p>
                <p><span className="text-gray-500">Company:</span> {email.extraction.company || "—"}</p>
                <p><span className="text-gray-500">Amount:</span> {email.extraction.amount ? `${email.extraction.amount} ${email.extraction.currency}` : "—"}</p>
                <p><span className="text-gray-500">Deadline:</span> {email.extraction.deadline || "—"}</p>
                <p><span className="text-gray-500">Sentiment:</span> {email.extraction.sentiment}</p>
              </div>
            )}
            {email.priority && (
              <div>
                <p className="text-gray-500 mb-1">Priority factors:</p>
                <ul className="list-disc pl-4 text-xs text-gray-600 space-y-1">
                  {email.priority.factors.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
            )}
          </div>

          {/* Draft Panel */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-700">Draft Reply</h3>
              {latestDraft && (
                <span className={`text-xs px-2 py-0.5 rounded ${draftStatusColor(latestDraft.status)}`}>
                  {latestDraft.status}
                </span>
              )}
            </div>

            {!latestDraft ? (
              <div className="text-center py-6">
                <p className="text-sm text-gray-500 mb-4">No draft generated yet.</p>
                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  className="bg-black text-white px-4 py-2 rounded text-sm hover:bg-gray-800 disabled:opacity-50"
                >
                  {generating ? "Generating… (may take 20s)" : "✨ Generate Draft"}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-xs text-gray-500 border-b pb-2 mb-2">
                  {latestDraft.subject && <p className="font-medium text-gray-700 mb-1">Subject: {latestDraft.subject}</p>}
                  <p>Model: {latestDraft.meta.provider} | Confidence: {Math.round(latestDraft.confidence * 100)}%</p>
                </div>
                <div className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-3 rounded border border-gray-100 max-h-60 overflow-y-auto">
                  {latestDraft.body_text}
                </div>
                
                {latestDraft.warnings.length > 0 && (
                  <div className="bg-yellow-50 text-yellow-800 text-xs p-2 rounded border border-yellow-200">
                    ⚠️ {latestDraft.warnings.join(", ")}
                  </div>
                )}

                <div className="flex flex-col gap-2 pt-2">
                  {latestDraft.status === "draft" && (
                    <>
                      <button
                        onClick={() => handleAction("approve")}
                        disabled={actionLoading}
                        className="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => setShowReject(!showReject)}
                        disabled={actionLoading}
                        className="bg-red-100 text-red-700 px-3 py-1.5 rounded text-sm hover:bg-red-200 disabled:opacity-50"
                      >
                        ✗ Reject
                      </button>
                      {showReject && (
                        <div className="flex gap-2 mt-1">
                          <input
                            type="text"
                            placeholder="Reason for rejection"
                            className="border rounded px-2 py-1 text-sm flex-1"
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                          />
                          <button
                            onClick={() => handleAction("reject")}
                            disabled={actionLoading || !rejectReason}
                            className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 disabled:opacity-50"
                          >
                            Confirm
                          </button>
                        </div>
                      )}
                    </>
                  )}
                  
                  {latestDraft.status === "approved" && (
                    <button
                      onClick={() => handleAction("send")}
                      disabled={actionLoading}
                      className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                    >
                      ✈️ Send (Stub)
                    </button>
                  )}

                  <button
                    onClick={handleGenerate}
                    disabled={generating || actionLoading}
                    className="text-gray-500 text-xs hover:text-black underline mt-2 self-center"
                  >
                    {generating ? "Regenerating…" : "Regenerate"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}