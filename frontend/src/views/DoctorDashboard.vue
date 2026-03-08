<template>
  <div class="container my-4">
    <h3 class="mb-4">Doctor Dashboard</h3>

    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'appointments' }" @click="activeTab = 'appointments'">Appointments</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'patients' }" @click="activeTab = 'patients'; fetchPatients()">My Patients</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'availability' }" @click="activeTab = 'availability'; fetchAvailability()">Availability</button>
      </li>
    </ul>

    <div v-if="activeTab === 'appointments'">
      <div class="mb-4 d-flex gap-2">
        <button class="btn btn-outline-primary" :class="{active: range==='day'}" @click="setRange('day')">Today</button>
        <button class="btn btn-outline-primary" :class="{active: range==='week'}" @click="setRange('week')">Next 7 days</button>
      </div>

      <div v-if="loading" class="text-center my-4"><div class="spinner-border text-primary"></div></div>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-if="appointments.length === 0 && !loading" class="alert alert-info">No upcoming appointments found for this period.</div>

      <div class="row">
        <div class="col-md-6 mb-3" v-for="a in appointments" :key="a.id">
          <div class="card h-100 shadow-sm">
            <div class="card-body">
              <h5 class="card-title">{{ a.patient_name }}</h5>
              <h6 class="card-subtitle mb-2 text-primary">{{ formatIST(a.scheduled_at) }}</h6>
              <p class="card-text"><strong>Reason:</strong> {{ a.reason || 'None provided' }}</p>
              
              <span 
                class="badge" 
                :class="a.status === 'booked' ? (isPast(a.scheduled_at) ? 'bg-warning text-dark border border-warning' : 'bg-primary') : (a.status === 'completed' ? 'bg-success' : 'bg-danger')"
              >
                {{ a.status === 'booked' && isPast(a.scheduled_at) ? 'PATIENT WAITING / OVERDUE' : a.status.toUpperCase() }}
              </span>
            </div>
            <div class="card-footer bg-transparent" v-if="a.status === 'booked'">
              <button class="btn btn-sm btn-success me-2" @click="openCompleteForm(a.id)">Mark Completed</button>
              <button class="btn btn-sm btn-danger" @click="cancelAppointment(a.id)">Cancel</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showCompleteForm" class="card mt-4 border-success">
        <div class="card-header bg-success text-white">Provide Treatment Details</div>
        <div class="card-body">
          <form @submit.prevent="submitComplete">
            <div class="mb-3">
              <label class="form-label fw-bold">Diagnosis <span class="text-danger">*</span></label>
              <textarea v-model="form.diagnosis" class="form-control" rows="2" required></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Prescription & Medications</label>
              <textarea v-model="form.prescriptionText" class="form-control" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label fw-bold">Additional Treatment Notes</label>
              <textarea v-model="form.notes" class="form-control" rows="2"></textarea>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-success" type="submit">Save Record & Complete</button>
              <button class="btn btn-outline-secondary" type="button" @click="showCompleteForm = false">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'patients'">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4>Assigned Patients</h4>
        
        <div class="d-flex w-50 gap-2">
          <div class="input-group">
            <span class="input-group-text bg-white">🔍</span>
            <input v-model="patientSearchQuery" class="form-control" placeholder="Search patients by name or contact..." />
          </div>
          <button class="btn btn-outline-success text-nowrap" @click="exportAssignedPatients" :disabled="isExporting">
            <span v-if="isExporting" class="spinner-border spinner-border-sm me-1"></span>
            Export to CSV
          </button>
        </div>
      </div>

      <div v-if="loading" class="text-center my-4"><div class="spinner-border text-primary"></div></div>
      <div v-if="filteredPatients.length === 0 && !loading" class="alert alert-info">No patients found.</div>
      
      <div class="table-responsive" v-if="filteredPatients.length > 0">
        <table class="table table-hover align-middle shadow-sm bg-white rounded">
          <thead class="table-light">
            <tr>
              <th>Patient Name</th>
              <th>DOB</th>
              <th>Age</th>
              <th>Contact Number</th>
              <th>Gender</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filteredPatients" :key="p.id">
              <td class="fw-bold">{{ p.name }}</td>
              <td>{{ p.dob || 'N/A' }}</td>
              <td>{{ calculateAge(p.dob) }}</td>
              <td>{{ p.contact || 'N/A' }}</td>
              <td>{{ p.gender || 'N/A' }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary" @click="openPatientHistory(p)">View Treatment History</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="activeTab === 'availability'">
      <h4>Manage Availability (Next 7 Days)</h4>
      <div class="card mt-3 shadow-sm">
        <div class="card-body">
          <div class="row mb-4">
            <div class="col-md-4">
              <label class="form-label fw-bold">Select Date</label>
              <input type="date" class="form-control" v-model="selectedDate" :min="minDate" :max="maxDate"/>
            </div>
          </div>
          <div class="mb-4">
            <label class="form-label fw-bold">Select Available Time Slots</label>
            <div class="d-flex flex-wrap gap-2">
              <button 
                v-for="time in timeSlots" 
                :key="time" 
                type="button" 
                class="btn time-slot-btn"
                :class="isSlotSelected(time) ? 'btn-warning fw-bold border-warning' : 'btn-outline-warning text-dark border-secondary'"
                :disabled="isSlotPast(time) && !isSlotSelected(time)"
                @click="toggleSlot(time)"
              >
                {{ time }}
              </button>
            </div>
          </div>
          <button class="btn btn-primary px-4" @click="updateAvailability" :disabled="loading">
            Save Availability
          </button>
        </div>
      </div>
    </div>

    <div ref="historyModalEl" class="modal fade" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content" v-if="selectedPatient">
          <div class="modal-header bg-light">
            <h5 class="modal-title">Treatment History: {{ selectedPatient.name }}</h5>
            <button type="button" class="btn-close" @click="closePatientHistory"></button>
          </div>
          <div class="modal-body bg-light">
            
            <div v-if="loadingHistory" class="text-center my-3"><div class="spinner-border text-primary"></div></div>
            <div v-if="!loadingHistory && patientHistory.length === 0" class="alert alert-info">This patient has no past treatment records.</div>
            
            <div v-for="record in patientHistory" :key="record.id" class="card mb-3 shadow-sm border-0">
              <div class="card-body">
                <div class="d-flex justify-content-between border-bottom pb-2 mb-2">
                  <strong class="text-primary">Treated by Dr. {{ record.doctor_name }} ({{ record.specialization }})</strong>
                  <span class="text-muted small">{{ formatIST(record.date) }}</span>
                </div>
                <p class="mb-1" v-if="record.reason"><strong>Patient's Reason:</strong> {{ record.reason }}</p>
                <p class="mb-1"><strong>Diagnosis:</strong> {{ record.diagnosis }}</p>
                <p class="mb-1 text-muted" v-if="record.notes"><strong>Notes:</strong> {{ record.notes }}</p>
                
                <strong v-if="record.prescription && Object.keys(record.prescription).length > 0">Prescription:</strong>
                <ul class="mb-0 ps-3" v-if="record.prescription && Object.keys(record.prescription).length > 0">
                  <li v-for="(val, key) in record.prescription" :key="key">{{ key }}: {{ val }}</li>
                </ul>
              </div>
            </div>

          </div>
          <div class="modal-footer">
            <button 
              v-if="patientHistory.length > 0 && !loadingHistory" 
              class="btn btn-outline-success" 
              @click="exportPatientHistory"
              :disabled="isExporting"
            >
              <span v-if="isExporting" class="spinner-border spinner-border-sm me-1"></span>
              Export to CSV
            </button>
            <button class="btn btn-secondary" @click="closePatientHistory">Close</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api';
import { Modal } from 'bootstrap'; 

export default {
  name: 'DoctorDashboard',
  data() {
    return {
      activeTab: 'appointments',
      appointments: [],
      patients: [],
      
      availabilityData: {}, 
      selectedDate: this.formatDate(new Date()), 
      timeSlots: [
        '09:00', '09:30', '10:00', '10:30',
        '11:00', '11:30', '12:00', '12:30',
        '13:00', '13:30', '14:00', '14:30',
        '15:00', '15:30', '16:00', '16:30',
        '17:00'
      ],

      loading: false,
      error: null,
      range: 'day',
      showCompleteForm: false,
      currentApptId: null,
      form: { diagnosis: '', prescriptionText: '', notes: '' },
      
      patientSearchQuery: '',
      historyModalInstance: null,
      selectedPatient: null,
      patientHistory: [],
      loadingHistory: false,
      
      isExporting: false
    };
  },
  computed: {
    minDate() { return this.formatDate(new Date()); },
    maxDate() {
      const d = new Date();
      d.setDate(d.getDate() + 7);
      return this.formatDate(d);
    },
    filteredPatients() {
      if (!this.patientSearchQuery) return this.patients;
      const query = this.patientSearchQuery.toLowerCase();
      return this.patients.filter(p => {
        return (p.name || '').toLowerCase().includes(query) || 
               (p.contact || '').toLowerCase().includes(query);
      });
    }
  },
  mounted() {
    this.fetchAppointments();
    
    if (this.$refs.historyModalEl) {
      this.historyModalInstance = new Modal(this.$refs.historyModalEl);
    }
  },
  beforeUnmount() {
    if (this.historyModalInstance) {
      this.historyModalInstance.dispose();
    }
  },
  methods: {

    startExportPolling(taskId, baseRoute) {
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await api.get(`${baseRoute}/export/status/${taskId}`);
          
          if (statusRes.data.state === 'SUCCESS') {
            clearInterval(pollInterval);
            const filepath = statusRes.data.filepath;
            
            const downloadRes = await api.get(`${baseRoute}/export/download/${taskId}`, {
              responseType: 'blob' 
            });

            const url = window.URL.createObjectURL(new Blob([downloadRes.data]));
            const link = document.createElement('a');
            link.href = url;
            const filename = filepath.split('/').pop().split('\\').pop(); 
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
            
            this.isExporting = false;
            
          } else if (statusRes.data.state === 'FAILURE') {
            clearInterval(pollInterval);
            this.isExporting = false;
            alert('Export failed on the server.');
          }
        } catch (err) {
          clearInterval(pollInterval);
          this.isExporting = false;
          alert('Lost connection to export status.');
        }
      }, 2000); 
    },


    calculateAge(dobString) {
      if (!dobString) return 'N/A';
      const birthDate = new Date(dobString);
      const today = new Date();
      
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDifference = today.getMonth() - birthDate.getMonth();
      
      if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      
      return age;
    },
    
    formatIST(dateString) {
      if (!dateString) return '';
      const safeString = (dateString.endsWith('Z') || dateString.includes('+')) ? dateString : dateString + 'Z';
      return new Date(safeString).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' });
    },
    formatDate(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },

    isSlotPast(time) {
      const today = this.formatDate(new Date());
      if (this.selectedDate !== today) return false;

      const now = new Date();
      const [hours, minutes] = time.split(':').map(Number);
      
      const slotTime = new Date();
      slotTime.setHours(hours, minutes, 0, 0);

      return slotTime < now;
    },

    // NEW: Checks if an appointment date/time is in the past
    isPast(dateString) {
      if (!dateString) return false;
      const safeString = (dateString.endsWith('Z') || dateString.includes('+')) ? dateString : dateString + 'Z';
      return new Date(safeString) < new Date();
    },

    isSlotSelected(time) {
      return this.availabilityData[this.selectedDate]?.includes(time);
    },

    toggleSlot(time) {
      const slots = this.availabilityData[this.selectedDate] || [];
      const index = slots.indexOf(time);
      
      if (index > -1) {
        slots.splice(index, 1); 
      } else {
        if (this.isSlotPast(time)) {
          alert("You cannot select a time slot that has already passed.");
          return;
        }
        slots.push(time); 
      }
      this.availabilityData = { ...this.availabilityData, [this.selectedDate]: slots };
    },

    setRange(r) {
      this.range = r;
      this.fetchAppointments();
    },
    async fetchAppointments() {
      this.loading = true;
      try {
        const res = await api.get('/routes/doctor/appointments', { params: { range: this.range } });
        this.appointments = res.data;
      } catch (err) {
        this.error = 'Failed to load appointments';
      } finally {
        this.loading = false;
      }
    },
    async fetchPatients() {
      this.loading = true;
      try {
        const res = await api.get('/routes/doctor/patients');
        this.patients = res.data;
      } catch (err) {
        console.error("Failed to fetch patients");
      } finally {
        this.loading = false;
      }
    },
    async fetchAvailability() {
      this.loading = true;
      try {
        const res = await api.get('/routes/doctor/availability');
        this.availabilityData = res.data.available_slots || {};
      } catch (err) {
        console.error("Failed to fetch availability");
      } finally {
        this.loading = false;
      }
    },
    async updateAvailability() {
      this.loading = true;
      try {
        await api.put('/routes/doctor/availability', { slots: this.availabilityData });
        alert('Availability updated successfully!');
      } catch (err) {
        alert(err.response?.data?.msg || 'Server error updating availability.');
      } finally {
        this.loading = false;
      }
    },
    openCompleteForm(appointmentId) {
      this.currentApptId = appointmentId;
      this.showCompleteForm = true;
      this.form = { diagnosis: '', prescriptionText: '', notes: '' };
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    },
    async cancelAppointment(id) {
      if(!confirm("Are you sure you want to cancel this appointment?")) return;
      try {
        await api.put(`/routes/doctor/appointments/${id}/cancel`);
        this.fetchAppointments();
      } catch (err) {
        alert(err.response?.data?.msg || 'Failed to cancel appointment');
      }
    },
    async submitComplete() {
      try {
        const prescriptionObj = this.form.prescriptionText ? { "Medications": this.form.prescriptionText } : {};
        await api.put(`/routes/doctor/appointments/${this.currentApptId}/complete`, {
          diagnosis: this.form.diagnosis,
          prescription: prescriptionObj, 
          notes: this.form.notes
        });
        
        this.showCompleteForm = false;
        this.currentApptId = null;
        this.fetchAppointments();
        alert('Patient record updated successfully!');
      } catch (err) {
        alert(err.response?.data?.msg || 'Failed to complete appointment');
      }
    },
    
    async openPatientHistory(patient) {
      this.selectedPatient = patient;
      this.patientHistory = [];
      if (this.historyModalInstance) this.historyModalInstance.show();
      
      this.loadingHistory = true;
      try {
        const res = await api.get(`/routes/doctor/patients/${patient.id}/history`);
        this.patientHistory = res.data || [];
      } catch (e) {
        alert("Failed to load treatment history.");
      } finally {
        this.loadingHistory = false;
      }
    },
    closePatientHistory() {
      if (this.historyModalInstance) this.historyModalInstance.hide();
      setTimeout(() => { this.selectedPatient = null; }, 300);
    },

    async exportPatientHistory() {
      this.isExporting = true;
      try {
        const res = await api.post('/routes/doctor/export', { type: 'patient_history', patient_id: this.selectedPatient.id });
        this.startExportPolling(res.data.task_id, '/routes/doctor');
      } catch (e) {
        this.isExporting = false;
        alert("Failed to trigger export.");
      } 
    },

    async exportAssignedPatients() {
      this.isExporting = true;
      try {
        const res = await api.post('/routes/doctor/export', { type: 'assigned_patients', query: this.patientSearchQuery });
        this.startExportPolling(res.data.task_id, '/routes/doctor');
      } catch (e) {
        this.isExporting = false;
        alert("Failed to trigger export.");
      } 
    }
  }
};
</script>

<style scoped>
.time-slot-btn {
  width: 90px;
  border-radius: 4px;
}
</style>