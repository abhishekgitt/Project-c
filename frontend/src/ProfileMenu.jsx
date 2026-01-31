import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion as Motion, AnimatePresence } from "framer-motion";
import { User, LogOut, LogIn, UserPlus } from "lucide-react";
import "./ProfileMenu.css";

function ProfileMenu() {
    const [isOpen, setIsOpen] = useState(false);
    const navigate = useNavigate();
    const menuRef = useRef(null);

    // Check auth state
    const token = localStorage.getItem("access_token");

    // Close when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleLogout = () => {
        localStorage.clear();
        setIsOpen(false);
        navigate("/login");
    };

    const handleNavigation = (path) => {
        setIsOpen(false);
        navigate(path);
    };

    if (!token) {
        return (
            <button
                onClick={() => navigate('/login')}
                className="nav-login-btn"
            >
                <LogIn size={18} />
                <span>Login</span>
            </button>
        );
    }

    return (
        <div className="profile-menu-container" ref={menuRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="profile-btn"
                aria-label="Profile Menu"
            >
                <User size={20} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <Motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        transition={{ duration: 0.2 }}
                        className="profile-dropdown"
                    >
                        <button onClick={handleLogout} className="menu-item logout">
                            <LogOut size={16} />
                            <span>Logout</span>
                        </button>
                    </Motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default ProfileMenu;
