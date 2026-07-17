let accessToken = null
let onUnauthorized = () => {}

export function getAccessToken() {
  return accessToken
}

export function setAccessToken(token) {
  accessToken = token
}

export function clearAccessToken() {
  accessToken = null
}

/** Registered by AuthContext; called when a refresh attempt fails so the app can log the user out. */
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

export function notifyUnauthorized() {
  onUnauthorized()
}
