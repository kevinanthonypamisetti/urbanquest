import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, Mail, Phone, ShieldCheck } from 'lucide-react'
import './auth.css'

const API_URL = import.meta.env.VITE_AUTH_API_URL || (import.meta.env.VITE_AI_API_URL
  ? import.meta.env.VITE_AI_API_URL.replace(/\/chat\/?$/, '/auth')
  : 'http://localhost:8000/auth')

export function AuthPage({ mode = 'login' }) {
  const [step, setStep] = useState('start')
  const [method, setMethod] = useState('email')
  const [destination, setDestination] = useState('')
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const isSignup = mode === 'signup'

  useEffect(() => {
    if (!seconds) return undefined
    const timer = window.setInterval(() => setSeconds((value) => value - 1), 1000)
    return () => window.clearInterval(timer)
  }, [seconds])

  async function requestCode(event) {
    event.preventDefault()
    setError('')
    if (isSignup && !consent) {
      setError('Please agree to the terms and privacy policy to continue.')
      return
    }
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/request-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, destination, name: name || null, consent: isSignup ? consent : true }),
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.detail || 'We could not send your code.')
      setStep('verify')
      setSeconds(60)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  async function verifyCode(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, destination, name: name || null, code }),
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(result.detail || 'That code is not valid.')
      window.location.assign('/')
    } catch (verifyError) {
      setError(verifyError.message)
    } finally {
      setLoading(false)
    }
  }

  return <main className="auth-shell">
    <a className="auth-wordmark" href="/">urban<span>quest</span></a>
    <section className="auth-card">
      <div className="auth-card-top"><span className="auth-kicker"><ShieldCheck size={15} /> Secure access</span><span className="auth-step">{step === 'verify' ? '02' : '01'} / 02</span></div>
      {step === 'start' ? <form onSubmit={requestCode}>
        <h1>{isSignup ? 'Make room for more.' : 'Welcome back.'}</h1>
        <p className="auth-intro">{isSignup ? 'Create your UrbanQuest account and keep every field note in one place.' : 'Sign in to pick up where your next adventure left off.'}</p>
        <a className="google-button" href={`${API_URL}/google`}>Continue with Google <ArrowRight size={17} /></a>
        <div className="auth-divider"><span>or use a code</span></div>
        {isSignup && <label className="auth-field">Your name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Alex Morgan" required /></label>}
        <div className="auth-methods"><button type="button" className={method === 'email' ? 'selected' : ''} onClick={() => setMethod('email')}><Mail size={17} /> Email</button><button type="button" className={method === 'mobile' ? 'selected' : ''} onClick={() => setMethod('mobile')}><Phone size={17} /> Mobile</button></div>
        <label className="auth-field">{method === 'email' ? 'Email address' : 'Mobile number'}<input type={method === 'email' ? 'email' : 'tel'} value={destination} onChange={(event) => setDestination(event.target.value)} placeholder={method === 'email' ? 'you@example.com' : '+1 555 123 4567'} required /></label>
        {isSignup && <label className="auth-consent"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span>I agree to the <a href="/terms">terms</a> and <a href="/privacy">privacy policy</a>.</span></label>}
        <button className="auth-submit" disabled={loading}>{loading ? 'Sending code…' : 'Continue'} <ArrowRight size={17} /></button>
        <p className="auth-switch">{isSignup ? 'Already have an account?' : 'New to UrbanQuest?'} <a href={isSignup ? '/login' : '/signup'}>{isSignup ? 'Sign in' : 'Create one'}</a></p>
      </form> : <form onSubmit={verifyCode}>
        <button className="auth-back" type="button" onClick={() => { setStep('start'); setCode(''); setError('') }}><ArrowLeft size={15} /> Change {method === 'email' ? 'email' : 'number'}</button>
        <h1>Verify your account</h1><p className="auth-intro">We’ve sent a 6-digit code to<br /><strong>{destination}</strong></p>
        <label className="auth-field">Verification code<input className="otp-input" inputMode="numeric" maxLength="6" value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))} placeholder="______" autoFocus required /></label>
        <p className="auth-resend">Didn't receive it? {seconds ? <span>Resend in 00:{String(seconds).padStart(2, '0')}</span> : <button type="button" onClick={requestCode}>Resend code</button>}</p>
        <button className="auth-submit" disabled={loading || code.length !== 6}>{loading ? 'Verifying…' : 'Verify'} <Check size={17} /></button>
      </form>}
      {error && <p className="auth-error" role="alert">{error}</p>}
    </section>
    <p className="auth-footnote">Your session is protected with a secure, HttpOnly cookie.</p>
  </main>
}
