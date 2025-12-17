import { useState } from 'react'
import './App.css'
import LinkPaste from './LinkPaste'
import { AuroraBackground } from '@/components/ui/aurora-background'

function App() {
  return (
    <AuroraBackground>
      <div className="App relative z-10">
        <LinkPaste /> 
      </div>
    </AuroraBackground>
  )
}

export default App
