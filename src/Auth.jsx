import { useState } from 'react'
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail, UserRound } from 'lucide-react'
import { signIn, signUp, supabaseConfigured } from './supabase'
import './auth.css'

export function AuthPage({ mode = 'login' }) {
  const isSignup = mode === 'signup'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function submit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const result = isSignup ? await signUp({ name, email, password }) : await signIn(email, password)
      if (isSignup && !result.access_token) {
        setSuccess('Check your email to confirm your account, then sign in.')
        return
      }
      window.location.assign('/')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return <main className="auth-shell">
    <a className="auth-wordmark" href="/">urban<span>quest</span></a>
    <section className="auth-card">
      <span className="auth-kicker"><LockKeyhole size={15} /> Your private field notes</span>
      <h1>{isSignup ? 'Start wandering.' : 'Welcome back.'}</h1>
      <p className="auth-intro">{isSignup ? 'Create an account to save trips, preferences, and conversations with your travel agent.' : 'Sign in to return to your saved trips and travel plans.'}</p>
      {!supabaseConfigured && <p className="auth-error">Supabase is not configured. Add the Vercel variables before using authentication.</p>}
      <form onSubmit={submit}>
        {isSignup && <label className="auth-field"><span><UserRound size={14} /> Full name</span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Alex Morgan" required /></label>}
        <label className="auth-field"><span><Mail size={14} /> Email address</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required /></label>
        <label className="auth-field"><span><LockKeyhole size={14} /> Password</span><div className="password-input"><input type={showPassword ? 'text' : 'password'} minLength="8" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" required /><button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
        <button className="auth-submit" disabled={loading || !supabaseConfigured}>{loading ? 'Opening your notebook…' : isSignup ? 'Create account' : 'Sign in'} <ArrowRight size={17} /></button>
      </form>
      {error && <p className="auth-error" role="alert">{error}</p>}
      {success && <p className="auth-success" role="status">{success}</p>}
      <p className="auth-switch">{isSignup ? 'Already have an account?' : 'New to UrbanQuest?'} <a href={isSignup ? '/login' : '/signup'}>{isSignup ? 'Sign in' : 'Create one'}</a></p>
    </section>
    <p className="auth-footnote">Your account and saved trips are secured by Supabase Auth.</p>
  </main>
}
