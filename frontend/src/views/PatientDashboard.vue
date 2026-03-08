<template>
  <div class="container my-4">
    <h3 class="mb-4">Patient Dashboard</h3>

    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'appointments' }" @click="activeTab = 'appointments'; loadAppointments()">My Appointments</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'doctors' }" @click="activeTab = 'doctors'; loadDoctors()">Find a Doctor & Book</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'; loadHistory()">Treatment History</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">My Profile</button>
      </li>
    </ul>

    <div v-if="activeTab === 'appointments'">
      
      <h5 class="mb-3 text-primary">Upcoming & Pending Appointments</h5>
      <div v-if="upcomingAppointments.length === 0" class="alert alert-light border text-muted">No upcoming appointments.</div>
      
      <div class="row mb-4">
        <div class="col-md-6 mb-3" v-for="a in upcomingAppointments" :key="a.id">
          <div class="card shadow-sm h-100 border-primary">
            <div class="card-body">
              <h5 class="card-title">Dr. {{ a.doctor_name }}</h5>
              <h6 class="card-subtitle mb-3 text-muted">{{ a.specialization }}</h6>
              <p class="mb-1"><strong>Date & Time:</strong> {{ formatIST(a.scheduled_at) }}</p>
              <p class="mb-1 text-muted" v-if="a.reason"><strong>Reason for visit:</strong> {{ a.reason }}</p>
              
              <span class="badge mt-2" :class="isPast(a.scheduled_at) ? 'bg-warning text-dark border border-warning' : 'bg-primary'">
                {{ isPast(a.scheduled_at) ? 'PENDING DOCTOR UPDATE' : 'UPCOMING' }}
              </span>
            </div>
            <div class="card-footer bg-transparent border-0 pb-3">
              <button class="btn btn-sm btn-outline-danger w-100" @click="cancelAppointment(a.id)">Cancel Appointment</button>
            </div>
          </div>
        </div>
      </div>

      <h5 class="mb-3 text-secondary">Past & Recent Appointments</h5>
      <div v-if="pastAppointments.length === 0" class="alert alert-light border text-muted">No past appointments.</div>
      
      <div class="row">
        <div class="col-md-6 mb-3" v-for="a in pastAppointments" :key="a.id">
          <div class="card shadow-sm h-100 bg-light">
            <div class="card-body opacity-75">
              <h5 class="card-title">Dr. {{ a.doctor_name }}</h5>
              <h6 class="card-subtitle mb-3 text-muted">{{ a.specialization }}</h6>
              <p class="mb-1"><strong>Date & Time:</strong> {{ formatIST(a.scheduled_at) }}</p>
              <p class="mb-1 text-muted" v-if="a.reason"><strong>Reason for visit:</strong> {{ a.reason }}</p>
              
              <span class="badge mt-2" :class="a.status === 'completed' ? 'bg-success' : 'bg-danger'">
                {{ a.status.toUpperCase() }}
              </span>
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-if="activeTab === 'doctors'">
      
      <div class="mb-4">
        <h5>Filter by Department</h5>
        <div class="d-flex flex-wrap gap-2 mt-2">
          <button 
            class="btn btn-sm rounded-pill px-3"
            :class="selectedDepartment === '' ? 'btn-primary shadow-sm' : 'btn-outline-secondary'"
            @click="selectedDepartment = ''"
          >
            All Departments
          </button>
          
          <button 
            v-for="dept in uniqueDepartments" 
            :key="dept"
            class="btn btn-sm rounded-pill px-3"
            :class="selectedDepartment === dept ? 'btn-primary shadow-sm' : 'btn-outline-primary'"
            @click="selectedDepartment = dept"
          >
            {{ dept }}
          </button>
        </div>
      </div>

      <div class="mb-4">
        <input 
          type="text" 
          v-model="searchQuery" 
          class="form-control form-control-lg bg-light border-0 shadow-sm" 
          placeholder="🔍 Search doctors by name or specialization..." 
        />
      </div>

      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Doctor Directory & Availability (Next 7 Days)</h5>
      </div>
      
      <div v-if="filteredDoctors.length === 0" class="alert alert-info border-0 shadow-sm">
        No doctors found matching your selected filters.
      </div>

      <div class="card shadow-sm mb-3 border-0" v-for="doc in filteredDoctors" :key="doc.id">
        <div class="card-header bg-white border-bottom-0 pt-3 pb-0 d-flex justify-content-between align-items-center">
          <div>
            <h5 class="mb-0 text-primary">Dr. {{ doc.name }}</h5>
            <small class="text-muted fw-bold">{{ doc.department }}</small>
            <small class="text-muted ms-2">• {{ doc.specialization }}</small>
            <div class="small mt-1 text-secondary"><i>Qualifications: {{ doc.qualifications }}</i></div>
          </div>
        </div>
        
        <div class="card-body">
          <hr class="mt-0">
          <h6 class="mb-3">Available Time Slots</h6>
          
          <div v-if="Object.keys(doc.filtered_slots).length === 0" class="text-muted small">
            No upcoming slots currently available for this doctor.
          </div>

          <div v-else v-for="(slots, date) in doc.filtered_slots" :key="date" class="mb-3">
            <strong class="d-block mb-2">{{ new Date(date).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric', timeZone: 'Asia/Kolkata' }) }}</strong>
            <div class="d-flex flex-wrap gap-2">
              <button 
                v-for="time in slots" 
                :key="time" 
                class="btn btn-sm px-3"
                :class="isSlotBooked(doc, date, time) ? 'btn-light text-muted text-decoration-line-through cursor-not-allowed border' : 'btn-outline-success fw-bold'"
                @click="openBookingModal(doc, date, time)"
                :disabled="bookingInProgress || isSlotBooked(doc, date, time)"
              >
                {{ time }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'history'">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5>Treatment History & Prescriptions</h5>
        <button class="btn btn-sm btn-outline-secondary" @click="exportCSV" :disabled="exporting">
          {{ exporting ? 'Exporting...' : 'Export to CSV' }}
        </button>
      </div>

      <div v-if="history.length === 0" class="alert alert-info">No treatment history available yet.</div>

      <div class="card shadow-sm mb-3" v-for="record in history" :key="record.id">
        <div class="card-body">
          <h6 class="text-primary mb-1">{{ formatIST(record.date) }} - Treated by Dr. {{ record.doctor_name }}</h6>
          <hr>
          <p><strong>Diagnosis:</strong> {{ record.diagnosis || 'None recorded' }}</p>
          
          <strong>Prescription:</strong>
          <ul v-if="record.prescription && Object.keys(record.prescription).length > 0">
            <li v-for="(val, key) in record.prescription" :key="key">{{ key }}: {{ val }}</li>
          </ul>
          <p class="text-muted" v-else>No medications prescribed.</p>
          
          <div v-if="record.notes" class="mt-2 text-muted small"><strong>Notes:</strong> {{ record.notes }}</div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'profile'">
      <PatientProfile @updated="loadProfile" />
    </div>

    <div ref="bookingModalEl" class="modal fade" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Appointment</h5>
            <button type="button" class="btn-close" @click="closeBookingModal"></button>
          </div>
          <div class="modal-body" v-if="selectedBooking">
            <p>Are you sure you want to book an appointment with <strong>Dr. {{ selectedBooking.doctor.name }}</strong>?</p>
            <div class="bg-light p-3 rounded mb-3">
              <p class="mb-1"><strong>Date:</strong> {{ new Date(selectedBooking.date).toLocaleDateString('en-IN', { weekday: 'long', month: 'long', day: 'numeric', timeZone: 'Asia/Kolkata' }) }}</p>
              <p class="mb-0"><strong>Time:</strong> {{ selectedBooking.time }}</p>
            </div>
            
            <div class="mb-3">
              <label class="form-label fw-bold">Reason for Visit (Optional)</label>
              <textarea 
                v-model="bookingReason" 
                class="form-control" 
                rows="2" 
                placeholder="Briefly describe your symptoms or reason for visit..."
              ></textarea>
            </div>
            
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeBookingModal">Cancel</button>
            <button type="button" class="btn btn-primary" @click="confirmBooking" :disabled="bookingInProgress">
              <span v-if="bookingInProgress" class="spinner-border spinner-border-sm me-2"></span>
              Confirm Booking
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/services/api';
import PatientProfile from '@/views/PatientProfile.vue';
import { Modal } from 'bootstrap'; 

export default {
  name: 'PatientDashboard',
  components: { PatientProfile },
  data() {
    return {
      activeTab: 'appointments',
      appointments: [],
      doctors: [],
      history: [],
      exporting: false,
      bookingInProgress: false,
      searchQuery: '',
      selectedDepartment: '', // NEW: Tracks the selected department filter
      
      bookingModalInstance: null,
      selectedBooking: null,
      bookingReason: '' 
    };
  },
  computed: {
    upcomingAppointments() {
      return this.appointments.filter(a => this.isFuture(a.scheduled_at) && a.status === 'booked');
    },
    pastAppointments() {
      return this.appointments.filter(a => !this.isFuture(a.scheduled_at) || a.status !== 'booked');
    },
    uniqueSpecializations() {
      const specs = this.doctors.map(d => d.specialization);
      return [...new Set(specs)].filter(s => s !== 'General' && s !== '');
    },
    // NEW: Extracts unique departments dynamically
    uniqueDepartments() {
      const depts = this.doctors.map(d => d.department);
      return [...new Set(depts)].filter(d => d && d !== 'General' && d !== '');
    },
    // UPDATED: Filters by both department button and search text
    filteredDoctors() {
      let result = this.doctors;

      // 1. Filter by clicked Department Button
      if (this.selectedDepartment) {
        result = result.filter(doc => doc.department === this.selectedDepartment);
      }

      // 2. Filter by Search Query
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(doc => {
          const docName = (doc.name || '').toLowerCase();
          const docDept = (doc.department || '').toLowerCase();
          const docSpec = (doc.specialization || '').toLowerCase();
          return docName.includes(query) || docDept.includes(query) || docSpec.includes(query);
        });
      }

      return result;
    }
  },
  mounted() {
    this.loadAppointments();
    this.loadDoctors(); 
    
    if (this.$refs.bookingModalEl) {
      this.bookingModalInstance = new Modal(this.$refs.bookingModalEl, { backdrop: true, keyboard: true });
    }
  },
  beforeUnmount() {
    if (this.bookingModalInstance) {
      this.bookingModalInstance.dispose();
      this.bookingModalInstance = null;
    }
  },
  methods: {
    isPast(dateString) {
      if (!dateString) return false;
      return new Date(dateString) < new Date();
    },
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

    isSlotBooked(doc, date, time) {
      return doc.bookedMap && doc.bookedMap[date] && doc.bookedMap[date].includes(time);
    },

    async loadAppointments() {
      try {
        const res = await api.get('/routes/patient/appointments');
        this.appointments = res.data || [];
      } catch (e) {
        this.appointments = [];
      }
    },
    async loadDoctors() {
      try {
        const res = await api.get('/routes/patient/doctors');
        const docs = res.data || [];

        const now = new Date();
        const dateFormatter = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' });
        const todayIST = dateFormatter.format(now); 
        
        const timeFormatter = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false });
        const currentTimeIST = timeFormatter.format(now); 

        this.doctors = docs.map(doc => {
          const bookedMap = {};
          if (doc.booked_slots) {
            doc.booked_slots.forEach(isoString => {
              const safeIso = (isoString.endsWith('Z') || isoString.includes('+')) ? isoString : isoString + 'Z';
              const d = new Date(safeIso);
              
              const bDate = dateFormatter.format(d);
              
              const rawTime = timeFormatter.format(d);
              const bTime = rawTime.replace(/[^0-9:]/g, ''); 
              
              if (!bookedMap[bDate]) bookedMap[bDate] = [];
              bookedMap[bDate].push(bTime);
            });
          }
          doc.bookedMap = bookedMap; 

          const validSlots = {};
          if (doc.available_slots) {
            for (const [date, times] of Object.entries(doc.available_slots)) {
              if (date < todayIST) {
                continue; 
              }
              if (date === todayIST) {
                const futureTimes = times.filter(t => t > currentTimeIST);
                if (futureTimes.length > 0) {
                  validSlots[date] = futureTimes.sort();
                }
              } 
              else {
                validSlots[date] = [...times].sort();
              }
            }
          }
          doc.filtered_slots = validSlots;
          return doc;
        });

      } catch (e) {
        this.doctors = [];
      }
    },
    async loadHistory() {
      try {
        const res = await api.get('/routes/patient/history');
        this.history = res.data || [];
      } catch (e) {
        this.history = [];
      }
    },
    
    openBookingModal(doctor, date, time) {
      this.selectedBooking = { doctor, date, time };
      if (this.bookingModalInstance) {
        this.bookingModalInstance.show();
      }
    },
    
    closeBookingModal() {
      if (this.bookingModalInstance) {
        this.bookingModalInstance.hide();
      }
      setTimeout(() => {
        this.selectedBooking = null;
        this.bookingReason = ''; 
      }, 300); 
    },
    
    async confirmBooking() {
      if (!this.selectedBooking) return;
      
      this.bookingInProgress = true;
      try {
        const { doctor, date, time } = this.selectedBooking;
        const isoDateTime = new Date(`${date}T${time}:00+05:30`).toISOString();
        
        await api.post('/routes/patient/appointments', {
          doctor_id: doctor.id,
          scheduled_at: isoDateTime,
          reason: this.bookingReason 
        });
        
        alert('Appointment booked successfully!');
        this.closeBookingModal(); 
        this.activeTab = 'appointments';
        this.loadAppointments();
        this.loadDoctors(); 
        
      } catch (e) {
        alert(e.response?.data?.msg || 'Failed to book slot. It may have been taken.');
      } finally {
        this.bookingInProgress = false;
      }
    },
    
    async cancelAppointment(id) {
      if (!confirm('Are you sure you want to cancel this appointment?')) return;
      try {
        await api.delete(`/routes/patient/appointments/${id}`);
        this.loadAppointments();
        this.loadDoctors(); 
      } catch (e) {
        alert(e.response?.data?.msg || 'Cancel failed');
      }
    },
    async exportCSV() {
      this.exporting = true;
      try {
        // 1. Trigger the export and get the Task ID
        const res = await api.post('/routes/patient/export', {});
        const taskId = res.data.task_id;

        // 2. Start polling the backend every 2 seconds (2000ms)
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await api.get(`/routes/patient/export/status/${taskId}`);
            
            if (statusRes.data.state === 'SUCCESS') {
              clearInterval(pollInterval); // Stop polling!
              
              const filepath = statusRes.data.filepath;
              
              // 3. Fetch the actual file data securely with your JWT token using the taskId
              const downloadRes = await api.get(`/routes/patient/export/download/${taskId}`, {
                responseType: 'blob' // CRITICAL: Tells Axios we are downloading a file, not JSON
              });

              // 4. Force the browser to save it locally
              const url = window.URL.createObjectURL(new Blob([downloadRes.data]));
              const link = document.createElement('a');
              link.href = url;
              
              // Extract the filename from the path to name the download
              const filename = filepath.split('/').pop().split('\\').pop(); 
              link.setAttribute('download', filename);
              
              document.body.appendChild(link);
              link.click();
              link.remove();
              
              this.exporting = false;
              alert('Download complete!');
              
            } else if (statusRes.data.state === 'FAILURE') {
              clearInterval(pollInterval);
              this.exporting = false;
              alert('Export failed on the server.');
            }
            // If state is PENDING or STARTED, it just loops and asks again.
            
          } catch (err) {
            clearInterval(pollInterval);
            this.exporting = false;
            alert('Lost connection to export status.');
          }
        }, 2000);

      } catch (e) {
        this.exporting = false;
        alert('Failed to start export.');
      }
    },
    loadProfile() {
      // Stub
    }
  }
};
</script>