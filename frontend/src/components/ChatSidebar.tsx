import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Stethoscope,
  Pill,
  HeartPulse,
  Brain,
  Salad,
  AlertTriangle,
  Clock,
  MessageCircle,
  Trash2,
  Bell,
  Info,
  Plus,
  X,
  Edit2,
} from "lucide-react";

const PRESETS = [
  {
    icon: Stethoscope,
    text: "symptoms of gestational cholestasis",
    color: "text-primary",
  },
  {
    icon: Pill,
    text: "side effects of oxycodone hydrochloride",
    color: "text-secondary",
  },
  { icon: Pill, text: "what is lipitor used for", color: "text-sky-400" },
  {
    icon: Stethoscope,
    text: "warnings for fingolimod",
    color: "text-rose-400",
  },
  { icon: HeartPulse, text: "treatment for eczema", color: "text-teal-400" },
  {
    icon: AlertTriangle,
    text: "drug interaction aspirin ibuprofen",
    color: "text-amber-400",
  },
  { icon: Salad, text: "nutrition in pea curry", color: "text-emerald-400" },
  {
    icon: AlertTriangle,
    text: "what are the side effects of non_existent_medicine",
    color: "text-red-400",
  },
  {
    icon: Clock,
    text: "remind me to take aspirin at 8am",
    color: "text-orange-400",
  },
  {
    icon: Clock,
    text: "set alarm for lipitor at 2 30 pm",
    color: "text-yellow-400",
  },
  { icon: HeartPulse, text: "bp 160", color: "text-red-400" },
  { icon: Brain, text: "risk age 55 bp 160", color: "text-violet-400" },
  {
    icon: AlertTriangle,
    text: "covid-19 prevention guidelines",
    color: "text-cyan-400",
  },
  { icon: MessageCircle, text: "hi", color: "text-muted-foreground" },
];

export interface Reminder {
  id: string;
  medicine: string;
  reminder_time: string;
  status: string;
  notification_pref: string;
  frequency?: string;
  timezone: string;
  last_triggered_at?: string | null;
  next_occurrence_at?: string | null;
}

interface Props {
  role: string;
  onRoleChange: (r: string) => void;
  onPresetClick: (t: string) => void;
  onClear: () => void;
  onNewChat: () => void;
  sessions: { id: string; name: string }[];
  currentSessionId: string;
  onSelectSession: (id: string) => void;
  onRenameSession: (id: string, name: string) => void;
  onDeleteSession: (id: string) => void;
  width: number;
  onWidthChange: (w: number) => void;
  reminders: Reminder[];
  onDeleteReminder: (id: string) => Promise<void>;
  onAddReminder: (
    medicine: string,
    time: string,
    pref: string,
    freq: string,
    timezone: string,
  ) => Promise<void>;
  onUpdateReminder: (
    id: string,
    medicine: string,
    time: string,
    pref: string,
    freq: string,
    timezone: string,
  ) => Promise<void>;
  notificationPref: string;
  onNotificationPrefChange: (pref: string) => void;
  browserPermission: string;
  onRequestBrowserPermission: () => void;
}

function formatNextOccurrence(reminder: Reminder): string | null {
  if (!reminder.next_occurrence_at) return null;
  const occurrence = new Date(reminder.next_occurrence_at);
  if (Number.isNaN(occurrence.getTime())) return null;
  return occurrence.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function browserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

export default function ChatSidebar({
  role,
  onRoleChange,
  onPresetClick,
  onClear,
  onNewChat,
  sessions,
  currentSessionId,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  width,
  onWidthChange,
  reminders,
  onDeleteReminder,
  onAddReminder,
  onUpdateReminder,
  notificationPref,
  onNotificationPrefChange,
  browserPermission,
  onRequestBrowserPermission,
}: Props) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [newMed, setNewMed] = useState("");
  const [newHour, setNewHour] = useState("08");
  const [newMinute, setNewMinute] = useState("00");
  const [newAmpm, setNewAmpm] = useState("AM");
  const [prefInApp, setPrefInApp] = useState(true);
  const [prefBrowser, setPrefBrowser] = useState(false);
  const [prefEmail, setPrefEmail] = useState(false);
  const [newFreq, setNewFreq] = useState("once");
  const [reminderTimezone, setReminderTimezone] = useState(browserTimezone);
  const [submitting, setSubmitting] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMed.trim()) return;

    const selectedPrefs = [];
    if (prefInApp) selectedPrefs.push("in_app");
    if (prefBrowser) selectedPrefs.push("browser");
    if (prefEmail) selectedPrefs.push("email");

    if (selectedPrefs.length === 0) {
      alert("Please select at least one notification option.");
      return;
    }

    const hrVal = parseInt(newHour, 10);
    const minVal = parseInt(newMinute, 10);

    if (isNaN(hrVal) || hrVal < 1 || hrVal > 12) {
      alert("Please enter a valid hour between 01 and 12.");
      return;
    }
    if (isNaN(minVal) || minVal < 0 || minVal > 59) {
      alert("Please enter a valid minute between 00 and 59.");
      return;
    }

    const timeString = `${String(hrVal).padStart(2, "0")}:${String(minVal).padStart(2, "0")} ${newAmpm}`;
    const prefString = selectedPrefs.join(",");

    setSubmitting(true);
    try {
      if (editingId) {
        await onUpdateReminder(
          editingId,
          newMed.trim(),
          timeString,
          prefString,
          newFreq,
          reminderTimezone,
        );
      } else {
        await onAddReminder(
          newMed.trim(),
          timeString,
          prefString,
          newFreq,
          reminderTimezone,
        );
      }
      setNewMed("");
      setNewHour("08");
      setNewMinute("00");
      setNewAmpm("AM");
      setNewFreq("once");
      setReminderTimezone(browserTimezone());
      setPrefInApp(true);
      setPrefBrowser(false);
      setPrefEmail(false);
      setEditingId(null);
      setShowAddForm(false);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartEdit = (r: Reminder) => {
    setEditingId(r.id);
    setNewMed(r.medicine);
    setNewFreq(r.frequency || "once");
    setReminderTimezone(r.timezone || browserTimezone());

    const prefStr = r.notification_pref || "in_app";
    setPrefInApp(prefStr.includes("in_app"));
    setPrefBrowser(prefStr.includes("browser"));
    setPrefEmail(prefStr.includes("email"));

    // Parse time formats flexibly (e.g., "01:05 PM", "1 05 pm", "8am", "20:00")
    const clean = r.reminder_time.toLowerCase().trim();
    const period = clean.includes("pm") ? "PM" : "AM";

    const digits = clean.match(/\d+/g);
    if (digits && digits.length >= 1) {
      const hr = digits[0].padStart(2, "0");
      const min = digits.length >= 2 ? digits[1].padStart(2, "0") : "00";
      setNewHour(hr);
      setNewMinute(min);
      setNewAmpm(period);
    }
    setShowAddForm(true);
  };

  const handleSaveRename = (sId: string) => {
    if (renameValue.trim()) {
      onRenameSession(sId, renameValue.trim());
    }
    setRenamingId(null);
  };

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay: 0.1 }}
      className="hidden lg:flex flex-col glass-strong rounded-2xl overflow-hidden border-border/50 shadow-xl relative"
      style={{ width: `${width}px` }}
    >
      {/* New Chat Button */}
      <div className="p-3 border-b border-border/40 bg-card/15">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-primary to-emerald-500 hover:from-primary/95 text-primary-foreground text-xs font-bold shadow-lg shadow-primary/10 transition-all cursor-pointer"
        >
          <Plus size={14} />
          New Chat Session
        </motion.button>
      </div>
      {/* Unified Sidebar Scroll Wrapper */}
      <div className="flex-1 overflow-y-auto pr-1 select-none">
        {/* Role selector */}
        <div className="p-4 border-b border-border/40 bg-card/20">
          <label className="text-[10px] font-bold uppercase tracking-[2px] text-muted-foreground mb-2 block">
            Your Role
          </label>
          <select
            value={role}
            onChange={(e) => onRoleChange(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl bg-muted/40 border border-border text-foreground text-sm font-medium focus:outline-none focus:border-primary focus:glow-input transition-all cursor-pointer appearance-none shadow-inner"
          >
            <option value="user">👤 Patient / User</option>
            <option value="doctor">🩺 Doctor / Clinician</option>
          </select>
        </div>

        {/* Doctor Mode Clinician Dashboard */}
        {role === "doctor" && (
          <div className="p-4 border-b border-border/40 bg-emerald-500/5 flex flex-col gap-2">
            <div className="flex items-center gap-1.5 text-emerald-400">
              <HeartPulse size={14} className="animate-pulse" />
              <h4 className="text-[10px] font-bold uppercase tracking-[2px]">
                Clinician Dashboard
              </h4>
            </div>
            <p className="text-[10px] text-muted-foreground leading-relaxed">
              Authorized portal active. Reference clinical monographs, run
              diagnostics, and check patient alarms.
            </p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold uppercase">
                Rx Allowed
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-bold uppercase">
                Auditing Mode
              </span>
            </div>
          </div>
        )}

        {/* Recent Chats / Threads Section */}
        <div className="p-4 border-b border-border/40 bg-card/10 flex flex-col gap-2.5">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <MessageCircle size={14} className="text-secondary" />
            <h3 className="text-[10px] font-bold uppercase tracking-[2px]">
              Recent Consultations
            </h3>
          </div>

          {sessions.length === 0 ? (
            <p className="text-[10px] text-muted-foreground italic px-1 py-1">
              No active consultations
            </p>
          ) : (
            <div className="flex flex-col gap-1">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className={`group relative flex items-center justify-between rounded-xl border transition-all duration-200 ${
                    s.id === currentSessionId
                      ? "bg-gradient-to-r from-primary/10 to-secondary/5 border-primary/30"
                      : "border-transparent hover:bg-muted/40"
                  }`}
                >
                  {renamingId === s.id ? (
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => handleSaveRename(s.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleSaveRename(s.id);
                        if (e.key === "Escape") setRenamingId(null);
                      }}
                      className="bg-background/80 border border-primary/45 px-2.5 py-1 rounded-lg text-xs w-full focus:outline-none text-foreground m-1 shadow-inner"
                      autoFocus
                    />
                  ) : (
                    <>
                      <button
                        onClick={() => onSelectSession(s.id)}
                        className={`flex-1 text-left px-3 py-2 text-xs truncate cursor-pointer ${
                          s.id === currentSessionId
                            ? "text-foreground font-semibold"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                        title={s.name}
                      >
                        {s.name}
                      </button>
                      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-all mr-1">
                        <button
                          onClick={() => {
                            setRenamingId(s.id);
                            setRenameValue(s.name);
                          }}
                          className="p-1 text-muted-foreground hover:text-primary rounded hover:bg-primary/10 transition-all cursor-pointer"
                          title="Rename Consultation"
                        >
                          <Edit2 size={12} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (
                              confirm(
                                "Are you sure you want to delete this chat consultation?",
                              )
                            ) {
                              onDeleteSession(s.id);
                            }
                          }}
                          className="p-1 text-muted-foreground hover:text-danger rounded hover:bg-danger/10 transition-all cursor-pointer"
                          title="Delete Consultation"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Alarms & Reminders Manager */}
        <div className="p-4 border-b border-border/40 bg-card/10 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Bell size={14} className="text-primary animate-pulse" />
              <h3 className="text-[10px] font-bold uppercase tracking-[2px] text-muted-foreground">
                Alarms & Reminders
              </h3>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setShowInfo(!showInfo)}
                className="p-1 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                title="Notification channels info"
              >
                <Info size={13} />
              </button>
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="p-1 rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                title="Set medication reminder"
              >
                {showAddForm ? <X size={13} /> : <Plus size={13} />}
              </button>
            </div>
          </div>

          {/* Info panel */}
          <AnimatePresence>
            {showInfo && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="text-[11px] text-muted-foreground bg-muted/30 border border-border p-2.5 rounded-lg leading-relaxed overflow-hidden"
              >
                <p className="font-bold text-foreground mb-1">
                  Notification Channels:
                </p>
                <ul className="list-disc list-inside space-y-1">
                  <li>
                    <span className="text-primary font-medium">In-App</span>:
                    Visual overlay & audio chime when active.
                  </li>
                  <li>
                    <span className="text-secondary font-medium">Browser</span>:
                    OS push alerts (works in background).
                  </li>
                  <li>
                    <span className="text-emerald-400 font-medium">Email</span>:
                    Delivered by the server-side Resend reminder worker, even
                    when this browser is closed.
                  </li>
                </ul>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Add reminder inline form */}
          <AnimatePresence>
            {showAddForm && (
              <motion.form
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                onSubmit={handleSubmit}
                className="flex flex-col gap-2.5 bg-muted/20 border border-border/60 p-3 rounded-xl overflow-hidden text-xs"
              >
                <input
                  type="text"
                  required
                  placeholder="Medicine (e.g., Aspirin)"
                  value={newMed}
                  onChange={(e) => setNewMed(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-background/50 border border-border text-xs focus:outline-none focus:border-primary text-foreground"
                />

                {/* Time Selector */}
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] uppercase tracking-wider text-muted-foreground font-bold">
                    Scheduled Time
                  </label>
                  <div className="flex gap-1.5 items-center">
                    <input
                      type="text"
                      required
                      placeholder="HH"
                      maxLength={2}
                      value={newHour}
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, "");
                        setNewHour(val);
                      }}
                      className="w-12 px-2 py-1 text-center rounded bg-background/50 border border-border text-foreground focus:outline-none focus:border-primary text-xs font-semibold"
                    />
                    <span className="text-muted-foreground font-bold">:</span>
                    <input
                      type="text"
                      required
                      placeholder="MM"
                      maxLength={2}
                      value={newMinute}
                      onChange={(e) => {
                        const val = e.target.value.replace(/\D/g, "");
                        setNewMinute(val);
                      }}
                      className="w-12 px-2 py-1 text-center rounded bg-background/50 border border-border text-foreground focus:outline-none focus:border-primary text-xs font-semibold"
                    />
                    <select
                      value={newAmpm}
                      onChange={(e) => setNewAmpm(e.target.value)}
                      className="px-1.5 py-1 rounded bg-background/50 border border-border text-foreground focus:outline-none text-xs cursor-pointer"
                    >
                      <option value="AM">AM</option>
                      <option value="PM">PM</option>
                    </select>
                  </div>
                </div>

                {/* Frequency Selector */}
                <div className="flex flex-col gap-1">
                  <label className="text-[9px] uppercase tracking-wider text-muted-foreground font-bold">
                    Schedule Pattern
                  </label>
                  <select
                    value={newFreq}
                    onChange={(e) => setNewFreq(e.target.value)}
                    className="w-full px-2.5 py-1 rounded bg-background/50 border border-border text-foreground focus:outline-none text-xs cursor-pointer"
                  >
                    <option value="once">⏰ Once</option>
                    <option value="daily">🔄 Daily</option>
                    <option value="weekly">📅 Weekly</option>
                    <option value="every_8_hours">🕒 Every 8 Hours</option>
                  </select>
                </div>

                {/* Multi-select Notification Checkboxes */}
                <div className="flex flex-col gap-1.5 border-t border-border/40 pt-2">
                  <label className="text-[9px] uppercase tracking-wider text-muted-foreground font-bold">
                    Notification Channels
                  </label>
                  <div className="flex flex-col gap-1 px-1">
                    <label className="flex items-center gap-2 cursor-pointer select-none text-foreground hover:text-primary transition-colors">
                      <input
                        type="checkbox"
                        checked={prefInApp}
                        onChange={(e) => setPrefInApp(e.target.checked)}
                        className="rounded border-border text-primary focus:ring-primary h-3 w-3 cursor-pointer"
                      />
                      <span>💻 In-App Alert</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer select-none text-foreground hover:text-primary transition-colors">
                      <input
                        type="checkbox"
                        checked={prefBrowser}
                        onChange={(e) => setPrefBrowser(e.target.checked)}
                        className="rounded border-border text-primary focus:ring-primary h-3 w-3 cursor-pointer"
                      />
                      <span>🔔 Browser Push</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer select-none text-foreground hover:text-primary transition-colors">
                      <input
                        type="checkbox"
                        checked={prefEmail}
                        onChange={(e) => setPrefEmail(e.target.checked)}
                        className="rounded border-border text-primary focus:ring-primary h-3 w-3 cursor-pointer"
                      />
                      <span>📧 Email Alert</span>
                    </label>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-1.5 mt-1 bg-primary text-primary-foreground hover:bg-primary/95 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1 shadow-md shadow-primary/10"
                >
                  {editingId ? "💾 Save Changes" : "Set Reminder"}
                </button>
                {editingId && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(null);
                      setNewMed("");
                      setNewHour("08");
                      setNewMinute("00");
                      setNewAmpm("AM");
                      setNewFreq("once");
                      setReminderTimezone(browserTimezone());
                      setPrefInApp(true);
                      setPrefBrowser(false);
                      setPrefEmail(false);
                      setShowAddForm(false);
                    }}
                    className="w-full py-1.5 border border-border/80 text-foreground hover:bg-muted text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1"
                  >
                    Cancel Edit
                  </button>
                )}
              </motion.form>
            )}
          </AnimatePresence>

          {/* Reminders List */}
          <div className="space-y-1.5 pr-1">
            {reminders.length === 0 ? (
              <p className="text-[11px] text-muted-foreground italic text-center py-2">
                No active reminders set.
              </p>
            ) : (
              reminders.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-muted/20 border border-border/50 hover:border-primary/20 transition-all text-xs group"
                >
                  <div className="flex flex-col min-w-0">
                    <span className="font-semibold text-foreground truncate">
                      {r.medicine}
                    </span>
                    <span className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5 flex-wrap">
                      <Clock size={10} className="text-primary/70" />
                      {r.reminder_time}
                      {formatNextOccurrence(r) && (
                        <span className="w-full text-[9px] text-muted-foreground/90">
                          Next: {formatNextOccurrence(r)} ({r.timezone})
                        </span>
                      )}
                      {(r.notification_pref || "in_app")
                        .split(",")
                        .map((pref) => (
                          <span
                            key={pref}
                            className={`opacity-80 px-1 py-0.25 rounded text-[8px] ${
                              pref === "in_app"
                                ? "bg-primary/10 text-primary"
                                : pref === "browser"
                                  ? "bg-secondary/10 text-secondary"
                                  : "bg-emerald-400/10 text-emerald-400"
                            }`}
                          >
                            {pref === "in_app"
                              ? "In-App"
                              : pref === "browser"
                                ? "Push"
                                : "Email"}
                          </span>
                        ))}
                      <span className="opacity-80 px-1 py-0.25 rounded bg-secondary/10 text-secondary text-[8px]">
                        {r.frequency === "once"
                          ? "Once"
                          : r.frequency === "daily"
                            ? "Daily"
                            : r.frequency === "weekly"
                              ? "Weekly"
                              : "Every 8h"}
                      </span>
                    </span>
                  </div>
                  <div className="flex gap-1.5 flex-shrink-0">
                    <button
                      onClick={() => handleStartEdit(r)}
                      className="p-1 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                      title="Edit Alarm"
                    >
                      <Edit2 size={12} />
                    </button>
                    <button
                      onClick={() => onDeleteReminder(r.id)}
                      className="p-1 text-muted-foreground hover:text-danger hover:bg-danger/10 rounded transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                      title="Delete Reminder"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Browser notification helper */}
          {browserPermission !== "granted" && (
            <button
              onClick={onRequestBrowserPermission}
              className="w-full text-left flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-warning/20 bg-warning/5 hover:bg-warning/10 text-[10px] text-amber-500 font-semibold transition-all"
            >
              <Bell size={11} className="flex-shrink-0 animate-bounce" />
              Enable Browser Push Notifications
            </button>
          )}
        </div>

        {/* Quick queries */}
        <div className="p-3">
          <h3 className="text-[10px] font-bold uppercase tracking-[2px] text-muted-foreground mb-3 px-1">
            Quick Queries
          </h3>
          <div className="flex flex-col gap-1">
            {PRESETS.map((p, i) => (
              <motion.button
                key={i}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onPresetClick(p.text)}
                className="flex items-center gap-2.5 w-full text-left px-3 py-2.5 rounded-xl text-xs text-muted-foreground hover:text-foreground hover:bg-primary/10 hover:border-primary/20 border border-transparent transition-all duration-200"
              >
                <p.icon size={14} className={`${p.color} flex-shrink-0`} />
                <span className="line-clamp-1">{p.text}</span>
              </motion.button>
            ))}
          </div>
        </div>
      </div>{" "}
      {/* End Unified Scroll Wrapper */}
      {/* Clear */}
      <div className="p-3 border-t border-border bg-card/20">
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          onClick={onClear}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-danger/10 border border-danger/20 text-danger text-xs font-medium hover:bg-danger/15 transition-all"
        >
          <Trash2 size={14} />
          Clear Conversation
        </motion.button>
      </div>
      {/* Resizable Sidebar Drag Handle */}
      <div
        onMouseDown={(e) => {
          e.preventDefault();
          const startX = e.clientX;
          const startWidth = width;

          const handleMouseMove = (moveEvent: MouseEvent) => {
            const newWidth = Math.min(
              Math.max(startWidth + (moveEvent.clientX - startX), 240),
              450,
            );
            onWidthChange(newWidth);
          };

          const handleMouseUp = () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
          };

          document.addEventListener("mousemove", handleMouseMove);
          document.addEventListener("mouseup", handleMouseUp);
        }}
        className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-primary/50 hover:w-2 active:bg-primary/70 transition-all z-50 flex items-center justify-center group"
      >
        <div className="w-0.5 h-12 bg-border/80 group-hover:bg-primary rounded-full transition-colors" />
      </div>
    </motion.aside>
  );
}
