import { openDB, IDBPDatabase } from "idb";
import { enqueueSync } from "./sync";

type SessionRecord = {
  id: string;
  payload: unknown;
  version: number;
  updatedAt: string;
};

export function createReplica() {
  let dbPromise: Promise<IDBPDatabase> | null = null;

  async function db() {
    if (!dbPromise) {
      dbPromise = openDB("neuromotorica", 1, {
        upgrade(database) {
          database.createObjectStore("sessions", { keyPath: "id" });
        },
      });
    }
    return dbPromise;
  }

  return {
    async bootstrap() {
      const database = await db();
      const count = await database.count("sessions");
      if (count === 0) {
        await database.put("sessions", {
          id: crypto.randomUUID(),
          payload: {},
          version: 1,
          updatedAt: new Date().toISOString(),
        } satisfies SessionRecord);
      }
    },
    async persist(record: SessionRecord) {
      const database = await db();
      await database.put("sessions", record);
      enqueueSync(record);
    },
  };
}
