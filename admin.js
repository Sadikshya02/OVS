document.getElementById('adminLoginForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('admin.php', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const errorElement = document.getElementById('admin-error');
        if (data.success) {
            window.location.reload();
        } else {
            errorElement.textContent = data.error;
        }
    });
});

document.getElementById('addCandidateForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    formData.append('add_candidate', '1');
    fetch('admin.php', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const errorElement = document.getElementById('candidate-error');
        if (data.success) {
            errorElement.style.color = '#00cc00';
            errorElement.textContent = data.success;
            setTimeout(() => window.location.reload(), 1000);
        } else {
            errorElement.textContent = data.error;
        }
    });
});

function removeCandidate(id) {
    if (confirm('Are you sure you want to remove this candidate?')) {
        const formData = new FormData();
        formData.append('remove_candidate', '1');
        formData.append('candidate_id', id);
        fetch('admin.php', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        });
    }
}

function removeVoter(citizenshipId) {
    if (confirm('Are you sure you want to remove this voter?')) {
        const formData = new FormData();
        formData.append('remove_voter', '1');
        formData.append('citizenship_id', citizenshipId);
        fetch('admin.php', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        });
    }
}

// Load Chart
document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('voteChart').getContext('2d');
    const candidates = Array.from(document.querySelectorAll('#vote-tracking .candidate-entry')).map(entry => {
        const [name, votes] = entry.querySelector('span').textContent.split(': ');
        return { name, votes: parseInt(votes) };
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: candidates.map(c => c.name),
            datasets: [{
                label: 'Votes',
                data: candidates.map(c => c.votes),
                backgroundColor: 'rgba(107, 72, 255, 0.6)',
                borderColor: '#6b48ff',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Number of Votes' } },
                x: { title: { display: true, text: 'Candidates' } }
            },
            plugins: { legend: { display: false } }
        }
    });
});