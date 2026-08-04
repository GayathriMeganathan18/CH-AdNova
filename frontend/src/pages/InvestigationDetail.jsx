import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client.js";
import InvestigationResultView from "../components/InvestigationResultView.jsx";
import ExportBar from "../components/ExportBar.jsx";
import { SkeletonKpiRow, SkeletonChart } from "../components/ui/Skeleton.jsx";
import ErrorState from "../components/ui/ErrorState.jsx";

export default function InvestigationDetail() {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setError(null);
    setResult(null);
    api.getInvestigation(id).then(setResult).catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={`Couldn't load investigation: ${error}`} onRetry={load} />;

  if (!result) {
    return (
      <div className="space-y-4">
        <SkeletonKpiRow count={2} />
        <SkeletonChart height={200} />
        <SkeletonChart height={280} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ExportBar investigationId={id} />
      <InvestigationResultView result={result} />
    </div>
  );
}
