import { useState, type FormEvent, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Server } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getSetupStatus } from "@/api/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  const expired = (location.state as { expired?: boolean })?.expired;

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
      return;
    }
    // Check if setup is needed
    getSetupStatus()
      .then((status) => {
        if (!status.setup_complete) navigate("/setup", { replace: true });
      })
      .catch(() => {});
  }, [isAuthenticated, navigate]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/";
      navigate(from, { replace: true });
    } catch {
      setError("Invalid credentials. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-sm p-8">
        <div className="flex items-center justify-center mb-8">
          <Server className="w-10 h-10 text-accent" />
          <span className="ml-3 text-2xl font-bold">InventoryView</span>
        </div>

        {expired && (
          <div className="bg-state-maintenance/10 border border-state-maintenance/30 rounded-md px-4 py-3 mb-4 text-sm text-state-maintenance">
            Your session has expired. Please log in again.
          </div>
        )}

        {error && (
          <div className="bg-state-error/10 border border-state-error/30 rounded-md px-4 py-3 mb-4 text-sm text-state-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-text-muted mb-1.5">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full px-3 py-2 bg-surface border border-border rounded-md text-text placeholder-text-dim focus:outline-none focus:border-accent transition-colors"
              placeholder="admin"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-text-muted mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 bg-surface border border-border rounded-md text-text placeholder-text-dim focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
