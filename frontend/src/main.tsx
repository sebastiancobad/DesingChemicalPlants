import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Force full page reload on HMR to clear stale module cache
if (import.meta.hot) {
  import.meta.hot.on('vite:beforeFullReload', () => {
    window.location.reload()
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

console.log('[ChemScale] App loaded at', new Date().toISOString())
