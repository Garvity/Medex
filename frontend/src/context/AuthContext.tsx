import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { User } from "firebase/auth";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  updateProfile as updateFirebaseProfile,
} from "firebase/auth";
import { api } from "../api";
import { firebaseAuth } from "../firebase";

export interface Profile {
  id: string;
  name: string | null;
  phone: string | null;
  timezone: string;
}
interface SignupPayload {
  name: string;
  phone: string;
  email: string;
  password: string;
}
interface AuthContextValue {
  user: User | null;
  session: null;
  profile: Profile | null;
  loading: boolean;
  authError: string;
  clearAuthError: () => void;
  login: (email: string, password: string) => Promise<void>;
  signup: (
    payload: SignupPayload,
  ) => Promise<{ emailConfirmationRequired: boolean }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function browserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const clearAuthError = useCallback(() => setAuthError(""), []);

  const refreshProfile = useCallback(async () => {
    if (!firebaseAuth.currentUser) {
      setProfile(null);
      return;
    }
    // This is an IANA identifier from the browser, not a client-calculated timestamp.
    // The server remains the source of truth for reminder scheduling.
    setProfile(await api.updateProfile({ timezone: browserTimezone() }));
  }, []);

  useEffect(
    () =>
      onAuthStateChanged(firebaseAuth, async (nextUser) => {
        setUser(nextUser);
        if (!nextUser) {
          setProfile(null);
          setLoading(false);
          return;
        }
        try {
          await refreshProfile();
        } catch (error: any) {
          setAuthError(error.message || "Unable to load your profile.");
        } finally {
          setLoading(false);
        }
      }),
    [refreshProfile],
  );

  const login = useCallback(async (email: string, password: string) => {
    setAuthError("");
    await signInWithEmailAndPassword(firebaseAuth, email.trim(), password);
  }, []);

  const signup = useCallback(
    async ({ name, phone, email, password }: SignupPayload) => {
      setAuthError("");
      const credential = await createUserWithEmailAndPassword(
        firebaseAuth,
        email.trim(),
        password,
      );
      await updateFirebaseProfile(credential.user, {
        displayName: name.trim(),
      });
      await api.updateProfile({
        name: name.trim(),
        phone: phone.trim(),
        timezone: browserTimezone(),
      });
      await refreshProfile();
      return { emailConfirmationRequired: false };
    },
    [refreshProfile],
  );

  const logout = useCallback(async () => {
    setAuthError("");
    await signOut(firebaseAuth);
  }, []);
  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      session: null,
      profile,
      loading,
      authError,
      clearAuthError,
      login,
      signup,
      logout,
      refreshProfile,
    }),
    [
      authError,
      clearAuthError,
      loading,
      login,
      logout,
      profile,
      refreshProfile,
      signup,
      user,
    ],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}
