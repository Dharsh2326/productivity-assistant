import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import ProductivityApp from './ProductivityApp.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ProductivityApp />
  </StrictMode>
)