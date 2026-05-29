import { useState, useEffect } from 'react'

function getGreetingKey() {
  const h = new Date().getHours()
  if (h >= 5  && h < 12) return 'greetMorning'
  if (h >= 12 && h < 17) return 'greetAfternoon'
  if (h >= 17 && h < 21) return 'greetEvening'
  return 'greetNight'
}

export function useTimeGreeting() {
  const [key, setKey] = useState(getGreetingKey)

  useEffect(() => {
    const interval = setInterval(() => setKey(getGreetingKey()), 60_000)
    return () => clearInterval(interval)
  }, [])

  return key
}
