export function toggleTheme() {
  const currentTheme = localStorage.getItem('theme') || 'light'
  const newTheme = currentTheme === 'light' ? 'dark' : 'light'
  
  localStorage.setItem('theme', newTheme)
  document.documentElement.classList.toggle('dark-mode', newTheme === 'dark')
  
  return newTheme
}

export function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light'
  document.documentElement.classList.toggle('dark-mode', savedTheme === 'dark')
  return savedTheme
}

export function getCurrentTheme() {
  return localStorage.getItem('theme') || 'light'
}
