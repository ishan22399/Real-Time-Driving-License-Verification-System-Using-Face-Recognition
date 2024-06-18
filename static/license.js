// Array of Indian states
const indianStates = [
    'Andhra Pradesh',
    'Arunachal Pradesh',
    'Assam',
    'Bihar',
    'Chhattisgarh',
    'Goa',
    'Gujarat',
    'Haryana',
    'Himachal Pradesh',
    'Jharkhand',
    'Karnataka',
    'Kerala',
    'Madhya Pradesh',
    'Maharashtra',
    'Manipur',
    'Meghalaya',
    'Mizoram',
    'Nagaland',
    'Odisha',
    'Punjab',
    'Rajasthan',
    'Sikkim',
    'Tamil Nadu',
    'Telangana',
    'Tripura',
    'Uttar Pradesh',
    'Uttarakhand',
    'West Bengal'
];

// Get the select element for states
const stateSelect = document.getElementById("state");

// Populate the state dropdown with options
indianStates.forEach((state) => {
    const option = document.createElement("option");
    option.text = state;
    stateSelect.add(option);
});

document.getElementById("licenseForm").addEventListener("submit", function(event) {
    event.preventDefault();

    // Get form input values
    const name = document.getElementById("name").value;
    const dob = document.getElementById("dob").value;
    const state = document.getElementById("state").value;
    const country = document.getElementById("country").value;
    const district = document.getElementById("district").value;
    const city = document.getElementById("city").value;
    const addressLine = document.getElementById("addressLine").value;
    const landmark = document.getElementById("landmark").value;
    const licenseNumber = document.getElementById("licenseNumber").value;
    const dateOfIssue = document.getElementById("dateOfIssue").value;
    const issuingAuthority = document.getElementById("issuingAuthority").value;
    const validTill = document.getElementById("validTill").value;
    const cov = document.getElementById("cov").value;

    // Check if any required fields are empty
    if (!name || !dob || !state || !country || !district || !city || !addressLine || !landmark || !licenseNumber || !dateOfIssue || !issuingAuthority || !validTill || !cov) {
        alert("Please fill in all required fields.");
        return;
    }

    // Prepare the form data to send to the server (you can use FormData for file upload)
    const formData = new FormData();
    formData.append("name", name);
    formData.append("dob", dob);
    formData.append("state", state);
    formData.append("country", country);
    formData.append("district", district);
    formData.append("city", city);
    formData.append("addressLine", addressLine);
    formData.append("landmark", landmark);
    formData.append("licenseNumber", licenseNumber);
    formData.append("dateOfIssue", dateOfIssue);
    formData.append("issuingAuthority", issuingAuthority);
    formData.append("validTill", validTill);
    formData.append("cov", cov);
    // Append the license image file (you'll need to add the input file element with an ID)
    formData.append("licenseImage", document.getElementById("licenseImage").files[0]);

    // Perform AJAX request to send data to the server
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/submit", true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            alert("Data is successfully recorded.");
            // Optionally, reset the form after successful submission
            document.getElementById("licenseForm").reset();
        } else {
            alert("Failed to submit data. Please try again.");
        }
    };

    xhr.send(formData);
});


// Create a data structure with states and their issuing authorities
const statesWithIssuingAuthorities = [
    {
        state: 'Andhra Pradesh',
        authorities: [
            { city: 'Hyderabad', code: 'AP-HYD-01' },
            { city: 'Visakhapatnam', code: 'AP-VSKP-02' },
            { city: 'Guntur', code: 'AP-GNT-03' },
            { city: 'Vijayawada', code: 'AP-VJA-04' },
            { city: 'Tirupati', code: 'AP-TPT-05' },
            { city: 'Kurnool', code: 'AP-KNL-06' },
            { city: 'Nellore', code: 'AP-NLR-07' },
            { city: 'Anantapur', code: 'AP-ATP-08' },
            { city: 'Kakinada', code: 'AP-KKD-09' },
            { city: 'Rajahmundry', code: 'AP-RJY-10' },
            { city: 'Warangal', code: 'AP-WGL-11' },
            { city: 'Karimnagar', code: 'AP-KRMG-12' },
            { city: 'Nizamabad', code: 'AP-NZB-13' },
            { city: 'Kadapa', code: 'AP-KDP-14' },
            { city: 'Ongole', code: 'AP-ONG-15' },
            { city: 'Hindupur', code: 'AP-HNP-16' },
            { city: 'Tenali', code: 'AP-TEN-17' },
            { city: 'Chittoor', code: 'AP-CTT-18' },
            { city: 'Srikakulam', code: 'AP-SKL-19' },
            { city: 'Proddatur', code: 'AP-PRDT-20' },
            { city: 'Eluru', code: 'AP-ELR-21' },
            { city: 'Vizianagaram', code: 'AP-VZM-22' },
            { city: 'Adoni', code: 'AP-ADN-23' },
            { city: 'Nandyal', code: 'AP-NDY-24' },
            { city: 'Machilipatnam', code: 'AP-MKM-25' },
            { city: 'Srikalahasti', code: 'AP-SKH-26' },
            { city: 'Bhimavaram', code: 'AP-BVRM-27' },
            { city: 'Kavali', code: 'AP-KVL-28' },
            { city: 'Chirala', code: 'AP-CRL-29' },
            { city: 'Gudur', code: 'AP-GUD-30' },
            { city: 'Dharmavaram', code: 'AP-DVRM-31' },
            { city: 'Mandapeta', code: 'AP-MNDP-32' },
            { city: 'Venkatagiri', code: 'AP-VNK-33' },
            { city: 'Tadpatri', code: 'AP-TDPT-34' },
            { city: 'Sattenapalle', code: 'AP-STPL-35' },
            { city: 'Guntakal', code: 'AP-GTL-36' },
            { city: 'Narasaraopet', code: 'AP-NSRPT-37' },
            { city: 'Tadepalligudem', code: 'AP-TDPG-38' },
            { city: 'Kadiri', code: 'AP-KADR-39' },
            { city: 'Sangareddy', code: 'AP-SNGR-40' },
            { city: 'Markapur', code: 'AP-MRKP-41' },
            { city: 'Palasa', code: 'AP-PLS-42' },
            { city: 'Repalle', code: 'AP-RPL-43' },
            { city: 'Bobbili', code: 'AP-BBL-44' },
            { city: 'Piler', code: 'AP-PLR-45' },
            { city: 'Kandukur', code: 'AP-KDKR-46' },
            { city: 'Mangalagiri', code: 'AP-MGLG-47' },
            { city: 'Jaggaiahpeta', code: 'AP-JGPT-48' },
            { city: 'Gadwal', code: 'AP-GDWL-49' },
            { city: 'Tuni', code: 'AP-TUNI-50' },
            { city: 'Tenali', code: 'AP-TENALI-51' },
            { city: 'Ponnur', code: 'AP-PONNUR-52' },
            { city: 'Narasapuram', code: 'AP-NARSAPURAM-53' },
            { city: 'Amalapuram', code: 'AP-AMALAPURAM-54' },
            { city: 'Parvathipuram', code: 'AP-PARVATHIPURAM-55' },
            { city: 'Pulivendla', code: 'AP-PULIVENDLA-56' },
            // Add more authorities for Andhra Pradesh
        ]
    },
    
    {
        state: 'Arunachal Pradesh',
        authorities: [
            { city: 'Itanagar', code: 'AR-ITA-01' },
            { city: 'Naharlagun', code: 'AR-NHLG-02' },
            { city: 'Pasighat', code: 'AR-PST-03' },
            { city: 'Ziro', code: 'AR-ZRO-04' },
            { city: 'Tawang', code: 'AR-TWG-05' },
            { city: 'Bomdila', code: 'AR-BOMD-06' },
            { city: 'Aalo', code: 'AR-AALO-07' },
            { city: 'Tezu', code: 'AR-TEZU-08' },
            { city: 'Daporijo', code: 'AR-DPRJ-09' },
            { city: 'Roing', code: 'AR-ROING-10' },
            { city: 'Anini', code: 'AR-ANINI-11' },
            { city: 'Khonsa', code: 'AR-KHONSA-12' },
            { city: 'Seppa', code: 'AR-SEPPA-13' },
            { city: 'Yingkiong', code: 'AR-YKNG-14' },
            { city: 'Changlang', code: 'AR-CHNGLG-15' },
            { city: 'Tuting', code: 'AR-TUTING-16' },
            { city: 'Miao', code: 'AR-MIAO-17' },
            { city: 'Namsai', code: 'AR-NAMSAI-18' },
            { city: 'Hayuliang', code: 'AR-HAYULIANG-19' },
            { city: 'Diyun', code: 'AR-DIYUN-20' },
            { city: 'Tawang', code: 'AR-TAWANG-21' },
            { city: 'Rupa', code: 'AR-RUPA-22' },
            { city: 'Mechuka', code: 'AR-MECHUKA-23' },
            { city: 'Walong', code: 'AR-WALONG-24' },
            { city: 'Bhalukpong', code: 'AR-BHALUKPONG-25' },
            { city: 'Jairampur', code: 'AR-JAIRAMPUR-26' },
            { city: 'Vijoynagar', code: 'AR-VIJOYNAGAR-27' },
            // Add more authorities for Arunachal Pradesh
        ]
    },

    {
        state: "Assam",
        authorities: [
          { "city": "Guwahati", "code": "AS-GHT-01" },
          { "city": "Silchar", "code": "AS-SIL-02" },
          { "city": "Dibrugarh", "code": "AS-DIB-03" },
          { "city": "Jorhat", "code": "AS-JOR-04" },
          { "city": "Tezpur", "code": "AS-TEZ-05" },
          { "city": "Nagaon", "code": "AS-NAG-06" },
          { "city": "Lakhimpur", "code": "AS-LKP-07" },
          { "city": "Tinsukia", "code": "AS-TIN-08" },
          { "city": "Hailakandi", "code": "AS-HLK-09" },
          { "city": "Karimganj", "code": "AS-KMG-10" },
          { "city": "Dhemaji", "code": "AS-DMJ-11" },
          { "city": "Bongaigaon", "code": "AS-BNG-12" },
          { "city": "Barpeta", "code": "AS-BPT-13" },
          { "city": "Nalbari", "code": "AS-NLR-14" },
          { "city": "Kokrajhar", "code": "AS-KRJ-15" },
          { "city": "Dhubri", "code": "AS-DBR-16" },
          { "city": "Goalpara", "code": "AS-GLP-17" },
          { "city": "Chirang", "code": "AS-CHR-18" },
          { "city": "Kamrup (Rural)", "code": "AS-KMR-19" },
          { "city": "Karbi Anglong", "code": "AS-KBL-20" },
          { "city": "Dima Hasao", "code": "AS-DMH-21" },
          { "city": "Cachar", "code": "AS-CCR-22" }
        ]
      },

      {
        state: "Bihar",
        authorities: [
          { "city": "Patna", "code": "BR-PAT-01" },
          { "city": "Gaya", "code": "BR-GAY-02" },
          { "city": "Muzaffarpur", "code": "BR-MZR-03" },
          { "city": "Bhagalpur", "code": "BR-BGP-04" },
          { "city": "Darbhanga", "code": "BR-DRB-05" },
          { "city": "Purnia", "code": "BR-PUR-06" },
          { "city": "Bihar Sharif", "code": "BR-BSF-07" },
          { "city": "Arrah", "code": "BR-ARA-08" },
          { "city": "Katihar", "code": "BR-KAT-09" },
          { "city": "Chhapra", "code": "BR-CHP-10" },
          { "city": "Munger", "code": "BR-MGR-11" },
          { "city": "Buxar", "code": "BR-BXR-12" },
          { "city": "Bhojpur", "code": "BR-BJPR-13" },
          { "city": "Saran", "code": "BR-SAR-14" },
          { "city": "Siwan", "code": "BR-SIW-15" },
          { "city": "Gopalganj", "code": "BR-GPG-16" },
          { "city": "Nawada", "code": "BR-NWD-17" },
          { "city": "Jamui", "code": "BR-JMU-18" },
          { "city": "Sheikhpura", "code": "BR-SHP-19" },
          { "city": "Lakhisarai", "code": "BR-LRS-20" },
          { "city": "Khagaria", "code": "BR-KGG-21" },
          { "city": "Jehanabad", "code": "BR-JHD-22" }
        ]
      },
      


    // Add more states with their authorities
];

const stateDropdown = document.getElementById("state");
const issuingAuthorityDropdown = document.getElementById("issuingAuthority");

// Function to update the issuing authority dropdown based on the selected state
function updateIssuingAuthorities() {
    const selectedState = stateDropdown.value;
    
    // Find the selected state in the data structure
    const stateData = statesWithIssuingAuthorities.find((state) => state.state === selectedState);

    // Clear the current issuing authority options
    issuingAuthorityDropdown.innerHTML = '';

    if (stateData) {
        // Populate the issuing authority dropdown with options
        stateData.authorities.forEach((authority) => {
            const option = document.createElement("option");
            option.value = authority.code;
            option.text = `${authority.city} (${authority.code})`;
            issuingAuthorityDropdown.add(option);
        });
    }
}

// Add an event listener to the state dropdown
stateDropdown.addEventListener("change", updateIssuingAuthorities);

// Initial update when the page loads
updateIssuingAuthorities();
