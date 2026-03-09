export interface JobResponse {
  id: string;
  score: number;
  metadata: {
    title?: string;
    company?: string;
    description?: string;
  };
}
