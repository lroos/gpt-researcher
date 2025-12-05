declare module 'ai-research-assistant-ui' {
  import React from 'react';

  export interface AIResearchAssistantProps {
    apiUrl?: string;
    apiKey?: string;
    defaultPrompt?: string;
    onResultsChange?: (results: any) => void;
    theme?: any;
  }

  export const AIResearchAssistant: React.FC<AIResearchAssistantProps>;
}