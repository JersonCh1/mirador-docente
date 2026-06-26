/**
 * App — layout + routing de Mirador Docente.
 *
 * Rutas:
 *   /                       → SessionListPage (biblioteca)
 *   /upload                 → UploadPage
 *   /session/:id            → TeacherDashboard
 *   /session/:id/student    → StudentDashboard
 *   /institution            → InstitutionDashboard
 */
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar";
import SessionListPage from "./pages/SessionListPage";
import UploadPage from "./pages/UploadPage";
import TeacherDashboard from "./pages/TeacherDashboard";
import StudentDashboard from "./pages/StudentDashboard";
import InstitutionDashboard from "./pages/InstitutionDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-paper">
        <NavBar />
        <main>
          <Routes>
            <Route path="/" element={<SessionListPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/session/:id" element={<TeacherDashboard />} />
            <Route path="/session/:id/student" element={<StudentDashboard />} />
            <Route path="/institution" element={<InstitutionDashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-line py-6 text-center text-xs text-inkSoft">
          Mirador Docente · retroalimentación pedagógica anclada en evidencia
        </footer>
      </div>
    </BrowserRouter>
  );
}
