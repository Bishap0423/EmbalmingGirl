import { useMemo, useState } from "react";

import { ApiError, api } from "./api";
import type { Credentials, GameView, RoomSnapshot, VisibleCard } from "./types";
import { useRoom } from "./useRoom";

const STORAGE_KEY = "embalming-girl.credentials";

function readCredentials(): Credentials | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value ? (JSON.parse(value) as Credentials) : null;
  } catch {
    return null;
  }
}

function Card({
  card,
  selected,
  onClick,
}: {
  card: VisibleCard;
  selected?: boolean;
  onClick?: () => void;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  return (
    <button
      type="button"
      className={`game-card ${selected ? "selected" : ""}`}
      onClick={onClick}
      aria-pressed={selected}
    >
      {!imageFailed && (
        <img
          src={`/assets/temporary/cards/${card.definition_id}.webp`}
          alt=""
          onError={() => setImageFailed(true)}
        />
      )}
      <span className="card-mp">{card.mp}</span>
      <span className="card-name">{card.name}</span>
      <small>{card.definition_id}</small>
    </button>
  );
}

function Landing({ onConnected }: { onConnected: (value: Credentials) => void }) {
  const [name, setName] = useState("");
  const [roomId, setRoomId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (mode: "create" | "join") => {
    if (!name.trim()) return setError("请输入玩家名称");
    if (mode === "join" && !roomId.trim()) return setError("请输入房间码");
    setBusy(true);
    setError("");
    try {
      const value =
        mode === "create"
          ? await api.createRoom(name.trim())
          : await api.joinRoom(roomId.trim(), name.trim());
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
      onConnected(value);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "连接失败");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="landing">
      <section className="hero">
        <p className="eyebrow">Embalming Girl · Local Edition</p>
        <h1>冰冷的她醒来之前</h1>
        <p>在救援到来前完成调合，并找出藏在人群中的犯人。</p>
      </section>
      <section className="entry-panel">
        <label>
          你的名字
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={40} />
        </label>
        <button disabled={busy} onClick={() => void submit("create")}>
          创建房间
        </button>
        <div className="divider">或加入现有房间</div>
        <label>
          房间码
          <input value={roomId} onChange={(event) => setRoomId(event.target.value)} />
        </label>
        <button className="secondary" disabled={busy} onClick={() => void submit("join")}>
          加入房间
        </button>
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  );
}

function Lobby({
  snapshot,
  credentials,
  onUpdate,
}: {
  snapshot: RoomSnapshot;
  credentials: Credentials;
  onUpdate: (value: RoomSnapshot) => void;
}) {
  const viewer = snapshot.players.find((player) => player.id === snapshot.viewer_player_id);
  const host = snapshot.host_player_id === snapshot.viewer_player_id;
  const allReady = snapshot.players.length >= 3 && snapshot.players.every((player) => player.ready);
  const [error, setError] = useState("");

  const ready = async () => {
    try {
      await api.ready(credentials, !viewer?.ready);
      onUpdate(await api.snapshot(credentials));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "操作失败");
    }
  };
  const start = async () => {
    try {
      onUpdate(await api.start(credentials, Date.now()));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "无法开始");
    }
  };

  return (
    <main className="lobby">
      <header>
        <div>
          <p className="eyebrow">等待救援，也等待其他人</p>
          <h1>房间 {snapshot.room_id}</h1>
        </div>
        <button className="copy" onClick={() => void navigator.clipboard.writeText(snapshot.room_id)}>
          复制房间码
        </button>
      </header>
      <section className="player-list">
        {snapshot.players.map((player) => (
          <article key={player.id} className={player.ready ? "ready" : ""}>
            <span className="seat">{player.id.replace("player_", "0")}</span>
            <strong>{player.name}</strong>
            <small>{player.id === snapshot.host_player_id ? "房主" : "成员"}</small>
            <span>{player.ready ? "已准备" : "未准备"}</span>
          </article>
        ))}
      </section>
      <footer className="lobby-actions">
        <button onClick={() => void ready()}>{viewer?.ready ? "取消准备" : "准备"}</button>
        {host && (
          <button disabled={!allReady} onClick={() => void start()}>
            开始游戏
          </button>
        )}
        <p>{snapshot.players.length}/6 人 · 至少 3 人且全员准备后开始</p>
        {error && <p className="error">{error}</p>}
      </footer>
    </main>
  );
}

function GameTable({
  game,
  credentials,
  names,
  onUpdate,
}: {
  game: GameView;
  credentials: Credentials;
  names: Record<string, string>;
  onUpdate: (value: RoomSnapshot) => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [decisionValue, setDecisionValue] = useState("");
  const [error, setError] = useState("");
  const viewer = game.players.find((player) => player.id === credentials.player_id);
  const selectedCard = viewer?.hand?.find((card) => card.instance_id === selected);
  const isTurn = game.active_player_id === credentials.player_id && game.phase === "turn";

  const act = async (command: string, extra: Record<string, unknown> = {}) => {
    if (!selectedCard) return;
    setError("");
    try {
      const value = await api.command(credentials, {
        command,
        expected_revision: game.revision,
        card_instance_id: selectedCard.instance_id,
        ...extra,
      });
      setSelected(null);
      onUpdate(value);
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "行动失败");
    }
  };
  const submitDecision = async () => {
    if (!game.pending_decision) return;
    try {
      const value = await api.command(credentials, {
        command: "submit_decision",
        expected_revision: game.revision,
        decision_id: game.pending_decision.id,
        selections: decisionValue
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setDecisionValue("");
      onUpdate(value);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "决策提交失败");
    }
  };

  if (game.result) {
    const winners = game.result.winner_ids.map((id) => names[id] ?? id).join("、") || "无人";
    return (
      <main className="ending">
        <p className="eyebrow">Game Over</p>
        <h1>{game.result.annihilation ? "全灭" : "事件终结"}</h1>
        <p>胜者：{winners}</p>
        <p>调合值 {game.result.embalming_total} / 目标 {game.target}</p>
      </main>
    );
  }

  return (
    <main className="table">
      <header className="table-status">
        <div>
          <p className="eyebrow">目标调合值</p>
          <strong>{game.target}</strong>
        </div>
          <p>
            {isTurn
              ? "轮到你行动"
              : `等待 ${game.active_player_id ? names[game.active_player_id] ?? game.active_player_id : "结算"}`}
          </p>
        <span>修订 {game.revision}</span>
      </header>
      <section className="opponents">
        {game.players.map((player) => (
          <article key={player.id} className={player.id === game.active_player_id ? "active" : ""}>
            <h2>{names[player.id] ?? player.id}</h2>
            <p>手牌 {player.hand_count} · 疑惑 {player.suspicion_count}</p>
            <div className="used-cards">
              {player.used.map((card) => <Card key={card.instance_id} card={card} />)}
            </div>
            {isTurn && player.id !== credentials.player_id && selectedCard && (
              <button onClick={() => void act("play_suspicion", { target_player_id: player.id })}>
                对其放置疑惑
              </button>
            )}
          </article>
        ))}
      </section>
      <section className="center-board">
        <div className="corpse">
          <span>遗体</span>
          <strong>{game.embalming_count}</strong>
          <small>张调合牌</small>
        </div>
      </section>
      <section className="hand-area">
        <div className="action-bar">
          <span>{selectedCard ? `已选择：${selectedCard.name}` : "选择一张手牌"}</span>
          <button disabled={!isTurn || !selectedCard} onClick={() => void act("play_special")}>
            使用特技
          </button>
          <button disabled={!isTurn || !selectedCard} onClick={() => void act("play_embalming")}>
            加入调合
          </button>
        </div>
        <div className="hand">
          {viewer?.hand?.map((card) => (
            <Card
              key={card.instance_id}
              card={card}
              selected={selected === card.instance_id}
              onClick={() => setSelected(card.instance_id)}
            />
          ))}
        </div>
        {game.private_reveals.length > 0 && (
          <aside className="private-info">
            <strong>私密情报</strong>
            {game.private_reveals.map((reveal, index) => (
              <p key={`${reveal.reason}-${index}`}>{reveal.reason}：{reveal.values.join("、")}</p>
            ))}
          </aside>
        )}
        {game.pending_decision && !game.pending_decision.submitted && (
          <aside className="private-info decision">
            <strong>需要你的决策：{game.pending_decision.kind}</strong>
            <p>按提示输入选项 ID；多个选项用逗号分隔。</p>
            <input
              value={decisionValue}
              onChange={(event) => setDecisionValue(event.target.value)}
              aria-label="决策选项"
            />
            <button onClick={() => void submitDecision()}>提交决策</button>
          </aside>
        )}
        {error && <p className="error">{error}</p>}
      </section>
    </main>
  );
}

export function App() {
  const [credentials, setCredentials] = useState<Credentials | null>(readCredentials);
  const { snapshot, setSnapshot, connection } = useRoom(credentials);
  const leave = () => {
    localStorage.removeItem(STORAGE_KEY);
    setCredentials(null);
  };
  const content = useMemo(() => {
    if (!credentials) return <Landing onConnected={setCredentials} />;
    if (!snapshot) return <main className="loading">正在恢复房间…</main>;
    if (!snapshot.game) {
      return <Lobby snapshot={snapshot} credentials={credentials} onUpdate={setSnapshot} />;
    }
    return (
      <GameTable
        game={snapshot.game}
        credentials={credentials}
        names={Object.fromEntries(snapshot.players.map((player) => [player.id, player.name]))}
        onUpdate={setSnapshot}
      />
    );
  }, [credentials, snapshot, setSnapshot]);

  return (
    <>
      <div className={`connection ${connection}`}>{connection}</div>
      {credentials && (
        <button className="leave-room" onClick={leave}>
          退出房间
        </button>
      )}
      {content}
    </>
  );
}
