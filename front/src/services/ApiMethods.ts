import { API_BASE_URL } from "./apiConfig";

const BASE_URL = API_BASE_URL;

class ApiMethods {
  static apiRequest(method: string, url: string, body: any = null, token?: string) {
    const fullUrl = BASE_URL + url;
    const headers: HeadersInit = { "Content-Type": "application/json" };

    // Add Authorization header if token is provided
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (method !== "GET" && body) {
      options.body = JSON.stringify(body);
    }

    return new Promise((resolve, reject) => {
      fetch(fullUrl, options)
        .then((res) => {
          if (res.status === 404) {
            return null;
          }
          if (!res.ok) {
            if (res.status === 401) {
              throw new Error("Unauthorized - Please login again");
            }
            if (res.status === 403) {
              throw new Error("Forbidden - You don't have permission");
            }
            throw new Error(`Server error: ${res.status}`);
          }
          return res.json();
        })
        .then(resolve)
        .catch(reject);
    });
  }

  static get(url: string, token?: string) {
    return this.apiRequest("GET", url, null, token);
  }

  static post(url: string, body: any, token?: string) {
    return this.apiRequest("POST", url, body, token);
  }

  static put(url: string, body: any, token?: string) {
    return this.apiRequest("PUT", url, body, token);
  }

  static delete(url: string, token?: string) {
    return this.apiRequest("DELETE", url, null, token);
  }
}

export default ApiMethods;
