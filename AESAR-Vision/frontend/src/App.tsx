import { FormEvent, useEffect, useState } from "react";

type Status = { connected: boolean; fps: number; clients: number; error: string | null; source_label: string };
const emptyStatus: Status = { connected: false, fps: 0, clients: 0, error: null, source_label: "Local camera 0" };

type Detection = { class_name: string; confidence: number; count: number; bounding_box: number[] };
type AIStatus = { state: string; detail: string | null; inference_fps: number; target_fps: number; detections: Detection[]; frame_width: number; frame_height: number; defender_detection: string };
const emptyAI: AIStatus = { state: "model_loading", detail: null, inference_fps: 0, target_fps: 2, detections: [], frame_width: 0, frame_height: 0, defender_detection: "unavailable" };

type PlantStatus = {
  status: string;
  quality: string;
  green_percent: number;
  yellow_percent: number;
  brown_percent: number;
  leaf_area_percent: number;
  detail: string | null;
  analysis_fps: number;
  target_fps: number;
};
const emptyPlant: PlantStatus = {
  status: "unavailable",
  quality: "unavailable",
  green_percent: 0,
  yellow_percent: 0,
  brown_percent: 0,
  leaf_area_percent: 0,
  detail: null,
  analysis_fps: 0,
  target_fps: 2,
};

export function App() {
  const [kind, setKind] = useState<"local" | "ip">("local");
  const [index, setIndex] = useState(0);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<Status>(emptyStatus);
  const [streamKey, setStreamKey] = useState(0);
  const [ai, setAI] = useState<AIStatus>(emptyAI);
  const [plant, setPlant] = useState<PlantStatus>(emptyPlant);

  useEffect(() => {
    const update = () => fetch("/api/status").then((r) => r.json()).then(setStatus).catch(() => setStatus(emptyStatus));
    update();
    const id = window.setInterval(update, 1000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const update = () => fetch("/api/ai/status").then((r) => r.json()).then(setAI).catch(() => setAI({ ...emptyAI, state: "model_unavailable", detail: "AI service unavailable" }));
    update();
    const id = window.setInterval(update, 750);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const update = () =>
      fetch("/api/plant/status")
        .then((r) => r.json())
        .then(setPlant)
        .catch(() => setPlant(emptyPlant));
    update();
    const id = window.setInterval(update, 1000);
    return () => window.clearInterval(id);
  }, []);

  async function setAIrate(target_fps: number) {
    if (isNaN(target_fps) || target_fps < 0.1 || target_fps > 15) return;
    const response = await fetch("/api/ai/config", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_fps }) });
    if (response.ok) setAI(await response.json());
  }

  async function setPlantRate(target_fps: number) {
    if (isNaN(target_fps) || target_fps < 0.1 || target_fps > 10) return;
    const response = await fetch("/api/plant/config", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_fps }) });
    if (response.ok) setPlant(await response.json());
  }

  async function switchSource(event: FormEvent) {
    event.preventDefault();
    const body = kind === "local" ? { kind, device_index: index } : { kind, url };
    const response = await fetch("/api/source", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!response.ok) alert((await response.json()).detail ?? "Could not select camera.");
    else { setStatus(await response.json()); setStreamKey((key) => key + 1); }
  }

  return (
    <main>
      <header>
        <p className="eyebrow">AESAR-VISION · PHASE 3</p>
        <h1>Live Camera &amp; Vision Intelligence</h1>
      </header>

      <section className="preview" aria-label="Camera preview">
        <img key={streamKey} src={`/api/stream?preview=${streamKey}`} alt="Live camera preview" />
        {ai.frame_width > 0 && (
          <div className="detection-layer">
            {ai.detections.map((detection, i) => {
              const [x1, y1, x2, y2] = detection.bounding_box;
              return (
                <div
                  className="box"
                  key={`${detection.class_name}-${i}`}
                  style={{
                    left: `${(x1 / ai.frame_width) * 100}%`,
                    top: `${(y1 / ai.frame_height) * 100}%`,
                    width: `${((x2 - x1) / ai.frame_width) * 100}%`,
                    height: `${((y2 - y1) / ai.frame_height) * 100}%`,
                  }}
                >
                  <span>{detection.class_name} {Math.round(detection.confidence * 100)}%</span>
                </div>
              );
            })}
          </div>
        )}
        <div className={`badge ${status.connected ? "online" : "offline"}`}>
          {status.connected ? "CONNECTED" : "DISCONNECTED"}
        </div>
      </section>

      <section className="panel">
        <form onSubmit={switchSource}>
          <label>
            Source
            <select value={kind} onChange={(e) => setKind(e.target.value as "local" | "ip")}>
              <option value="local">Local webcam</option>
              <option value="ip">IP camera URL</option>
            </select>
          </label>
          {kind === "local" ? (
            <label>
              Camera index
              <input type="number" min="0" value={index} onChange={(e) => setIndex(Number(e.target.value))} />
            </label>
          ) : (
            <label>
              Camera URL
              <input
                type="url"
                required
                placeholder="http://camera.local:8080/video"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </label>
          )}
          <button type="submit">Switch camera</button>
        </form>
        <aside>
          <span>Source: {status.source_label}</span>
          <span>Camera FPS: {status.fps}</span>
          {status.error && <span className="error">{status.error}</span>}
        </aside>
      </section>

      <section className="panel ai-panel">
        <div>
          <p className="eyebrow">VISION AI</p>
          <strong className={ai.state === "ai_ready" ? "ready" : "error"}>{ai.state.replace(/_/g, " ")}</strong>
          <p>{ai.detail ?? `Inference: ${ai.inference_fps} FPS · Defender detection: ${ai.defender_detection}`}</p>
        </div>
        <label>
          AI target FPS
          <input
            type="number"
            min="0.1"
            max="15"
            step="0.1"
            value={ai.target_fps}
            onChange={(event) => setAIrate(Number(event.target.value))}
          />
        </label>
        <div className="detections">
          <strong>Detections ({ai.detections.length})</strong>
          {ai.detections.length === 0 ? (
            <span>None</span>
          ) : (
            ai.detections.map((d, i) => (
              <span key={i}>
                {d.class_name} · {Math.round(d.confidence * 100)}% · count {d.count}
              </span>
            ))
          )}
        </div>
      </section>

      <section className="panel plant-panel">
        <div className="plant-header">
          <div>
            <p className="eyebrow">PLANT VISUAL INDICATORS</p>
            <div className="quality-row">
              <span>Analysis Quality:</span>
              <strong className={`badge-inline quality-${plant.quality}`}>{plant.quality.toUpperCase()}</strong>
              {plant.detail && <span className="plant-detail">({plant.detail})</span>}
            </div>
          </div>
          <label>
            Analysis FPS
            <input
              type="number"
              min="0.1"
              max="10"
              step="0.1"
              value={plant.target_fps}
              onChange={(e) => setPlantRate(Number(e.target.value))}
            />
          </label>
        </div>

        {plant.status === "ready" ? (
          <>
            <div className="plant-metrics">
              <div className="metric green">
                <span className="label">Green</span>
                <strong className="value">{plant.green_percent}%</strong>
              </div>
              <div className="metric yellow">
                <span className="label">Yellow</span>
                <strong className="value">{plant.yellow_percent}%</strong>
              </div>
              <div className="metric brown">
                <span className="label">Brown</span>
                <strong className="value">{plant.brown_percent}%</strong>
              </div>
              <div className="metric leaf-area">
                <span className="label">Leaf Area</span>
                <strong className="value">{plant.leaf_area_percent}%</strong>
              </div>
            </div>

            <div className="composition-bar" aria-label="Leaf color composition bar">
              <div
                className="bar-segment seg-green"
                style={{ width: `${plant.green_percent}%` }}
                title={`Green: ${plant.green_percent}%`}
              />
              <div
                className="bar-segment seg-yellow"
                style={{ width: `${plant.yellow_percent}%` }}
                title={`Yellow: ${plant.yellow_percent}%`}
              />
              <div
                className="bar-segment seg-brown"
                style={{ width: `${plant.brown_percent}%` }}
                title={`Brown: ${plant.brown_percent}%`}
              />
            </div>
          </>
        ) : (
          <p className="plant-unavailable">
            {plant.detail ?? "No usable plant/leaf region detected in the camera frame."}
          </p>
        )}
      </section>
    </main>
  );
}
