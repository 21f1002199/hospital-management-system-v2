<!-- src/components/AppointmentCard.vue -->
<template>
  <div class="card mb-3">
    <div class="card-body d-flex justify-content-between align-items-center">
      <div>
        <h6 class="mb-1">Patient ID: {{ appt.patient_id }}</h6>
        <p class="mb-0 text-muted">{{ formattedDate }}</p>
      </div>
      <div class="text-end">
        <span class="badge bg-info text-dark me-2">{{ appt.status }}</span>
        <button v-if="canComplete" class="btn btn-sm btn-success" @click="$emit('complete', appt.id)">Complete</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppointmentCard',
  props: { appt: { type: Object, required: true } },
  computed: {
    formattedDate() {
      return new Date(this.appt.scheduled_at).toLocaleString();
    },
    canComplete() {
      return this.appt.status !== 'completed' && this.appt.status !== 'cancelled';
    }
  }
};
</script>