/**
 * In-memory TTL cache for API responses.
 * Falls back to sessionStorage for cross-reload persistence.
 */

const memCache = new Map()

const SESSION_PREFIX = 'py_cache_'

export function getCached(key) {
  const mem = memCache.get(key)
  if (mem && Date.now() < mem.expires) return mem.data

  try {
    const raw = sessionStorage.getItem(SESSION_PREFIX + key)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Date.now() < parsed.expires) {
        memCache.set(key, parsed)
        return parsed.data
      }
      sessionStorage.removeItem(SESSION_PREFIX + key)
    }
  } catch {}

  return null
}

export function setCached(key, data, ttlMs = 60_000) {
  const entry = { data, expires: Date.now() + ttlMs }
  memCache.set(key, entry)
  try {
    sessionStorage.setItem(SESSION_PREFIX + key, JSON.stringify(entry))
  } catch {}
}

export function invalidateCache(pattern) {
  for (const key of memCache.keys()) {
    if (key.startsWith(pattern)) memCache.delete(key)
  }
  try {
    for (const key of Object.keys(sessionStorage)) {
      if (key.startsWith(SESSION_PREFIX + pattern)) sessionStorage.removeItem(key)
    }
  } catch {}
}

export function clearAllCache() {
  memCache.clear()
  try {
    for (const key of Object.keys(sessionStorage)) {
      if (key.startsWith(SESSION_PREFIX)) sessionStorage.removeItem(key)
    }
  } catch {}
}
