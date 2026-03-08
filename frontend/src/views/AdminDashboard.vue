<template>
  <div class="container my-4">
    <h3 class="mb-4">Admin Dashboard</h3>

    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">Overview</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'doctors' }" @click="activeTab = 'doctors'; loadDoctors()">Manage Doctors</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'patients' }" @click="activeTab = 'patients'; loadPatients()">Manage Patients</button>
      </li>
    </ul>

    <div v-if="activeTab === 'overview'">
      <div class="row mb-4">
        <div class="col-md-4">
          <div class="card text-center shadow-sm">
            <div class="card-body">
              <h5 class="text-muted">Total Doctors</h5>
              <h2 class="text-primary">{{ stats.doctors }}</h2>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card text-center shadow-sm">
            <div class="card-body">
              <h5 class="text-muted">Total Patients</h5>
              <h2 class="text-success">{{ stats.patients }}</h2>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card text-center shadow-sm">
            <div class="card-body">
              <h5 class="text-muted">Total Appointments</h5>
              <h2 class="text-warning">{{ stats.appointments }}</h2>
            </div>
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="text-primary">Upcoming Appointments</h5>
        <button class="btn btn-sm btn-outline-secondary" @click="loadAppointments">Refresh</button>
      </div>
      <div v-if="upcomingAppointments.length === 0" class="alert alert-light border text-muted">
        No upcoming appointments currently booked.
      </div>
      <AppointmentsTable v-else :appointments="upcomingAppointments" />

      <div class="d-flex justify-content-between align-items-center mt-5 mb-3">
        <h5 class="text-secondary mb-0">Past & Recent Appointments</h5>
        <button 
          v-if="pastAppointments.length > 0" 
          class="btn btn-sm btn-outline-success" 
          @click="exportPastAppointments"
          :disabled="isExporting"
        >
          <span v-if="isExporting" class="spinner-border spinner-border-sm me-1"></span>
          Export to CSV
        </button>
      </div>
      
      <div v-if="pastAppointments.length === 0" class="alert alert-light border text-muted">
        No past appointments found.
      </div>
      <AppointmentsTable v-else :appointments="pastAppointments" />
    </div>

    <div v-if="activeTab === 'doctors'">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div class="input-group w-50">
          <span class="input-group-text bg-white">🔍</span>
          <input v-model="doctorSearchQuery" class="form-control" placeholder="Search doctors by name or department..." />
        </div>
        <div>
          <button class="btn btn-outline-success me-2" @click="exportDoctors" :disabled="isExporting">
             <span v-if="isExporting" class="spinner-border spinner-border-sm me-1"></span>
             Export to CSV
          </button>
          <button class="btn btn-primary" @click="showCreate = true">+ Add Doctor</button>
        </div>
      </div>

      <div class="table-responsive">
        <table class="table table-hover align-middle shadow-sm bg-white rounded">
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Specialization</th>
              <th>Department</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in filteredDoctors" :key="doc.id">
              <td>{{ doc.id }}</td>
              <td>
                <a href="#" class="text-decoration-none fw-bold" @click.prevent="openDoctorModal(doc)">Dr. {{ doc.name || doc.user?.full_name }}</a>
              </td>
              <td>{{ doc.specialization }}</td>
              <td>{{ doc.department || doc.department?.name }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-2" @click="openEditDoctor(doc)">Edit</button>
                <button class="btn btn-sm btn-outline-danger" @click="deleteDoctor(doc.id)">Delete</button>
              </td>
            </tr>
            <tr v-if="filteredDoctors.length === 0">
              <td colspan="5" class="text-center text-muted py-3">No doctors found matching your search.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="activeTab === 'patients'">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Registered Patients Directory</h5>
        
        <div class="input-group w-50">
          <span class="input-group-text bg-white">🔍</span>
          <input v-model="patientSearchQuery" class="form-control" placeholder="Search patients by name or contact..." />
        </div>
        
        <button class="btn btn-outline-success" @click="exportPatients" :disabled="isExporting">
           <span v-if="isExporting" class="spinner-border spinner-border-sm me-1"></span>
           Export to CSV
        </button>
      </div>
      
      <div class="table-responsive">
        <table class="table table-hover align-middle shadow-sm bg-white rounded">
          <thead class="table-light">
            <tr>
              <th>ID</th>
              <th>Patient Name</th>
              <th>Contact</th>
              <th>Gender</th>
              <th>Joined Date</th>
              <th>Action</th> 
            </tr>
          </thead>
          <tbody>
            <tr v-for="pat in filteredPatients" :key="pat.id">
              <td> {{ pat.id }}</td>
              <td>
                <a href="#" class="text-decoration-none fw-bold" @click.prevent="openPatientModal(pat)">{{ pat.name }}</a>
              </td>
              <td>{{ pat.contact || 'N/A' }}</td>
              <td>{{ pat.gender || 'N/A' }}</td>
              <td>{{ pat.created_at ? new Date(pat.created_at).toLocaleDateString() : 'N/A' }}</td>
              <td>
                <button class="btn btn-sm btn-outline-danger" @click="deletePatient(pat.id)">Remove</button>
              </td>
            </tr>
            <tr v-if="filteredPatients.length === 0">
              <td colspan="6" class="text-center text-muted py-3">No patients found matching your search.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div ref="doctorModalEl" class="modal fade" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content" v-if="selectedDoctor">
          <div class="modal-header bg-light">
            <h5 class="modal-title">Dr. {{ selectedDoctor.name || selectedDoctor.user?.full_name }}</h5>
            <button type="button" class="btn-close" @click="closeDoctorModal"></button>
          </div>
          <div class="modal-body">
            <p><strong>Email:</strong> <a :href="'mailto:' + selectedDoctor.email">{{ selectedDoctor.email || 'Not provided' }}</a></p>
            <p><strong>Department:</strong> {{ selectedDoctor.department || selectedDoctor.department?.name }}</p>
            <p><strong>Specialization:</strong> {{ selectedDoctor.specialization }}</p>
            <p><strong>Qualifications:</strong> {{ selectedDoctor.qualifications || 'Not specified' }}</p>
            <p><strong>Contact:</strong> {{ selectedDoctor.contact || 'Not provided' }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeDoctorModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <div ref="patientModalEl" class="modal fade" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content" v-if="selectedPatient">
          <div class="modal-header bg-light">
            <h5 class="modal-title">Patient Profile: {{ selectedPatient.name }}</h5>
            <button type="button" class="btn-close" @click="closePatientModal"></button>
          </div>
          <div class="modal-body">
            <div class="row mb-3">
              <div class="col-md-6">
                <p class="mb-1"><strong>Email:</strong> {{ selectedPatient.email }}</p>
                <p class="mb-1"><strong>Contact:</strong> {{ selectedPatient.contact || 'N/A' }}</p>
              </div>
              <div class="col-md-6">
                <p class="mb-1"><strong>Gender:</strong> {{ selectedPatient.gender || 'N/A' }}</p>
                <p class="mb-1"><strong>DOB:</strong> {{ selectedPatient.dob || 'N/A' }}</p>
              </div>
            </div>

            <hr>
            
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h6 class="mb-0">Treatment History</h6>
              <button class="btn btn-sm btn-primary" @click="fetchPatientHistory(selectedPatient.id)">
                {{ loadingHistory ? 'Loading...' : 'Show Treatment History' }}
              </button>
            </div>

            <div v-if="showHistorySection">
              <div v-if="patientHistory.length === 0" class="alert alert-info py-2">No past appointments found.</div>
              
              <div v-for="record in patientHistory" :key="record.id" class="card mb-2 border-info shadow-sm">
                <div class="card-body py-2">
                  <div class="d-flex justify-content-between">
                    <strong class="text-primary">Dr. {{ record.doctor_name }} ({{ record.specialization }})</strong>
                    <small class="text-muted">{{ formatIST(record.date) }}</small>
                  </div>
                  <div class="mt-2 small">
                    <p class="mb-1" v-if="record.reason"><strong>Reason:</strong> {{ record.reason }}</p>
                    <p class="mb-1"><strong>Diagnosis:</strong> {{ record.diagnosis }}</p>
                    <p class="mb-1 text-muted" v-if="record.notes"><strong>Notes:</strong> {{ record.notes }}</p>
                    
                    <strong v-if="record.prescription && Object.keys(record.prescription).length > 0">Prescription:</strong>
                    <ul class="mb-0 ps-3" v-if="record.prescription && Object.keys(record.prescription).length > 0">
                      <li v-for="(val, key) in record.prescription" :key="key">{{ key }}: {{ val }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

          </div>
          <div class="modal-footer">
            <button 
              v-if="showHistorySection && patientHistory.length > 0" 
              class="btn btn-outline-success" 
              @click="exportPatientHistory"
              :disabled="isExporting"
            >
              <span v-if="isExporting" class="spinner-border spinner-border-sm me-1"></span>
              Export to CSV
            </button>
            <button class="btn btn-secondary" @click="closePatientModal">Close</button>
          </div>
        </div>
      </div>
    </div>

    <CreateDoctorModal v-if="showCreate" @close="showCreate=false" @created="onDoctorCreated" />
    
    <EditDoctorModal 
      v-if="showEditDoctor" 
      :doctor="editingDoctor" 
      @close="closeEditDoctor" 
      @updated="onDoctorUpdated" 
    />
  </div>
</template>

<script>
import api from '@/services/api';
import CreateDoctorModal from '@/components/CreateDoctorModal.vue';
import EditDoctorModal from '@/components/EditDoctorModal.vue'; 
import AppointmentsTable from '@/components/AppointmentsTable.vue';
import { Modal } from 'bootstrap';

export default {
  name: 'AdminDashboard',
  components: { CreateDoctorModal, EditDoctorModal, AppointmentsTable },
  data() {
    return {
      activeTab: 'overview',
      stats: { doctors: 0, patients: 0, appointments: 0 },
      doctors: [],
      patients: [],
      appointments: [],
      
      doctorSearchQuery: '',
      patientSearchQuery: '',
      
      showCreate: false,
      showEditDoctor: false, 
      editingDoctor: null,   

      doctorModalInstance: null,
      patientModalInstance: null,
      selectedDoctor: null,
      selectedPatient: null,
      
      patientHistory: [],
      loadingHistory: false,
      showHistorySection: false,
      
      // NEW: State for loading spinner on export buttons
      isExporting: false 
    };
  },
  computed: {
    upcomingAppointments() {
      return this.appointments.filter(a => this.isFuture(a.scheduled_at) && a.status === 'booked');
    },
    pastAppointments() {
      return this.appointments.filter(a => !this.isFuture(a.scheduled_at) || a.status !== 'booked');
    },
    filteredDoctors() {
      if (!this.doctorSearchQuery) return this.doctors;
      const query = this.doctorSearchQuery.toLowerCase();
      return this.doctors.filter(doc => {
        const docName = (doc.name || '').toLowerCase();
        const docDept = (doc.department || '').toLowerCase();
        return docName.includes(query) || docDept.includes(query);
      });
    },
    filteredPatients() {
      if (!this.patientSearchQuery) return this.patients;
      const query = this.patientSearchQuery.toLowerCase();
      return this.patients.filter(pat => {
        const patName = (pat.name || '').toLowerCase();
        const patContact = (pat.contact || '').toLowerCase();
        return patName.includes(query) || patContact.includes(query);
      });
    }
  },
  mounted() {
    this.loadDashboard();
    this.loadAppointments();
    
    if (this.$refs.doctorModalEl) this.doctorModalInstance = new Modal(this.$refs.doctorModalEl);
    if (this.$refs.patientModalEl) this.patientModalInstance = new Modal(this.$refs.patientModalEl);
  },
  beforeUnmount() {
    if (this.doctorModalInstance) this.doctorModalInstance.dispose();
    if (this.patientModalInstance) this.patientModalInstance.dispose();
  },
  methods: {
    isFuture(dateString) {
      if (!dateString) return false;
      const safeString = (dateString.endsWith('Z') || dateString.includes('+')) ? dateString : dateString + 'Z';
      return new Date(safeString) > new Date(); 
    },
    formatIST(dateString) {
      if (!dateString) return '';
      const safeString = (dateString.endsWith('Z') || dateString.includes('+')) ? dateString : dateString + 'Z';
      return new Date(safeString).toLocaleString('en-IN', { 
        timeZone: 'Asia/Kolkata', 
        dateStyle: 'medium', 
        timeStyle: 'short' 
      });
    },
    async loadDashboard() {
      try {
        const res = await api.get('/routes/admin/dashboard');
        this.stats = res.data;
      } catch (e) {
        console.error(e);
      }
    },
    async loadAppointments() {
      try {
        const res = await api.get('/routes/admin/appointments');
        this.appointments = res.data || [];
      } catch (e) {
        this.appointments = [];
      }
    },
    async loadDoctors() {
      try {
        const res = await api.get('/routes/admin/doctors', { params: { subject: 'doctor_list' }});
        this.doctors = res.data || [];
      } catch (e) {
        this.doctors = [];
      }
    },
    async loadPatients() {
      try {
        const res = await api.get('/routes/admin/patients');
        this.patients = res.data || [];
      } catch (e) {
        this.patients = [];
      }
    },
    openDoctorModal(doc) {
      this.selectedDoctor = doc;
      if (this.doctorModalInstance) this.doctorModalInstance.show();
    },
    closeDoctorModal() {
      if (this.doctorModalInstance) this.doctorModalInstance.hide();
      setTimeout(() => { this.selectedDoctor = null; }, 300);
    },
    async deleteDoctor(id) {
      if (!confirm("Are you sure you want to delete this doctor?")) return;
      try {
        await api.delete(`/routes/admin/doctors/${id}`);
        this.loadDoctors();
        this.loadDashboard();
      } catch(e) {
        alert("Delete failed.");
      }
    },
    openEditDoctor(doc) {
      this.editingDoctor = doc;
      this.showEditDoctor = true;
    },
    closeEditDoctor() {
      this.showEditDoctor = false;
      this.editingDoctor = null;
    },
    onDoctorCreated() {
      this.showCreate = false;
      this.loadDashboard();
      if (this.activeTab === 'doctors') this.loadDoctors();
    },
    onDoctorUpdated() {
      this.closeEditDoctor();
      this.loadDoctors();
    },
    openPatientModal(pat) {
      this.selectedPatient = pat;
      this.showHistorySection = false; 
      this.patientHistory = [];
      if (this.patientModalInstance) this.patientModalInstance.show();
    },
    closePatientModal() {
      if (this.patientModalInstance) this.patientModalInstance.hide();
      setTimeout(() => { 
        this.selectedPatient = null; 
        this.showHistorySection = false;
      }, 300);
    },
    async fetchPatientHistory(id) {
      this.loadingHistory = true;
      this.showHistorySection = true;
      try {
        const res = await api.get(`/routes/admin/patients/${id}/history`);
        this.patientHistory = res.data || [];
      } catch (e) {
        alert("Failed to load history.");
      } finally {
        this.loadingHistory = false;
      }
    },
    async deletePatient(id) {
      if (!confirm("Are you sure you want to completely remove this patient? This action cannot be undone.")) return;
      try {
        await api.delete(`/routes/admin/patients/${id}`);
        this.loadPatients();
        this.loadDashboard(); 
      } catch (e) {
        alert(e.response?.data?.msg || "Failed to remove patient.");
      }
    },

    // --- NEW: ASYNC CSV EXPORT LOGIC ---
    
    startExportPolling(taskId, baseRoute) {
      const pollInterval = setInterval(async () => {
        try {
          // 1. Check status
          const statusRes = await api.get(`${baseRoute}/export/status/${taskId}`);
          
          if (statusRes.data.state === 'SUCCESS') {
            clearInterval(pollInterval);
            const filepath = statusRes.data.filepath;
            
            // 2. Fetch the file blob securely using taskId
            const downloadRes = await api.get(`${baseRoute}/export/download/${taskId}`, {
              responseType: 'blob' 
            });

            // 3. Force browser download
            const url = window.URL.createObjectURL(new Blob([downloadRes.data]));
            const link = document.createElement('a');
            link.href = url;
            
            // Extract filename safely from the returned filepath
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
      }, 2000); // Check every 2 seconds
    },

    async exportDoctors() {
      this.isExporting = true;
      try {
        const res = await api.post('/routes/admin/export', { type: 'doctors', query: this.doctorSearchQuery });
        this.startExportPolling(res.data.task_id, '/routes/admin');
      } catch (e) {
        this.isExporting = false;
        alert("Failed to trigger export.");
      } 
    },

    async exportPatients() {
      this.isExporting = true;
      try {
        const res = await api.post('/routes/admin/export', { type: 'patients', query: this.patientSearchQuery });
        this.startExportPolling(res.data.task_id, '/routes/admin');
      } catch (e) {
        this.isExporting = false;
        alert("Failed to trigger export.");
      } 
    },

    async exportPatientHistory() {
      this.isExporting = true;
      try {
        const res = await api.post('/routes/admin/export', { type: 'patient_history', patient_id: this.selectedPatient.id });
        this.startExportPolling(res.data.task_id, '/routes/admin');
      } catch (e) {
        this.isExporting = false;
        alert("Failed to trigger export.");
      } 
    },

    async exportPastAppointments() {
      this.isExporting = true;
      try {
        const res = await api.post('/routes/admin/export', { type: 'past_appointments' });
        this.startExportPolling(res.data.task_id, '/routes/admin');
      } catch (e) {
        this.isExporting = false;
        alert("Failed to trigger export.");
      } 
    }
  }
};
</script>