"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiErrorMessage } from "@/lib/api";

export interface UseApiDataOptions {
  /** Intervalo de refresco en ms. Sin valor, sólo se ejecuta una vez. */
  pollMs?: number;
  /** Permite desactivar la petición (p. ej. cuando faltan precondiciones). */
  enabled?: boolean;
}

export interface UseApiDataResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Hook de carga de datos con polling, cancelación y estados explícitos.
 *
 * Devuelve `data`, `loading`, `error` y `reload` para que cada vista pueda
 * renderizar estados de carga, vacío y error reales (no simulados).
 */
export function useApiData<T>(
  fetcher: () => Promise<T>,
  options: UseApiDataOptions = {},
): UseApiDataResult<T> {
  const { pollMs, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(enabled);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    const run = async () => {
      try {
        const result = await fetcherRef.current();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(apiErrorMessage(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void run();

    const interval =
      pollMs && pollMs > 0 ? setInterval(() => void run(), pollMs) : null;

    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [enabled, pollMs, nonce]);

  return { data, loading, error, reload };
}

export default useApiData;
