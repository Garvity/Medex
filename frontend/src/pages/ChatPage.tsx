import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, Loader2, Sparkles, Bell, BellRing, Settings, Info, Volume2, AlertCircle, Clock, Edit2 } from 'lucide-react';
import ChatMessage from '../components/ChatMessage';
import ChatSidebar, { Reminder } from '../components/ChatSidebar';
import TypingIndicator from '../components/TypingIndicator';
import { useAuth } from '../context/AuthContext';
import { api, isUuid } from '../api';
import {
  getStoredSessionId,
  getStoredSessionNames,
  setStoredSessionId,
  setStoredSessionNames,
} from '../chatSessionStorage';

const SUGGESTIONS = [
  'symptoms of gestational cholestasis',
  'side effects of oxycodone hydrochloride',
  'what is lipitor used for',
  'warnings for fingolimod',
  'treatment for eczema',
  'drug interaction aspirin ibuprofen',
  'nutrition in pea curry',
  'what are the side effects of non_existent_medicine',
  'remind me to take aspirin at 8am',
  'set alarm for lipitor at 2 30 pm',
  'bp 160',
  'risk age 55 bp 160',
  'covid-19 prevention guidelines',
  'hi'
];


interface Msg {
  user: string;
  bot: string;
  role: string;
  createdAt: string;
}

// Web Audio API Synthesized alarm chime
function playChime() {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sine';
    // Ascending major chord (C5 -> E5 -> G5 -> C6)
    osc.frequency.setValueAtTime(523.25, ctx.currentTime); 
    osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.15); 
    osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.3); 
    osc.frequency.setValueAtTime(1046.50, ctx.currentTime + 0.45); 
    
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.9);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + 0.9);
  } catch (e) {
    console.warn("AudioContext chime failed:", e);
  }
}

// Convert string like "8am", "9:30pm", "14:20" to minutes past midnight
function parseReminderTimeToMinutes(timeStr: string): number | null {
  const clean = timeStr.trim().toLowerCase();
  
  // HH:MM 24hr match
  const hhmmMatch = clean.match(/^(\d{1,2}):(\d{2})$/);
  if (hhmmMatch) {
    const hrs = parseInt(hhmmMatch[1], 10);
    const mins = parseInt(hhmmMatch[2], 10);
    if (hrs >= 0 && hrs < 24 && mins >= 0 && mins < 60) {
      return hrs * 60 + mins;
    }
  }

  // 12hr AM/PM match (e.g. 8am, 9:30pm, 12:00 am, or 1 05 pm)
  const ampmMatch = clean.match(/^(\d{1,2})(?::| )?(\d{2})?\s*(am|pm)$/);
  if (ampmMatch) {
    let hrs = parseInt(ampmMatch[1], 10);
    const mins = ampmMatch[2] ? parseInt(ampmMatch[2], 10) : 0;
    const period = ampmMatch[3];
    
    if (period === 'pm' && hrs < 12) hrs += 12;
    if (period === 'am' && hrs === 12) hrs = 0;
    
    if (hrs >= 0 && hrs < 24 && mins >= 0 && mins < 60) {
      return hrs * 60 + mins;
    }
  }

  // Pure digits hour match (e.g. "8", "20")
  const hourMatch = clean.match(/^(\d{1,2})$/);
  if (hourMatch) {
    const hrs = parseInt(hourMatch[1], 10);
    if (hrs >= 0 && hrs < 24) {
      return hrs * 60;
    }
  }

  return null;
}

export default function ChatPage() {
  const { user, profile, authError } = useAuth();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Msg[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [allMessages, setAllMessages] = useState<any[]>([]);
  const [customNames, setCustomNames] = useState<{ [key: string]: string }>({});
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('sidebar_width');
    return saved ? parseInt(saved, 10) : 320;
  });
  const [role, setRole] = useState('user');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [chatError, setChatError] = useState('');
  const [toastMessage, setToastMessage] = useState('');

  // Group chats by session_id to show in the sidebar
  const chatSessions = useMemo(() => {
    const map: { [key: string]: { id: string; name: string; time: number } } = {};
    allMessages.forEach((m) => {
      const sId = m.sessionId || '00000000-0000-0000-0000-000000000000';
      if (!map[sId]) {
        const isNewLoading = !m.bot;
        const baseName = m.sessionName || m.user.substring(0, 24) + (m.user.length > 24 ? '...' : '');
        map[sId] = {
          id: sId,
          name: customNames[sId] || (isNewLoading ? "New Chat..." : baseName),
          time: new Date(m.createdAt || 0).getTime()
        };
      }
    });
    return Object.values(map).sort((a, b) => b.time - a.time);
  }, [allMessages, customNames]);

  // Sync displayed messages to the active session ID
  useEffect(() => {
    if (!sessionId) return;
    const filtered = allMessages.filter(m => m.sessionId === sessionId);
    setMessages(filtered);
  }, [sessionId, allMessages]);
  
  // Reminders / Alarm states
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [notificationPref, setNotificationPref] = useState('in_app');
  const [browserPermission, setBrowserPermission] = useState(
    typeof window !== 'undefined' ? Notification.permission : 'default'
  );
  const [activeAlarm, setActiveAlarm] = useState<Reminder | null>(null);

  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const hasFetched = useRef(false);
  const isSendingRef = useRef(false);
  const lastTriggeredReminderRef = useRef<string>('');
  const activeUserIdRef = useRef<string | null>(null);

  // Chat state is deliberately scoped to the authenticated Firebase user. This
  // prevents a session UUID from one account being sent with another account's
  // Firebase token after an account switch in the same browser.
  useEffect(() => {
    const uid = user?.uid;
    activeUserIdRef.current = uid ?? null;
    hasFetched.current = false;
    isSendingRef.current = false;
    lastTriggeredReminderRef.current = '';

    setSessionId('');
    setAllMessages([]);
    setMessages([]);
    setCustomNames({});
    setReminders([]);
    setActiveAlarm(null);
    setChatError('');
    setToastMessage('');
    setHistoryLoading(false);
    setLoading(false);

    if (!uid) return;

    const storedSessionId = getStoredSessionId(uid);
    const nextSessionId = isUuid(storedSessionId)
      ? storedSessionId
      : self.crypto.randomUUID();

    if (nextSessionId !== storedSessionId) {
      setStoredSessionId(uid, nextSessionId);
    }

    setCustomNames(getStoredSessionNames(uid));
    setSessionId(nextSessionId);
  }, [user?.uid]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (!toastMessage) return;
    const timer = window.setTimeout(() => setToastMessage(''), 4500);
    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  // Request browser push permission
  const requestBrowserPermission = () => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      Notification.requestPermission().then((permission) => {
        setBrowserPermission(permission);
        if (permission === 'granted') {
          setToastMessage('🔔 Browser notifications enabled successfully!');
          new Notification("MedAssist AI", {
            body: "Notifications are now active.",
            icon: "/medical-logo.png"
          });
        }
      });
    }
  };

  // Fetch reminders list
  const loadReminders = useCallback(async (currentUser: any) => {
    if (!currentUser) return;
    const currentUserId = currentUser.uid;
    try {
      const nextReminders = (await api.listReminders()) as Reminder[];
      if (activeUserIdRef.current === currentUserId) {
        setReminders(nextReminders);
      }
    } catch (err) {
      if (activeUserIdRef.current === currentUserId) {
        console.error("Exception loading reminders:", err);
      }
    }
  }, []);

  // Fetch chat history
  const loadHistory = useCallback(async (currentUser: any) => {
    if (!currentUser) {
      setHistoryLoading(false);
      return;
    }
    const currentUserId = currentUser.uid;

    setHistoryLoading(true);
    setChatError('');

    try {
      const sessions = await api.listSessions();
      const messagesBySession = await Promise.all(sessions.map(async (session) => ({
        session,
        messages: await api.listMessages(session.id),
      })));
      if (activeUserIdRef.current === currentUserId) {
        setAllMessages(messagesBySession.flatMap(({ session, messages }) => messages.map((message) => ({
          user: message.query,
          bot: message.response,
          role: message.role,
          createdAt: message.created_at,
          sessionId: message.session_id,
          sessionName: session.name,
        }))));
      }
    } catch (err: any) {
      if (activeUserIdRef.current === currentUserId) {
        console.error("Exception loading history:", err);
        const msg = `Exception loading history: ${err.message || 'Unknown error'}`;
        setChatError(msg);
        setToastMessage(msg);
      }
    } finally {
      if (activeUserIdRef.current === currentUserId) {
        setHistoryLoading(false);
      }
    }
  }, []);

  // Initialize data on user login
  useEffect(() => {
    if (user && !hasFetched.current) {
      hasFetched.current = true;
      loadHistory(user);
      loadReminders(user);
    }
  }, [user, loadHistory, loadReminders]);

  // Background reminder/alarm checker loop (runs every 10 seconds)
  useEffect(() => {
    if (!user || reminders.length === 0) return;

    const interval = setInterval(() => {
      const now = new Date();
      const currentMin = now.getHours() * 60 + now.getMinutes();
      const todayTimestamp = now.getTime();

      reminders.forEach((r) => {
        if (r.status !== 'active') return;
        const targetMin = parseReminderTimeToMinutes(r.reminder_time);
        
        let shouldTrigger = false;
        const lastTriggered = r.last_triggered_at ? new Date(r.last_triggered_at).getTime() : null;

        if (r.frequency === "every_8_hours") {
          // Trigger if not triggered yet, or if 8 hours have passed (8 * 60 * 60 * 1000 ms)
          shouldTrigger = !lastTriggered || (todayTimestamp - lastTriggered) >= 8 * 60 * 60 * 1000;
        } else if (targetMin !== null && targetMin === currentMin) {
          if (r.frequency === "once") {
            shouldTrigger = !lastTriggered;
          } else if (r.frequency === "daily") {
            // Trigger if not triggered today (at least 20 hours ago to avoid double trigger in same minute)
            shouldTrigger = !lastTriggered || (todayTimestamp - lastTriggered) >= 20 * 60 * 60 * 1000;
          } else if (r.frequency === "weekly") {
            // Trigger if weekly (at least 6 days ago)
            shouldTrigger = !lastTriggered || (todayTimestamp - lastTriggered) >= 6 * 24 * 60 * 60 * 1000;
          }
        }

        if (shouldTrigger) {
          const runKey = `${r.id}-${currentMin}`;
          if (lastTriggeredReminderRef.current !== runKey) {
            lastTriggeredReminderRef.current = runKey;
            
            const prefStr = r.notification_pref || 'in_app';

            // 1. Trigger In-App Alarm Modal & Chime Sound
            if (prefStr.includes('in_app')) {
              setActiveAlarm(r);
              playChime();
            }
            
            // 2. Deliver Browser Push Alert
            if (Notification.permission === 'granted' && prefStr.includes('browser')) {
              new Notification("🏥 Medication Alarm!", {
                body: `Time to take ${r.medicine}! Scheduled at ${r.reminder_time}.`,
                icon: "/medical-logo.png"
              });
              
              if (!prefStr.includes('in_app')) {
                setToastMessage(`🔔 Push Notification triggered for ${r.medicine}`);
              }
            }
            
            // Email delivery is claimed and sent by the standalone backend worker.
            // The browser never claims that it has sent an email.

            // A browser-only reminder is acknowledged locally. Email-enabled reminders
            // are left for the worker so this client cannot affect delivery state.
            if (!prefStr.includes('in_app') && !prefStr.includes('email')) {
              api.markReminderTriggered(r.id).then(() => loadReminders(user)).catch(console.error);
            }
          }
        }
      });
    }, 10000);

    return () => clearInterval(interval);
  }, [reminders, user]);

  // Send Query to AI
  const sendQuery = useCallback(async (text?: string) => {
    if (isSendingRef.current) return;

    const q = (text || query).trim();
    if (!q) return;

    isSendingRef.current = true;
    setChatError('');
    setLoading(true);
    setQuery('');
    const requestUserId = user?.uid;
    const requestSessionId = sessionId;

    // Pre-append user message to chat UI immediately
    const tempUserMessage: any = {
      user: q,
      bot: '',
      role,
      createdAt: new Date().toISOString(),
      sessionId: requestSessionId || '00000000-0000-0000-0000-000000000000'
    };
    
    // We update local state first
    setAllMessages((prev) => [...prev, tempUserMessage]);

    try {
      // Build context history payload (last 12 turns) to send to backend
      const historyPayload = messages.slice(-12).map(m => ({
        user: m.user,
        assistant: m.bot
      }));

      const data = await api.ask({
        query: q,
        role,
        session_id: requestSessionId || undefined,
        history: historyPayload,
      });
      const rawResponse = data.response;
      if (typeof rawResponse !== 'string' || !rawResponse.trim()) {
        throw new Error('Fetch failed: server returned no response.');
      }
      if (!requestUserId || activeUserIdRef.current !== requestUserId) return;

      // Update the last message in state with the bot response
      setAllMessages((prev) => {
        const copy = [...prev];
        const lastMsg = copy[copy.length - 1];
        if (lastMsg && lastMsg.user === q && lastMsg.sessionId === requestSessionId) {
          lastMsg.bot = rawResponse;
        }
        return copy;
      });
      if (data.session_id !== requestSessionId) {
        setSessionId(data.session_id);
        setStoredSessionId(requestUserId, data.session_id);
      }

      // If response mentions reminder creation, refresh reminders from database
      if (rawResponse.toLowerCase().includes('remind') || rawResponse.toLowerCase().includes('schedule')) {
        setTimeout(() => loadReminders(user), 1500);
      }

    } catch (err: any) {
      if (!requestUserId || activeUserIdRef.current !== requestUserId) return;
      const message = String(err?.message || 'Unknown fetch error');
      const fetchFailed = message.toLowerCase().includes('no response') || message.toLowerCase().includes('fetch failed');
      const validationFailed = err?.status === 422;
      const knowledgeBaseUnavailable = err?.status === 503;
      const botMessage = fetchFailed
        ? 'Fetch failed: the server did not return a response. Please try again.'
        : validationFailed
          ? `Request validation error: ${message}. Please revise the message and try again.`
        : knowledgeBaseUnavailable
          ? `Medical knowledge base is not ready: ${message}`
        : `Connection error: ${message}. Make sure backend is running.`;

      const bannerMessage = fetchFailed
        ? 'Fetch failed: server returned no response.'
        : validationFailed
          ? `Request validation error: ${message}`
        : knowledgeBaseUnavailable
          ? `Medical knowledge base is not ready: ${message}`
        : `Connection error: ${message}`;

      setChatError(bannerMessage);
      setToastMessage(bannerMessage);
      
      setAllMessages((prev) => {
        const copy = [...prev];
        const lastMsg = copy[copy.length - 1];
        if (lastMsg && lastMsg.user === q && lastMsg.sessionId === requestSessionId) {
          lastMsg.bot = botMessage;
        }
        return copy;
      });
    } finally {
      isSendingRef.current = false;
      if (activeUserIdRef.current === requestUserId) {
        setLoading(false);
        inputRef.current?.focus();
      }
    }
  }, [query, role, messages, user, loadReminders, sessionId, allMessages]);

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSendingRef.current) {
        sendQuery();
      }
    }
  };

  const clearChat = useCallback(async () => {
    if (!user) return;
    const existingSessions = await api.listSessions();
    await Promise.all(existingSessions.map((session) => api.deleteSession(session.id)));
    setAllMessages([]);
    setChatError('');
    const newId = self.crypto.randomUUID();
    setStoredSessionId(user.uid, newId);
    setSessionId(newId);

  }, [user]);

  const startNewChat = useCallback(() => {
    if (!user) return;
    const newId = self.crypto.randomUUID();
    setStoredSessionId(user.uid, newId);
    setSessionId(newId);
    setChatError('');
    setToastMessage('✨ Started a new chat session.');
  }, [user]);

  const renameSession = useCallback(async (sId: string, newName: string) => {
    if (!user) return;
    setCustomNames((prev) => {
      const copy = { ...prev, [sId]: newName };
      setStoredSessionNames(user.uid, copy);
      return copy;
    });

    // Update in-memory state instantly
    setAllMessages((prev) =>
      prev.map((msg) =>
        msg.sessionId === sId ? { ...msg, sessionName: newName } : msg
      )
    );

    await api.renameSession(sId, newName);
  }, [user]);

  const deleteSession = useCallback(async (sId: string) => {
    if (!user) return;
    // 1. Remove from allMessages state
    setAllMessages((prev) => prev.filter((m) => m.sessionId !== sId));

    // 2. Clear from customNames localStorage
    setCustomNames((prev) => {
      const copy = { ...prev };
      delete copy[sId];
      setStoredSessionNames(user.uid, copy);
      return copy;
    });

    // 3. Delete from PostgreSQL through the authenticated backend
    try {
      await api.deleteSession(sId);
      setToastMessage('🗑️ Consultation deleted successfully.');
    } catch (err: any) {
      setToastMessage(`Error deleting consultation: ${err?.message || 'DB Sync failed'}`);
    }

    // 4. Fallback if the active session is deleted
    if (sessionId === sId) {
      const remainingIds = Array.from(new Set(allMessages.filter(m => m.sessionId !== sId).map(m => m.sessionId)));
      const nextId = remainingIds.find(id => id && id !== '00000000-0000-0000-0000-000000000000');
      if (nextId) {
        setSessionId(nextId);
        setStoredSessionId(user.uid, nextId);
      } else {
        startNewChat();
      }
    }
  }, [user, sessionId, allMessages, startNewChat]);

  // Delete/dismiss medication reminder
  const deleteReminder = async (id: string) => {
    try {
      await api.deleteReminder(id);
      setToastMessage('⏰ Reminder deleted successfully.');
      loadReminders(user);
    } catch (error: any) {
      setToastMessage(`Error deleting reminder: ${error.message}`);
    }
  };

  // Add medication reminder manually
  const addReminder = async (medicine: string, time: string, pref: string, freq: string, timezone: string) => {
    if (!user) return;
    try {
      await api.createReminder({
        medicine,
        reminder_time: time,
        notification_pref: pref,
        frequency: freq,
        timezone,
      });
      setToastMessage('⏰ Medication reminder set successfully!');
      loadReminders(user);
    } catch (error: any) {
      setToastMessage(`Error scheduling reminder: ${error.message}`);
      throw error;
    }
  };

  // Update/Edit medication reminder
  const updateReminder = async (
    id: string, medicine: string, time: string, pref: string, freq: string, timezone: string
  ) => {
    if (!user) return;
    try {
      await api.updateReminder(id, {
        medicine,
        reminder_time: time,
        notification_pref: pref,
        frequency: freq,
        timezone,
        status: 'active',
      });
      setToastMessage('⏰ Medication reminder updated successfully!');
      loadReminders(user);
    } catch (error: any) {
      setToastMessage(`Error updating reminder: ${error.message}`);
      throw error;
    }
  };

  // Alarm modal dismissal
  const dismissAlarm = async () => {
    if (!activeAlarm) return;
    
    // For once-off, mark status as completed. For recurring, just update last_triggered_at.
    await api.markReminderTriggered(activeAlarm.id).catch(console.error);
    
    setActiveAlarm(null);
    loadReminders(user);
  };

  const snoozeAlarm = () => {
    if (!activeAlarm) return;
    setActiveAlarm(null);
    setToastMessage('⏰ Snoozed medication reminder for 5 minutes.');
  };

  const handleSelectSession = (sId: string) => {
    if (!user) return;
    setSessionId(sId);
    setStoredSessionId(user.uid, sId);
  };

  const handleWidthChange = (w: number) => {
    setSidebarWidth(w);
    localStorage.setItem('sidebar_width', String(w));
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex-1 flex gap-4 p-4 overflow-hidden relative z-10 h-[calc(100vh-64px)]"
    >
      <ChatSidebar
        role={role}
        onRoleChange={setRole}
        onPresetClick={(t) => sendQuery(t)}
        onClear={clearChat}
        onNewChat={startNewChat}
        sessions={chatSessions}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onRenameSession={renameSession}
        onDeleteSession={deleteSession}
        width={sidebarWidth}
        onWidthChange={handleWidthChange}
        reminders={reminders}
        onDeleteReminder={deleteReminder}
        onAddReminder={addReminder}
        onUpdateReminder={updateReminder}
        notificationPref={notificationPref}
        onNotificationPrefChange={setNotificationPref}
        browserPermission={browserPermission}
        onRequestBrowserPermission={requestBrowserPermission}
      />

      <div className="flex-1 flex flex-col glass-strong rounded-2xl overflow-hidden shadow-2xl border border-border/50 relative">
        
        {/* Active Alarm Modal Overlay */}
        <AnimatePresence>
          {activeAlarm && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/80 backdrop-blur-md z-40 flex items-center justify-center p-6"
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                className="bg-card border-2 border-primary/45 rounded-2xl p-8 max-w-md w-full shadow-2xl text-center flex flex-col items-center gap-6 glow-neon-strong"
              >
                <div className="relative">
                  <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
                  <div className="w-16 h-16 rounded-full bg-primary/10 border-2 border-primary flex items-center justify-center text-primary relative">
                    <BellRing size={28} className="animate-bounce" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-foreground">Medication Reminder!</h3>
                  <p className="text-muted-foreground text-sm mt-2">
                    Time to take your scheduled dose:
                  </p>
                  <p className="text-2xl font-black text-neon mt-3 tracking-wide">
                    {activeAlarm.medicine}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center justify-center gap-1.5">
                    <Clock size={12} className="text-primary/70" />
                    Scheduled for {activeAlarm.reminder_time}
                  </p>
                </div>
                
                <div className="flex gap-3 w-full mt-2">
                  <button
                    onClick={snoozeAlarm}
                    className="flex-1 py-3 px-4 rounded-xl border border-border hover:bg-muted text-foreground text-sm font-semibold transition-all"
                  >
                    Snooze
                  </button>
                  <button
                    onClick={dismissAlarm}
                    className="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-primary to-emerald-500 hover:from-primary/95 text-primary-foreground text-sm font-bold shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-1.5"
                  >
                    <Volume2 size={16} /> Take Dose
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Header Toast messages */}
        {toastMessage && (
          <div className="absolute right-6 top-6 z-30 max-w-sm rounded-xl border border-primary/30 bg-primary/10 px-4 py-3 text-xs text-foreground shadow-xl backdrop-blur-md flex items-center gap-2 glow-neon">
            <Sparkles size={14} className="text-primary animate-pulse" />
            <span className="font-medium">{toastMessage}</span>
          </div>
        )}

        {/* Chat header area */}
        <div className="px-6 py-4 border-b border-border/40 bg-card/10 flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-secondary p-0.5 shadow-md shadow-primary/10">
                <img src="/medical-logo.png" alt="MedAssist logo" className="w-full h-full rounded-md object-cover bg-background" />
              </div>
              <div>
                <h2 className="text-foreground font-black text-base flex items-center gap-1.5">
                  MedAssist AI
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-bold uppercase tracking-wider">v2.0</span>
                </h2>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-primary text-[10px] font-bold uppercase tracking-wider">Agent RAG Active</span>
            </div>
            
            <div className="text-right hidden sm:block">
              <p className="text-xs font-bold text-foreground truncate max-w-[150px]">
                {profile?.name?.trim() || 'Patient'}
              </p>
              <p className="text-[10px] text-muted-foreground truncate max-w-[150px]">
                {user?.email}
              </p>
            </div>
          </div>
        </div>

        {/* Inline alerts/loading indicators */}
        {(authError || chatError || historyLoading) && (
          <div className="px-6 py-2.5 border-b border-border/30 text-xs bg-card/5 flex items-center gap-4">
            {historyLoading && (
              <span className="inline-flex items-center gap-2 text-muted-foreground mr-4">
                <Loader2 size={12} className="animate-spin text-primary" />
                Retrieving consultation archives...
              </span>
            )}
            {authError && <span className="text-danger flex items-center gap-1"><AlertCircle size={12} /> {authError}</span>}
            {chatError && <span className="text-danger flex items-center gap-1"><AlertCircle size={12} /> {chatError}</span>}
          </div>
        )}

        {/* Message scroll lane */}
        <div className="flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-6">
          <div className="max-w-3xl mx-auto w-full flex-1 flex flex-col gap-6">
            {messages.length === 0 && !loading && !historyLoading ? (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex-1 flex flex-col items-center justify-center text-center py-10"
              >
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                  className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-secondary p-1 mb-8 shadow-2xl shadow-primary/25 relative glow-neon"
                >
                  <img src="/medical-logo.png" alt="MedAssist logo" className="w-full h-full rounded-[20px] object-cover bg-background" />
                </motion.div>
                
                <h3 className="text-foreground text-3xl font-black mb-3 tracking-tight">
                  Welcome to <span className="text-gradient">MedAssist AI</span>
                </h3>
                <p className="text-muted-foreground text-sm max-w-lg mb-10 leading-relaxed font-medium">
                  Your secure clinical assistant. Query drug interactions, medical profiles, nutrition data, or schedule medication alarms directly here or in the sidebar.
                </p>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl text-left">
                  {SUGGESTIONS.map((s, i) => (
                    <motion.button
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      whileHover={{ y: -2, scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => sendQuery(s)}
                      className="p-4 rounded-2xl glass hover:bg-primary/5 hover:border-primary/30 transition-all text-xs font-semibold text-muted-foreground hover:text-foreground flex flex-col justify-between h-20 border border-border/60 hover:glow-primary"
                    >
                      <span className="line-clamp-2">{s}</span>
                      <span className="text-[10px] text-primary/70 font-bold uppercase tracking-wider self-end mt-2">Try query →</span>
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            ) : (
              <>
                <div className="flex flex-col gap-6">
                  {messages.map((msg, i) => (
                    <ChatMessage key={i} message={msg} />
                  ))}
                </div>
                {loading && (
                  <div className="flex justify-start items-center gap-3">
                    <TypingIndicator />
                  </div>
                )}
              </>
            )}
            <div ref={endRef} />
          </div>
        </div>

        {/* Input Form container */}
        <div className="p-4 bg-gradient-to-t from-card/30 to-transparent border-t border-border/40">
          <div className="max-w-3xl mx-auto w-full relative flex flex-col gap-2">
            
            <div className="flex gap-3 items-end relative glass rounded-2xl border border-border/80 p-2 focus-within:border-primary focus-within:glow-neon transition-all bg-card/45 shadow-lg">
              <textarea
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKey}
                disabled={loading || historyLoading}
                placeholder="Message MedAssist... (e.g. remind me to take Lipitor at 9 PM)"
                rows={1}
                className="flex-1 max-h-[160px] min-h-[36px] py-2 px-3 bg-transparent text-foreground text-sm placeholder:text-muted-foreground focus:outline-none resize-none leading-relaxed"
                autoFocus
              />
              
              <div className="flex items-center gap-2 pb-1.5 pr-1">
                <button
                  type="button"
                  className="p-2 rounded-xl text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all"
                  title="Voice dictation (Coming soon)"
                >
                  <Mic size={16} />
                </button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => sendQuery()}
                  disabled={loading || historyLoading || !query.trim()}
                  className="w-9 h-9 rounded-xl bg-gradient-to-r from-primary to-emerald-500 text-primary-foreground flex items-center justify-center shadow-lg shadow-primary/25 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  title="Send message"
                >
                  <Send size={14} />
                </motion.button>
              </div>
            </div>
            
            <div className="flex items-center justify-between px-2 text-[10px] text-muted-foreground">
              <span>Shift + Enter for line break | Enter to send</span>
              <span className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wider text-primary/80">
                <Info size={10} /> Disclaimers: General medical guidance only
              </span>
            </div>
          </div>
        </div>

      </div>
    </motion.div>
  );
}
