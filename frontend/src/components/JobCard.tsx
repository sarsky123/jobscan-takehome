import type { JobResponse } from "../types";
import "./JobCard.css";

const DESCRIPTION_MAX_LENGTH = 200;

function truncateDescription(description: string): string {
  if (description.length <= DESCRIPTION_MAX_LENGTH) return description;
  return description.slice(0, DESCRIPTION_MAX_LENGTH) + "...";
}

export function JobCard({ job }: { job: JobResponse }) {
  const { id, score, metadata } = job;
  const title = metadata.title ?? "";
  const company = metadata.company ?? "";
  const description = metadata.description ?? "";
  const displayDescription = truncateDescription(description);
  const scorePercent = (score * 100).toFixed(2);

  return (
    <article className="job-card" data-job-id={id}>
      <header className="job-card-header">
        <h3 className="job-card-title">{title || "Untitled"}</h3>
        {company && <p className="job-card-company">{company}</p>}
        <p className="job-card-score">{scorePercent}% Match</p>
      </header>
      {displayDescription && (
        <p className="job-card-description">{displayDescription}</p>
      )}
    </article>
  );
}
