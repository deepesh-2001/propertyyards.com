import { Routes, Route } from 'react-router-dom'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
    </Routes>
  )
}

function Home() {
  return (
    <div style={{ fontFamily: 'sans-serif', textAlign: 'center', marginTop: '4rem' }}>
      <h1>PropertyYards</h1>
      <p>Real estate platform — coming soon.</p>
    </div>
  )
}

export default App
