export type HealthResponse = {
  service: string;
  status: string;
  boundary: string;
};

const coreApiUrl = import.meta.env.VITE_CORE_API_URL ?? "http://localhost:8000";

export async function fetchCoreHealth(): Promise<HealthResponse> {
  const response = await fetch(`${coreApiUrl}/healthz`);

  if (!response.ok) {
    throw new Error(`Core API health check failed: ${response.status}`);
  }

  return parseHealthResponse(await response.json());
}

function parseHealthResponse(value: unknown): HealthResponse {
  if (!isRecord(value)) {
    throw new Error("Core API health response was not an object");
  }

  const { service, status, boundary } = value;

  if (typeof service !== "string" || typeof status !== "string" || typeof boundary !== "string") {
    throw new Error("Core API health response had an unexpected shape");
  }

  return { service, status, boundary };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

