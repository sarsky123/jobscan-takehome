import type { JobResponse } from "../types";
import { useId, useMemo, useState } from "react";
import "./JobCard.css";

const DESCRIPTION_MAX_LENGTH = 200;

function getDescriptionPreview(description: string): string {
  if (description.length <= DESCRIPTION_MAX_LENGTH) return description;
  return description.slice(0, DESCRIPTION_MAX_LENGTH).trimEnd() + "…";
}

export function JobCard({ job }: { job: JobResponse }) {
  const { id, score, metadata } = job;
  const title = metadata.title ?? "";
  const company = metadata.company ?? "";
  const description = metadata.description ?? "";
  const previewDescription = getDescriptionPreview(description);
  const isTruncatable = description.length > DESCRIPTION_MAX_LENGTH;
  const [isExpanded, setIsExpanded] = useState(false);
  const reactId = useId();
  const descriptionId = useMemo(
    () => `job-desc-${id || reactId}`,
    [id, reactId]
  );
  const scorePercent = (score * 100).toFixed(2);

  return (
    <article className="job-card" data-job-id={id}>
      <header className="job-card-header">
        <h3 className="job-card-title">{title || "Untitled"}</h3>
        {company && <p className="job-card-company">{company}</p>}
        <p className="job-card-score">{scorePercent}% Match</p>
      </header>
      {description && (
        <div className="job-card-description">
          <p id={descriptionId} className="job-card-description-text">
            {isExpanded || !isTruncatable ? description : previewDescription}
          </p>
          {isTruncatable && (
            <button
              type="button"
              className="job-card-toggle"
              aria-expanded={isExpanded}
              aria-controls={descriptionId}
              onClick={() => setIsExpanded((v) => !v)}
            >
              {isExpanded ? "Show less" : "Show more"}
            </button>
          )}
        </div>
      )}
    </article>
  );
}
