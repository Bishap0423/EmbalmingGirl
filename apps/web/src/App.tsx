import { useEffect, useState } from "react";

type Health = {
  status: string;
  ruleset: string;
  card_types: number;
  card_instances: number;
};

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`health check failed: ${response.status}`);
        }
        return response.json() as Promise<Health>;
      })
      .then(setHealth)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setOffline(true);
      });
    return () => controller.abort();
  }, []);

  return (
    <main>
      <section className="panel" aria-labelledby="title">
        <p className="eyebrow">Embalming Girl · Development Build</p>
        <h1 id="title">冰冷的她醒来之前</h1>
        <p className="summary">本地规则引擎与 Web 界面已完成工程初始化。</p>
        <dl>
          <div>
            <dt>服务</dt>
            <dd>{health ? "已连接" : offline ? "未启动" : "检测中"}</dd>
          </div>
          <div>
            <dt>规则集</dt>
            <dd>{health?.ruleset ?? "—"}</dd>
          </div>
          <div>
            <dt>卡牌</dt>
            <dd>{health ? `${health.card_types} 种 / ${health.card_instances} 张` : "—"}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
