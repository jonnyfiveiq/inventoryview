import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Server } from "lucide-react";

export default function SetupPage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/setup/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });

      if (res.status === 201) {
        setSuccess(true);
        setTimeout(() => navigate("/login", { replace: true }), 2000);
        return;
      }
      if (res.status === 409) {
        setError("Setup has already been completed.");
        return;
      }
      const body = await res.json().catch(() => null);
      setError(body?.detail ?? `Unexpected error (${res.status}).`);
    } catch {
      setError("Network error. Is the server running?");
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

        <h2 className="text-lg font-semibold mb-1">Initial Setup</h2>
        <p className="text-sm text-text-muted mb-6">Create the admin password to get started.</p>

        {error && (
          <div className="bg-state-error/10 border border-state-error/30 rounded-md px-4 py-3 mb-4 text-sm text-state-error">
            {error}
          </div>
        )}

        {success ? (
          <div className="bg-state-on/10 border border-state-on/30 rounded-md px-4 py-3 text-sm text-state-on">
            Admin password set successfully. Redirecting to login...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-muted mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={12}
                required
                autoFocus
                className="w-full px-3 py-2 bg-surface border border-border rounded-md text-text placeholder-text-dim focus:outline-none focus:border-accent transition-colors"
              />
            </div>
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-text-muted mb-1.5">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={12}
                required
                className="w-full px-3 py-2 bg-surface border border-border rounded-md text-text placeholder-text-dim focus:outline-none focus:border-accent transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? "Setting up..." : "Set Admin Password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
