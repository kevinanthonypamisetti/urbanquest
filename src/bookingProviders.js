const providers = {
  flights: [
    { provider: 'Google Flights', baseUrl: 'https://www.google.com/travel/flights' },
    { provider: 'Skyscanner', baseUrl: 'https://www.skyscanner.com/transport/flights' },
  ],
  hotels: [
    { provider: 'Google Hotels', baseUrl: 'https://www.google.com/travel/search' },
    { provider: 'Booking.com', baseUrl: 'https://www.booking.com/searchresults.html' },
  ],
  trains: [
    { provider: 'Google Travel', baseUrl: 'https://www.google.com/travel/search' },
    { provider: '12Go', baseUrl: 'https://12go.asia/en' },
  ],
  activities: [
    { provider: 'GetYourGuide', baseUrl: 'https://www.getyourguide.com/s/' },
    { provider: 'Tripadvisor', baseUrl: 'https://www.tripadvisor.com/Search' },
  ],
}

function queryUrl(baseUrl, params) {
  return `${baseUrl}?${new URLSearchParams(params).toString()}`
}

export function getBookingOptions({ origin, destination, departure, returnDate, travelers }) {
  const dates = { departure, returnDate, travelers: String(travelers) }
  return {
    flights: providers.flights.map(({ provider, baseUrl }) => ({
      provider,
      label: `Search ${provider}`,
      url: queryUrl(baseUrl, { ...dates, from: origin, to: destination }),
    })),
    hotels: providers.hotels.map(({ provider, baseUrl }) => ({
      provider,
      label: `Search ${provider}`,
      url: queryUrl(baseUrl, { ...dates, q: destination }),
    })),
    trains: providers.trains.map(({ provider, baseUrl }) => ({
      provider,
      label: `Search ${provider}`,
      url: queryUrl(baseUrl, { ...dates, from: origin, to: destination }),
    })),
    activities: providers.activities.map(({ provider, baseUrl }) => ({
      provider,
      label: `Explore ${provider}`,
      url: queryUrl(baseUrl, { ...dates, q: `${destination} activities` }),
    })),
  }
}
