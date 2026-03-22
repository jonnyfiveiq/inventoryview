import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/auth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isTokenExpired } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated || isTokenExpired()) {
    return <Navigate to="/login" state={{ from: location, expired: isAuthenticated && isTokenExpired() }} replace />;
  }

  return <>{children}</>;
}
