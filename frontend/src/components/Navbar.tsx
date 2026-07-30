import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { House, MessageSquare, LogIn, UserPlus, LogOut, Menu, X, Sun, Moon } from 'lucide-react';
import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

const loggedInLinks = [
  { to: '/', label: 'Home', icon: House },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
];

const loggedOutLinks = [
  { to: '/', label: 'Home', icon: House },
  { to: '/login', label: 'Login', icon: LogIn },
  { to: '/signup', label: 'Signup', icon: UserPlus },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const { user, logout } = useAuth();
  const links = user ? loggedInLinks : loggedOutLinks;

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // AuthContext already handles user-facing errors.
    }
    setOpen(false);
  };

  return (
    <motion.nav
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="relative z-50 flex items-center justify-between px-6 py-3 glass-strong"
    >
      <NavLink to="/" className="flex items-center gap-2.5 group">
        <motion.div
          whileHover={{ rotate: [0, -10, 10, 0] }}
          transition={{ duration: 0.5 }}
          className="w-9 h-9 rounded-xl overflow-hidden bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20 group-hover:shadow-primary/40 transition-shadow"
        >
          <img src="/medical-logo.png" alt="MedAssist logo" className="w-full h-full object-cover" />
        </motion.div>
        <span className="text-foreground font-bold text-lg tracking-tight hidden sm:block">
          Medical AI Assistant
        </span>
      </NavLink>

      <div className="hidden md:flex items-center gap-1">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-primary/15 text-primary glow-primary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
              }`
            }
          >
            <l.icon size={16} />
            {l.label}
          </NavLink>
        ))}

        {user && (
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-all duration-200"
          >
            <LogOut size={16} />
            Logout
          </button>
        )}

        {/* Theme toggle */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9, rotate: 180 }}
          onClick={toggle}
          className="ml-2 w-9 h-9 rounded-xl flex items-center justify-center text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          <AnimatePresence mode="wait" initial={false}>
            {theme === 'dark' ? (
              <motion.div key="sun" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.2 }}>
                <Sun size={17} />
              </motion.div>
            ) : (
              <motion.div key="moon" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.2 }}>
                <Moon size={17} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>

      {/* Mobile */}
      <div className="flex items-center gap-2 md:hidden">
        <motion.button whileTap={{ scale: 0.9, rotate: 180 }} onClick={toggle} className="w-9 h-9 rounded-xl flex items-center justify-center text-muted-foreground hover:text-primary transition-all">
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </motion.button>
        <button className="text-muted-foreground hover:text-foreground transition-colors" onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 glass-strong rounded-b-2xl p-4 flex flex-col gap-1 md:hidden"
          >
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
                  }`
                }
              >
                <l.icon size={18} />
                {l.label}
              </NavLink>
            ))}

            {user && (
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-all"
              >
                <LogOut size={18} />
                Logout
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
