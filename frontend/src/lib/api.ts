const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let inMemoryAccessToken: string | null = null;
let inMemoryRefreshToken: string | null = null;

export function getAccessToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("sesis_access_token") || inMemoryAccessToken;
  }
  return inMemoryAccessToken;
}

export function getRefreshToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("sesis_refresh_token") || inMemoryRefreshToken;
  }
  return inMemoryRefreshToken;
}

export function setTokens(access: string, refresh?: string): void {
  inMemoryAccessToken = access;
  if (refresh) inMemoryRefreshToken = refresh;
  if (typeof window !== "undefined") {
    localStorage.setItem("sesis_access_token", access);
    if (refresh) localStorage.setItem("sesis_refresh_token", refresh);
  }
}

export function clearTokens(): void {
  inMemoryAccessToken = null;
  inMemoryRefreshToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("sesis_access_token");
    localStorage.removeItem("sesis_refresh_token");
  }
}

export function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export async function login(
  username: string,
  password: string
): Promise<{ access_token: string; refresh_token: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "No se pudo iniciar sesión" }));
    throw new Error(err.detail || "Error de autenticación");
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token || refresh);
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

export interface ApiFetchOptions extends RequestInit {
  body?: any;
  /** Si es `false`, no adjunta el token de acceso (endpoints públicos). */
  auth?: boolean;
}

export async function apiFetch<T = any>(
  endpoint: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { auth = true, ...requestOptions } = options;
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  let token = auth ? getAccessToken() : null;

  const headers = new Headers(requestOptions.headers || {});
  if (!headers.has("Content-Type") && !(requestOptions.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const fetchOptions: RequestInit = {
    ...requestOptions,
    headers,
    body:
      requestOptions.body &&
      !(requestOptions.body instanceof FormData) &&
      typeof requestOptions.body !== "string"
        ? JSON.stringify(requestOptions.body)
        : requestOptions.body,
  };

  let res = await fetch(url, fetchOptions);

  if (res.status === 401 && getRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      res = await fetch(url, { ...fetchOptions, headers });
    }
  }

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const message = errorBody.detail || errorBody.message || `HTTP ${res.status}: ${res.statusText}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json();
  }
  return res.text() as unknown as T;
}

export const apiRequest = apiFetch;

export function apiErrorMessage(err: unknown): string {
  if (err instanceof Error) {
    // Los mensajes nativos del navegador llegan en inglés; se traducen los frecuentes.
    if (err.message === "Failed to fetch" || err.message === "Load failed") {
      return "No se pudo contactar con el núcleo C2. Revisa la conexión y reintenta.";
    }
    return err.message;
  }
  if (typeof err === "string") return err;
  return "Error de red inesperado. Verifica la conexión con el núcleo C2.";
}
