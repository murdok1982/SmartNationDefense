"use client";
import { FileText, Target, Crosshair, Radio } from "lucide-react";

const actions = [
  { label: "Generar OPORD", icon: FileText, color: "text-green-400 border-green-700 hover:bg-green-900/30" },
  { label: "Simular COA", icon: Target, color: "text-blue-400 border-blue-700 hover:bg-blue-900/30" },
  { label: "Evaluar BDA", icon: Crosshair, color: "text-orange-400 border-orange-700 hover:bg-orange-900/30" },
  { label: "Alerta Maxima", icon: Radio, color: "text-red-400 border-red-700 hover:bg-red-900/30" },
];

export default function QuickActions() {
  return (
    <div className="flex gap-2">
      {actions.map((a) => {
        const Icon = a.icon;
        return (
          <button
            key={a.label}
            className={`flex items-center gap-1.5 bg-gray-800 text-xs font-mono px-3 py-1.5 rounded border ${a.color} transition-colors`}
          >
            <Icon size={14} />
            {a.label}
          </button>
        );
      })}
    </div>
  );
}
