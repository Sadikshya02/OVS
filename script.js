// Utility Functions
function logout() {
    localStorage.removeItem('loggedInUser');
    window.location.href = 'index.html';
}

// Handle Register Form Submission
document.getElementById('registerForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const citizenshipId = document.getElementById('citizenship_id').value;
    const name = document.getElementById('name').value;
    const gender = document.getElementById('gender').value;
    const age = parseInt(document.getElementById('age').value);
    const address = document.getElementById('address').value;
    const errorElement = document.getElementById('form-error');

    if (!citizenshipId.match(/^\d{6,}$/)) {
        errorElement.textContent = 'Citizenship ID must be at least 6 digits.';
        return;
    }
    if (age < 18) {
        errorElement.textContent = 'You must be at least 18 to register.';
        return;
    }
    if (!name || !gender || !address) {
        errorElement.textContent = 'Please fill out all fields.';
        return;
    }

    const user = { citizenshipId, name, gender, age, address, hasVoted: false };
    localStorage.setItem(`user_${citizenshipId}`, JSON.stringify(user));
    
    // Add voter to a centralized voter list for admin access
    const voters = JSON.parse(localStorage.getItem('voters') || '[]');
    if (!voters.some(v => v.citizenshipId === citizenshipId)) {
        voters.push(user);
        localStorage.setItem('voters', JSON.stringify(voters));
    }

    errorElement.style.color = '#00cc00';
    errorElement.textContent = 'Registration successful! Redirecting to login...';
    setTimeout(() => window.location.href = 'login.html', 2000);
});

// Handle Login Form Submission
document.getElementById('loginForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const citizenshipId = document.getElementById('login_citizenship_id').value;
    const name = document.getElementById('login_name').value;
    const errorElement = document.getElementById('login-error');

    const storedUser = JSON.parse(localStorage.getItem(`user_${citizenshipId}`));
    if (storedUser && storedUser.name === name) {
        localStorage.setItem('loggedInUser', citizenshipId);
        errorElement.style.color = '#00cc00';
        errorElement.textContent = 'Login successful! Redirecting to vote...';
        setTimeout(() => window.location.href = 'vote.html', 1000);
    } else {
        errorElement.textContent = 'Invalid Citizenship ID or Name.';
    }
});

// Handle Voting Form Submission
document.getElementById('voteForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const loggedInUser = localStorage.getItem('loggedInUser');
    const statusElement = document.getElementById('vote-status');
    if (!loggedInUser) {
        statusElement.textContent = 'Please log in to vote.';
        return;
    }

    const user = JSON.parse(localStorage.getItem(`user_${loggedInUser}`));
    if (user.hasVoted) {
        statusElement.textContent = 'You have already voted.';
        return;
    }

    const selectedCandidate = document.querySelector('input[name="candidate"]:checked');
    if (!selectedCandidate) {
        statusElement.textContent = 'Please select a candidate.';
        return;
    }

    const candidates = JSON.parse(localStorage.getItem('candidates') || '[]');
    const candidate = candidates.find(c => c.name === selectedCandidate.value);
    candidate.votes = (candidate.votes || 0) + 1;
    localStorage.setItem('candidates', JSON.stringify(candidates));

    user.hasVoted = true;
    localStorage.setItem(`user_${loggedInUser}`, JSON.stringify(user));

    statusElement.style.color = '#00cc00';
    statusElement.textContent = 'Vote submitted successfully!';
});

// Load Candidates for Voting
document.addEventListener('DOMContentLoaded', function () {
    const candidateList = document.getElementById('candidate-list');
    if (candidateList) {
        const candidates = JSON.parse(localStorage.getItem('candidates') || '[]');
        candidateList.innerHTML = candidates.map(c => `
            <label class="candidate-option">
                <input type="radio" name="candidate" value="${c.name}"> ${c.name}
            </label>
        `).join('');
    }
});

// Admin Login
document.getElementById('adminLoginForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const username = document.getElementById('admin-username').value;
    const password = document.getElementById('admin-password').value;
    const errorElement = document.getElementById('admin-error');

    if (username === 'admin' && password === 'admin123') {
        document.getElementById('admin-login').classList.add('hidden');
        document.getElementById('admin-panel').classList.remove('hidden');
        loadAdminData();
    } else {
        errorElement.textContent = 'Invalid admin credentials.';
    }
});

// Add Candidate
document.getElementById('addCandidateForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const name = document.getElementById('candidate-name').value;
    const errorElement = document.getElementById('candidate-error');

    const candidates = JSON.parse(localStorage.getItem('candidates') || '[]');
    if (candidates.some(c => c.name === name)) {
        errorElement.textContent = 'Candidate already exists.';
        return;
    }

    candidates.push({ name, votes: 0 });
    localStorage.setItem('candidates', JSON.stringify(candidates));
    errorElement.style.color = '#00cc00';
    errorElement.textContent = 'Candidate added successfully!';
    document.getElementById('candidate-name').value = '';
    loadAdminData();
});

// Load Admin Data (Candidates, Votes, Voters, and Chart)
let voteChart = null; // Store chart instance to update it
function loadAdminData() {
    const voteTracking = document.getElementById('vote-tracking');
    const totalVotesElement = document.getElementById('total-votes');
    const voterList = document.getElementById('voter-list');
    const totalVotersElement = document.getElementById('total-voters');
    const candidates = JSON.parse(localStorage.getItem('candidates') || '[]');
    const voters = JSON.parse(localStorage.getItem('voters') || '[]');

    // Update candidate list with Remove buttons
    voteTracking.innerHTML = candidates.map(c => `
        <div class="candidate-entry">
            <span>${c.name}: ${c.votes || 0} votes</span>
            <button onclick="removeCandidate('${c.name}')">Remove</button>
        </div>
    `).join('');

    // Calculate total votes
    const totalVotes = candidates.reduce((sum, c) => sum + (c.votes || 0), 0);
    totalVotesElement.textContent = totalVotes;

    // Update voter list with Remove buttons
    voterList.innerHTML = voters.map(v => `
        <div class="voter-entry">
            <span>${v.name} (ID: ${v.citizenshipId})</span>
            <button onclick="removeVoter('${v.citizenshipId}')">Remove</button>
        </div>
    `).join('');

    // Update total voters
    totalVotersElement.textContent = voters.length;

    // Prepare chart data
    const ctx = document.getElementById('voteChart').getContext('2d');
    const labels = candidates.map(c => c.name);
    const votes = candidates.map(c => c.votes || 0);

    // Destroy existing chart if it exists to avoid overlap
    if (voteChart) {
        voteChart.destroy();
    }

    // Create new chart
    voteChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Votes',
                data: votes,
                backgroundColor: 'rgba(107, 72, 255, 0.6)',
                borderColor: '#6b48ff',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Votes'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Candidates'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Remove Candidate
function removeCandidate(candidateName) {
    let candidates = JSON.parse(localStorage.getItem('candidates') || '[]');
    candidates = candidates.filter(c => c.name !== candidateName);
    localStorage.setItem('candidates', JSON.stringify(candidates));
    loadAdminData();
}

// Remove Voter
function removeVoter(citizenshipId) {
    let voters = JSON.parse(localStorage.getItem('voters') || '[]');
    voters = voters.filter(v => v.citizenshipId !== citizenshipId);
    localStorage.setItem('voters', JSON.stringify(voters));
    localStorage.removeItem(`user_${citizenshipId}`); // Remove individual user data too
    loadAdminData();
}