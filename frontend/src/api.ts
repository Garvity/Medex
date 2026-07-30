import { firebaseAuth } from './firebase';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value: unknown): value is string {
  return typeof value === 'string' && UUID_PATTERN.test(value);
}

export class ApiRequestError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((issue) => {
        if (!issue || typeof issue !== 'object') return null;
        const typedIssue = issue as { loc?: unknown[]; msg?: string };
        const field = Array.isArray(typedIssue.loc) ? typedIssue.loc.filter((part) => part !== 'body').join('.') : '';
        return typedIssue.msg ? `${field ? `${field}: ` : ''}${typedIssue.msg}` : null;
      })
      .filter((message): message is string => Boolean(message));
    if (messages.length) return messages.join('; ');
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const user = firebaseAuth.currentUser;
  if (!user) throw new Error('You must be signed in.');
  const token = await user.getIdToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiRequestError(response.status, formatApiError(body.detail, `Request failed (${response.status}).`));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export interface ApiSession { id: string; name: string; created_at: string; updated_at: string; }
export interface ApiMessage { id: string; session_id: string; query: string; response: string; role: string; sources: object[]; created_at: string; }
export interface ApiReminder {
  id: string; medicine: string; reminder_time: string; frequency: string; notification_pref: string;
  timezone: string; status: string; last_triggered_at?: string | null; next_occurrence_at?: string | null;
}
export type ReminderCreatePayload = Pick<ApiReminder, 'medicine' | 'reminder_time' | 'timezone' | 'frequency' | 'notification_pref'>;
export type ReminderUpdatePayload = ReminderCreatePayload & Pick<ApiReminder, 'status'>;

export const api = {
  getProfile: () => request<{ id: string; name: string | null; phone: string | null; timezone: string }>('/profile'),
  updateProfile: (payload: { name?: string; phone?: string; timezone?: string }) => request<{ id: string; name: string | null; phone: string | null; timezone: string }>('/profile', { method: 'PUT', body: JSON.stringify(payload) }),
  ask: (payload: { query: string; role: string; session_id?: string; history?: { user: string; assistant: string }[] }) => {
    const normalizedPayload = {
      ...payload,
      session_id: isUuid(payload.session_id) ? payload.session_id : undefined,
      history: payload.history?.slice(-12).map((turn) => ({
        user: String(turn.user || ''),
        assistant: String(turn.assistant || ''),
      })),
    };
    return request<{ response: string; session_id: string; sources: object[]; guardrail_action: string }>('/ask', { method: 'POST', body: JSON.stringify(normalizedPayload) });
  },
  listSessions: () => request<ApiSession[]>('/sessions'),
  listMessages: (sessionId: string) => request<ApiMessage[]>(`/sessions/${sessionId}/messages`),
  renameSession: (sessionId: string, name: string) => request<ApiSession>(`/sessions/${sessionId}`, { method: 'PUT', body: JSON.stringify({ name }) }),
  deleteSession: (sessionId: string) => request<void>(`/sessions/${sessionId}`, { method: 'DELETE' }),
  listReminders: () => request<ApiReminder[]>('/reminders'),
  createReminder: (payload: ReminderCreatePayload) => request<ApiReminder>('/reminders', { method: 'POST', body: JSON.stringify(payload) }),
  updateReminder: (id: string, payload: ReminderUpdatePayload) => request<ApiReminder>(`/reminders/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteReminder: (id: string) => request<void>(`/reminders/${id}`, { method: 'DELETE' }),
  markReminderTriggered: (id: string) => request<ApiReminder>(`/reminders/${id}/trigger`, { method: 'POST' }),
};
