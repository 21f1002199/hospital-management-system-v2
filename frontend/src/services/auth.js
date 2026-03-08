// src/services/auth.js
const TOKEN_KEY = 'hms_token';
const ROLE_KEY = 'hms_role';
const USER_KEY = 'hms_user';

export function saveAuth(token, role, userId) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
  localStorage.setItem(USER_KEY, userId);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUserRole() {
  return localStorage.getItem(ROLE_KEY);
}

export function getUserId() {
  return localStorage.getItem(USER_KEY);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USER_KEY);
}