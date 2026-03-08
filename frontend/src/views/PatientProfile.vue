<template>
  <div class="card shadow-sm border-0">
    <div class="card-header bg-white pb-0 border-0">
      <h4 class="mb-0">Edit Profile</h4>
    </div>
    <div class="card-body">
      
      <div v-if="loading" class="text-center my-4">
        <div class="spinner-border text-primary"></div>
      </div>

      <form v-else @submit.prevent="saveProfile">
        <div class="mb-4">
          <label class="form-label text-muted small fw-bold text-uppercase">Account Info</label>
          <input type="text" class="form-control bg-light" :value="username" disabled title="Username cannot be changed">
          <small class="text-muted">Username cannot be changed.</small>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Full Name</label>
            <input v-model="form.full_name" type="text" class="form-control" />
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Email Address</label>
            <input v-model="form.email" type="email" class="form-control" />
          </div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Contact Number</label>
            <input v-model="form.contact" type="tel" class="form-control" placeholder="10-digit mobile number" />
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label fw-bold">Gender</label>
            <select v-model="form.gender" class="form-select">
              <option value="" disabled>Select Gender</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>

        <div class="mb-4">
          <label class="form-label fw-bold">Date of Birth</label>
          <div class="d-flex align-items-center gap-3">
            <input v-model="form.dob" type="date" class="form-control w-50" :max="todayDate" />
            
            <span v-if="calculatedAge !== null" class="badge bg-info text-dark px-3 py-2" style="font-size: 0.9rem;">
              Age: {{ calculatedAge }}
            </span>
          </div>
        </div>

        <div class="d-flex align-items-center gap-3">
          <button class="btn btn-primary px-4" type="submit" :disabled="saving">
            <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
            Save Changes
          </button>
          
          <span v-if="msg" class="text-success fw-bold">{{ msg }}</span>
          <span v-if="error" class="text-danger fw-bold">{{ error }}</span>
        </div>
      </form>
      
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'PatientProfile',
  emits: ['updated'],
  data() {
    return {
      username: '',
      form: {
        full_name: '',
        email: '',
        contact: '',
        gender: '',
        dob: ''
      },
      loading: false,
      saving: false,
      msg: '',
      error: ''
    };
  },
  computed: {
    // Restricts the calendar to prevent selecting dates in the future
    todayDate() {
      const today = new Date();
      return today.toISOString().split('T')[0];
    },
    // Instantly calculates age based on DOB
    calculatedAge() {
      if (!this.form.dob) return null;
      
      const birthDate = new Date(this.form.dob);
      const today = new Date();
      
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      
      return age >= 0 ? age : null;
    }
  },
  mounted() {
    this.loadProfile();
  },
  methods: {
    async loadProfile() {
      this.loading = true;
      this.error = '';
      try {
        const res = await api.get('/routes/patient/profile');
        this.username = res.data.username;
        this.form.full_name = res.data.full_name || '';
        this.form.email = res.data.email || '';
        
        // NEW: Load the new fields from the database
        this.form.contact = res.data.contact || '';
        this.form.gender = res.data.gender || '';
        this.form.dob = res.data.dob || '';
        
      } catch (e) {
        this.error = 'Failed to load profile data.';
      } finally {
        this.loading = false;
      }
    },
    async saveProfile() {
      this.saving = true;
      this.msg = '';
      this.error = '';
      try {
        await api.put('/routes/patient/profile', this.form);
        this.msg = 'Profile updated successfully!';
        this.$emit('updated');
        
        // Clear the success message after 3 seconds
        setTimeout(() => {
          this.msg = '';
        }, 3000);
        
      } catch (e) {
        this.error = e.response?.data?.msg || 'Failed to update profile.';
      } finally {
        this.saving = false;
      }
    }
  }
};
</script>