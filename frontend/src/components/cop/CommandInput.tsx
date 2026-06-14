"use client";
import { useState } from "react";
import { Send } from "lucide-react";

export default function CommandInput() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);

  const send = () => {
    if (!input.trim()) return;
    setHistory(h => [`> ${input}`, ...h.slice(0, 10)]);
    setInput("");
  };

  return (
    <div className="bg-gray-900 rounded p-2 border border-gray-700 w-80">
      <div className="text-xs font-bold text-green-400 mb-1">fsociety LLM</div>
      <div className="max-h-16 overflow-y-auto mb-1">
        {history.map((h, i) => (
          <div key={i} className="text-[10px] font-mono text-gray-400">{h}</div>
        ))}
      </div>
      <div className="flex gap-1">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          className="flex-1 bg-gray-800 text-green-400 text-xs font-mono p-1 rounded border border-gray-600 outline-none focus:border-green-600"
          placeholder="Ordenar a fsociety..."
        />
        <button
          onClick={send}
          className="bg-green-800 hover:bg-green-700 text-green-200 p-1 rounded transition-colors"
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
