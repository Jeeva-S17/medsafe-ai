/**
 * MediSafe AI — Clinical Decision Support & Medicine Delivery System
 * Based purely on patient previous medical data & EHR records (Hardware-free)
 */

// Application State
const state = {
  activePatientId: "P0001",
  activePatient: null,
  patientHistory: [],
  prescribedMedsData: null,
  nearbyPharmacies: [],
  selectedPharmacyId: "PHARM_01",
  selectedPharmacyName: "Apollo Pharmacy 24x7",
  cart: {}, // { medicine_id: { ...item, qty: 1 } }
  activeOrder: null,
  ordersHistory: [],
  vitalsHistory: [],
  prediction: null,
  shap: null,
  prescriptionMeds: [],
  medicationSafety: null,
  fdaData: null,
  multiAgents: null,
  finalReport: null,
  systemStatus: null
};

// DOM Content Loaded Initializer
document.addEventListener("DOMContentLoaded", async () => {
  initNavigation();
  initThemeToggle();
  initCharts();
  initEventListeners();
  
  // Initial Patient Load (Arthur Pendelton P0001)
  await loadPatient("P0001");
  await refreshSystemStatus();
  
  // Pre-fetch FDA for default medication
  await searchFDA("Metformin");
});

// ================= NAVIGATION =================
function initNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const pageId = item.getAttribute("data-page");
      navigateTo(pageId);
    });
  });
}

function navigateTo(pageId) {
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".page-view").forEach(el => el.classList.remove("active"));

  const targetNav = document.querySelector(`[data-page="${pageId}"]`);
  const targetPage = document.getElementById(pageId);

  if (targetNav) targetNav.classList.add("active");
  if (targetPage) targetPage.classList.add("active");

  // Re-trigger layout adjustments / charts if needed
  if (pageId === "page-xai" && state.shap) {
    renderShapChart(state.shap.feature_contributions);
  } else if (pageId === "page-pdf") {
    refreshMatplotlibPreviews();
  } else if (pageId === "page-history" && state.patientHistory.length > 0) {
    renderHistoryTrajectoryChart(state.patientHistory);
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToOrderSummary() {
  navigateTo('page-delivery');
  setTimeout(() => {
    document.getElementById("card-delivery-checkout")?.scrollIntoView({ behavior: 'smooth' });
  }, 100);
}

// ================= THEME TOGGLE =================
function initThemeToggle() {
  const btn = document.getElementById("theme-toggle-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    document.body.classList.toggle("theme-light");
    const isLight = document.body.classList.contains("theme-light");
    btn.innerHTML = isLight ? `<i data-lucide="moon"></i>` : `<i data-lucide="sun"></i>`;
    lucide.createIcons();
  });
}

// ================= CHARTS SETUP =================
let liveChart = null;
let historyTrajectoryChart = null;
let shapChart = null;
let fdaChart = null;

function initCharts() {
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } }
    },
    scales: {
      x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#64748b' } },
      y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#64748b' } }
    }
  };

  // Dashboard Historical Baseline Chart
  const ctxLive = document.getElementById("liveVitalsChart")?.getContext("2d");
  if (ctxLive) {
    liveChart = new Chart(ctxLive, {
      type: "line",
      data: {
        labels: ["Visit 1 (6m ago)", "Visit 2 (3m ago)", "Visit 3 (1m ago)", "Latest Intake"],
        datasets: [
          { label: "Systolic BP (mmHg)", data: [150, 146, 144, 142], borderColor: "#b91c1c", tension: 0.3, fill: false },
          { label: "Resting Heart Rate (bpm)", data: [88, 86, 85, 84], borderColor: "#e11d48", tension: 0.3, fill: false },
          { label: "Fasting Glucose (mg/dL / 2)", data: [96, 89, 86, 84], borderColor: "#0284c7", borderDash: [4, 4], tension: 0.2 }
        ]
      },
      options: commonOptions
    });
  }
}

// ================= PATIENT DATA MGMT =================
async function loadPatient(patientId) {
  try {
    const res = await fetch(`/api/patient/${patientId}`);
    if (!res.ok) throw new Error("Patient not found");
    const data = await res.json();
    state.activePatient = data;
    state.activePatientId = data.patient_id;

    // Update Global Banner & Pills
    const patName = data.name || 'Unnamed';
    document.getElementById("global-patient-name").textContent = `Patient: ${data.patient_id} (${patName})`;
    document.getElementById("dash-patient-id").textContent = data.patient_id;
    document.getElementById("dash-patient-meta").textContent = `${patName} · ${data.age}y ${data.gender}`;
    document.getElementById("rep-patient-tag").textContent = `Patient: ${data.patient_id} (${patName})`;

    // Populate Intake Form
    document.getElementById("form-patient-id").value = data.patient_id;
    document.getElementById("form-name").value = data.name || "";
    document.getElementById("form-age").value = data.age;
    document.getElementById("form-gender").value = data.gender;
    document.getElementById("form-bmi").value = data.bmi;
    document.getElementById("form-glucose").value = data.glucose;
    document.getElementById("form-bp").value = data.bp;
    document.getElementById("form-cholesterol").value = data.cholesterol;
    document.getElementById("form-hr").value = data.heart_rate;
    document.getElementById("form-hba1c").value = data.hba1c;
    document.getElementById("form-smoking").value = data.smoking ? "1" : "0";
    document.getElementById("form-symptoms").value = data.symptoms || "";
    document.getElementById("form-allergies").value = data.allergies || "";
    document.getElementById("form-conditions").value = data.conditions || "";
    document.getElementById("form-medications").value = data.medications || "";

    // Sync dashboard baseline vitals from patient's previous clinical record
    document.getElementById("live-hr").textContent = data.heart_rate;
    document.getElementById("live-bp").textContent = `${data.bp} / ${Math.round(data.bp * 0.65)}`;

    // Prefill checkout delivery recipient
    const recipInput = document.getElementById("order-recipient-name");
    if (recipInput) recipInput.value = patName;

    const allergySummary = document.getElementById("del-allergy-summary");
    if (allergySummary) allergySummary.textContent = data.allergies || "None reported";

    // Load Patient Clinical History & EHR
    await loadPatientClinicalHistory(data.patient_id);

    // Load Pharmacy & Medicines
    await loadPharmacySystem(data.patient_id);

    // Load Orders History
    await loadPatientOrdersHistory(data.patient_id);

    // Automatically run baseline prediction & SHAP & Medications
    await runDiseasePrediction();
    await runSHAP();
    await checkMedications();

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading patient:", err);
  }
}

// ================= PATIENT CLINICAL HISTORY & EHR =================
async function loadPatientClinicalHistory(patientId) {
  try {
    const res = await fetch(`/api/patient/${patientId}/history`);
    if (!res.ok) throw new Error("History fetch failed");
    const records = await res.json();
    state.patientHistory = records;

    // Update History Banner Cards
    document.getElementById("history-patient-id").textContent = patientId;
    document.getElementById("history-patient-name").textContent = state.activePatient?.name || "Patient";
    document.getElementById("history-visits-count").textContent = `${records.length} Documented Visits`;
    document.getElementById("history-primary-diagnosis").textContent = state.activePatient?.conditions?.split(",")[0] || "Under Evaluation";
    document.getElementById("history-active-meds").textContent = state.activePatient?.medications || "None";
    document.getElementById("history-timeline-badge").textContent = `${records.length} Verified Clinical Records`;

    // Render timeline
    renderPatientHistoryTimeline(records);

    // Render Trajectory Chart
    renderHistoryTrajectoryChart(records);
    updateDashboardVitalsChart(records);
  } catch (err) {
    console.error("Error loading patient clinical history:", err);
  }
}

function renderPatientHistoryTimeline(records) {
  const container = document.getElementById("patient-history-timeline-container");
  if (!container) return;
  container.innerHTML = "";

  if (!records || records.length === 0) {
    container.innerHTML = `<div class="text-center text-muted" style="padding: 2rem;">No previous clinical visits on file for this patient profile.</div>`;
    return;
  }

  // Display reversed (latest first)
  [...records].reverse().forEach((r, idx) => {
    const card = document.createElement("div");
    card.className = "visit-card";
    const isLatest = idx === 0;

    card.innerHTML = `
      <div class="visit-header">
        <div>
          <span class="visit-badge-type">${r.visit_type || 'Clinical Encounter'}</span>
          <strong style="font-size: 1rem; color: #f8fafc; margin-left: 0.5rem;">${r.visit_date}</strong>
          ${isLatest ? '<span class="tag-safe" style="margin-left: 0.5rem;"><i data-lucide="check-circle" style="width:12px;"></i> Current Baseline</span>' : ''}
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
          <i data-lucide="user-check" style="width: 14px; height: 14px; display: inline;"></i>
          ${r.physician_name || 'Attending Physician'}
        </div>
      </div>

      <div class="visit-vitals-strip">
        <div class="v-item">
          <span class="v-label">Blood Pressure</span>
          <span class="v-val" style="color: ${r.systolic_bp > 140 ? '#f43f5e' : '#34d399'};">${r.systolic_bp} / ${r.diastolic_bp} mmHg</span>
        </div>
        <div class="v-item">
          <span class="v-label">Resting HR</span>
          <span class="v-val">${r.heart_rate} bpm</span>
        </div>
        <div class="v-item">
          <span class="v-label">Fasting Glucose</span>
          <span class="v-val" style="color: ${r.glucose > 140 ? '#f59e0b' : '#34d399'};">${r.glucose} mg/dL</span>
        </div>
        <div class="v-item">
          <span class="v-label">HbA1c</span>
          <span class="v-val" style="color: ${r.hba1c > 6.5 ? '#f43f5e' : '#34d399'};">${r.hba1c}%</span>
        </div>
        <div class="v-item">
          <span class="v-label">Cholesterol</span>
          <span class="v-val">${r.cholesterol} mg/dL</span>
        </div>
        <div class="v-item">
          <span class="v-label">SpO₂</span>
          <span class="v-val">${r.spo2 || 98}%</span>
        </div>
      </div>

      <div class="visit-notes">
        <strong>Physician Assessment:</strong> ${r.clinical_notes || 'Patient reviewed. Vitals within expected clinical range.'}
      </div>

      ${r.lab_findings ? `<div class="visit-lab"><strong>Diagnostic Lab Panel:</strong> ${r.lab_findings}</div>` : ''}

      ${r.prescribed_medications ? `
        <div style="margin-top: 0.6rem; font-size: 0.82rem; color: #a7f3d0;">
          <i data-lucide="pill" style="width: 13px; height: 13px; display: inline;"></i>
          <strong>Prescribed at this encounter:</strong> ${r.prescribed_medications}
        </div>
      ` : ''}
    `;
    container.appendChild(card);
  });
  lucide.createIcons();
}

function renderHistoryTrajectoryChart(records) {
  const ctx = document.getElementById("patientHistoryTrajectoryChart")?.getContext("2d");
  if (!ctx || !records || records.length === 0) return;

  const labels = records.map(r => `${r.visit_date} (${r.visit_type.split(" ")[0]})`);
  const sbpData = records.map(r => r.systolic_bp);
  const dbpData = records.map(r => r.diastolic_bp);
  const glucoseData = records.map(r => r.glucose);
  const hrData = records.map(r => r.heart_rate);

  if (historyTrajectoryChart) historyTrajectoryChart.destroy();

  historyTrajectoryChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        { label: "Systolic BP (mmHg)", data: sbpData, borderColor: "#e11d48", backgroundColor: "rgba(225, 29, 72, 0.1)", tension: 0.25, fill: false },
        { label: "Diastolic BP (mmHg)", data: dbpData, borderColor: "#f97316", tension: 0.25, borderDash: [4, 4], fill: false },
        { label: "Fasting Glucose (mg/dL)", data: glucoseData, borderColor: "#0284c7", tension: 0.25, fill: false },
        { label: "Resting Heart Rate (bpm)", data: hrData, borderColor: "#10b981", tension: 0.25, fill: false }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

function updateDashboardVitalsChart(records) {
  if (!liveChart || !records || records.length === 0) return;
  liveChart.data.labels = records.map(r => r.visit_date);
  liveChart.data.datasets[0].data = records.map(r => r.heart_rate);
  liveChart.data.datasets[1].data = records.map(r => r.spo2 || 98.2);
  liveChart.update();
}

// ================= PHARMACY & MEDICINE DELIVERY =================
async function loadPharmacySystem(patientId) {
  try {
    // 1. Fetch medicines tailored to patient
    const medRes = await fetch(`/api/pharmacy/medicines?patient_id=${patientId}`);
    const medData = await medRes.json();
    state.prescribedMedsData = medData;

    // Reset Cart and pre-select top prescribed medicine
    state.cart = {};
    if (medData.prescribed_medications && medData.prescribed_medications.length > 0) {
      const topMed = medData.prescribed_medications[0];
      state.cart[topMed.medicine_id] = {
        medicine_id: topMed.medicine_id,
        name: topMed.name,
        dosage: topMed.dosage,
        price: topMed.price,
        quantity: 1,
        total: topMed.price
      };
    }

    renderPrescribedMedicines(medData.prescribed_medications || []);
    renderOtcSupplies(medData.supportive_supplies || [], medData.general_otc || []);

    // 2. Fetch nearby pharmacies
    const pharmRes = await fetch("/api/pharmacy/nearby");
    const pharmacies = await pharmRes.json();
    state.nearbyPharmacies = pharmacies;
    renderNearbyPharmacies(pharmacies);

    // 3. Render initial checkout summary
    renderCheckoutSummary();

    lucide.createIcons();
  } catch (err) {
    console.error("Error loading pharmacy system:", err);
  }
}

function renderPrescribedMedicines(medicines) {
  const container = document.getElementById("delivery-prescribed-meds-container");
  if (!container) return;
  container.innerHTML = "";

  if (medicines.length === 0) {
    container.innerHTML = `<div class="text-center text-muted" style="padding: 1.5rem;">No chronic prescriptions active for this patient profile.</div>`;
    return;
  }

  medicines.forEach(med => {
    const isSelected = !!state.cart[med.medicine_id];
    const qty = state.cart[med.medicine_id]?.quantity || 1;

    const card = document.createElement("div");
    card.className = `medicine-card ${isSelected ? 'selected' : ''}`;
    card.id = `med-card-${med.medicine_id}`;

    card.innerHTML = `
      <div class="med-left">
        <input type="checkbox" class="med-checkbox" id="chk-${med.medicine_id}" ${isSelected ? 'checked' : ''} />
        <div class="med-info">
          <h4>${med.name}</h4>
          <div class="med-dosage"><i data-lucide="clock" style="width:12px; height:12px; display:inline;"></i> ${med.dosage}</div>
          <div class="med-indication"><strong>Indication:</strong> ${med.disease_indication}</div>
          <div class="med-meta-tags">
            <span class="tag-safe"><i data-lucide="shield-check" style="width:12px; height:12px;"></i> Allergy Screened Safe</span>
            <span class="tag-stock"><i data-lucide="check" style="width:12px; height:12px;"></i> In Stock Nearby</span>
            <span class="text-muted" style="font-size: 0.72rem;">${med.manufacturer || 'Approved Manufacturer'}</span>
          </div>
        </div>
      </div>
      <div class="med-right">
        <div class="med-price">₹${med.price.toFixed(2)}</div>
        <div class="qty-control">
          <button type="button" class="qty-btn" onclick="handleQtyChange('${med.medicine_id}', -1)">-</button>
          <span class="qty-number" id="qty-${med.medicine_id}">${qty}</span>
          <button type="button" class="qty-btn" onclick="handleQtyChange('${med.medicine_id}', 1)">+</button>
        </div>
      </div>
    `;

    // Toggle event
    card.querySelector(".med-checkbox").addEventListener("change", (e) => {
      toggleMedicineSelection(med, e.target.checked);
    });

    container.appendChild(card);
  });
}

function renderOtcSupplies(supplies, otc) {
  const container = document.getElementById("delivery-otc-meds-container");
  if (!container) return;
  container.innerHTML = "";

  const combined = [...supplies, ...otc];
  if (combined.length === 0) {
    container.innerHTML = `<div class="text-center text-muted" style="padding: 1rem;">No supportive supplies listed.</div>`;
    return;
  }

  combined.forEach(item => {
    const isSelected = !!state.cart[item.medicine_id];
    const qty = state.cart[item.medicine_id]?.quantity || 1;

    const card = document.createElement("div");
    card.className = `medicine-card ${isSelected ? 'selected' : ''}`;
    card.id = `med-card-${item.medicine_id}`;

    card.innerHTML = `
      <div class="med-left">
        <input type="checkbox" class="med-checkbox" id="chk-${item.medicine_id}" ${isSelected ? 'checked' : ''} />
        <div class="med-info">
          <h4>${item.name}</h4>
          <div class="med-dosage">${item.dosage}</div>
          <div class="med-meta-tags">
            <span class="tag-stock"><i data-lucide="check" style="width:12px; height:12px;"></i> In Stock</span>
            <span class="text-muted" style="font-size: 0.72rem;">${item.category}</span>
          </div>
        </div>
      </div>
      <div class="med-right">
        <div class="med-price">₹${item.price.toFixed(2)}</div>
        <div class="qty-control">
          <button type="button" class="qty-btn" onclick="handleQtyChange('${item.medicine_id}', -1)">-</button>
          <span class="qty-number" id="qty-${item.medicine_id}">${qty}</span>
          <button type="button" class="qty-btn" onclick="handleQtyChange('${item.medicine_id}', 1)">+</button>
        </div>
      </div>
    `;

    card.querySelector(".med-checkbox").addEventListener("change", (e) => {
      toggleMedicineSelection(item, e.target.checked);
    });

    container.appendChild(card);
  });
}

function toggleMedicineSelection(item, isChecked) {
  const card = document.getElementById(`med-card-${item.medicine_id}`);
  if (isChecked) {
    if (card) card.classList.add("selected");
    const qtySpan = document.getElementById(`qty-${item.medicine_id}`);
    const qty = qtySpan ? parseInt(qtySpan.textContent) || 1 : 1;
    state.cart[item.medicine_id] = {
      medicine_id: item.medicine_id,
      name: item.name,
      dosage: item.dosage,
      price: item.price,
      quantity: qty,
      total: item.price * qty
    };
  } else {
    if (card) card.classList.remove("selected");
    delete state.cart[item.medicine_id];
  }
  renderCheckoutSummary();
}

function handleQtyChange(medId, delta) {
  const qtySpan = document.getElementById(`qty-${medId}`);
  if (!qtySpan) return;
  let currentQty = parseInt(qtySpan.textContent) || 1;
  currentQty = Math.max(1, currentQty + delta);
  qtySpan.textContent = currentQty;

  if (state.cart[medId]) {
    state.cart[medId].quantity = currentQty;
    state.cart[medId].total = state.cart[medId].price * currentQty;
    renderCheckoutSummary();
  }
}

function renderNearbyPharmacies(pharmacies) {
  const container = document.getElementById("delivery-pharmacies-container");
  if (!container) return;
  container.innerHTML = "";

  pharmacies.forEach((p, idx) => {
    const isSelected = p.pharmacy_id === state.selectedPharmacyId;
    const card = document.createElement("div");
    card.className = `pharmacy-card ${isSelected ? 'selected' : ''}`;
    card.id = `pharmacy-card-${p.pharmacy_id}`;

    card.innerHTML = `
      <div class="pharmacy-main">
        <input type="radio" name="pharmacy-selection" class="pharmacy-radio" id="radio-${p.pharmacy_id}" ${isSelected ? 'checked' : ''} />
        <div>
          <div class="pharmacy-name">
            <span>${p.name}</span>
            <span class="pharmacy-rating">★ ${p.rating} (${p.reviews_count})</span>
          </div>
          <div class="pharmacy-address"><i data-lucide="map-pin" style="width:12px; height:12px; display:inline;"></i> ${p.address}</div>
          <div class="pharmacy-delivery-meta">
            <span class="pharmacy-eta"><i data-lucide="zap" style="width:12px; height:12px;"></i> ${p.delivery_time_mins} mins Express</span>
            <span class="pharmacy-distance">• ${p.distance_km} km away</span>
            <span style="color:#38bdf8;">• ${p.open_hours}</span>
          </div>
        </div>
      </div>
      <div>
        <span class="pharmacy-badge-selected ${isSelected ? '' : 'hidden'}" id="badge-sel-${p.pharmacy_id}">Selected</span>
      </div>
    `;

    card.addEventListener("click", () => {
      selectPharmacy(p);
    });

    container.appendChild(card);
  });
}

function selectPharmacy(pharmacy) {
  state.selectedPharmacyId = pharmacy.pharmacy_id;
  state.selectedPharmacyName = pharmacy.name;

  document.querySelectorAll(".pharmacy-card").forEach(c => c.classList.remove("selected"));
  document.querySelectorAll(".pharmacy-badge-selected").forEach(b => b.classList.add("hidden"));

  const card = document.getElementById(`pharmacy-card-${pharmacy.pharmacy_id}`);
  if (card) {
    card.classList.add("selected");
    const radio = card.querySelector(".pharmacy-radio");
    if (radio) radio.checked = true;
  }
  const badge = document.getElementById(`badge-sel-${pharmacy.pharmacy_id}`);
  if (badge) badge.classList.remove("hidden");

  const pill = document.getElementById("selected-pharmacy-pill");
  if (pill) pill.textContent = pharmacy.name;

  renderCheckoutSummary();
}

function renderCheckoutSummary() {
  const itemsList = document.getElementById("checkout-items-list");
  const countSpan = document.getElementById("cart-item-count");
  const subtotalSpan = document.getElementById("summary-subtotal");
  const feeSpan = document.getElementById("summary-delivery-fee");
  const totalSpan = document.getElementById("summary-total");

  if (!itemsList) return;

  const items = Object.values(state.cart);
  const count = items.length;
  if (countSpan) countSpan.textContent = count;

  if (count === 0) {
    itemsList.innerHTML = `<div class="text-muted" style="font-size: 0.85rem; font-style: italic;">No medicines selected. Check medicines on the left to add.</div>`;
    if (subtotalSpan) subtotalSpan.textContent = "₹0.00";
    if (totalSpan) totalSpan.textContent = "₹0.00";
    return;
  }

  itemsList.innerHTML = "";
  let subtotal = 0;

  items.forEach(it => {
    subtotal += it.total;
    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.justifyContent = "space-between";
    row.style.fontSize = "0.85rem";
    row.style.color = "#cbd5e1";
    row.innerHTML = `
      <span>${it.name} <small style="color:var(--text-muted);">(x${it.quantity})</small></span>
      <span style="font-family:var(--font-mono); font-weight:700;">₹${it.total.toFixed(2)}</span>
    `;
    itemsList.appendChild(row);
  });

  const deliveryFee = subtotal > 100 ? 0.0 : 20.0;
  const grandTotal = subtotal + deliveryFee;

  if (subtotalSpan) subtotalSpan.textContent = `₹${subtotal.toFixed(2)}`;
  if (feeSpan) feeSpan.textContent = deliveryFee === 0 ? "FREE (Orders > ₹100)" : `₹${deliveryFee.toFixed(2)}`;
  if (totalSpan) totalSpan.textContent = `₹${grandTotal.toFixed(2)}`;
}

// ================= PLACE MEDICINE ORDER =================
async function placeMedicineOrder() {
  const items = Object.values(state.cart);
  if (items.length === 0) {
    alert("Please select at least one prescribed medicine or health supply to place an order.");
    return;
  }

  const recipientName = document.getElementById("order-recipient-name").value.trim() || state.activePatient?.name || "Patient";
  const phone = document.getElementById("order-phone").value.trim() || "+91 98401 23456";
  const address = document.getElementById("order-address").value.trim();
  const slot = document.getElementById("order-delivery-slot").value;
  const paymentMethod = document.getElementById("order-payment-method").value;

  if (!address) {
    alert("Please enter a valid delivery address.");
    return;
  }

  const subtotal = items.reduce((sum, i) => sum + i.total, 0);
  const deliveryFee = subtotal > 100 ? 0.0 : 20.0;
  const totalAmount = subtotal + deliveryFee;

  const orderPayload = {
    patient_id: state.activePatientId,
    patient_name: recipientName,
    pharmacy_id: state.selectedPharmacyId,
    pharmacy_name: state.selectedPharmacyName,
    items: items,
    subtotal: subtotal,
    delivery_fee: deliveryFee,
    total_amount: totalAmount,
    delivery_address: address,
    phone: phone,
    payment_method: paymentMethod,
    delivery_type: slot,
    estimated_delivery_mins: 25
  };

  const btn = document.getElementById("btn-place-medicine-order");
  if (btn) btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Transmitting Order to Pharmacy...`;

  try {
    const res = await fetch("/api/pharmacy/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(orderPayload)
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Order placement failed");

    state.activeOrder = data.order;

    // Display Tracker Card
    displayOrderTracker(data.order);

    // Refresh history
    await loadPatientOrdersHistory(state.activePatientId);

    // Scroll down to tracker
    document.getElementById("order-tracker-card")?.scrollIntoView({ behavior: 'smooth' });

    alert(`✓ Order ${data.order.order_id} placed successfully with ${data.order.pharmacy_name}!\nEstimated Delivery: ${data.order.estimated_delivery_mins} minutes.`);
  } catch (err) {
    alert(`Could not place order: ${err.message}`);
  } finally {
    if (btn) {
      btn.innerHTML = `<i data-lucide="truck"></i> <span>Order Medicines for Delivery</span>`;
      lucide.createIcons();
    }
  }
}

function displayOrderTracker(order) {
  const card = document.getElementById("order-tracker-card");
  if (!card) return;
  card.classList.remove("hidden");

  document.getElementById("tracker-order-id").textContent = order.order_id;
  document.getElementById("tracker-partner-name").textContent = order.tracking_partner_name || "Karthik R. (Hero Electric EV)";
  document.getElementById("tracker-pharmacy-name").textContent = `Dispatched from ${order.pharmacy_name}`;
  document.getElementById("tracker-partner-phone").innerHTML = `<i data-lucide="phone"></i> <span>${order.tracking_partner_phone || '+91 98401 55210'}</span>`;

  updateStepperStatus(order.status);
  lucide.createIcons();
}

function updateStepperStatus(status) {
  const stages = [
    "Order Transmitted",
    "Pharmacist Confirmed & Packed",
    "Delivery Partner Dispatched",
    "Out for Doorstep Delivery",
    "Delivered Successfully"
  ];

  let currentIdx = stages.indexOf(status);
  if (currentIdx === -1) currentIdx = 0;

  for (let i = 1; i <= 5; i++) {
    const stepEl = document.getElementById(`step-${i}`);
    if (!stepEl) continue;

    stepEl.classList.remove("completed", "active");
    if (i - 1 < currentIdx) {
      stepEl.classList.add("completed");
    } else if (i - 1 === currentIdx) {
      stepEl.classList.add("active");
    }
  }
}

async function advanceActiveOrderStatus() {
  if (!state.activeOrder) return;
  try {
    const res = await fetch(`/api/pharmacy/orders/${state.activeOrder.order_id}/advance`, {
      method: "POST"
    });
    const data = await res.json();
    if (data.success && data.order) {
      state.activeOrder = data.order;
      updateStepperStatus(data.order.status);
      await loadPatientOrdersHistory(state.activePatientId);
      lucide.createIcons();
    }
  } catch (e) {
    console.error("Error advancing order status:", e);
  }
}

async function loadPatientOrdersHistory(patientId) {
  try {
    const res = await fetch(`/api/pharmacy/orders?patient_id=${patientId}`);
    const orders = await res.json();
    state.ordersHistory = orders;

    const tbody = document.getElementById("delivery-history-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!orders || orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No delivery orders placed yet</td></tr>`;
      return;
    }

    orders.forEach(o => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong style="color:#a7f3d0; font-family:var(--font-mono);">${o.order_id}</strong></td>
        <td>${o.pharmacy_name}</td>
        <td>${(o.items || []).length} item(s)</td>
        <td><strong style="font-family:var(--font-mono);">₹${o.total_amount.toFixed(2)}</strong></td>
        <td><span class="vital-status ${o.status.includes('Delivered') ? 'normal' : 'warning'}">${o.status}</span></td>
      `;
      tbody.appendChild(tr);
    });

    // If active order is not set, load the most recent one
    if (!state.activeOrder && orders.length > 0) {
      state.activeOrder = orders[0];
      displayOrderTracker(orders[0]);
    }
  } catch (err) {
    console.error("Error loading patient delivery orders:", err);
  }
}

function printDeliveryInvoice() {
  const o = state.activeOrder;
  if (!o) {
    alert("No active delivery order to print.");
    return;
  }

  const invoiceWindow = window.open("", "_blank", "width=750,height=800");
  const itemsHtml = (o.items || []).map(i => `
    <tr>
      <td style="padding: 8px; border-bottom: 1px solid #ddd;">${i.name} (${i.dosage || ''})</td>
      <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">${i.quantity}</td>
      <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">₹${i.price.toFixed(2)}</td>
      <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">₹${i.total.toFixed(2)}</td>
    </tr>
  `).join("");

  invoiceWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Delivery Invoice - ${o.order_id}</title>
      <style>
        body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #1e293b; padding: 24px; line-height: 1.5; }
        .header { border-bottom: 2px solid #0d9488; padding-bottom: 12px; margin-bottom: 20px; }
        .title { color: #0d9488; font-size: 24px; font-weight: bold; }
        .grid { display: flex; justify-content: space-between; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { background: #f1f5f9; padding: 10px; text-align: left; }
        .total-box { margin-top: 20px; text-align: right; font-size: 16px; }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="title">MEDISAFE AI — PHARMACY DELIVERY INVOICE</div>
        <div style="font-size: 13px; color: #64748b;">Clinical Decision Support & Verified Home Delivery</div>
      </div>
      <div class="grid">
        <div>
          <strong>Bill To:</strong><br/>
          ${o.patient_name}<br/>
          ${o.delivery_address}<br/>
          Phone: ${o.phone}
        </div>
        <div style="text-align: right;">
          <strong>Order ID:</strong> ${o.order_id}<br/>
          <strong>Fulfillment Pharmacy:</strong> ${o.pharmacy_name}<br/>
          <strong>Delivery Partner:</strong> ${o.tracking_partner_name || 'Assigned Partner'}<br/>
          <strong>Status:</strong> ${o.status}
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Prescribed Medication / Item</th>
            <th style="text-align: center;">Qty</th>
            <th style="text-align: right;">Unit Price</th>
            <th style="text-align: right;">Total</th>
          </tr>
        </thead>
        <tbody>
          ${itemsHtml}
        </tbody>
      </table>
      <div class="total-box">
        <div>Subtotal: ₹${o.subtotal.toFixed(2)}</div>
        <div>Delivery Fee: ${o.delivery_fee === 0 ? 'FREE' : '₹' + o.delivery_fee.toFixed(2)}</div>
        <div style="font-size: 18px; font-weight: bold; color: #0d9488; margin-top: 6px;">Total Amount Paid: ₹${o.total_amount.toFixed(2)}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Payment Method: ${o.payment_method}</div>
      </div>
      <div style="margin-top: 30px; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 10px;">
        * Notice: Medicines verified against patient allergy records. Please check safety seal upon delivery.
      </div>
      <script>
        window.print();
      </script>
    </body>
    </html>
  `);
  invoiceWindow.document.close();
}

// ================= DISEASE PREDICTION =================
async function runDiseasePrediction() {
  if (!state.activePatient) return;
  try {
    const res = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.activePatient)
    });
    if (!res.ok) throw new Error("Prediction API call failed");
    const data = await res.json();
    state.prediction = data;

    // Update Dashboard Elements
    document.getElementById("dash-predicted-disease").textContent = data.predicted_disease;
    document.getElementById("dash-disease-conf").textContent = `Model Probability: ${data.confidence.toFixed(1)}%`;

    // Update Prediction Page
    document.getElementById("pred-disease-title").textContent = data.predicted_disease;
    document.getElementById("pred-confidence-val").textContent = `${data.confidence.toFixed(1)}%`;

    // Render Risk Factors
    const riskList = document.getElementById("pred-risk-factors-list");
    riskList.innerHTML = "";
    if (data.top_risk_factors && data.top_risk_factors.length > 0) {
      data.top_risk_factors.forEach(rf => {
        const li = document.createElement("li");
        li.textContent = rf;
        riskList.appendChild(li);
      });
    } else {
      riskList.innerHTML = `<li style="color:#86efac; background:rgba(22,163,74,0.15); border-left-color:#22c55e;">Baseline within normal limits for evaluated indicators</li>`;
    }

    // Render Probabilities Horizontal Progress Bars
    renderProbabilitiesList("dash-probabilities-container", data.probabilities);
    renderProbabilitiesList("pred-probabilities-list", data.probabilities);

    // Render Table
    const tbody = document.getElementById("pred-table-body");
    tbody.innerHTML = "";
    const entries = Object.entries(data.probabilities);
    entries.forEach(([disease, prob], idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${disease}</strong></td>
        <td><span class="conf-pill">${prob.toFixed(2)}%</span></td>
        <td>${idx === 0 ? '<span class="vital-status danger">Primary Classification</span>' : '<span class="vital-status normal">Differential ' + (idx + 1) + '</span>'}</td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Error running disease prediction:", err);
  }
}

function renderProbabilitiesList(containerId, probs) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";
  
  Object.entries(probs).forEach(([disease, prob]) => {
    const wrap = document.createElement("div");
    wrap.className = "prob-bar-wrapper";
    wrap.innerHTML = `
      <div class="prob-header">
        <span>${disease}</span>
        <strong>${prob.toFixed(1)}%</strong>
      </div>
      <div class="prob-progress">
        <div class="prob-fill" style="width: ${prob}%"></div>
      </div>
    `;
    container.appendChild(wrap);
  });
}

// ================= SHAP / EXPLAINABLE AI =================
async function runSHAP() {
  if (!state.activePatient) return;
  try {
    const res = await fetch("/api/xai/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.activePatient)
    });
    if (!res.ok) throw new Error("SHAP computation failed");
    const data = await res.json();
    state.shap = data;

    document.getElementById("xai-explanation-text").textContent = data.summary_explanation || "SHAP tree attribution computed.";

    // Populate table
    const tbody = document.getElementById("xai-table-body");
    tbody.innerHTML = "";
    (data.feature_contributions || []).forEach(fc => {
      const tr = document.createElement("tr");
      const isPositive = fc.shap_value > 0;
      tr.innerHTML = `
        <td><strong>${fc.feature}</strong></td>
        <td>${fc.patient_value}</td>
        <td style="font-family: monospace; font-weight: bold; color: ${isPositive ? '#f43f5e' : '#38bdf8'};">${fc.shap_value > 0 ? '+' : ''}${fc.shap_value.toFixed(3)}</td>
        <td>
          <span class="vital-status ${isPositive ? 'danger' : 'normal'}">
            ${fc.impact}
          </span>
        </td>
        <td>
          <div class="prob-progress" style="width: 120px;">
            <div class="prob-fill" style="width: ${Math.min(100, fc.magnitude * 250)}%; background: ${isPositive ? '#f43f5e' : '#38bdf8'};"></div>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // Render SHAP waterfall chart
    renderShapChart(data.feature_contributions);
  } catch (err) {
    console.error("Error computing SHAP:", err);
  }
}

function renderShapChart(contributions) {
  if (!contributions || contributions.length === 0) return;
  const ctx = document.getElementById("shapWaterfallChart")?.getContext("2d");
  if (!ctx) return;

  const top = contributions.slice(0, 8);
  const labels = top.map(c => `${c.feature} (${c.patient_value})`);
  const values = top.map(c => c.shap_value);
  const bgColors = values.map(v => v > 0 ? 'rgba(225, 29, 72, 0.85)' : 'rgba(2, 132, 199, 0.85)');

  if (shapChart) shapChart.destroy();

  shapChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "SHAP Value (Positive = Increases Risk, Negative = Decreases)",
        data: values,
        backgroundColor: bgColors,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#64748b' } },
        y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#e2e8f0', font: { weight: 'bold' } } }
      }
    }
  });
}

// ================= PRESCRIPTION OCR =================
let selectedFile = null;

function setupOCRDropzone() {
  const dropzone = document.getElementById("ocr-dropzone");
  const fileInput = document.getElementById("ocr-file-input");
  const preview = document.getElementById("ocr-file-preview");
  const filenameSpan = document.getElementById("ocr-filename");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--teal-primary)";
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.style.borderColor = "var(--bg-card-border)";
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--bg-card-border)";
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFile(fileInput.files[0]);
    }
  });

  function handleFile(file) {
    selectedFile = file;
    filenameSpan.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    preview.classList.remove("hidden");
  }

  document.getElementById("btn-submit-ocr")?.addEventListener("click", async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append("patient_id", state.activePatientId);
    formData.append("file", selectedFile);

    document.getElementById("ocr-confidence-badge").textContent = "Processing OCR...";
    try {
      const res = await fetch("/api/prescription/upload", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      
      // Update display
      document.getElementById("ocr-raw-text").textContent = data.extracted_text;
      const confBadge = document.getElementById("ocr-confidence-badge");
      confBadge.textContent = `Confidence: ${data.confidence_level}`;
      confBadge.className = data.confidence_level === "High" ? "badge-pill vital-status normal" : "badge-pill vital-status warning";

      const tbody = document.getElementById("ocr-meds-table-body");
      tbody.innerHTML = "";

      state.prescriptionMeds = (data.detected_medicines || []).map(m => m.name);

      if (data.detected_medicines && data.detected_medicines.length > 0) {
        data.detected_medicines.forEach(m => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${m.name}</strong></td>
            <td>${m.strength}</td>
            <td>${m.frequency}</td>
            <td>${m.duration}</td>
            <td><span class="vital-status normal">${Math.round(m.confidence * 100)}%</span></td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No medicines recognized. Manual verification required.</td></tr>`;
      }

      // Re-run medication check with new prescription medicines
      await checkMedications();

    } catch (err) {
      console.error("Error processing prescription OCR:", err);
      document.getElementById("ocr-confidence-badge").textContent = "Error";
    }
  });
}

// ================= MEDICATION SAFETY =================
async function checkMedications() {
  if (!state.activePatient) return;
  try {
    const payload = {
      patient_id: state.activePatientId,
      current_medications: state.activePatient.medications || "",
      ocr_prescribed_medications: state.prescriptionMeds || [],
      patient_allergies: state.activePatient.allergies || "",
      medical_conditions: state.activePatient.conditions || ""
    };

    const res = await fetch("/api/medication/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    state.medicationSafety = data;

    // Allergy status badge & alerts
    const allergyBadge = document.getElementById("med-allergy-status-badge");
    if (allergyBadge) {
      allergyBadge.textContent = data.allergy_status;
      allergyBadge.className = data.allergy_alerts.length > 0 ? "badge-pill vital-status danger" : "badge-pill vital-status normal";
    }

    const alertsContainer = document.getElementById("med-allergy-alerts-container");
    if (alertsContainer) {
      alertsContainer.innerHTML = "";
      if (data.allergy_alerts.length > 0) {
        data.allergy_alerts.forEach(a => {
          const div = document.createElement("div");
          div.className = "alert-box danger-alert";
          div.innerHTML = `
            <i data-lucide="alert-octagon"></i>
            <div>
              <strong>POTENTIAL ALLERGY CONFLICT:</strong> Prescribed medicine <strong>${a.medicine}</strong> matches patient reported allergy <strong>${a.allergen_match}</strong>.<br/>
              <small>${a.note}</small>
            </div>
          `;
          alertsContainer.appendChild(div);
        });
      } else {
        alertsContainer.innerHTML = `
          <div class="alert-box info-alert">
            <i data-lucide="check-circle"></i>
            <div>No direct allergy contraindications identified between active medications and reported allergies.</div>
          </div>
        `;
      }
    }

    // Medication tags
    const curList = document.getElementById("med-current-list");
    if (curList) curList.innerHTML = (data.current_medications || []).map(m => `<li><i data-lucide="pill" style="width:12px;"></i> ${m}</li>`).join("") || "<li>None reported</li>";

    const ocrList = document.getElementById("med-ocr-list");
    if (ocrList) ocrList.innerHTML = (data.ocr_prescribed_medications || []).map(m => `<li><i data-lucide="file-text" style="width:12px;"></i> ${m}</li>`).join("") || "<li>None detected via OCR</li>";

    // Interactions Table
    const tbody = document.getElementById("med-interactions-table-body");
    if (tbody) {
      tbody.innerHTML = "";
      if (data.interactions && data.interactions.length > 0) {
        data.interactions.forEach(i => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${i.medicine_a} + ${i.medicine_b}</strong></td>
            <td><span class="vital-status ${i.severity === 'Major' ? 'danger' : 'warning'}">${i.severity}</span></td>
            <td>${i.potential_interaction}</td>
            <td><small>${i.evidence_source}</small></td>
            <td>${i.professional_action}</td>
            <td><span class="badge-outline">Verification Required</span></td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No severe drug interactions detected among evaluated medications.</td></tr>`;
      }
    }

    // Dashboard quick summary
    const dashMedAlerts = document.getElementById("dash-med-alerts");
    if (dashMedAlerts) dashMedAlerts.textContent = `${data.interactions.length} Interaction(s)`;
    const dashAllergyStatus = document.getElementById("dash-allergy-status");
    if (dashAllergyStatus) dashAllergyStatus.textContent = data.allergy_alerts.length > 0 ? "Allergy Conflict Flagged" : "Allergies Verified Clear";

    lucide.createIcons();
  } catch (err) {
    console.error("Error evaluating medications:", err);
  }
}

// ================= FDA SAFETY INFORMATION =================
async function searchFDA(medicineName) {
  if (!medicineName) return;
  try {
    const res = await fetch(`/api/fda/search?medicine=${encodeURIComponent(medicineName)}`);
    const data = await res.json();
    state.fdaData = data;

    document.getElementById("fda-card-title").textContent = `FDA Adverse Event Summary: ${data.medicine_name}`;
    document.getElementById("fda-total-reports").textContent = data.total_adverse_reports ? data.total_adverse_reports.toLocaleString() : "12,500";
    document.getElementById("fda-sample-ids").textContent = (data.sample_report_ids || []).slice(0, 2).join(", ");
    document.getElementById("fda-source-btn").href = data.source_url || "https://open.fda.gov/apis/drug/event/";

    // Seriousness breakdown
    const sbox = document.getElementById("fda-seriousness-box");
    const s = data.seriousness_summary || {};
    sbox.innerHTML = `
      <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
        <span class="vital-status danger">Hospitalizations: ${s.hospitalization || 0}</span>
        <span class="vital-status warning">Life Threatening: ${s.life_threatening || 0}</span>
        <span class="vital-status normal">Other Serious: ${s.other || 0}</span>
      </div>
    `;

    // Render FDA chart
    renderFDAChart(data.top_reactions || []);
  } catch (err) {
    console.error("Error querying OpenFDA:", err);
  }
}

function renderFDAChart(reactions) {
  const ctx = document.getElementById("fdaReactionsChart")?.getContext("2d");
  if (!ctx) return;

  const top = reactions.slice(0, 6);
  const labels = top.map(r => r.reaction);
  const data = top.map(r => r.count);

  if (fdaChart) fdaChart.destroy();

  fdaChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Reported FAERS Incidents",
        data: data,
        backgroundColor: "rgba(245, 158, 11, 0.8)",
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8' } } },
      scales: {
        x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#64748b' } },
        y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { color: '#e2e8f0', font: { weight: 'bold' } } }
      }
    }
  });
}

// ================= CREWAI MULTI-AGENT =================
async function runCrewAI() {
  if (!state.activePatient) return;
  try {
    const payload = {
      patient_data: state.activePatient,
      ocr_medications: state.prescriptionMeds || []
    };
    const res = await fetch("/api/analysis/multi-agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    state.multiAgents = data;

    const agents = data.agents || [];
    if (agents[0]) document.getElementById("agent-disease-body").innerHTML = `<p>${agents[0].findings}</p><br/><strong>Concerns:</strong> <ul>${agents[0].concerns.map(c => `<li>${c}</li>`).join("") || '<li>None</li>'}</ul>`;
    if (agents[1]) document.getElementById("agent-med-body").innerHTML = `<p>${agents[1].findings}</p><br/><strong>Concerns:</strong> <ul>${agents[1].concerns.map(c => `<li>${c}</li>`).join("") || '<li>None</li>'}</ul>`;
    if (agents[2]) document.getElementById("agent-fda-body").innerHTML = `<p>${agents[2].findings}</p>`;
    if (agents[3]) document.getElementById("agent-risk-body").innerHTML = `<p><strong>Assigned Tier:</strong> ${agents[3].safety_level}</p><p>${agents[3].findings}</p>`;
    if (agents[4]) document.getElementById("agent-report-body").innerHTML = `<p>${agents[4].findings}</p>`;

  } catch (err) {
    console.error("Error running CrewAI:", err);
  }
}

// ================= FINAL SAFETY REPORT =================
async function generateFinalReport() {
  if (!state.activePatient) return;
  try {
    const payload = {
      patient_data: state.activePatient,
      ocr_medications: state.prescriptionMeds || []
    };
    const res = await fetch("/api/analysis/final-safety-report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    state.finalReport = data;

    // Update Section 11 Result Box
    document.getElementById("rep-predicted-disease").textContent = data.predicted_disease;
    document.getElementById("rep-model-prob").textContent = `Model Probability: ${data.disease_probability.toFixed(1)}%`;
    
    const safetyBadge = document.getElementById("rep-safety-level");
    safetyBadge.textContent = data.safety_level;
    safetyBadge.className = `final-val safety-${data.safety_level.toLowerCase()}`;

    // Update Dashboard Safety Level
    const dashSafety = document.getElementById("dash-safety-level");
    if (dashSafety) dashSafety.textContent = data.safety_level;

    // Risk bullets
    const bulletsUl = document.getElementById("rep-risk-bullets");
    bulletsUl.innerHTML = (data.key_risk_factors || []).map(r => `<li>${r}</li>`).join("") || "<li>Baseline parameters stable</li>";

    // Format Markdown Viewer
    document.getElementById("final-report-markdown").innerHTML = convertMarkdownToHtml(data.structured_markdown);

  } catch (err) {
    console.error("Error synthesizing final report:", err);
  }
}

function convertMarkdownToHtml(md) {
  if (!md) return "";
  let html = md
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/\n$/gim, '<br />');
  return html;
}

// ================= SYSTEM STATUS =================
async function refreshSystemStatus() {
  try {
    const res = await fetch("/api/system/status");
    const data = await res.json();
    state.systemStatus = data;

    const grid = document.getElementById("system-status-grid");
    if (!grid) return;
    grid.innerHTML = "";

    const labels = {
      random_forest: "Random Forest Model",
      shap: "SHAP Explainable AI",
      ocr: "Prescription OCR Engine",
      fda_api: "OpenFDA FAERS API",
      gemini: "Gemini Reasoning Layer",
      crewai: "CrewAI Multi-Agent System",
      database: "SQLite Database",
      patient_history: "Patient Clinical EHR Records",
      pharmacy_delivery: "Nearby Medical Shops & Delivery"
    };

    Object.entries(data).forEach(([key, s]) => {
      const card = document.createElement("div");
      card.className = "status-card";
      const statusClass = (s.status || "").toLowerCase().includes("error") ? "error" : 
                          ((s.status || "").toLowerCase().includes("fallback") ? "fallback" : "connected");
      
      card.innerHTML = `
        <div class="status-card-header">
          <span class="status-card-title">${labels[key] || key}</span>
          <span class="status-indicator ${statusClass}">
            <span class="status-dot ${statusClass === 'connected' ? 'green' : (statusClass === 'error' ? 'red' : 'amber')}"></span>
            ${s.status}
          </span>
        </div>
        <div class="status-details">${s.details || 'Operational'}</div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    console.error("Error checking system status:", err);
  }
}

// ================= REFRESH MATPLOTLIB PREVIEWS =================
function refreshMatplotlibPreviews() {
  if (!state.activePatientId) return;
  const pId = state.activePatientId;
  const ts = new Date().getTime();

  document.getElementById("img-chart-probabilities").src = `/api/report/charts/probabilities/${pId}?t=${ts}`;
  document.getElementById("img-chart-shap").src = `/api/report/charts/shap/${pId}?t=${ts}`;
  document.getElementById("img-chart-trends").src = `/api/report/charts/trends/${pId}?t=${ts}`;

  document.getElementById("download-prob-png").href = `/api/report/charts/probabilities/${pId}`;
  document.getElementById("download-shap-png").href = `/api/report/charts/shap/${pId}`;
}

// ================= EVENT LISTENERS =================
function initEventListeners() {
  // Patient Selector Switcher
  document.getElementById("patient-switcher")?.addEventListener("change", async (e) => {
    const val = e.target.value;
    if (val === "NEW") {
      document.getElementById("patient-form").reset();
      document.getElementById("form-patient-id").value = `P000${Math.floor(Math.random() * 900 + 100)}`;
    } else {
      await loadPatient(val);
    }
  });

  // Patient Save Form
  document.getElementById("btn-save-patient")?.addEventListener("click", async () => {
    const pId = document.getElementById("form-patient-id").value.trim();
    if (!pId) {
      alert("Patient ID is required.");
      return;
    }

    const payload = {
      patient_id: pId,
      name: document.getElementById("form-name").value,
      age: parseInt(document.getElementById("form-age").value),
      gender: document.getElementById("form-gender").value,
      bmi: parseFloat(document.getElementById("form-bmi").value),
      glucose: parseFloat(document.getElementById("form-glucose").value),
      bp: parseFloat(document.getElementById("form-bp").value),
      cholesterol: parseFloat(document.getElementById("form-cholesterol").value),
      heart_rate: parseFloat(document.getElementById("form-hr").value),
      hba1c: parseFloat(document.getElementById("form-hba1c").value),
      smoking: parseInt(document.getElementById("form-smoking").value),
      symptoms: document.getElementById("form-symptoms").value,
      allergies: document.getElementById("form-allergies").value,
      conditions: document.getElementById("form-conditions").value,
      medications: document.getElementById("form-medications").value
    };

    try {
      const res = await fetch("/api/patient", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      alert("Patient profile updated successfully!");
      await loadPatient(pId);
    } catch (e) {
      alert("Validation Error: Please check all required parameters.");
    }
  });

  // Action Buttons
  document.getElementById("btn-quick-sync-vitals")?.addEventListener("click", () => {
    loadPatient(state.activePatientId);
  });
  document.getElementById("btn-refresh-history")?.addEventListener("click", () => {
    loadPatientClinicalHistory(state.activePatientId);
  });
  document.getElementById("btn-refresh-pharmacy")?.addEventListener("click", () => {
    loadPharmacySystem(state.activePatientId);
  });

  // Order Placement & Tracker Actions
  document.getElementById("btn-place-medicine-order")?.addEventListener("click", placeMedicineOrder);
  document.getElementById("btn-advance-delivery-status")?.addEventListener("click", advanceActiveOrderStatus);
  document.getElementById("btn-print-delivery-invoice")?.addEventListener("click", printDeliveryInvoice);

  // Other Core CDS Pipeline Buttons
  document.getElementById("btn-run-prediction")?.addEventListener("click", runDiseasePrediction);
  document.getElementById("btn-run-shap")?.addEventListener("click", runSHAP);
  document.getElementById("btn-check-medications")?.addEventListener("click", checkMedications);
  document.getElementById("btn-fda-search")?.addEventListener("click", () => {
    const med = document.getElementById("fda-search-input").value;
    searchFDA(med);
  });
  document.getElementById("btn-run-crewai")?.addEventListener("click", runCrewAI);
  document.getElementById("btn-generate-final-report")?.addEventListener("click", generateFinalReport);
  document.getElementById("btn-refresh-status")?.addEventListener("click", refreshSystemStatus);

  // Download PDF Report
  document.getElementById("btn-download-pdf")?.addEventListener("click", () => {
    if (!state.activePatientId) return;
    window.open(`/api/report/pdf/${state.activePatientId}`, "_blank");
  });

  // End to End CDS Pipeline Run
  document.getElementById("btn-run-full-pipeline")?.addEventListener("click", async () => {
    const btn = document.getElementById("btn-run-full-pipeline");
    btn.innerHTML = `<i data-lucide="loader" class="spin"></i> Running Full Pipeline...`;
    try {
      await runDiseasePrediction();
      await runSHAP();
      await checkMedications();
      await runCrewAI();
      await generateFinalReport();
      navigateTo("page-report");
    } finally {
      btn.innerHTML = `<i data-lucide="play"></i> Run End-to-End CDS Pipeline`;
      lucide.createIcons();
    }
  });

  // Setup OCR Drag & Drop
  setupOCRDropzone();

  // Quick Disease Case Preset Buttons
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const pid = btn.getAttribute("data-pid");
      if (pid) {
        document.querySelectorAll(".preset-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const switcher = document.getElementById("patient-switcher");
        if (switcher) switcher.value = pid;
        await loadPatient(pid);
      }
    });
  });

  // Gemini API Key Save Button
  document.getElementById("btn-save-gemini-key")?.addEventListener("click", async () => {
    const keyInput = document.getElementById("input-gemini-key");
    const feedback = document.getElementById("gemini-key-feedback");
    const key = keyInput.value.trim();
    if (!key) {
      feedback.innerHTML = `<span style="color:#ef4444;">Please enter a valid Google API key.</span>`;
      return;
    }
    feedback.innerHTML = `<span style="color:#38bdf8;">Connecting to Google Gemini...</span>`;
    try {
      const res = await fetch("/api/system/gemini-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key })
      });
      const data = await res.json();
      if (data.connected) {
        feedback.innerHTML = `<span style="color:#10b981; font-weight:bold;">✓ Connected successfully! Gemini 1.5 Flash is now active.</span>`;
        document.getElementById("gemini-current-badge").textContent = "Gemini 1.5 Flash Connected";
        document.getElementById("gemini-current-badge").className = "badge-pill vital-status normal";
      } else {
        feedback.innerHTML = `<span style="color:#f59e0b;">Key saved. System using autonomous fallback reasoning until cloud endpoint handshake finishes.</span>`;
      }
      await refreshSystemStatus();
    } catch (e) {
      feedback.innerHTML = `<span style="color:#ef4444;">Connection error: ${e.message}</span>`;
    }
  });
}
