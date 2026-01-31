import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion as Motion } from "framer-motion";
import Home from "./Home";
import SummaryPage from "./SummaryPage";
import Login from "./Login";
import Signup from "./Signup";
import ChatPage from "./ChatPage";

const isAuthenticated = () => {
  return !!localStorage.getItem("access_token");
};

function ProtectedRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" />;
}

const PageWrapper = ({ children }) => (
  <Motion.div
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{ type: "spring", stiffness: 260, damping: 20 }}
  >
    {children}
  </Motion.div>
);

function App() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* PUBLIC */}
        <Route path="/login" element={<PageWrapper><Login /></PageWrapper>} />
        <Route path="/signup" element={<PageWrapper><Signup /></PageWrapper>} />

        {/* PROTECTED */}
        <Route
          path="/"
          element={
            <PageWrapper><Home /></PageWrapper>
          }
        />

        <Route
          path="/summary/:id"
          element={
            <ProtectedRoute>
              <PageWrapper><SummaryPage /></PageWrapper>
            </ProtectedRoute>
          }
        />

        <Route
          path="/chat/:id"
          element={
            <ProtectedRoute>
              <PageWrapper><ChatPage /></PageWrapper>
            </ProtectedRoute>
          }
        />

        {/* FALLBACK */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </AnimatePresence>
  );
}

export default App;


