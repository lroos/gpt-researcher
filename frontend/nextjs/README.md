# AI Research Assistant UI

A React component library for building AI-powered research applications. This is a hackathon-focused demo interface for exploring AI research capabilities.

## About

This is the frontend interface for the AI Research Assistant, built with Next.js and React. It provides a modern, intuitive interface for conducting AI-powered research and generating comprehensive reports.

## Installation

```bash
npm install ai-research-assistant-ui
```

## Usage

```javascript
import React from 'react';
import { AIResearchAssistant } from 'ai-research-assistant-ui';

function App() {
  return (
    <div className="App">
      <AIResearchAssistant 
        apiUrl="http://localhost:8000"
        defaultPrompt="What is quantum computing?"
        onResultsChange={(results) => console.log('Research results:', results)}
      />
    </div>
  );
}

export default App;
```

## Advanced Usage

```javascript
import React, { useState } from 'react';
import { AIResearchAssistant } from 'ai-research-assistant-ui';

function App() {
  const [results, setResults] = useState([]);

  const handleResultsChange = (newResults) => {
    setResults(newResults);
    console.log('Research progress:', newResults);
  };

  return (
    <div className="App">
      <h1>My Research Application</h1>
      
      <AIResearchAssistant 
        apiUrl="http://localhost:8000"
        apiKey="your-api-key-if-needed"
        defaultPrompt="Explain the impact of quantum computing on cryptography"
        onResultsChange={handleResultsChange}
      />
      
      {/* You can use the results state elsewhere in your app */}
      <div className="results-summary">
        {results.length > 0 && (
          <p>Research in progress: {results.length} items processed</p>
        )}
      </div>
    </div>
  );
}

export default App;
```

## Features

- Modern, responsive interface
- Real-time research streaming
- Multiple report types (summary, detailed, multi-agent)
- Chat interface for follow-up questions
- Customizable settings (tone, source, layout)
- Mobile-optimized views

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## License

MIT