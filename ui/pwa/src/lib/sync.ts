const queue: Array<{ id: string; version: number; payload: unknown }> = [];

export function enqueueSync(record: { id: string; version: number; payload: unknown }) {
  queue.push(record);
}

export async function flushSync(endpoint = "/v1/session") {
  const batch = queue.splice(0, queue.length);
  if (batch.length === 0) {
    return;
  }

  await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ batch }),
  });
}
