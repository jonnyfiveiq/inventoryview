import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="ml-56 max-[1280px]:ml-16 transition-all duration-200 p-6">
        <Outlet />
      </main>
    </div>
  );
}
