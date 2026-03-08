<template>
  <div>
    <div v-if="doctors.length === 0" class="text-muted p-3 text-center border rounded bg-light">
      No doctors found.
    </div>
    
    <div class="table-responsive" v-else>
      <table class="table table-hover align-middle border">
        <thead class="table-light">
          <tr>
            <th scope="col" style="width: 5%;">#</th>
            <th scope="col" style="width: 35%;">Doctor Details</th>
            <th scope="col" style="width: 35%;">Specialization / Dept</th>
            <th scope="col" style="width: 25%; text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(d, index) in doctors" :key="d.id">
            
            <td><strong>{{ index + 1 }}</strong></td>
            
            <td>
              <div class="fw-bold">{{ d.full_name || d.username || 'Unknown Doctor' }}</div>
              <div class="text-muted small" v-if="d.email">
                📧 {{ d.email }}
              </div>
              <div class="text-muted small" v-if="d.contact">
                📞 {{ d.contact }}
              </div>
            </td>
            
            <td>
              <span class="badge bg-secondary mb-1">{{ d.specialization || 'General' }}</span>
              <div class="text-muted small" v-if="d.department && d.department !== 'N/A'">
                {{ d.department }}
              </div>
            </td>
            
            <td class="text-end">
              <button class="btn btn-sm btn-outline-primary me-2" @click="openEditModal(d)">
                Edit
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteDoctor(d.id)">
                Delete
              </button>
            </td>
            
          </tr>
        </tbody>
      </table>
    </div>

    <EditDoctorModal 
      v-if="showModal" 
      :doctor="selectedDoctor" 
      @close="showModal = false" 
      @updated="onDoctorUpdated" 
    />

  </div>
</template>

<script>
import api from '@/services/api';
import EditDoctorModal from '@/components/EditDoctorModal.vue';

export default {
  name: 'DoctorList',
  components: { EditDoctorModal },
  props: { 
    doctors: { type: Array, default: () => [] } 
  },
  data() {
    return {
      showModal: false,
      selectedDoctor: null
    };
  },
  methods: {
    async deleteDoctor(id) {
      if (!confirm('Are you sure you want to delete this doctor?')) return;
      try {
        await api.delete(`/routes/admin/doctors/${id}`);
        this.$emit('deleted', id);
      } catch (e) {
        alert(e.response?.data?.msg || 'Delete failed');
      }
    },
    openEditModal(doctor) {
      this.selectedDoctor = doctor;
      this.showModal = true;
    },
    onDoctorUpdated() {
      // Pass the event up to AdminDashboard to refresh the list
      this.$emit('updated'); 
      this.showModal = false;
    }
  }
};
</script>