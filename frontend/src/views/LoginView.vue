<template>
  <div 
    class="container-fluid p-0 d-flex align-items-center" 
    :style="{ 
      backgroundImage: `url(${bgImage})`, 
      backgroundSize: 'cover', 
      backgroundPosition: 'center', 
      backgroundRepeat: 'no-repeat',
      minHeight: 'calc(100vh - 60px)' 
    }"
  >
    <div class="row w-100 m-0 justify-content-end">
      
      <div class="col-12 col-md-8 col-lg-4 pe-lg-5">
        
        <div class="card shadow-lg border-0 bg-light bg-opacity-75 my-4">
          <div class="card-body p-4 p-md-5">
            
            <h4 class="card-title text-center mb-4">Login</h4>
            
            <form @submit.prevent="submit">
              <div class="mb-3">
                <label class="form-label fw-bold">Username</label>
                <input v-model="username" class="form-control form-control-lg" required />
              </div>
              
              <div class="mb-4">
                <label class="form-label fw-bold">Password</label>
                <input v-model="password" type="password" class="form-control form-control-lg" required />
              </div>
              
              <div class="d-grid">
                <button class="btn btn-primary btn-lg" type="submit" :disabled="loading">
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                  Login
                </button>
              </div>
            </form>
            
            <div class="mt-4 text-center">
              <router-link to="/register" class="text-decoration-none">Create an account</router-link>
            </div>
            
            <div v-if="error" class="alert alert-danger mt-3 text-center">{{ error }}</div>
            
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';
import { saveAuth } from '@/services/auth';

// 1. IMPORT the image so Vue knows it exists and packages it up
import loginBackground from '@/assets/Login_Background.jpg';

export default {
  name: 'LoginView',
  data() {
    return { 
      username: '', 
      password: '', 
      loading: false, 
      error: null,
      bgImage: loginBackground // 2. Assign the imported image to a variable your template can read
    };
  },
  methods: {
    async submit() {
      this.error = null;
      this.loading = true;
      try {
        const res = await api.post('/api/auth/login', {
          username: this.username,
          password: this.password
        });
        const { access_token, role, user_id } = res.data;
        saveAuth(access_token, role, user_id);
        
        if (role === 'admin') {
          this.$router.push('/admin');
        } else if (role === 'doctor') {
          this.$router.push('/doctor');
        } else if (role === 'patient') {
          this.$router.push('/patient');
        } else {
          // fallback: go to a safe page or show message
          this.$router.push('/');
        }

      } catch (err) {
        this.error = err.response?.data?.msg || 'Login failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>