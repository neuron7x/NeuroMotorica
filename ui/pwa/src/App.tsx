import { useEffect, useMemo, useState } from "react";
import { createInferenceWorker } from "./workers/inference.worker";
import { createReplica } from "./lib/indexedDbClient";

const worker = createInferenceWorker();

export default function App() {
  const replica = useMemo(() => createReplica(), []);
  const [status, setStatus] = useState("Idle");
  const [heartRate, setHeartRate] = useState<number | null>(null);

  useEffect(() => {
    const unsubscribe = worker.subscribe((message) => {
      if (message.type === "metrics") {
        setHeartRate(message.payload.heartRate ?? null);
        setStatus("Realtime inference running");
      }
    });

    replica.bootstrap().catch((error) => {
      console.error(error);
      setStatus("Replica bootstrap failed");
    });

    return () => unsubscribe();
  }, [replica]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <section className="max-w-xl mx-auto p-6 space-y-4">
        <header>
          <h1 className="text-2xl font-semibold">NeuroMotorica Coach</h1>
          <p className="text-sm text-slate-400">Offline-first progressive web experience.</p>
        </header>
        <article className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
          <p className="text-sm uppercase tracking-wide text-slate-500">Status</p>
          <p className="text-lg">{status}</p>
          {heartRate !== null ? (
            <p className="text-sm text-emerald-400">Heart rate: {heartRate} bpm</p>
          ) : (
            <p className="text-sm text-slate-500">No heart rate signal yet.</p>
          )}
        </article>
      </section>
    </main>
  );
}
