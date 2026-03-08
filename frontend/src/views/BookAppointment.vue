<template>
  <div>
    <div class="mb-2">
      <label class="form-label">Select Doctor</label>
      <select v-model="doctorId" class="form-select">
        <option v-for="d in doctors" :key="d.id" :value="d.id">
          {{ d.user?.full_name || d.doctor_identifier || d.id }} — {{ d.specialization }}
        </option>
      </select>
    </div>

    <div class="mb-2">
      <label class="form-label">Date & Time</label>
      <input v-model="scheduled_at" type="datetime-local" class="form-control" />
    </div>

    <div class="d-grid">
      <button class="btn btn-success" @click="book" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
        Book
      </button>
    </div>

    <div v-if="error" class="alert alert-danger mt-2">{{ error }}</div>
    <div v-if="success" class="alert alert-success mt-2">{{ success }}</div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'BookAppointment',
  data() {
    return { doctors: [], doctorId: null, scheduled_at: '', loading: false, error: null, success: null };
  },
  mounted() {
    this.loadDoctors();
  },
  methods: {
    async loadDoctors() {
      try {
        const res = await api.get('/routes/admin/doctors'); // reuse admin doctors list; if not available, add GET doctors endpoint
        this.doctors = res.data || [];
        if (this.doctors.length) this.doctorId = this.doctors[0].id;
      } catch (e) {
        this.doctors = [];
      }
    },
    async book() {
      this.error = null;
      this.success = null;
      if (!this.doctorId || !this.scheduled_at) {
        this.error = 'Select doctor and date/time';
        return;
      }
      this.loading = true;
      try {
        await api.post('/routes/patient/appointments', { doctor_id: this.doctorId, scheduled_at: this.scheduled_at });
        this.success = 'Appointment booked';
        this.$emit('booked');
      } catch (e) {
        this.error = e.response?.data?.msg || 'Booking failed';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>