import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getUsageSummary, getFeatureDetail, getLoginAudit } from "@/api/usage";
import type { FeatureAreaSummary } from "@/api/usage";
import TimeRangeFilter from "@/components/usage/TimeRangeFilter";
import FeatureAreaCard from "@/components/usage/FeatureAreaCard";
import FeatureDetail from "@/components/usage/FeatureDetail";
import LoginAuditTable from "@/components/usage/LoginAuditTable";

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return formatDate(d);
}

export default function UsageDashboardPage() {
  const today = formatDate(new Date());
  const [startDate, setStartDate] = useState(daysAgo(7));
  const [endDate, setEndDate] = useState(today);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [loginPage, setLoginPage] = useState(1);

  const summaryQuery = useQuery({
    queryKey: ["usage", "summary", startDate, endDate],
    queryFn: () => getUsageSummary(startDate, endDate),
  });

  const featureDetailQuery = useQuery({
    queryKey: ["usage", "feature", selectedFeature, startDate, endDate],
    queryFn: () => getFeatureDetail(selectedFeature!, startDate, endDate),
    enabled: !!selectedFeature,
  });

  const loginQuery = useQuery({
    queryKey: ["usage", "logins", startDate, endDate, loginPage],
    queryFn: () => getLoginAudit(startDate, endDate, loginPage),
  });

  const handleRangeChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    setLoginPage(1);
    // Preserve selectedFeature — time range change should not reset drill-down
  };

  const handleFeatureClick = (fa: FeatureAreaSummary) => {
    setSelectedFeature(fa.feature_area);
  };

  const handleBack = () => {
    setSelectedFeature(null);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-semibold text-text">Usage Analytics</h1>
          <p className="text-sm text-text-muted mt-0.5">
            Track UI feature engagement and login activity
          </p>
        </div>
        <TimeRangeFilter
          startDate={startDate}
          endDate={endDate}
          onRangeChange={handleRangeChange}
        />
      </div>

      {/* Totals bar */}
      {summaryQuery.data && (
        <div className="flex gap-6 text-sm text-text-muted">
          <span>
            <strong className="text-text">
              {summaryQuery.data.total_events.toLocaleString()}
            </strong>{" "}
            total events
          </span>
          <span>
            <strong className="text-text">
              {summaryQuery.data.total_unique_users}
            </strong>{" "}
            unique users
          </span>
        </div>
      )}

      {/* Feature area drill-down or grid */}
      {selectedFeature ? (
        <FeatureDetail
          featureArea={selectedFeature}
          data={featureDetailQuery.data ?? null}
          isLoading={featureDetailQuery.isLoading}
          onBack={handleBack}
        />
      ) : (
        <>
          {summaryQuery.isLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="bg-surface border border-border rounded-lg p-4 animate-pulse h-28"
                />
              ))}
            </div>
          )}

          {summaryQuery.data && summaryQuery.data.feature_areas.length === 0 && (
            <div className="text-center py-12 text-text-muted">
              <p className="text-lg">No usage data for the selected period</p>
              <p className="text-sm mt-1">
                Events will appear here as users interact with the application.
              </p>
            </div>
          )}

          {summaryQuery.data && summaryQuery.data.feature_areas.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {summaryQuery.data.feature_areas.map((fa) => (
                <FeatureAreaCard
                  key={fa.feature_area}
                  data={fa}
                  onClick={() => handleFeatureClick(fa)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Login activity section */}
      <div className="border-t border-border pt-6">
        <h2 className="text-lg font-semibold text-text mb-4">Login Activity</h2>
        <LoginAuditTable
          data={loginQuery.data ?? null}
          isLoading={loginQuery.isLoading}
          page={loginPage}
          onPageChange={setLoginPage}
        />
      </div>
    </div>
  );
}
