import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-text-dim mb-4">404</h1>
        <p className="text-text-muted mb-6">The page you're looking for doesn't exist.</p>
        <Link
          to="/"
          className="inline-block px-6 py-2.5 bg-accent hover:bg-accent-hover text-white rounded-md transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
