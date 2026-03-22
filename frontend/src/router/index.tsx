import { createBrowserRouter } from "react-router-dom";
import { lazy, Suspense } from "react";
import ProtectedRoute from "./ProtectedRoute";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const SetupPage = lazy(() => import("@/pages/SetupPage"));
const LandingPage = lazy(() => import("@/pages/LandingPage"));
const ProviderPage = lazy(() => import("@/pages/ProviderPage"));
const VendorPage = lazy(() => import("@/pages/VendorPage"));
const ResourceDetailPage = lazy(() => import("@/pages/ResourceDetailPage"));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function Loading() {
  return (
    <div className="flex items-center justify-center h-screen text-text-muted">
      Loading...
    </div>
  );
}

function Protected({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <Suspense fallback={<Loading />}>{children}</Suspense>
    </ProtectedRoute>
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
    path: "/",
    element: <Protected><LandingPage /></Protected>,
  },
  {
    path: "/providers/:vendor",
    element: <Protected><ProviderPage /></Protected>,
  },
  {
    path: "/vendors/:vendor",
    element: <Protected><VendorPage /></Protected>,
  },
  {
    path: "/resources/:uid",
    element: <Protected><ResourceDetailPage /></Protected>,
  },
  {
    path: "/analytics",
    element: <Protected><AnalyticsPage /></Protected>,
  },
  {
    path: "*",
    element: <Suspense fallback={<Loading />}><NotFoundPage /></Suspense>,
  },
]);
