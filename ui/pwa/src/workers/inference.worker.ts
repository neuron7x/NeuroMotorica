import { InferenceSession } from "onnxruntime-web";

type WorkerMessage = { type: "metrics"; payload: { heartRate?: number } };
type Subscriber = (message: WorkerMessage) => void;

class InferenceBus {
  private subscribers: Set<Subscriber> = new Set();

  subscribe(subscriber: Subscriber) {
    this.subscribers.add(subscriber);
    return () => this.subscribers.delete(subscriber);
  }

  publish(message: WorkerMessage) {
    for (const subscriber of this.subscribers) {
      subscriber(message);
    }
  }
}

const bus = new InferenceBus();

async function bootstrap() {
  try {
    await InferenceSession.create("/models/policy.onnx");
  } catch (error) {
    console.warn("Inference session fallback", error);
  }

  setInterval(() => {
    bus.publish({ type: "metrics", payload: { heartRate: Math.round(60 + Math.random() * 40) } });
  }, 2000);
}

bootstrap();

export function createInferenceWorker() {
  return {
    subscribe: (subscriber: Subscriber) => bus.subscribe(subscriber),
  };
}
