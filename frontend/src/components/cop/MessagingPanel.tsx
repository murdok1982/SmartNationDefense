"use client";
import { useState, useRef, useEffect, useMemo } from "react";
import { MessageSquare, Send, Radio, AlertTriangle, ChevronRight, Check, Reply } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { useApiData } from "@/lib/use-api-data";
import { apiFetch, apiErrorMessage } from "@/lib/api";
import { mapMessage, type BackendMessage } from "@/lib/mappers";
import type { TacticalMessage, Conversation } from "@/lib/cop-types";

const priorityConfig: Record<string, { color: string; bg: string; border: string }> = {
  CRITICAL: { color: "text-red-400", bg: "bg-red-900/20", border: "border-l-red-500" },
  HIGH: { color: "text-yellow-400", bg: "bg-yellow-900/20", border: "border-l-yellow-500" },
  MEDIUM: { color: "text-blue-400", bg: "bg-blue-900/20", border: "border-l-blue-500" },
  LOW: { color: "text-gray-400", bg: "bg-gray-800/50", border: "border-l-gray-600" },
};

const typeIcons: Record<string, string> = {
  TEXT: "TXT",
  COMMAND: "CMD",
  ALERT: "ALT",
  STATUS: "STS",
  LOCATION: "LOC",
};

const OPERATOR_ID = "OPERATOR";

export default function MessagingPanel() {
  const { messages, setMessages, acknowledgeMessage, state } = useCOPStore();
  const [selectedConv, setSelectedConv] = useState<string | null>(null);
  const [newContent, setNewContent] = useState("");
  const [newSubject, setNewSubject] = useState("");
  const [newRecipients, setNewRecipients] = useState("");
  const [msgType, setMsgType] = useState<TacticalMessage["type"]>("TEXT");
  const [msgPriority, setMsgPriority] = useState<TacticalMessage["priority"]>("MEDIUM");
  const [msgClassification, setMsgClassification] = useState("RESTRICTED");
  const [isBroadcast, setIsBroadcast] = useState(false);
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  const { loading, error, reload } = useApiData(
    async () => {
      const data = await apiFetch<BackendMessage[]>(`/api/v1/messaging/history?user_id=${OPERATOR_ID}&limit=100`);
      setMessages(data.map(mapMessage));
      return data.length;
    },
    { pollMs: 15000 },
  );

  const conversations = useMemo<Conversation[]>(() => {
    const byThread = new Map<string, TacticalMessage[]>();
    for (const m of messages) {
      const key = m.threadId ?? m.id;
      const list = byThread.get(key) ?? [];
      list.push(m);
      byThread.set(key, list);
    }
    const convs: Conversation[] = [];
    for (const [threadId, msgs] of byThread) {
      const sorted = [...msgs].sort((a, b) => b.timestamp.localeCompare(a.timestamp));
      const latest = sorted[0];
      const participants = Array.from(new Set(msgs.flatMap(m => [m.sender, ...m.recipients])));
      convs.push({
        id: threadId,
        participants,
        lastMessage: latest.content,
        lastTimestamp: latest.timestamp,
        unreadCount: msgs.filter(m => !m.acknowledged).length,
      });
    }
    return convs.sort((a, b) => b.lastTimestamp.localeCompare(a.lastTimestamp));
  }, [messages]);

  const filteredMessages = selectedConv
    ? messages.filter(m => (m.threadId ?? m.id) === selectedConv)
    : messages;

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [filteredMessages.length]);

  const handleSend = async () => {
    if (!newContent.trim()) return;
    const recipients = isBroadcast
      ? state.units.map(u => u.name)
      : newRecipients.split(",").map(r => r.trim()).filter(Boolean);
    if (recipients.length === 0) {
      setSendError(isBroadcast ? "No hay unidades registradas para broadcast" : "Indique destinatarios");
      return;
    }
    setSending(true);
    setSendError(null);
    try {
      await apiFetch<BackendMessage>("/api/v1/messaging/send", {
        method: "POST",
        body: {
          recipient_ids: recipients,
          message_type: msgType,
          priority: msgPriority,
          content: newContent,
          subject: newSubject || undefined,
          classification: msgClassification,
          parent_id: replyTo ?? undefined,
        },
      });
      setNewContent("");
      setNewSubject("");
      setReplyTo(null);
      await reload();
    } catch (e) {
      setSendError(apiErrorMessage(e));
    } finally {
      setSending(false);
    }
  };

  const handleAck = async (id: string) => {
    try {
      await apiFetch(`/api/v1/messaging/${id}/ack?user_id=${OPERATOR_ID}`, { method: "PUT" });
      acknowledgeMessage(id);
    } catch (e) {
      setSendError(apiErrorMessage(e));
    }
  };

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <MessageSquare size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">MENSAJERIA TACTICA</span>
        <span className="text-[10px] text-gray-600 ml-auto">{messages.filter(m => !m.acknowledged).length} sin ACK</span>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-1/3 border-r border-gray-700 overflow-y-auto">
          <div className="p-2 space-y-1">
            {loading && conversations.length === 0 && (
              <div className="text-[10px] font-mono text-gray-500 animate-pulse p-2">Cargando mensajes...</div>
            )}
            {error && (
              <div className="text-[10px] font-mono text-red-400 p-2">{error}</div>
            )}
            {!loading && !error && conversations.length === 0 && (
              <div className="text-[10px] font-mono text-gray-600 p-2">Sin conversaciones</div>
            )}
            {conversations.map(c => (
              <button
                key={c.id}
                onClick={() => setSelectedConv(c.id)}
                className={`w-full text-left p-2 rounded text-xs font-mono transition-colors ${
                  selectedConv === c.id ? "bg-gray-700 border border-gray-600" : "bg-gray-800/50 hover:bg-gray-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-green-400 font-bold truncate">{c.participants.join(", ")}</span>
                  {c.unreadCount > 0 && (
                    <span className="bg-red-600 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                      {c.unreadCount}
                    </span>
                  )}
                </div>
                <div className="text-gray-500 truncate mt-0.5">{c.lastMessage}</div>
                <div className="text-gray-600 text-[10px] mt-0.5">
                  {c.lastTimestamp ? new Date(c.lastTimestamp).toISOString().slice(11, 16) : "--"}Z
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div ref={chatRef} className="flex-1 overflow-y-auto p-2 space-y-1">
            {filteredMessages.length === 0 && !loading && (
              <div className="text-[10px] font-mono text-gray-600 text-center py-4">Sin mensajes</div>
            )}
            {filteredMessages.map(m => {
              const cfg = priorityConfig[m.priority] || priorityConfig.LOW;
              return (
                <div key={m.id} className={`text-xs font-mono p-2 rounded border-l-2 ${cfg.bg} ${cfg.border}`}>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-green-400 font-bold">{m.sender}</span>
                    <ChevronRight size={10} className="text-gray-600" />
                    <span className="text-gray-500">{m.recipients.join(", ")}</span>
                    <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded font-bold ${cfg.color}`}>
                      {m.priority}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] px-1 py-0.5 bg-gray-700 rounded text-gray-300">
                      {typeIcons[m.type]}
                    </span>
                    <span className="text-gray-300 font-bold">{m.subject}</span>
                    <span className="text-gray-600 text-[10px] ml-auto">
                      {m.timestamp ? new Date(m.timestamp).toISOString().slice(11, 16) : "--"}Z
                    </span>
                  </div>
                  <div className="text-gray-300">{m.content}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-[10px] px-1 py-0.5 rounded ${
                      m.classification === "SECRET" ? "text-red-400 bg-red-900/30" :
                      m.classification === "TOP SECRET" ? "text-purple-400 bg-purple-900/30" :
                      "text-yellow-400 bg-yellow-900/30"
                    }`}>
                      {m.classification}
                    </span>
                    {m.acknowledged ? (
                      <span className="text-green-500 text-[10px] flex items-center gap-0.5">
                        <Check size={10} /> ACK
                      </span>
                    ) : (
                      <button
                        onClick={() => void handleAck(m.id)}
                        className="text-[10px] text-yellow-400 hover:text-yellow-300 flex items-center gap-0.5"
                      >
                        <AlertTriangle size={10} /> ACK
                      </button>
                    )}
                    <button
                      onClick={() => setReplyTo(m.id)}
                      className="text-[10px] text-gray-500 hover:text-gray-300 flex items-center gap-0.5"
                    >
                      <Reply size={10} /> Responder
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="border-t border-gray-700 p-2 space-y-1">
            {replyTo && (
              <div className="flex items-center gap-1 text-[10px] text-gray-500">
                <Reply size={10} />
                Respondiendo a: {messages.find(m => m.id === replyTo)?.subject}
                <button onClick={() => setReplyTo(null)} className="text-red-400 ml-auto">x</button>
              </div>
            )}
            {sendError && <div className="text-[10px] font-mono text-red-400">{sendError}</div>}
            <div className="flex gap-1">
              <select
                value={msgType}
                onChange={e => setMsgType(e.target.value as TacticalMessage["type"])}
                className="bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
              >
                <option value="TEXT">TEXTO</option>
                <option value="COMMAND">COMANDO</option>
                <option value="ALERT">ALERTA</option>
                <option value="STATUS">ESTADO</option>
                <option value="LOCATION">UBICACION</option>
              </select>
              <select
                value={msgPriority}
                onChange={e => setMsgPriority(e.target.value as TacticalMessage["priority"])}
                className="bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
              >
                <option value="LOW">BAJA</option>
                <option value="MEDIUM">MEDIA</option>
                <option value="HIGH">ALTA</option>
                <option value="CRITICAL">CRITICA</option>
              </select>
              <select
                value={msgClassification}
                onChange={e => setMsgClassification(e.target.value)}
                className="bg-gray-800 text-gray-300 text-[10px] rounded px-1 py-1 border border-gray-700"
              >
                <option value="UNCLASSIFIED">NO CLASIF</option>
                <option value="RESTRICTED">RESTRINGIDO</option>
                <option value="CONFIDENTIAL">CONFIDENCIAL</option>
                <option value="SECRET">SECRETO</option>
                <option value="TOP SECRET">ALTO SECRETO</option>
              </select>
              <button
                onClick={() => setIsBroadcast(!isBroadcast)}
                className={`flex items-center gap-0.5 text-[10px] px-1.5 py-1 rounded border transition-colors ${
                  isBroadcast
                    ? "bg-red-900/30 border-red-700 text-red-400"
                    : "bg-gray-800 border-gray-700 text-gray-500"
                }`}
              >
                <Radio size={10} /> BROADCAST
              </button>
            </div>
            {!isBroadcast && (
              <input
                value={newRecipients}
                onChange={e => setNewRecipients(e.target.value)}
                placeholder="Destinatarios (separados por coma)..."
                className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
              />
            )}
            <input
              value={newSubject}
              onChange={e => setNewSubject(e.target.value)}
              placeholder="Asunto..."
              className="w-full bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
            />
            <div className="flex gap-1">
              <input
                value={newContent}
                onChange={e => setNewContent(e.target.value)}
                onKeyDown={e => e.key === "Enter" && void handleSend()}
                placeholder="Mensaje tactico..."
                className="flex-1 bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
              />
              <button
                onClick={() => void handleSend()}
                disabled={sending}
                className="bg-green-800 hover:bg-green-700 disabled:opacity-50 text-green-100 text-xs px-3 py-1 rounded flex items-center gap-1 transition-colors"
              >
                <Send size={12} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
