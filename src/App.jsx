import { useMemo, useState } from 'react'
import { ArrowDown, ArrowRight, BusFront, ChevronDown, CircleHelp, Compass, CreditCard, LocateFixed, Map, Plane, Search, TrainFront, WalletCards } from 'lucide-react'
import { getBookingOptions } from './bookingProviders'
import './App.css'

const places = {
  USA: { name: 'United States', flag: '🇺🇸', currency: 'USD', symbol: '$', rate: 1, regions: { California: ['San Francisco', 'Los Angeles'], NewYork: ['New York City', 'Buffalo'], Texas: ['Austin', 'Houston'] } },
  India: { name: 'India', flag: '🇮🇳', currency: 'INR', symbol: '₹', rate: 87, regions: { Telangana: ['Hyderabad', 'Warangal'], Maharashtra: ['Mumbai', 'Pune'], Karnataka: ['Bengaluru', 'Mysuru'] } },
  Japan: { name: 'Japan', flag: '🇯🇵', currency: 'JPY', symbol: '¥', rate: 158, regions: { Tokyo: ['Tokyo', 'Hachioji'], Kyoto: ['Kyoto', 'Uji'], Osaka: ['Osaka', 'Sakai'] } },
  UK: { name: 'United Kingdom', flag: '🇬🇧', currency: 'GBP', symbol: '£', rate: 0.79, regions: { England: ['London', 'Manchester'], Scotland: ['Edinburgh', 'Glasgow'], Wales: ['Cardiff', 'Swansea'] } },
}
const transport = [
  { icon: Plane, label: 'Flights', detail: 'Compare routes and fares', meta: 'SFO → HYD' },
  { icon: TrainFront, label: 'Trains', detail: 'Plan the next city', meta: 'Rail connections' },
  { icon: BusFront, label: 'Local transit', detail: 'Metro · bus · cab · auto', meta: 'Save on arrival' },
]

function LocationPicker({ label, value, onChange }) {
  const place = places[value.country]
  const region = Object.keys(place.regions).find((key) => place.regions[key].includes(value.city)) || Object.keys(place.regions)[0]
  const cities = place.regions[region]
  function setCountry(country) {
    const nextPlace = places[country]
    const nextRegion = Object.keys(nextPlace.regions)[0]
    onChange({ country, city: nextPlace.regions[nextRegion][0] })
  }
  return <section className="location-panel">
    <div className="eyebrow">{label}</div>
    <div className="location-main"><span className="flag" aria-hidden="true">{place.flag}</span><select value={value.country} onChange={(event) => setCountry(event.target.value)} aria-label={`${label} country`}>{Object.entries(places).map(([code, option]) => <option key={code} value={code}>{option.name}</option>)}</select><ChevronDown size={16} strokeWidth={1.5} aria-hidden="true" /></div>
    <div className="location-subfields"><label><span>State / region</span><select value={region} onChange={(event) => onChange({ country: value.country, city: place.regions[event.target.value][0] })}>{Object.keys(place.regions).map((option) => <option key={option} value={option}>{option}</option>)}</select></label><label><span>City</span><select value={value.city} onChange={(event) => onChange({ ...value, city: event.target.value })}>{cities.map((option) => <option key={option} value={option}>{option}</option>)}</select></label></div>
  </section>
}

function BookingGroup({ title, icon, options }) {
  return <section className="booking-group"><h4>{icon} {title}</h4>{options.map((option) => <a href={option.url} target="_blank" rel="noreferrer" key={option.provider}><span>{option.provider}</span><strong>{option.label} <ArrowRight size={14} /></strong></a>)}</section>
}

function TripDNA({ dna }) {
  const scores = [['Adventure', dna.adventure], ['Food', dna.food], ['Nightlife', dna.nightlife], ['Culture', dna.culture], ['Relaxation', dna.relaxation]]
  return <section className="dna-card"><div className="dna-heading"><span className="eyebrow">Trip DNA</span><small>{dna.walking} walking · {dna.crowds} crowds</small></div>{scores.map(([label, score]) => <div className="dna-row" key={label}><span>{label}</span><div><i style={{ width: `${score}%` }} /></div><strong>{score}%</strong></div>)}</section>
}

function App() {
  const [origin, setOrigin] = useState({ country: 'USA', city: 'San Francisco' })
  const [destination, setDestination] = useState({ country: 'India', city: 'Hyderabad' })
  const [amount, setAmount] = useState('100')
  const [activeTransport, setActiveTransport] = useState(null)
  const [tripOptions, setTripOptions] = useState({ duration: '3 hours', style: 'Historic & local', flight: 'Best value', stay: 'Boutique hotel', food: 'Local favourites', transport: 'Walking + transit', departure: '2026-10-20', returnDate: '2026-10-23', travelers: '2' })
  const [conciergeResponse, setConciergeResponse] = useState(null)
  const [conciergeError, setConciergeError] = useState('')
  const [isPlanning, setIsPlanning] = useState(false)
  const originPlace = places[origin.country]
  const destinationPlace = places[destination.country]
  const converted = useMemo(() => Math.round(Number(amount || 0) * destinationPlace.rate / originPlace.rate), [amount, destinationPlace.rate, originPlace.rate])
  const spend = [['Local transport', Math.round(converted * 0.09)], ['Food & cafés', Math.round(converted * 0.17)], ['Heritage experiences', Math.round(converted * 0.12)], ['Micro-adventures', Math.round(converted * 0.23)]]
  const spent = spend.reduce((sum, [, item]) => sum + item, 0)
  const remaining = Math.max(converted - spent, 0)
  const bookingOptions = getBookingOptions({ origin: origin.city, destination: destination.city, ...tripOptions })

  async function askConcierge(event) {
    event.preventDefault()
    setIsPlanning(true)
    setConciergeError('')
    try {
      const response = await fetch(import.meta.env.VITE_AI_API_URL || 'http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Plan a ${tripOptions.duration} ${tripOptions.style.toLowerCase()} trip. Flights: ${tripOptions.flight}. Stay: ${tripOptions.stay}. Food: ${tripOptions.food}. Transport: ${tripOptions.transport}.`,
          context: {
            home: { country: originPlace.name, city: origin.city },
            destination: { country: destinationPlace.name, city: destination.city },
            home_currency: originPlace.currency,
            destination_currency: destinationPlace.currency,
            budget_home: Number(amount || 0),
            budget_destination: converted,
            available_minutes: Number(tripOptions.duration.split(' ')[0]) * (tripOptions.duration.includes('day') ? 1440 : 60),
            interests: [tripOptions.style],
            transport_mode: tripOptions.transport.toLowerCase().includes('walking') ? 'walking' : 'transit',
          },
        }),
      })
      if (!response.ok) throw new Error('The concierge could not build a plan right now.')
      setConciergeResponse(await response.json())
    } catch (error) {
      setConciergeResponse(null)
      setConciergeError(error.message)
    } finally {
      setIsPlanning(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar"><a className="wordmark" href="/">urban<span>quest</span></a><nav><a href="#planner">Trip planner</a><a href="#getting-there">Getting there</a><button className="icon-button" title="Help"><CircleHelp size={18} /></button></nav></header>
      <section className="hero-section"><div className="hero-copy"><p className="kicker"><Compass size={15} /> A more considered way to travel</p><h1>Go somewhere.<br /><em>Do something.</em></h1><p className="intro">A city guide shaped around where you begin, what you carry, and the places worth taking the long way to.</p></div><div className="hero-image" role="img" aria-label="A quiet view of Hyderabad's Charminar at dusk" /></section>
      <section className="planner" id="planner"><div className="section-heading"><div><span className="section-number">01</span><h2>Set your bearings</h2></div><p>Tell us where you are, then we will make the distance useful.</p></div><div className="location-grid"><LocationPicker label="I'm from" value={origin} onChange={setOrigin} /><div className="route-mark"><ArrowDown size={18} /></div><LocationPicker label="I'm traveling to" value={destination} onChange={setDestination} /></div></section>
      <section className="money-section"><div className="money-intro"><span className="section-number">02</span><h2>What are you taking with you?</h2><p>See the buying power of your everyday budget in {destination.city}.</p></div><div className="money-grid"><div className="amount-panel"><label htmlFor="amount">I have</label><div className="amount-input"><span>{originPlace.symbol}</span><input id="amount" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value.replace(/[^0-9.]/g, ''))} /><span className="currency-code">{originPlace.currency}</span></div><div className="exchange-line"><ArrowRight size={14} /> 1 {originPlace.currency} ≈ {(destinationPlace.rate / originPlace.rate).toFixed(destinationPlace.rate < 2 ? 2 : 0)} {destinationPlace.currency}</div><div className="destination-total"><span>In {destination.city}</span><strong>{destinationPlace.symbol}{converted.toLocaleString()}</strong><small>{destinationPlace.currency} destination equivalent</small></div></div><div className="spend-panel"><div className="panel-title"><span>Here’s what that can mean</span><WalletCards size={17} /></div>{spend.map(([label, value]) => <div className="spend-row" key={label}><span>{label}</span><strong>{destinationPlace.symbol}{value.toLocaleString()}</strong></div>)}<div className="spend-row remaining"><span>Remaining</span><strong>{destinationPlace.symbol}{remaining.toLocaleString()}</strong></div><p className="budget-note">That is enough room for <b>3–5 micro-adventures</b> at an unhurried pace.</p></div></div><button className="primary-button" type="button" onClick={() => document.getElementById('getting-there').scrollIntoView({ behavior: 'smooth' })}>Explore {destination.city} <ArrowRight size={17} /></button></section>
      <section className="getting-there" id="getting-there"><div className="section-heading"><div><span className="section-number">03</span><h2>Getting there</h2></div><p>Plan the whole journey, from your first departure to your first good meal.</p></div><div className="journey-line"><div className="journey-stop"><LocateFixed size={16} /><span>{origin.city}</span></div><div className="journey-connector" /><div className="journey-stop"><Map size={16} /><span>{destination.city}</span></div></div><div className="transport-grid">{transport.map(({ icon: Icon, label, detail, meta }) => <button className={`transport-card ${activeTransport === label ? 'active' : ''}`} key={label} type="button" onClick={() => setActiveTransport(label)}><span className="transport-icon"><Icon size={20} /></span><span className="transport-copy"><b>{label}</b><small>{detail}</small></span><span className="transport-meta">{activeTransport === label ? 'Selected' : meta}<ArrowRight size={16} /></span></button>)}</div></section>
      <section className="concierge-section" id="concierge"><div className="section-heading"><div><span className="section-number">04</span><h2>Build your trip</h2></div><p>Choose your preferences. We will handle the route, stay, food, activities, and transport.</p></div><form className="concierge-form" onSubmit={askConcierge}><div className="trip-options">{[['duration', 'How long?', ['3 hours', '6 hours', '1 day', '2 days', '3 days', '5 days', '7 days'] ], ['departure', 'Departure', ['2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23']], ['returnDate', 'Return', ['2026-10-23', '2026-10-24', '2026-10-25', '2026-10-26']], ['travelers', 'Travelers', ['1', '2', '3', '4', '5']], ['style', 'Trip mood', ['Historic & local', 'Food & cafés', 'Art & hidden gems']], ['flight', 'Flights', ['Best value', 'Fastest route', 'Most comfortable']], ['stay', 'Where to stay', ['Boutique hotel', 'Central hotel', 'Best value stay']], ['food', 'What to eat', ['Local favourites', 'Street food', 'Vegetarian spots']], ['transport', 'Getting around', ['Walking + transit', 'Taxi + walking', 'Public transit']]].map(([key, label, options]) => <label className="trip-option" key={key}>{label}<select value={tripOptions[key]} onChange={(event) => setTripOptions({ ...tripOptions, [key]: event.target.value })}>{options.map((option) => <option key={option}>{option}</option>)}</select></label>)}</div><div className="selected-budget"><span>Budget from section 02</span><strong>{originPlace.symbol}{Number(amount || 0).toLocaleString()} {originPlace.currency}</strong></div><button className="primary-button" type="submit" disabled={isPlanning}>{isPlanning ? 'Building your adventure…' : 'Build my adventure'} <ArrowRight size={17} /></button></form>{conciergeError && <p className="concierge-error" role="alert">{conciergeError}</p>}{conciergeResponse && <article className="concierge-result"><div className="concierge-result-heading"><div><span className="eyebrow">Your field notes</span><h3>{conciergeResponse.plan.title}</h3></div><span className="concierge-cost">{destinationPlace.symbol}{conciergeResponse.plan.estimated_cost.toLocaleString()} · {Math.ceil(conciergeResponse.plan.duration_minutes / 60)} hours</span></div><p>{conciergeResponse.message}</p><div className="trip-summary"><span>✈ {tripOptions.flight}</span><span>⌂ {tripOptions.stay}</span><span>🍽 {tripOptions.food}</span><span>↗ {tripOptions.transport}</span></div><TripDNA dna={conciergeResponse.plan.trip_dna} /><section className="bundle-card"><span className="eyebrow">Experience system</span><h4>{conciergeResponse.plan.experience_bundle.title}</h4><p>{conciergeResponse.plan.experience_bundle.description}</p><div>{conciergeResponse.plan.experience_bundle.experiences.map((experience) => <span key={experience.name}>{experience.name}</span>)}</div></section><div className="day-list">{conciergeResponse.plan.days.map((day) => <section className="day-card" key={day.day}><div className="day-heading"><span>DAY {day.day}</span><strong>{day.title}</strong></div>{day.activities.length ? day.activities.map((stop) => <div className="concierge-stop" key={stop.name}><strong>{stop.name}</strong><span>{stop.duration_minutes} min · {destinationPlace.symbol}{stop.estimated_cost.toLocaleString()}</span><small>{stop.description}</small></div>) : <p className="day-placeholder">Hotel check-in, {tripOptions.food.toLowerCase()}, and time to explore at your own pace.</p>}</section>)}</div><div className="booking-grid"><BookingGroup title="Flights" icon="✈" options={bookingOptions.flights} /><BookingGroup title="Hotels" icon="⌂" options={bookingOptions.hotels} /><BookingGroup title="Trains" icon="↔" options={bookingOptions.trains} /><BookingGroup title="Activities" icon="✦" options={bookingOptions.activities} /></div></article>}</section>
      <footer><span>urbanquest / field notes for the curious</span><span><CreditCard size={15} /> Rates are indicative · cards welcome worldwide</span><Search size={17} /></footer>
    </main>
  )
}

export default App
