// Session monitoring service - 5 minutes timeout
let sessionTimer = null
let lastActivity = Date.now()
const SESSION_TIMEOUT = 5 * 60 * 1000 // 5 minutes in milliseconds

export const startSessionMonitor = (onTimeout) => {
  // Reset timer on any user activity
  const resetTimer = () => {
    lastActivity = Date.now()
    
    if (sessionTimer) {
      clearTimeout(sessionTimer)
    }

    sessionTimer = setTimeout(() => {
      const inactiveTime = Date.now() - lastActivity
      
      if (inactiveTime >= SESSION_TIMEOUT) {
        onTimeout()
      }
    }, SESSION_TIMEOUT)
  }

  // Listen to user activities
  const activities = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
  
  activities.forEach(activity => {
    document.addEventListener(activity, resetTimer, true)
  })

  // Start initial timer
  resetTimer()
}

export const resetSessionTimer = (onTimeout) => {
  lastActivity = Date.now()
  
  if (sessionTimer) {
    clearTimeout(sessionTimer)
  }

  sessionTimer = setTimeout(() => {
    onTimeout()
  }, SESSION_TIMEOUT)
}

export const stopSessionMonitor = () => {
  if (sessionTimer) {
    clearTimeout(sessionTimer)
    sessionTimer = null
  }
}

export const getSessionRemainingTime = () => {
  const elapsed = Date.now() - lastActivity
  const remaining = Math.max(0, SESSION_TIMEOUT - elapsed)
  return Math.floor(remaining / 1000) // Return in seconds
}
