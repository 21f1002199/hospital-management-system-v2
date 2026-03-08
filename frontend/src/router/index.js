// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Login from '@/views/LoginView.vue';
import Register from '@/views/RegisterView.vue';
import DoctorDashboard from '@/views/DoctorDashboard.vue';
import AdminDashboard from '@/views/AdminDashboard.vue';
import PatientDashboard from '@/views/PatientDashboard.vue';
import { getToken, getUserRole } from '@/services/auth';

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/doctor', component: DoctorDashboard, meta: { requiresAuth: true, role: 'doctor' } },
  { path: '/admin', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/patient', component: PatientDashboard, meta: { requiresAuth: true, role: 'patient' } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const token = getToken();
  if (to.meta.requiresAuth && !token) return next('/login');
  if (to.meta.role && getUserRole() !== to.meta.role) return next('/login');
  next();
});

export default router;