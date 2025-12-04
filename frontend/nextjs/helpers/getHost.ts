interface GetHostParams {
  purpose?: string;
}

export const getHost = ({ purpose }: GetHostParams = {}): string => {
  if (typeof window !== 'undefined') {
    let { host } = window.location;
    const apiUrlInLocalStorage = localStorage.getItem("GPTR_API_URL");
    
    const urlParams = new URLSearchParams(window.location.search);
    const apiUrlInUrlParams = urlParams.get("GPTR_API_URL");
    
    if (apiUrlInLocalStorage) {
      return apiUrlInLocalStorage;
    } else if (apiUrlInUrlParams) {
      return apiUrlInUrlParams;
    } else if (process.env.NEXT_PUBLIC_GPTR_API_URL) {
      return process.env.NEXT_PUBLIC_GPTR_API_URL;
    } else if (process.env.REACT_APP_GPTR_API_URL) {
      return process.env.REACT_APP_GPTR_API_URL;
    } else if (purpose === 'langgraph-gui') {
      return host.includes('localhost') ? 'http%3A%2F%2F127.0.0.1%3A8123' : `https://${host}`;
    } else {
      if (host.includes('localhost')) {
        return 'http://localhost:8000';
      }
      
      // Handle GitHub Codespaces port forwarding
      if (host.includes('github.dev')) {
        // If we are on port 3000, try to guess port 8000
        if (host.includes('-3000')) {
          return `https://${host.replace('-3000', '-8000')}`;
        }
      }
      
      return `https://${host}`;
    }
  }
  return '';
};