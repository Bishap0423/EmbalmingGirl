export type Credentials = {
  room_id: string;
  player_id: string;
  player_token: string;
};

export type VisibleCard = {
  instance_id: string;
  definition_id: string;
  name: string;
  mp: number;
  art_key: string;
};

export type PlayerView = {
  id: string;
  seat: number;
  finished: boolean;
  hand_count: number;
  hand: VisibleCard[] | null;
  used: VisibleCard[];
  suspicion_count: number;
};

export type GameResult = {
  embalming_total: number;
  embalming_succeeded: boolean;
  suspicion_totals: [string, number][];
  imprisoned_player_ids: string[];
  winner_ids: string[];
  winning_priority: number | null;
  annihilation: boolean;
};

export type GameView = {
  id: string;
  ruleset_version: string;
  revision: number;
  phase: "turn" | "resolving" | "scoring" | "finished";
  target: number;
  active_player_id: string | null;
  players: PlayerView[];
  embalming_count: number;
  pending_decision: {
    id: string;
    kind: string;
    context: Record<string, string>;
    submitted: boolean;
  } | null;
  private_reveals: { reason: string; values: string[] }[];
  result: GameResult | null;
};

export type RoomSnapshot = {
  room_id: string;
  host_player_id: string;
  viewer_player_id: string;
  players: { id: string; name: string; ready: boolean }[];
  game?: GameView;
};
