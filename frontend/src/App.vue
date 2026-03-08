<template>
  <div class="min-vh-100 d-flex flex-column">
    
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <div class="container">
        <router-link class="navbar-brand" to="/">Hospital Management System</router-link>
        
        <div class="collapse navbar-collapse d-flex justify-content-end">
          <ul class="navbar-nav">
            
            <li class="nav-item" v-if="!isAuthenticated">
              <router-link class="nav-link" to="/login">Login</router-link>
            </li>
            
            <li class="nav-item" v-if="!isAuthenticated">
              <router-link class="nav-link" to="/register">Register</router-link>
            </li>
            
            <li class="nav-item dropdown" v-if="isAuthenticated">
              <a class="nav-link dropdown-toggle" href="#" @click.prevent="dropdownOpen = !dropdownOpen">
                {{ userRole }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end" :class="{ show: dropdownOpen, 'd-block': dropdownOpen }">
                <li><a class="dropdown-item" href="#" @click.prevent="logout">Logout</a></li>
              </ul>
            </li>

          </ul>
        </div>
      </div>
    </nav>

    <main class="container-fluid p-0 flex-grow-1 d-flex flex-column">
      <router-view />
    </main>
    
  </div>
</template>

<script>
import { getToken, getUserRole, clearAuth } from './services/auth';

export default {
  name: 'App',
  data() {
    return {
      isAuthenticated: false,
      userRole: 'Guest',
      dropdownOpen: false
    };
  },
  watch: {
    $route() {
      this.checkAuth();
      this.dropdownOpen = false; 
    }
  },
  mounted() {
    this.checkAuth(); 
  },
  methods: {
    checkAuth() {
      this.isAuthenticated = !!getToken();
      this.userRole = getUserRole() || 'Guest';
    },
    logout() {
      clearAuth();
      this.checkAuth(); 
      this.$router.push('/login');
    }
  }
};
</script>