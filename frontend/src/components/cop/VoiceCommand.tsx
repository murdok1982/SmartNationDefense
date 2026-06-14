"use client";
import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Radio, ChevronDown, ChevronUp } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";

const availableCommands = [
  { command: "Enviar mensaje a [unidad]", category: "COMMS" },
  { command: "Generar SITREP", category: "REPORTES" },
  { command: "Generar SPOTREP", category: "REPORTES" },
  { command: "Mostrar mapa de [zona]", category: "MAPA" },
  { command: "Alerta maxima", category: "ALERTAS" },
  { command: "Solicitar MEDEVAC", category: "EMERGENCIA" },
  { command: "Estado de unidades", category: "C2" },
  { command: "Analisis de terreno", category: "TERRAIN" },
  { command: "Prediccion de amenazas", category: "INTEL" },
  { command: "Cambiar clasificacion a [nivel]", category: "SISTEMA" },
];

const statusColors: Record<string, string> = {
  IDLE: "text-gray-500",
  LISTENING: "text-green-400",
  PROCESSING: "text-yellow-400",
};

export default function VoiceCommand() {
  const { voiceCommands, voiceStatus, setVoiceStatus, addVoiceCommand } = useCOPStore();
  const [showCommands, setShowCommands] = useState(false);
  const [waveformBars, setWaveformBars] = useState<number[]>(Array(20).fill(2));
  const animRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (voiceStatus === "LISTENING") {
      animRef.current = setInterval(() => {
        setWaveformBars(Array(20).fill(0).map(() => Math.random() * 20 + 2));
      }, 100);
    } else {
      if (animRef.current) clearInterval(animRef.current);
      setWaveformBars(Array(20).fill(2));
    }
    return () => { if (animRef.current) clearInterval(animRef.current); };
  }, [voiceStatus]);

  const toggleMic = () => {
    if (voiceStatus === "IDLE") {
      setVoiceStatus("LISTENING");
      setTimeout(() => {
        setVoiceStatus("PROCESSING");
        const commands = [
          "Enviar mensaje a Alfa-1",
          "Generar SITREP",
          "Mostrar mapa de sector Delta",
          "Estado de unidades",
          "Prediccion de amenazas",
        ];
        const cmd = commands[Math.floor(Math.random() * commands.length)];
        setTimeout(() => {
          addVoiceCommand({
            id: `vc${Date.now()}`,
            command: cmd,
            timestamp: new Date().toISOString(),
            status: "SUCCESS",
          });
          setVoiceStatus("IDLE");
        }, 1500);
      }, 3000);
    }
  };

  return (
    <div className="bg-gray-900 rounded border border-gray-700 flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-700">
        <Mic size={14} className="text-green-400" />
        <span className="text-xs font-bold text-gray-400">COMANDOS DE VOZ</span>
        <span className={`ml-auto text-[10px] font-mono font-bold ${statusColors[voiceStatus]}`}>
          {voiceStatus === "IDLE" ? "INACTIVO" : voiceStatus === "LISTENING" ? "ESCUCHANDO" : "PROCESANDO"}
        </span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <button
          onClick={toggleMic}
          disabled={voiceStatus !== "IDLE"}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
            voiceStatus === "IDLE"
              ? "bg-gray-800 border-2 border-gray-600 hover:border-green-400 hover:bg-gray-700"
              : voiceStatus === "LISTENING"
                ? "bg-green-900/30 border-2 border-green-400 animate-pulse"
                : "bg-yellow-900/30 border-2 border-yellow-400 animate-pulse"
          }`}
        >
          {voiceStatus === "IDLE" ? (
            <Mic size={32} className="text-gray-400" />
          ) : (
            <Mic size={32} className={voiceStatus === "LISTENING" ? "text-green-400" : "text-yellow-400"} />
          )}
        </button>

        <div className="flex items-end gap-0.5 h-8 mt-3">
          {waveformBars.map((h, i) => (
            <div
              key={i}
              className={`w-1 rounded-t transition-all duration-100 ${
                voiceStatus === "LISTENING" ? "bg-green-400" :
                voiceStatus === "PROCESSING" ? "bg-yellow-400" : "bg-gray-700"
              }`}
              style={{ height: `${h}px` }}
            />
          ))}
        </div>

        <div className="text-[10px] text-gray-500 mt-2">
          {voiceStatus === "IDLE" && "Pulsar para activar"}
          {voiceStatus === "LISTENING" && "Escuchando comando..."}
          {voiceStatus === "PROCESSING" && "Procesando..."}
        </div>
      </div>

      <div className="border-t border-gray-700">
        <button
          onClick={() => setShowCommands(!showCommands)}
          className="w-full flex items-center gap-1 text-[10px] text-gray-500 hover:text-gray-300 px-3 py-1.5 transition-colors"
        >
          {showCommands ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          Comandos disponibles
        </button>
        {showCommands && (
          <div className="px-3 pb-2 space-y-0.5 max-h-32 overflow-y-auto">
            {availableCommands.map((c, i) => (
              <div key={i} className="text-[10px] font-mono flex items-center gap-1">
                <span className="text-[9px] px-1 py-0.5 rounded bg-gray-800 text-gray-500">{c.category}</span>
                <span className="text-gray-400">{c.command}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-gray-700 p-2">
        <div className="text-[10px] text-gray-500 font-bold mb-1">HISTORIAL</div>
        <div className="space-y-0.5 max-h-24 overflow-y-auto">
          {voiceCommands.map(vc => (
            <div key={vc.id} className="text-[10px] font-mono flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${
                vc.status === "SUCCESS" ? "bg-green-400" : vc.status === "FAILED" ? "bg-red-400" : "bg-gray-600"
              }`} />
              <span className="text-gray-400">{vc.command}</span>
              <span className="text-gray-600 ml-auto">{new Date(vc.timestamp).toISOString().slice(11, 16)}Z</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
