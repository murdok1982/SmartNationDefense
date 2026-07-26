"use client";
import { useState, useRef } from "react";
import { Mic, ChevronDown, ChevronUp, MicOff } from "lucide-react";
import { useCOPStore } from "@/store/cop-store";
import { apiFetch, apiErrorMessage } from "@/lib/api";

const availableCommands = [
  { command: "Enviar mensaje a [unidad]", category: "COMMS" },
  { command: "Generar [SITREP|SPOTREP]", category: "REPORTES" },
  { command: "Mostrar mapa de [zona]", category: "MAPA" },
  { command: "Alerta maxima", category: "ALERTAS" },
  { command: "Solicitar MEDEVAC", category: "EMERGENCIA" },
  { command: "Estado de [unidad]", category: "C2" },
  { command: "Situacion actual", category: "C2" },
];

const statusColors: Record<string, string> = {
  IDLE: "text-gray-500",
  LISTENING: "text-green-400",
  PROCESSING: "text-yellow-400",
};

interface SpeechRecognitionResultItem {
  transcript: string
}

interface SpeechRecognitionResultList {
  readonly length: number
  [index: number]: { [index: number]: SpeechRecognitionResultItem }
}

interface SpeechRecognitionEventLike {
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionLike {
  lang: string
  interimResults: boolean
  maxAlternatives: number
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getSpeechRecognition(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

interface VoiceCommandResponse {
  command_id: string
  transcript: string
  command_type: string
  execution_result: { status: string; message: string }
  confidence: number
  timestamp: string
}

const WAVEFORM_HEIGHTS = [4, 8, 14, 20, 12, 6, 16, 22, 10, 5, 18, 24, 12, 7, 15, 21, 9, 4, 13, 19];

export default function VoiceCommand() {
  const { voiceCommands, voiceStatus, setVoiceStatus, addVoiceCommand } = useCOPStore();
  const [showCommands, setShowCommands] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  const RecognitionCtor = getSpeechRecognition();
  const supported = RecognitionCtor !== null;

  const sendCommand = async (transcript: string) => {
    setVoiceStatus("PROCESSING");
    try {
      const result = await apiFetch<VoiceCommandResponse>("/api/v1/voice/command", {
        method: "POST",
        body: { text_command: transcript, language: "es", user_id: "OPERATOR" },
      });
      addVoiceCommand({
        id: result.command_id,
        command: result.transcript,
        timestamp: result.timestamp,
        status: result.command_type === "UNKNOWN" ? "UNKNOWN" : "SUCCESS",
        resultMessage: result.execution_result.message,
      });
    } catch (e) {
      addVoiceCommand({
        id: `vc${Date.now()}`,
        command: transcript,
        timestamp: new Date().toISOString(),
        status: "FAILED",
        resultMessage: apiErrorMessage(e),
      });
    } finally {
      setVoiceStatus("IDLE");
    }
  };

  const toggleMic = () => {
    if (!supported || voiceStatus !== "IDLE") return;
    setError(null);
    const recognition = new RecognitionCtor();
    recognition.lang = "es-ES";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript ?? "";
      if (transcript) void sendCommand(transcript);
      else setVoiceStatus("IDLE");
    };
    recognition.onerror = () => {
      setError("Error en el reconocimiento de voz");
      setVoiceStatus("IDLE");
    };
    recognition.onend = () => {
      recognitionRef.current = null;
      if (useCOPStore.getState().voiceStatus === "LISTENING") setVoiceStatus("IDLE");
    };
    recognitionRef.current = recognition;
    setVoiceStatus("LISTENING");
    recognition.start();
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
        {!supported ? (
          <div className="text-center space-y-2">
            <MicOff size={32} className="text-gray-600 mx-auto" />
            <div className="text-[10px] font-mono text-gray-500">
              Reconocimiento de voz no disponible en este navegador.
            </div>
            <div className="text-[10px] font-mono text-gray-600">
              Se requiere Web Speech API (Chrome / Edge).
            </div>
          </div>
        ) : (
          <>
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
              <Mic size={32} className={
                voiceStatus === "IDLE" ? "text-gray-400" :
                voiceStatus === "LISTENING" ? "text-green-400" : "text-yellow-400"
              } />
            </button>

            <div className="flex items-end gap-0.5 h-8 mt-3">
              {WAVEFORM_HEIGHTS.map((h, i) => (
                <div
                  key={i}
                  className={`w-1 rounded-t transition-all duration-300 ${
                    voiceStatus === "LISTENING" ? "bg-green-400 animate-pulse" :
                    voiceStatus === "PROCESSING" ? "bg-yellow-400" : "bg-gray-700"
                  }`}
                  style={{ height: `${voiceStatus === "IDLE" ? 2 : h}px` }}
                />
              ))}
            </div>

            <div className="text-[10px] text-gray-500 mt-2">
              {voiceStatus === "IDLE" && "Pulsar para activar"}
              {voiceStatus === "LISTENING" && "Escuchando comando..."}
              {voiceStatus === "PROCESSING" && "Procesando..."}
            </div>
            {error && <div className="text-[10px] font-mono text-red-400 mt-1">{error}</div>}
          </>
        )}
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
          {voiceCommands.length === 0 && (
            <div className="text-[10px] font-mono text-gray-600">Sin comandos procesados</div>
          )}
          {voiceCommands.map(vc => (
            <div key={vc.id} className="text-[10px] font-mono">
              <div className="flex items-center gap-1">
                <span className={`w-1.5 h-1.5 rounded-full ${
                  vc.status === "SUCCESS" ? "bg-green-400" : vc.status === "FAILED" ? "bg-red-400" : "bg-gray-600"
                }`} />
                <span className="text-gray-400">{vc.command}</span>
                <span className="text-gray-600 ml-auto">{new Date(vc.timestamp).toISOString().slice(11, 16)}Z</span>
              </div>
              {vc.resultMessage && (
                <div className="text-gray-600 ml-3">{vc.resultMessage}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
