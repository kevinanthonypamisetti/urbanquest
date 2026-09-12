const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey)

async function supabaseFetch(path, options = {}) {
  if (!supabaseConfigured) throw new Error('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.')
  const { accessToken, headers, ...requestOptions } = options
  const response = await fetch(`${supabaseUrl}${path}`, {
    ...requestOptions,
    headers: {
      apikey: supabaseAnonKey,
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
  })
  const result = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(result.msg || result.error_description || result.message || 'Supabase request failed.')
  return result
}

export function getStoredSession() {
  try {
    return JSON.parse(localStorage.getItem('urbanquest-supabase-session') || 'null')
  } catch {
    return null
  }
}

export function clearStoredSession() {
  localStorage.removeItem('urbanquest-supabase-session')
}

export async function signIn(email, password) {
  const session = await supabaseFetch('/auth/v1/token?grant_type=password', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  localStorage.setItem('urbanquest-supabase-session', JSON.stringify(session))
  return session
}

export async function signUp({ name, email, password }) {
  const result = await supabaseFetch('/auth/v1/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password, data: { name } }),
  })
  if (result.access_token) localStorage.setItem('urbanquest-supabase-session', JSON.stringify(result))
  if (result.access_token && result.user) await saveProfile(result.access_token, result.user.id, name, email)
  return result
}

async function saveProfile(accessToken, userId, name, email) {
  await supabaseFetch('/rest/v1/profiles?on_conflict=id', {
    method: 'POST',
    accessToken,
    headers: { Prefer: 'resolution=merge-duplicates' },
    body: JSON.stringify({ id: userId, name, email }),
  })
}

export async function signOut() {
  const session = getStoredSession()
  if (session?.access_token) await supabaseFetch('/auth/v1/logout', { method: 'POST', accessToken: session.access_token })
  clearStoredSession()
}

export async function saveTrip(title, tripData) {
  const session = getStoredSession()
  if (!session?.access_token || !session.user?.id) throw new Error('Sign in to save this trip.')
  return supabaseFetch('/rest/v1/saved_trips', {
    method: 'POST',
    accessToken: session.access_token,
    headers: { Prefer: 'return=minimal' },
    body: JSON.stringify({ user_id: session.user.id, title, trip_data: tripData }),
  })
}
