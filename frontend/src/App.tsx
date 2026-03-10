import { useState, useCallback } from "react";
import { JobCard } from "./components/JobCard";
import type { JobResponse } from "./types";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/recommendations`
  : "http://localhost:8000/recommendations";
const MIN_RESUME_LENGTH = 10;

export default function App() {
  const [resumeText, setResumeText] = useState("");
  const [k, setK] = useState(5);
  const [results, setResults] = useState<JobResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isResumeTooShort = resumeText.trim().length < MIN_RESUME_LENGTH;
  const isButtonDisabled = isLoading || isResumeTooShort;

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (isButtonDisabled) return;

      setIsLoading(true);
      setError(null);
      setResults([]);

      try {
        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resumeText: resumeText.trim(), k }),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          const detail = data.detail;
          let message: string;
          if (typeof detail === "string") message = detail;
          else if (Array.isArray(detail) && detail.length > 0 && detail[0].msg)
            message = detail.map((d: { msg?: string }) => d.msg).join("; ");
          else if (detail && typeof detail === "object" && "msg" in detail)
            message = String((detail as { msg: string }).msg);
          else message = `Request failed: ${res.status}`;
          throw new Error(message);
        }

        const data: JobResponse[] = await res.json();
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setIsLoading(false);
      }
    },
    [resumeText, k, isButtonDisabled]
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>Job Recommendations</h1>
        <p className="app-subtitle">Paste your resume to get matched jobs.</p>
      </header>

      <form onSubmit={handleSubmit} className="app-form">
        <label className="app-label" htmlFor="resume">
          Resume text
        </label>
        <textarea
          id="resume"
          className="app-textarea"
          placeholder="Paste your resume here..."
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          rows={10}
          disabled={isLoading}
        />

        <div className="app-row">
          <label className="app-label" htmlFor="k">
            Number of recommendations (1–20)
          </label>
          <input
            id="k"
            type="number"
            min={1}
            max={20}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="app-input"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          className="app-button"
          disabled={isButtonDisabled}
        >
          {isLoading ? "Loading…" : "Recommend Jobs"}
        </button>
      </form>

      {error && <p className="app-error" role="alert">{error}</p>}

      {results.length > 0 && (
        <section className="app-results" aria-label="Recommended jobs">
          <h2>Results</h2>
          <ul className="app-results-list">
            {results.map((job) => (
              <li key={job.id}>
                <JobCard job={job} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
