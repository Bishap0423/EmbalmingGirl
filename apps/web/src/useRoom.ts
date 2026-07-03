import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";
import type { Credentials, RoomSnapshot } from "./types";

export function useRoom(credentials: Credentials | null) {
  const [snapshot, setSnapshot] = useState<RoomSnapshot | null>(null);
  const [connection, setConnection] = useState<"offline" | "connecting" | "online">(
    credentials ? "connecting" : "offline",
  );
  const retry = useRef<number | undefined>(undefined);

  const refresh = useCallback(async () => {
    if (!credentials) return;
    setSnapshot(await api.snapshot(credentials));
  }, [credentials]);

  useEffect(() => {
    if (!credentials) {
      setSnapshot(null);
      setConnection("offline");
      return;
    }
    let stopped = false;
    let socket: WebSocket | null = null;

    const connect = () => {
      setConnection("connecting");
      const scheme = location.protocol === "https:" ? "wss" : "ws";
      const room = encodeURIComponent(credentials.room_id);
      const token = encodeURIComponent(credentials.player_token);
      socket = new WebSocket(`${scheme}://${location.host}/ws/rooms/${room}?token=${token}`);
      socket.onopen = () => setConnection("online");
      socket.onmessage = (event) => {
        const message = JSON.parse(String(event.data)) as {
          type: string;
          payload: RoomSnapshot;
        };
        if (message.type === "snapshot") setSnapshot(message.payload);
      };
      socket.onclose = () => {
        if (stopped) return;
        setConnection("offline");
        retry.current = window.setTimeout(connect, 1200);
      };
    };

    void refresh().catch(() => setConnection("offline"));
    connect();
    return () => {
      stopped = true;
      if (retry.current) window.clearTimeout(retry.current);
      socket?.close();
    };
  }, [credentials, refresh]);

  return { snapshot, setSnapshot, connection, refresh };
}
