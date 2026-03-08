<template>
  <div ref="modalEl" class="modal fade" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Add Doctor</h5>
          <button type="button" class="btn-close" @click="close"></button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="submit">
            
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Username <span class="text-danger">*</span></label>
                <input v-model="form.username" class="form-control" required />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Password <span class="text-danger">*</span></label>
                <input v-model="form.password" type="password" class="form-control" required />
              </div>
            </div>

            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Full Name</label>
                <input v-model="form.full_name" class="form-control" />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Email</label>
                <input v-model="form.email" type="email" class="form-control" />
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Contact Number</label>
              <input v-model="form.contact" type="text" class="form-control" placeholder="Phone number" />
            </div>

            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Department</label>
                <input v-model="form.department" class="form-control" placeholder="e.g. Cardiology" />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Specialization</label>
                <input v-model="form.specialization" class="form-control" placeholder="e.g. Surgeon" />
              </div>
            </div>

            <div class="mb-4">
              <label class="form-label">Qualifications</label>
              <input v-model="form.qualifications" class="form-control" placeholder="e.g. MBBS, MD" />
            </div>

            <div class="d-grid">
              <button class="btn btn-primary" type="submit" :disabled="loading">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                Create Doctor
              </button>
            </div>
            
          </form>

          <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';
import { Modal } from 'bootstrap';

export default {
  name: 'CreateDoctorModal',
  emits: ['created', 'close'],
  data() {
    return {
      form: {
        username: '',
        password: '',
        full_name: '',
        email: '',
        contact: '', 
        specialization: '',
        department: '',
        qualifications: '' 
      },
      loading: false,
      error: null,
      bsModal: null,
      onHiddenBound: null,
      successData: null 
    };
  },
  mounted() {
    this.bsModal = new Modal(this.$refs.modalEl, { backdrop: true, keyboard: true });
    this.bsModal.show();
    this.onHiddenBound = this.onHidden.bind(this);
    if (this.$refs.modalEl) {
      this.$refs.modalEl.addEventListener('hidden.bs.modal', this.onHiddenBound);
    }
  },
  beforeUnmount() {
    try {
      if (this.$refs.modalEl && this.onHiddenBound) {
        this.$refs.modalEl.removeEventListener('hidden.bs.modal', this.onHiddenBound);
      }
    } catch (err) {
      console.debug('Cleanup: Listener removal skipped'); // FIX: Added to satisfy ESLint
    }

    if (this.bsModal) {
      try {
        if (this.$refs.modalEl) this.bsModal.hide();
      } catch (err) {
        console.debug('Cleanup: Modal hide skipped'); // FIX: Added to satisfy ESLint
      }
      try {
        this.bsModal.dispose();
      } catch (err) {
        console.debug('Cleanup: Modal dispose skipped'); // FIX: Added to satisfy ESLint
      }
      this.bsModal = null;
    }
    this.onHiddenBound = null;
  },
  methods: {
    onHidden() {
      if (this.successData) {
        this.$emit('created', this.successData);
      } else {
        this.$emit('close');
      }
    },
    close() {
      if (this.bsModal) {
        try {
          this.bsModal.hide();
        } catch (err) {
          this.$emit('close');
        }
      } else {
        this.$emit('close');
      }
    },
    async submit() {
      this.error = null;
      this.loading = true;
      try {
        const res = await api.post('/routes/admin/doctors', this.form);
        this.successData = res.data;
        
        if (this.bsModal) {
          try {
            this.bsModal.hide();
          } catch (err) {
            this.$emit('created', this.successData);
            this.$emit('close');
            return;
          }
        } else {
          this.$emit('created', this.successData);
          this.$emit('close');
          return;
        }
      } catch (e) {
        this.error = e.response?.data?.msg || 'Create failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>