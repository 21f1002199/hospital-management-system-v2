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
      
      <div class="col-12 col-md-10 col-lg-6 pe-lg-5">
        
        <div class="card shadow-lg border-0 bg-light bg-opacity-75 my-4">
          <div class="card-body p-4 p-md-5">
            
            <h4 class="card-title text-center mb-4">Register (Patient)</h4>
            
            <form @submit.prevent="submit">
              
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Username <span class="text-danger">*</span></label>
                  <input v-model="username" class="form-control" required />
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Email</label>
                  <input v-model="email" type="email" class="form-control" />
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label fw-bold">Full Name</label>
                <input v-model="full_name" class="form-control" />
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Contact Number</label>
                  <input v-model="contact" type="tel" class="form-control" placeholder="10-digit mobile number" />
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Gender</label>
                  <select v-model="gender" class="form-select">
                    <option value="" disabled>Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label fw-bold">Date of Birth</label>
                <div class="d-flex align-items-center gap-3">
                  <input v-model="dob" type="date" class="form-control" :max="todayDate" />
                  
                  <span v-if="calculatedAge !== null" class="badge bg-info text-dark px-3 py-2" style="font-size: 0.9rem;">
                    Age: {{ calculatedAge }}
                  </span>
                </div>
              </div>

              <div class="row mt-2">
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Password <span class="text-danger">*</span></label>
                  <input v-model="password" type="password" class="form-control" required />
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Confirm Password <span class="text-danger">*</span></label>
                  <input v-model="confirm" type="password" class="form-control" required />
                </div>
              </div>

              <div class="d-grid mt-4">
                <button class="btn btn-success btn-lg" type="submit" :disabled="loading">
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                  Register
                </button>
              </div>
            </form>
            
            <div class="mt-4 text-center">
              <router-link to="/login" class="text-decoration-none">Already have an account? Login here</router-link>
            </div>
            
            <div v-if="error" class="alert alert-danger mt-3 text-center">{{ error }}</div>
            <div v-if="success" class="alert alert-success mt-3 text-center">{{ success }}</div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

// 1. IMPORT the image so Vue bundles it correctly
import registerBackground from '@/assets/Regis_Background.jpg';

export default {
  name: 'RegisterView',
  data() {
    return { 
      username: '', password: '', confirm: '', full_name: '', email: '', 
      contact: '', gender: '', dob: '', 
      loading: false, error: null, success: null,
      
      // 2. Assign it to a variable for the template
      bgImage: registerBackground
    };
  },
  computed: {
    // Restricts the calendar to prevent selecting dates in the future
    todayDate() {
      const today = new Date();
      return today.toISOString().split('T')[0];
    },
    // Instantly calculates age when a DOB is selected
    calculatedAge() {
      if (!this.dob) return null;
      
      const birthDate = new Date(this.dob);
      const today = new Date();
      
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      
      return age >= 0 ? age : null;
    }
  },
  methods: {
    async submit() {
      this.error = null;
      this.success = null;
      
      if (this.password !== this.confirm) {
        this.error = 'Passwords do not match';
        return;
      }
      
      this.loading = true;
      try {
        await api.post('/api/auth/register', {
          username: this.username,
          password: this.password,
          full_name: this.full_name,
          email: this.email,
          contact: this.contact, 
          gender: this.gender,
          dob: this.dob
        });
        
        this.success = 'Registration successful! Redirecting to login in 3 seconds...';
        
        this.username = this.password = this.confirm = this.full_name = this.email = '';
        this.contact = this.gender = this.dob = '';
        
        setTimeout(() => {
          this.$router.push('/login');
        }, 3000);

      } catch (err) {
        this.error = err.response?.data?.msg || 'Registration failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>