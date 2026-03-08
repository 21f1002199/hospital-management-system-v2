<template>
  <div class="modal fade show d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Edit Doctor Profile</h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="saveChanges">
            
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Full Name</label>
                <input type="text" class="form-control" v-model="formData.name" required />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Email Address</label>
                <input type="email" class="form-control" v-model="formData.email" />
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Contact Number</label>
              <input type="text" class="form-control" v-model="formData.contact" />
            </div>

            <div class="row">
              <div class="col-md-12 mb-3">
                <label class="form-label">Department Name</label>
                <input type="text" class="form-control" v-model="formData.department_name" placeholder="e.g. Cardiology, Neurology" />
              </div>
            </div>

            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Specialization</label>
                <input type="text" class="form-control" v-model="formData.specialization" />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Qualifications</label>
                <input type="text" class="form-control" v-model="formData.qualifications" placeholder="e.g. MBBS, MD" />
              </div>
            </div>

          </form>
        </div>
        
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">Cancel</button>
          <button type="button" class="btn btn-primary" @click="saveChanges" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'EditDoctorModal',
  props: {
    doctor: { type: Object, required: true }
  },
  data() {
    // Check if the department is sent as an object (dept.name) or a string from the API
    const currentDept = this.doctor.department?.name || this.doctor.department || '';
    
    return {
      loading: false,
      formData: {
        name: this.doctor.name || this.doctor.user?.full_name || '',
        email: this.doctor.email || '',
        specialization: this.doctor.specialization || '',
        qualifications: this.doctor.qualifications || '',
        contact: this.doctor.contact || '',
        department_name: currentDept // NEW: Map to department_name
      }
    };
  },
  methods: {
    async saveChanges() {
      this.loading = true;
      try {
        await api.put(`/routes/admin/doctors/${this.doctor.id}`, this.formData);
        this.$emit('updated'); 
        this.$emit('close');   
      } catch (e) {
        alert(e.response?.data?.msg || 'Failed to update doctor.');
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>