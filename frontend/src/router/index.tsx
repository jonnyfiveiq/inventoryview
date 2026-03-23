import { createBrowserRouter } from "react-router-dom";
import { lazy, Suspense } from "react";
import ProtectedRoute from "./ProtectedRoute";
import AppLayout from "@/components/layout/AppLayout";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const SetupPage = lazy(() => import("@/pages/SetupPage"));
const LandingPage = lazy(() => import("@/pages/LandingPage"));
const ProviderPage = lazy(() => import("@/pages/ProviderPage"));
const VendorPage = lazy(() => import("@/pages/VendorPage"));
const ResourceDetailPage = lazy(() => import("@/pages/ResourceDetailPage"));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage"));
const PlaylistDetailPage = lazy(() => import("@/pages/PlaylistDetailPage"));
const AutomationDashboardPage = lazy(() => import("@/pages/AutomationDashboardPage"));
const AutomationUploadPage = lazy(() => import("@/pages/AutomationUploadPage"));
const AutomationReviewPage = lazy(() => import("@/pages/AutomationReviewPage"));
const UsageDashboardPage = lazy(() => import("@/pages/UsageDashboardPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function Loading() {
  return (
    <div className="flex items-center justify-center h-screen text-text-muted">
      Loading...
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <Suspense fallback={<Loading />}><LoginPage /></Suspense>,
  },
  {
    path: "/setup",
    element: <Suspense fallback={<Loading />}><SetupPage /></Suspense>,
  },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: "/",
        element: <Suspense fallback={<Loading />}><LandingPage /></Suspense>,
      },
      {
        path: "/providers/:vendor",
        element: <Suspense fallback={<Loading />}><ProviderPage /></Suspense>,
      },
      {
        path: "/vendors/:vendor",
        element: <Suspense fallback={<Loading />}><VendorPage /></Suspense>,
      },
      {
        path: "/resources/:uid",
        element: <Suspense fallback={<Loading />}><ResourceDetailPage /></Suspense>,
      },
      {
        path: "/playlists/:identifier",
        element: <Suspense fallback={<Loading />}><PlaylistDetailPage /></Suspense>,
      },
      {
        path: "/automations",
        element: <Suspense fallback={<Loading />}><AutomationDashboardPage /></Suspense>,
      },
      {
        path: "/automations/upload",
        element: <Suspense fallback={<Loading />}><AutomationUploadPage /></Suspense>,
      },
      {
        path: "/automations/review",
        element: <Suspense fallback={<Loading />}><AutomationReviewPage /></Suspense>,
      },
      {
        path: "/analytics",
        element: <Suspense fallback={<Loading />}><AnalyticsPage /></Suspense>,
      },
      {
        path: "/admin/usage",
        element: <Suspense fallback={<Loading />}><UsageDashboardPage /></Suspense>,
      },
    ],
  },
  {
    path: "*",
    element: <Suspense fallback={<Loading />}><NotFoundPage /></Suspense>,
  },
]);
