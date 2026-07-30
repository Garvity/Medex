type ChatSessionNames = Record<string, string>;

function sessionIdKey(uid: string): string {
  return `medassist:chat_session_id:${uid}`;
}

function sessionNamesKey(uid: string): string {
  return `medassist:chat_session_names:${uid}`;
}

export function getStoredSessionId(uid: string): string | null {
  return localStorage.getItem(sessionIdKey(uid));
}

export function setStoredSessionId(uid: string, sessionId: string): void {
  localStorage.setItem(sessionIdKey(uid), sessionId);
}

export function getStoredSessionNames(uid: string): ChatSessionNames {
  try {
    const stored = localStorage.getItem(sessionNamesKey(uid));
    if (!stored) return {};

    const parsed: unknown = JSON.parse(stored);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};

    return Object.fromEntries(
      Object.entries(parsed).filter(
        ([key, value]) => typeof key === 'string' && typeof value === 'string',
      ),
    );
  } catch {
    return {};
  }
}

export function setStoredSessionNames(uid: string, names: ChatSessionNames): void {
  localStorage.setItem(sessionNamesKey(uid), JSON.stringify(names));
}
