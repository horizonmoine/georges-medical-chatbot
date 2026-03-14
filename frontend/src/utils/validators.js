// Form validation utilities

export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(String(email).toLowerCase())
}

export const validatePassword = (password) => {
  const errors = []
  
  if (password.length < 8) {
    errors.push('Minimum 8 caractères requis')
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Au moins 1 majuscule requise')
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Au moins 1 minuscule requise')
  }
  
  if (!/\d/.test(password)) {
    errors.push('Au moins 1 chiffre requis')
  }
  
  if (!/[@$!%*?&]/.test(password)) {
    errors.push('Au moins 1 caractère spécial requis (@$!%*?&)')
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}

export const validatePhone = (phone) => {
  const re = /^(\+33|0)[1-9](\d{2}){4}$/
  return re.test(String(phone).replace(/\s/g, ''))
}

export const validateDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  
  // Check if valid date
  if (isNaN(date.getTime())) {
    return { valid: false, error: 'Date invalide' }
  }
  
  // Check if not in future
  if (date > now) {
    return { valid: false, error: 'La date ne peut pas être dans le futur' }
  }
  
  // Check if reasonable age (between 0 and 120 years)
  const age = (now - date) / (1000 * 60 * 60 * 24 * 365.25)
  if (age < 0 || age > 120) {
    return { valid: false, error: 'Date de naissance invalide' }
  }
  
  return { valid: true }
}

export const sanitizeInput = (input) => {
  // Remove HTML tags and dangerous characters
  return String(input)
    .replace(/<[^>]*>/g, '')
    .replace(/[<>]/g, '')
    .trim()
}

export const validateRequired = (value, fieldName = 'Ce champ') => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    return { valid: false, error: `${fieldName} est requis` }
  }
  return { valid: true }
}

export const validateLength = (value, min, max, fieldName = 'Ce champ') => {
  const length = String(value).length
  
  if (length < min) {
    return { valid: false, error: `${fieldName} doit contenir au moins ${min} caractères` }
  }
  
  if (max && length > max) {
    return { valid: false, error: `${fieldName} ne peut pas dépasser ${max} caractères` }
  }
  
  return { valid: true }
}
