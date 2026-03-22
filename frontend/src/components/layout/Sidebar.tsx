import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Home,
  Server,
  Search,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useAllResources } from "@/hooks/useResources";

interface SidebarProps {
  onSearchClick?: () => void;
}

export default function Sidebar({ onSearchClick }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [providersOpen, setProvidersOpen] = useState(true);
  const location = useLocation();
  const { logout, username } = useAuth();
  const { data: resourceData } = useAllResources();

  const vendors = resourceData
    ? [...new Set(resourceData.data.map((r) => r.vendor))].sort()
    : [];

  const isActive = (path: string) => location.pathname === path;
  const isProviderActive = (vendor: string) =>
    location.pathname === `/providers/${vendor}`;

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 1280px)");
    const handler = (e: MediaQueryListEvent) => setCollapsed(e.matches);
    setCollapsed(mq.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen bg-surface border-r border-border flex flex-col transition-all duration-200 z-40",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-14 px-4 border-b border-border">
        <Server className="w-6 h-6 text-accent shrink-0" />
        {!collapsed && (
          <span className="ml-3 font-semibold text-sm tracking-wide">
            InventoryView
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 overflow-y-auto">
        <NavItem
          to="/"
          icon={<Home className="w-5 h-5" />}
          label="Home"
          active={isActive("/")}
          collapsed={collapsed}
        />

        {/* Search */}
        <button
          onClick={onSearchClick}
          className={cn(
            "flex items-center w-full px-4 py-2.5 text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors",
            collapsed && "justify-center"
          )}
          title={collapsed ? "Search (⌘K)" : undefined}
        >
          <Search className="w-5 h-5 shrink-0" />
          {!collapsed && (
            <>
              <span className="ml-3 flex-1 text-left">Search</span>
              <kbd className="text-[10px] font-mono text-text-dim bg-surface-hover px-1.5 py-0.5 rounded border border-border">
                ⌘K
              </kbd>
            </>
          )}
        </button>

        {/* Providers section */}
        <div>
          <button
            onClick={() => setProvidersOpen(!providersOpen)}
            className={cn(
              "flex items-center w-full px-4 py-2.5 text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors",
              collapsed && "justify-center"
            )}
          >
            <Server className="w-5 h-5 shrink-0" />
            {!collapsed && (
              <>
                <span className="ml-3 flex-1 text-left">Providers</span>
                <ChevronDown
                  className={cn(
                    "w-4 h-4 transition-transform",
                    !providersOpen && "-rotate-90"
                  )}
                />
              </>
            )}
          </button>
          {providersOpen && !collapsed && vendors.length > 0 && (
            <div className="ml-8 border-l border-border">
              {vendors.map((vendor) => (
                <Link
                  key={vendor}
                  to={`/providers/${vendor}`}
                  className={cn(
                    "block px-4 py-1.5 text-sm transition-colors",
                    isProviderActive(vendor)
                      ? "text-accent"
                      : "text-text-muted hover:text-text"
                  )}
                >
                  {vendor}
                </Link>
              ))}
            </div>
          )}
        </div>

        <NavItem
          to="/analytics"
          icon={<BarChart3 className="w-5 h-5" />}
          label="Analytics"
          active={isActive("/analytics")}
          collapsed={collapsed}
        />
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-3">
        {!collapsed && username && (
          <div className="text-xs text-text-dim mb-2 px-1 truncate">
            {username}
          </div>
        )}
        <button
          onClick={logout}
          className={cn(
            "flex items-center w-full rounded-md px-3 py-2 text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors",
            collapsed && "justify-center px-0"
          )}
          title="Logout"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span className="ml-2">Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-surface border border-border flex items-center justify-center text-text-muted hover:text-text transition-colors"
      >
        {collapsed ? (
          <ChevronRight className="w-3 h-3" />
        ) : (
          <ChevronLeft className="w-3 h-3" />
        )}
      </button>
    </aside>
  );
}

function NavItem({
  to,
  icon,
  label,
  active,
  collapsed,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
  collapsed: boolean;
}) {
  return (
    <Link
      to={to}
      className={cn(
        "flex items-center px-4 py-2.5 text-sm transition-colors",
        active
          ? "text-accent bg-accent/10"
          : "text-text-muted hover:text-text hover:bg-surface-hover",
        collapsed && "justify-center"
      )}
      title={collapsed ? label : undefined}
    >
      <span className="shrink-0">{icon}</span>
      {!collapsed && <span className="ml-3">{label}</span>}
    </Link>
  );
}
