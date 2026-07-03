import type { Credentials, RoomSnapshot } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code = "REQUEST_FAILED",
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) {
    headers.set("content-type", "application/json");
  }
  if (token) {
    headers.set("X-Player-Token", token);
  }
  const response = await fetch(path, { ...init, headers });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: { code?: string; message?: string } | string;
    } | null;
    const detail = payload?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message ?? `请求失败（${response.status}）`;
    throw new ApiError(message, typeof detail === "object" ? detail?.code : undefined);
  }
  return (await response.json()) as T;
}

export const api = {
  createRoom(name: string) {
    return request<Credentials>("/api/rooms", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },
  joinRoom(roomId: string, name: string) {
    return request<Credentials>(`/api/rooms/${encodeURIComponent(roomId)}/players`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },
  snapshot(credentials: Credentials) {
    return request<RoomSnapshot>(
      `/api/rooms/${encodeURIComponent(credentials.room_id)}`,
      {},
      credentials.player_token,
    );
  },
  ready(credentials: Credentials, ready: boolean) {
    return request<{ ready: boolean }>(
      `/api/rooms/${encodeURIComponent(credentials.room_id)}/ready`,
      { method: "PUT", body: JSON.stringify({ ready }) },
      credentials.player_token,
    );
  },
  start(credentials: Credentials, seed: number) {
    return request<RoomSnapshot>(
      `/api/rooms/${encodeURIComponent(credentials.room_id)}/start`,
      { method: "POST", body: JSON.stringify({ seed }) },
      credentials.player_token,
    );
  },
  command(credentials: Credentials, command: Record<string, unknown>) {
    return request<RoomSnapshot>(
      `/api/rooms/${encodeURIComponent(credentials.room_id)}/commands`,
      { method: "POST", body: JSON.stringify(command) },
      credentials.player_token,
    );
  },
};
