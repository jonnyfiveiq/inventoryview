import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Home,
  Server,
  Search,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  LogOut,
  ChevronDown,
  ListMusic,
  Plus,
  Pencil,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useAllResources } from "@/hooks/useResources";
import { usePlaylists, useCreatePlaylist, useUpdatePlaylist, useDeletePlaylist } from "@/hooks/usePlaylists";

interface SidebarProps {
  onSearchClick?: () => void;
}

export default function Sidebar({ onSearchClick }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [providersOpen, setProvidersOpen] = useState(true);
  const [playlistsOpen, setPlaylistsOpen] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, username } = useAuth();
  const { data: resourceData } = useAllResources();
  const { data: playlistData } = usePlaylists();
  const createPlaylist = useCreatePlaylist();
  const updatePlaylist = useUpdatePlaylist();
  const deletePlaylistMut = useDeletePlaylist();

  const vendors = resourceData
    ? [...new Set(resourceData.data.map((r) => r.vendor))].sort()
    : [];

  const isActive = (path: string) => location.pathname === path;
  const isProviderActive = (vendor: string) =>
    location.pathname === `/providers/${vendor}`;
  const isPlaylistActive = (slug: string) =>
    location.pathname === `/playlists/${slug}`;

  const playlists = playlistData?.data ?? [];

  const handleCreatePlaylist = () => {
    createPlaylist.mutate(
      { name: "New Playlist" },
      {
        onSuccess: (created) => {
          navigate(`/playlists/${created.slug}`);
          setEditingId(created.id);
          setEditName(created.name);
        },
      },
    );
  };

  const handleRenameSubmit = (id: string, slug: string) => {
    if (editName.trim() && editName.trim() !== "") {
      updatePlaylist.mutate(
        { identifier: slug, updates: { name: editName.trim() } },
        { onSettled: () => setEditingId(null) },
      );
    } else {
      setEditingId(null);
    }
  };

  const handleDeletePlaylist = (slug: string, name: string) => {
    if (window.confirm(`Delete playlist "${name}"? This cannot be undone.`)) {
      deletePlaylistMut.mutate(slug, {
        onSuccess: () => {
          if (location.pathname === `/playlists/${slug}`) {
            navigate("/");
          }
        },
      });
    }
  };

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

        {/* Providers section header */}
        <div
          onClick={() => {
            if (collapsed) {
              setCollapsed(false);
              setProvidersOpen(true);
            } else {
              setProvidersOpen(!providersOpen);
            }
          }}
          className={cn(
            "flex items-center w-full px-4 py-2.5 text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors cursor-pointer select-none",
            collapsed && "justify-center"
          )}
          title={collapsed ? "Providers" : undefined}
        >
          <Server className="w-5 h-5 shrink-0" />
          {!collapsed && (
            <>
              <span className="ml-3 flex-1 text-left">Providers</span>
              <ChevronDown
                className={cn(
                  "w-4 h-4 ml-1 transition-transform",
                  !providersOpen && "-rotate-90"
                )}
              />
            </>
          )}
        </div>
        {/* Provider items — flat, not nested */}
        {providersOpen && !collapsed && vendors.map((vendor) => (
          <Link
            key={vendor}
            to={`/providers/${vendor}`}
            className={cn(
              "block pl-12 pr-4 py-1.5 text-sm transition-colors border-l border-border ml-8",
              isProviderActive(vendor)
                ? "text-accent"
                : "text-text-muted hover:text-text hover:bg-surface-hover"
            )}
          >
            {vendor}
          </Link>
        ))}

        {/* Playlists section header */}
        <div
          onClick={() => {
            if (collapsed) {
              setCollapsed(false);
              setPlaylistsOpen(true);
            } else {
              setPlaylistsOpen(!playlistsOpen);
            }
          }}
          className={cn(
            "flex items-center w-full px-4 py-2.5 text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors cursor-pointer select-none",
            collapsed && "justify-center"
          )}
          title={collapsed ? "Playlists" : undefined}
        >
          <ListMusic className="w-5 h-5 shrink-0" />
          {!collapsed && (
            <>
              <span className="ml-3 flex-1 text-left">Playlists</span>
              <span
                role="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCreatePlaylist();
                }}
                className="p-0.5 rounded hover:bg-surface text-text-dim hover:text-text transition-colors cursor-pointer"
                title="New Playlist"
              >
                <Plus className="w-3.5 h-3.5" />
              </span>
              <ChevronDown
                className={cn(
                  "w-4 h-4 ml-1 transition-transform",
                  !playlistsOpen && "-rotate-90"
                )}
              />
            </>
          )}
        </div>
        {/* Playlist items — flat, not nested */}
        {playlistsOpen && !collapsed && playlists.length === 0 && (
          <div className="pl-12 pr-4 py-2 text-xs text-text-dim border-l border-border ml-8">No playlists yet</div>
        )}
        {playlistsOpen && !collapsed && playlists.map((pl) =>
          editingId === pl.id ? (
            <div
              key={pl.id}
              className="flex items-center pl-12 pr-4 py-1.5 text-sm border-l border-border ml-8"
            >
              <input
                autoFocus
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onBlur={() => handleRenameSubmit(pl.id, pl.slug)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleRenameSubmit(pl.id, pl.slug);
                  if (e.key === "Escape") setEditingId(null);
                }}
                className="flex-1 bg-transparent border-b border-accent text-sm text-text outline-none py-0"
              />
            </div>
          ) : (
            <Link
              key={pl.id}
              to={`/playlists/${pl.slug}`}
              className={cn(
                "group flex items-center pl-12 pr-4 py-1.5 text-sm transition-colors border-l border-border ml-8",
                isPlaylistActive(pl.slug)
                  ? "text-accent"
                  : "text-text-muted hover:text-text hover:bg-surface-hover"
              )}
            >
              <span className="flex-1 truncate">{pl.name}</span>
              <span className="text-[10px] text-text-dim mr-1">{pl.member_count}</span>
              <span
                role="button"
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  setEditingId(pl.id);
                  setEditName(pl.name);
                }}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-surface-hover transition-all"
                title="Rename"
              >
                <Pencil className="w-3 h-3" />
              </span>
              <span
                role="button"
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  handleDeletePlaylist(pl.slug, pl.name);
                }}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-surface-hover text-red-400 transition-all"
                title="Delete"
              >
                <Trash2 className="w-3 h-3" />
              </span>
            </Link>
          )
        )}

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
