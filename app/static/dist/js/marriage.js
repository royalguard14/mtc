  document.addEventListener("DOMContentLoaded", function () {
    function setupLocation(provinceId, municipalityId, barangayId = null) {
      const province = document.getElementById(provinceId);
      const municipality = document.getElementById(municipalityId);
      const barangay = barangayId ? document.getElementById(barangayId) : null;
    if (!province || !municipality) return; // prevent crash
    province.addEventListener('change', function () {
      if (!this.value) return;
      fetch(`/marriages/get_municipalities/${this.value}`)
      .then(res => res.json())
      .then(data => {
        municipality.innerHTML = '<option value="">Select Municipality</option>';
        if (barangay) {
          barangay.innerHTML = '<option value="">Select Barangay</option>';
        }
        data.forEach(m => {
          municipality.innerHTML +=
        `<option value="${m.id}">${m.name}</option>`;
      });
      });
    });
    if (barangay) {
      municipality.addEventListener('change', function () {
        if (!this.value) return;
        fetch(`/marriages/get_barangays/${this.value}`)
        .then(res => res.json())
        .then(data => {
          barangay.innerHTML = '<option value="">Select Barangay</option>';
          data.forEach(b => {
            barangay.innerHTML +=
          `<option value="${b.id}">${b.name}</option>`;
        });
        });
      });
    }
  }
  setupLocation('h_recudence_province','h_recudence_city','h_recudence_brgy');
  setupLocation('h_pob_province','h_pob_city');
  setupLocation('w_pob_province','w_pob_city');
  setupLocation('w_recudence_province','w_recudence_city','w_recudence_brgy');
  setupLocation('w_guardian_province','w_guardian_city');
  setupLocation('h_guardian_province','h_guardian_city');
  setupLocation('pom_province','pom_city');
});


 // --------------------
// Residence: Country Select
// --------------------
  function setupForeignResidence(countryId, localFieldsId, foreignFieldsId, localSelectIds = []) {
    const countryEl = document.getElementById(countryId);
    const localFields = document.getElementById(localFieldsId);
    const foreignFields = document.getElementById(foreignFieldsId);
    const toggle = () => {
      const country = countryEl.value.trim().toLowerCase();
      if (country !== 'philippines') {
      // Disable local selects
        localSelectIds.forEach(id => document.getElementById(id).disabled = true);
        foreignFields.style.display = 'flex';
        localFields.style.display = 'none';
      } else {
        localSelectIds.forEach(id => document.getElementById(id).disabled = false);
        foreignFields.style.display = 'none';
        localFields.style.display = 'flex';
      }
    };
    countryEl.addEventListener('change', toggle);
  toggle(); // run once on page load
}
// --------------------
// Place of Birth: Checkbox
// --------------------
function setupForeignPOB(checkboxId, localFieldsId, foreignFieldsId) {
  const checkboxEl = document.getElementById(checkboxId);
  const localFields = document.getElementById(localFieldsId);
  const foreignFields = document.getElementById(foreignFieldsId);
  const toggle = () => {
    if (checkboxEl.checked) {
      localFields.style.display = 'none';
      foreignFields.style.display = 'block';
    } else {
      localFields.style.display = 'block';
      foreignFields.style.display = 'none';
    }
  };
  checkboxEl.addEventListener('change', toggle);
  toggle(); // run once on page load
}
// --------------------
// Initialize
// --------------------
// Husband Residence
setupForeignResidence(
  'h_recudence_country',
  'h_recudence_local_fields',
  'h_recudence_foreign_fields',
  ['h_recudence_province', 'h_recudence_city', 'h_recudence_brgy']
  );
// Wife Residence
setupForeignResidence(
  'w_recudence_country',
  'w_recudence_local_fields',
  'w_recudence_foreign_fields',
  ['w_recudence_province', 'w_recudence_city', 'w_recudence_brgy']
  );
// Husband Place of Birth
setupForeignPOB('h_pob_foreign', 'h_pob_local', 'h_pob_foreign_fields');
// Wife Place of Birth
setupForeignPOB('w_pob_foreign', 'w_pob_local', 'w_pob_foreign_fields');


  const requiredFields = [
  // =================== HUSBAND ===================
    'h_firstname', 'h_lastname',
    'h_dob', 'h_sex', 'h_citizenship', 'h_religion', 'h_civilstatus',
    'h_pob_province', 'h_pob_city',
    'h_recudence_city', 'h_recudence_province',
    'h_father_firstname', 'h_father_lastname', 'h_father_citizenship',
    'h_mother_firstname', 'h_mother_lastname', 'h_mother_citizenship',
  // =================== WIFE ===================
    'w_firstname', 'w_lastname',
    'w_dob', 'w_sex', 'w_citizenship', 'w_religion', 'w_civilstatus',
    'w_pob_province', 'w_pob_city',
    'w_recudence_city', 'w_recudence_province',
    'w_father_firstname', 'w_father_lastname', 'w_father_citizenship',
    'w_mother_firstname', 'w_mother_lastname', 'w_mother_citizenship',
  // =================== PLACE OF MARRIAGE ===================
    'pom_mosque', 'pom_province', 'pom_city',
    'dom_date', 'tom',
  // =================== WITNESSES ===================
    'witness1', 'witness2'
  ];
  document.getElementById('saveBtn').addEventListener('click', function () {
  // ================= VALIDATION =================
    let allFilled = true;
    requiredFields.forEach(id => {
      const field = document.getElementById(id);
      if (!field) return;
      if (field.value.trim() === '') {
        allFilled = false;
        field.classList.add('is-invalid');
      } else {
        field.classList.remove('is-invalid');
      }
    });
    if (!allFilled) {
      alert('Please fill all required fields before submitting.');
      return;
    }
  // ================= DATE SPLITTING =================
    const hDob = document.getElementById('h_dob').value.split('-');
    const wDob = document.getElementById('w_dob').value.split('-');
    const domDate = document.getElementById('dom_date').value.split('-');
  // ================= RESIDENCE =================
    const hCountry = document.getElementById('h_recudence_country')?.value || '';
    const wCountry = document.getElementById('w_recudence_country')?.value || '';
    const h_recudence_province = document.getElementById('h_recudence_province')?.value || '';
    const h_recudence_city = document.getElementById('h_recudence_city')?.value || '';
    const w_recudence_province = document.getElementById('w_recudence_province')?.value || '';
    const w_recudence_city = document.getElementById('w_recudence_city')?.value || '';
  // ================= POB =================
    const hPobForeign = document.getElementById('h_pob_foreign')?.checked || false;
    const wPobForeign = document.getElementById('w_pob_foreign')?.checked || false;
    const h_pob_city = hPobForeign
    ? document.getElementById('h_pob_city_foreign')?.value || ''
    : document.getElementById('h_pob_city')?.value || '';
    const h_pob_province = hPobForeign
    ? document.getElementById('h_pob_province_foreign')?.value || ''
    : document.getElementById('h_pob_province')?.value || '';
    const h_pob_country = hPobForeign
    ? document.getElementById('h_pob_country_foreign')?.value || ''
    : 'Philippines';
    const w_pob_city = wPobForeign
    ? document.getElementById('w_pob_city_foreign')?.value || ''
    : document.getElementById('w_pob_city')?.value || '';
    const w_pob_province = wPobForeign
    ? document.getElementById('w_pob_province_foreign')?.value || ''
    : document.getElementById('w_pob_province')?.value || '';
    const w_pob_country = wPobForeign
    ? document.getElementById('w_pob_country_foreign')?.value || ''
    : 'Philippines';
  // ================= DATA OBJECT =================
    const data = {
    // Husband
      h_firstname: document.getElementById('h_firstname').value,
      h_midlename: document.getElementById('h_midlename').value,
      h_lastname: document.getElementById('h_lastname').value,
      h_dob_day: hDob[2],
      h_bod_month: hDob[1],
      h_bod_year: hDob[0],
      h_sex: document.getElementById('h_sex').value,
      h_citizenship: document.getElementById('h_citizenship').value,
      h_religion: document.getElementById('h_religion').value,
      h_civilstatus: document.getElementById('h_civilstatus').value,
      h_pob_city,
      h_pob_province,
      h_pob_country,
      h_recidence_house_street: document.getElementById('h_recidence_house_street').value,
      h_recudence_city,
      h_recudence_province,
      h_recudence_country: hCountry,
      h_father_firstname: document.getElementById('h_father_firstname').value,
      h_father_lastname: document.getElementById('h_father_lastname').value,
      h_father_citizenship: document.getElementById('h_father_citizenship').value,
      h_mother_firstname: document.getElementById('h_mother_firstname').value,
      h_mother_lastname: document.getElementById('h_mother_lastname').value,
      h_mother_citizenship: document.getElementById('h_mother_citizenship').value,
    // Wife
      w_firstname: document.getElementById('w_firstname').value,
      w_midlename: document.getElementById('w_midlename').value,
      w_lastname: document.getElementById('w_lastname').value,
      w_dob_day: wDob[2],
      w_bod_month: wDob[1],
      w_bod_year: wDob[0],
      w_sex: document.getElementById('w_sex').value,
      w_citizenship: document.getElementById('w_citizenship').value,
      w_religion: document.getElementById('w_religion').value,
      w_civilstatus: document.getElementById('w_civilstatus').value,
      w_pob_city,
      w_pob_province,
      w_pob_country,
      w_recidence_house_street: document.getElementById('w_recidence_house_street').value,
      w_recudence_city,
      w_recudence_province,
      w_recudence_country: wCountry,
      w_father_firstname: document.getElementById('w_father_firstname').value,
      w_father_lastname: document.getElementById('w_father_lastname').value,
      w_father_citizenship: document.getElementById('w_father_citizenship').value,
      w_mother_firstname: document.getElementById('w_mother_firstname').value,
      w_mother_lastname: document.getElementById('w_mother_lastname').value,
      w_mother_citizenship: document.getElementById('w_mother_citizenship').value,
    // Marriage
      pom_mosque: document.getElementById('pom_mosque').value,
      pom_province: document.getElementById('pom_province').value,
      pom_city: document.getElementById('pom_city').value,
      dom_day: domDate[2],
      dom_month: domDate[1],
      dom_year: domDate[0],
      tom: document.getElementById('tom').value,
    // Witnesses
      witness1: document.getElementById('witness1').value,
      witness2: document.getElementById('witness2').value,
      witness3: document.getElementById('witness3')?.value || '',
      witness4: document.getElementById('witness4')?.value || '',
    // Officer
      solemnizing_officer_id: document.getElementById('solemnizing_officer_id')?.value || null
    };
  // ================= AJAX =================
    fetch("{{ url_for('marriages.create') }}", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(resp => {
      if (resp.success) {
        alert('Marriage record created successfully!');
        location.reload();
      } else {
        alert('Error: ' + resp.message);
      }
    })
    .catch(err => {
      console.error(err);
      alert('Unexpected error occurred.');
    });
  });
