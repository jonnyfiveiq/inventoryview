import { useState, useEffect, useCallback } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import SpotlightOverlay from "../search/SpotlightOverlay";

export default function AppLayout() {
  const [searchOpen, setSearchOpen] = useState(false);

  const openSearch = useCallback(() => setSearchOpen(true), []);
  const closeSearch = useCallback(() => setSearchOpen(false), []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar onSearchClick={openSearch} />
      <main className="ml-56 max-[1280px]:ml-16 transition-all duration-200 p-6">
        <Outlet />
      </main>
      <SpotlightOverlay isOpen={searchOpen} onClose={closeSearch} />
    </div>
  );
}
