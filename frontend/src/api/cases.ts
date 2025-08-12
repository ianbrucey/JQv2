import { openHands } from "./open-hands-axios";

export type CaseStorage =
  | { type: "local"; path: string }
  | { type: "s3"; bucket: string; prefix: string };

export type Case = {
  id: string;
  name: string;
  description?: string;
  storage: CaseStorage;
  created_at: string;
  updated_at: string;
  last_opened_at?: string;
  size_bytes?: number;
};

export type ListCasesResponse = {
  items: Case[];
  total: number;
};

export async function listCases(q?: string): Promise<ListCasesResponse> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  const { data } = await openHands.get<ListCasesResponse>(
    `/api/cases?${params.toString()}`,
  );
  return data;
}

export async function createCase(payload: {
  name: string;
  description?: string;
  storage?: CaseStorage;
}): Promise<Case> {
  const { data } = await openHands.post<Case>("/api/cases", payload);
  return data;
}

