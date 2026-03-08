<template>
  <div class="table-responsive">
    <table class="table table-hover align-middle shadow-sm bg-white rounded">
      <thead class="table-light">
        <tr>
          <th>ID</th>
          <th>Doctor</th>
          <th>Patient</th>
          <th>Date & Time (IST)</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="appt in appointments" :key="appt.id">
          <td>{{ appt.id }}</td>
          <td class="fw-bold text-primary">Dr. {{ appt.doctor_name }}</td>
          <td>{{ appt.patient_name }}</td>
          <td>{{ formatIST(appt.scheduled_at) }}</td>
          <td>
            <span class="badge" :class="statusBadge(appt.status)">
              {{ appt.status.toUpperCase() }}
            </span>
          </td>
        </tr>
        <tr v-if="!appointments || appointments.length === 0">
          <td colspan="5" class="text-center text-muted py-3">No appointments found.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'AppointmentsTable',
  props: {
    appointments: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    formatIST(dateString) {
      if (!dateString) return '';
      const safeString = (dateString.endsWith('Z') || dateString.includes('+')) ? dateString : dateString + 'Z';
      return new Date(safeString).toLocaleString('en-IN', { 
        timeZone: 'Asia/Kolkata', 
        dateStyle: 'medium', 
        timeStyle: 'short' 
      });
    },
    statusBadge(status) {
      if (status === 'booked') return 'bg-primary';
      if (status === 'completed') return 'bg-success';
      if (status === 'cancelled') return 'bg-danger';
      return 'bg-secondary';
    }
  }
};
</script>