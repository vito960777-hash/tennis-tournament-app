// Global state
let currentMatch = null;
let isAdmin = false;

// DOM Elements
const newTournamentBtn = document.getElementById('newTournamentBtn');
const setupPlayoffsBtn = document.getElementById('setupPlayoffsBtn');
const matchModal = document.getElementById('matchModal');
const closeModal = document.querySelector('.close');
const submitScoreBtn = document.getElementById('submitScoreBtn');
const notification = document.getElementById('notification');
const adminLoginBtn = document.getElementById('adminLoginBtn');
const adminLogoutBtn = document.getElementById('adminLogoutBtn');
const adminModal = document.getElementById('adminModal');
const closeAdminModal = document.querySelector('.close-admin');
const submitAdminBtn = document.getElementById('submitAdminBtn');
const adminPassword = document.getElementById('adminPassword');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkAdminStatus();
    initMobileFixes();
});

// Mobile fixes for iOS Safari
function initMobileFixes() {
    // Fix viewport height for iOS Safari
    const setVH = () => {
        let vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);

    // Prevent double-tap zoom on buttons
    let lastTouchEnd = 0;
    document.addEventListener('touchend', (e) => {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, false);

    // Smooth scroll for tabs
    const tabs = document.querySelector('.tabs');
    if (tabs) {
        tabs.addEventListener('touchstart', (e) => {
            e.stopPropagation();
        }, { passive: true });
    }

    // Prevent body scroll when modal is open
    const observeModal = (modal) => {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'style') {
                    if (modal.style.display === 'block') {
                        document.body.style.overflow = 'hidden';
                        document.body.style.position = 'fixed';
                        document.body.style.width = '100%';
                    } else {
                        document.body.style.overflow = '';
                        document.body.style.position = '';
                        document.body.style.width = '';
                    }
                }
            });
        });

        observer.observe(modal, { attributes: true });
    };

    observeModal(matchModal);
    observeModal(adminModal);
}

// Event Listeners
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // New tournament
    newTournamentBtn.addEventListener('click', createNewTournament);

    // Setup playoffs
    setupPlayoffsBtn.addEventListener('click', setupPlayoffs);

    // Admin
    adminLoginBtn.addEventListener('click', () => adminModal.style.display = 'block');
    adminLogoutBtn.addEventListener('click', adminLogout);
    submitAdminBtn.addEventListener('click', adminLogin);

    // Admin modal
    closeAdminModal.addEventListener('click', () => adminModal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === adminModal) adminModal.style.display = 'none';
    });

    // Enter key in admin password
    adminPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') adminLogin();
    });

    // Match modal
    closeModal.addEventListener('click', () => matchModal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === matchModal) matchModal.style.display = 'none';
    });

    // Submit score
    submitScoreBtn.addEventListener('click', submitScore);

    // Enter key in score inputs
    document.getElementById('player1Score').addEventListener('keypress', handleEnterKey);
    document.getElementById('player2Score').addEventListener('keypress', handleEnterKey);
}

function handleEnterKey(e) {
    if (e.key === 'Enter') {
        submitScore();
    }
}

// Admin functions
async function checkAdminStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        isAdmin = data.is_admin;
        updateAdminUI();
        loadTournamentInfo();
    } catch (error) {
        console.error('Error checking admin status:', error);
    }
}

async function adminLogin() {
    const password = adminPassword.value;

    if (!password) {
        showNotification('Enter password', 'error');
        return;
    }

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password }),
        });

        const data = await response.json();

        if (data.success) {
            isAdmin = true;
            adminModal.style.display = 'none';
            adminPassword.value = '';
            showNotification('Logged in as admin', 'success');
            updateAdminUI();
        } else {
            showNotification(data.message || 'Invalid password', 'error');
        }
    } catch (error) {
        showNotification('Login error', 'error');
        console.error(error);
    }
}

async function adminLogout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
        });

        isAdmin = false;
        showNotification('Logged out', 'success');
        updateAdminUI();
    } catch (error) {
        console.error('Error logging out:', error);
    }
}

function updateAdminUI() {
    if (isAdmin) {
        adminLoginBtn.style.display = 'none';
        adminLogoutBtn.style.display = 'block';
        newTournamentBtn.style.display = 'block';
    } else {
        adminLoginBtn.style.display = 'block';
        adminLogoutBtn.style.display = 'none';
        newTournamentBtn.style.display = 'none';
    }
}

// Tab switching
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Reload data for specific tabs
    if (tabName === 'groups') {
        loadTournamentInfo();
    } else if (tabName === 'schedule') {
        loadSchedule();
    } else if (tabName === 'playoffs') {
        loadPlayoffs();
    } else if (tabName === 'results') {
        loadResults();
    }
}

// Create new tournament
async function createNewTournament() {
    try {
        const response = await fetch('/api/tournament/new', {
            method: 'POST',
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Tournament created successfully!', 'success');
            loadTournamentInfo();
            loadSchedule();
            loadPlayoffs();
            loadResults();
        }
    } catch (error) {
        showNotification('Error creating tournament', 'error');
        console.error(error);
    }
}

// Load tournament info (groups and matches)
async function loadTournamentInfo() {
    try {
        const response = await fetch('/api/tournament/info');

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        // Render groups
        renderGroups(data.groups);

        // Render group matches
        renderGroupMatches(data.group_matches);

        // Check if all group matches are played
        const allPlayed = data.group_matches.every(match => match.played);
        setupPlayoffsBtn.disabled = !allPlayed;

    } catch (error) {
        console.error('Error loading tournament info:', error);
    }
}

// Render groups tables
function renderGroups(groups) {
    groups.forEach((group, index) => {
        const tbody = document.getElementById(`group-${group.name.toLowerCase()}-body`);
        tbody.innerHTML = '';

        group.players.forEach(player => {
            const row = document.createElement('tr');
            const diff = player.game_difference >= 0 ? `+${player.game_difference}` : player.game_difference;

            row.innerHTML = `
                <td>${player.name}</td>
                <td>${player.level}</td>
                <td>${player.wins}</td>
                <td>${player.losses}</td>
                <td>${player.games_won}-${player.games_lost}</td>
                <td>${diff}</td>
            `;

            tbody.appendChild(row);
        });
    });
}

// Render group matches
function renderGroupMatches(matches) {
    const container = document.getElementById('group-matches');
    container.innerHTML = '';

    // Define rounds with time slots
    const rounds = [
        {
            number: 1,
            groups: [
                { name: 'A', time: '8:00-9:00' },
                { name: 'B', time: '9:00-10:00' }
            ]
        },
        {
            number: 2,
            groups: [
                { name: 'A', time: '10:00-11:00' },
                { name: 'B', time: '11:00-12:00' }
            ]
        },
        {
            number: 3,
            groups: [
                { name: 'A', time: '12:00-13:00' },
                { name: 'B', time: '13:00-14:00' }
            ]
        }
    ];

    // Render each round
    rounds.forEach(round => {
        // Create round header
        const roundHeader = document.createElement('div');
        roundHeader.className = 'round-header';
        roundHeader.innerHTML = `<h3>Round ${round.number}</h3>`;
        container.appendChild(roundHeader);

        // Render each group in the round
        round.groups.forEach(groupInfo => {
            // Filter matches for this time slot and group
            const groupMatches = matches.filter(match =>
                match.time === groupInfo.time &&
                match.stage === `Group ${groupInfo.name}`
            );

            if (groupMatches.length > 0) {
                // Group subheader
                const groupSubheader = document.createElement('div');
                groupSubheader.className = 'group-subheader';
                groupSubheader.innerHTML = `
                    <span class="group-label">Group ${groupInfo.name}</span>
                    <span class="time-label">⏰ ${groupInfo.time}</span>
                `;
                container.appendChild(groupSubheader);

                // Matches grid for this group
                const matchesGrid = document.createElement('div');
                matchesGrid.className = 'matches-grid';

                // Sort by court and render
                groupMatches.sort((a, b) => a.court - b.court).forEach(match => {
                    const card = createMatchCard(match, 'group');
                    matchesGrid.appendChild(card);
                });

                container.appendChild(matchesGrid);
            }
        });
    });
}

// Create match card
function createMatchCard(match, type) {
    const card = document.createElement('div');
    card.className = `match-card ${match.played ? 'played' : ''} ${isAdmin ? 'admin-mode' : ''}`;

    // Allow admins to edit only
    if (isAdmin) {
        card.addEventListener('click', () => openMatchModal(match, type));
    }

    const statusBadge = match.played
        ? `<span class="match-status completed">✓ Played${isAdmin ? ' (click to edit)' : ''}</span>`
        : `<span class="match-status pending">Pending</span>`;

    const scoreDisplay = match.score
        ? `<div class="match-score">${match.score[0]} - ${match.score[1]}</div>`
        : '';

    card.innerHTML = `
        <div class="match-header">
            <span class="match-time">⏰ ${match.time}</span>
            <span class="match-court">Court ${match.court}</span>
        </div>
        <div class="match-players">${match.player1} vs ${match.player2}</div>
        ${scoreDisplay}
        ${statusBadge}
    `;

    return card;
}

// Load schedule
async function loadSchedule() {
    try {
        const response = await fetch('/api/tournament/schedule');

        if (!response.ok) {
            return;
        }

        const data = await response.json();
        renderSchedule(data.schedule);

    } catch (error) {
        console.error('Error loading schedule:', error);
    }
}

// Render schedule
function renderSchedule(schedule) {
    const container = document.getElementById('full-schedule');
    container.innerHTML = '';

    // Separate group stage and playoff matches
    const groupMatches = schedule.filter(m => m.type === 'group');
    const playoffMatches = schedule.filter(m => m.type === 'playoff');

    // Render Group Stage
    if (groupMatches.length > 0) {
        const groupStageHeader = document.createElement('div');
        groupStageHeader.className = 'stage-header';
        groupStageHeader.innerHTML = '<h2>🎄 GROUP STAGE</h2>';
        container.appendChild(groupStageHeader);

        // Define rounds
        const rounds = [
            {
                number: 1,
                groups: [
                    { name: 'A', time: '8:00-9:00' },
                    { name: 'B', time: '9:00-10:00' }
                ]
            },
            {
                number: 2,
                groups: [
                    { name: 'A', time: '10:00-11:00' },
                    { name: 'B', time: '11:00-12:00' }
                ]
            },
            {
                number: 3,
                groups: [
                    { name: 'A', time: '12:00-13:00' },
                    { name: 'B', time: '13:00-14:00' }
                ]
            }
        ];

        // Render each round
        rounds.forEach(round => {
            const roundDiv = document.createElement('div');
            roundDiv.className = 'schedule-round';

            const roundHeader = document.createElement('div');
            roundHeader.className = 'round-header-schedule';
            roundHeader.innerHTML = `<h3>Round ${round.number}</h3>`;
            roundDiv.appendChild(roundHeader);

            // Render each group in the round
            round.groups.forEach(groupInfo => {
                const groupMatches = schedule.filter(match =>
                    match.time === groupInfo.time &&
                    match.stage === `Group ${groupInfo.name}`
                );

                if (groupMatches.length > 0) {
                    const timeSlotDiv = document.createElement('div');
                    timeSlotDiv.className = 'schedule-time-slot';

                    const header = document.createElement('div');
                    header.className = 'time-slot-header';
                    header.innerHTML = `⏰ ${groupInfo.time} - Group ${groupInfo.name}`;
                    timeSlotDiv.appendChild(header);

                    const matchesDiv = document.createElement('div');
                    matchesDiv.className = 'schedule-matches';

                    groupMatches.sort((a, b) => a.court - b.court).forEach(match => {
                        const matchCard = createMatchCard(match, match.type);
                        matchesDiv.appendChild(matchCard);
                    });

                    timeSlotDiv.appendChild(matchesDiv);
                    roundDiv.appendChild(timeSlotDiv);
                }
            });

            container.appendChild(roundDiv);
        });
    }

    // Render Playoffs
    if (playoffMatches.length > 0) {
        const playoffHeader = document.createElement('div');
        playoffHeader.className = 'stage-header';
        playoffHeader.innerHTML = '<h2>⭐ PLAYOFFS</h2>';
        container.appendChild(playoffHeader);

        // Group playoff matches by time
        const playoffTimes = {
            '14:00-15:00': [],
            '15:00-16:00': []
        };

        playoffMatches.forEach(match => {
            if (playoffTimes[match.time]) {
                playoffTimes[match.time].push(match);
            }
        });

        Object.keys(playoffTimes).forEach(time => {
            if (playoffTimes[time].length > 0) {
                const slotDiv = document.createElement('div');
                slotDiv.className = 'schedule-time-slot';

                const header = document.createElement('div');
                header.className = 'time-slot-header';
                header.innerHTML = `⏰ ${time}`;
                slotDiv.appendChild(header);

                const matchesDiv = document.createElement('div');
                matchesDiv.className = 'schedule-matches';

                playoffTimes[time].sort((a, b) => a.court - b.court).forEach(match => {
                    const matchCard = createMatchCard(match, match.type);
                    matchesDiv.appendChild(matchCard);
                });

                slotDiv.appendChild(matchesDiv);
                container.appendChild(slotDiv);
            }
        });
    }
}

// Load playoffs
async function loadPlayoffs() {
    try {
        const response = await fetch('/api/tournament/schedule');

        if (!response.ok) {
            return;
        }

        const data = await response.json();
        const playoffMatches = data.schedule.filter(m => m.type === 'playoff');

        if (playoffMatches.length > 0) {
            renderPlayoffMatches(playoffMatches);
            document.querySelector('.playoffs-info').style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading playoffs:', error);
    }
}

// Render playoff matches
function renderPlayoffMatches(matches) {
    const container = document.getElementById('playoffs-matches');
    container.innerHTML = '';

    // Group by type
    const semifinals = matches.filter(m => m.playoff_type === 'semifinal');
    const finals = matches.filter(m => m.playoff_type === 'final');
    const thirdPlace = matches.filter(m => m.playoff_type === 'third_place');

    if (semifinals.length > 0) {
        const title = document.createElement('h3');
        title.className = 'section-title';
        title.textContent = '🎾 Semifinals';
        container.appendChild(title);

        semifinals.forEach(match => {
            const card = createPlayoffMatchCard(match);
            container.appendChild(card);
        });
    }

    if (finals.length > 0 || thirdPlace.length > 0) {
        const title = document.createElement('h3');
        title.className = 'section-title';
        title.textContent = '🏆 Final Matches';
        container.appendChild(title);

        [...thirdPlace, ...finals].forEach(match => {
            const card = createPlayoffMatchCard(match);
            container.appendChild(card);
        });
    }
}

// Create playoff match card
function createPlayoffMatchCard(match) {
    const card = document.createElement('div');
    card.className = `match-card ${match.played ? 'played' : ''} ${isAdmin ? 'admin-mode' : ''}`;

    // Allow admins to edit only
    if (isAdmin) {
        card.addEventListener('click', () => openPlayoffMatchModal(match));
    }

    const statusBadge = match.played
        ? `<span class="match-status completed">✓ Played${isAdmin ? ' (click to edit)' : ''}</span>`
        : `<span class="match-status pending">Pending</span>`;

    const scoreDisplay = match.score
        ? `<div class="match-score">${match.score[0]} - ${match.score[1]}</div>`
        : '';

    card.innerHTML = `
        <div class="match-header">
            <span class="match-time">⏰ ${match.time}</span>
            <span class="match-court">Court ${match.court}</span>
        </div>
        <div style="font-size: 0.9rem; color: #667eea; font-weight: 600; margin-bottom: 0.5rem;">
            ${match.stage}
        </div>
        <div class="match-players">${match.player1} vs ${match.player2}</div>
        ${scoreDisplay}
        ${statusBadge}
    `;

    return card;
}

// Setup playoffs
async function setupPlayoffs() {
    try {
        const response = await fetch('/api/playoffs/setup', {
            method: 'POST',
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Playoffs set up!', 'success');
            switchTab('playoffs');
        } else {
            showNotification(data.error || 'Error', 'error');
        }
    } catch (error) {
        showNotification('Error setting up playoffs', 'error');
        console.error(error);
    }
}

// Open match modal
function openMatchModal(match, type) {
    currentMatch = { ...match, type };

    // Update title based on match status
    const modalTitle = document.querySelector('.modal-title');
    if (match.score) {
        modalTitle.textContent = 'Edit Match Result';
    } else {
        modalTitle.textContent = 'Enter Match Result';
    }

    document.getElementById('matchPlayers').textContent =
        `${match.player1} vs ${match.player2}`;

    // If there's an existing score, show it
    const p1Input = document.getElementById('player1Score');
    const p2Input = document.getElementById('player2Score');

    if (match.score) {
        p1Input.value = match.score[0];
        p2Input.value = match.score[1];
    } else {
        p1Input.value = '';
        p2Input.value = '';
    }

    matchModal.style.display = 'block';

    // Auto-focus first input on mobile
    setTimeout(() => {
        if (window.innerWidth <= 480) {
            p1Input.focus();
        }
    }, 300);
}

// Open playoff match modal
function openPlayoffMatchModal(match) {
    currentMatch = { ...match, type: 'playoff' };

    // Update title based on match status
    const modalTitle = document.querySelector('.modal-title');
    if (match.score) {
        modalTitle.textContent = 'Edit Match Result';
    } else {
        modalTitle.textContent = 'Enter Match Result';
    }

    document.getElementById('matchPlayers').textContent =
        `${match.stage}: ${match.player1} vs ${match.player2}`;

    // If there's an existing score, show it
    const p1Input = document.getElementById('player1Score');
    const p2Input = document.getElementById('player2Score');

    if (match.score) {
        p1Input.value = match.score[0];
        p2Input.value = match.score[1];
    } else {
        p1Input.value = '';
        p2Input.value = '';
    }

    matchModal.style.display = 'block';

    // Auto-focus first input on mobile
    setTimeout(() => {
        if (window.innerWidth <= 480) {
            p1Input.focus();
        }
    }, 300);
}

// Submit score
async function submitScore() {
    const p1Score = parseInt(document.getElementById('player1Score').value);
    const p2Score = parseInt(document.getElementById('player2Score').value);

    if (isNaN(p1Score) || isNaN(p2Score)) {
        showNotification('Enter both scores', 'error');
        return;
    }

    const score = `${p1Score}-${p2Score}`;

    try {
        let url, payload;

        if (currentMatch.type === 'playoff') {
            url = '/api/playoffs/match';
            payload = {
                player1: currentMatch.player1,
                player2: currentMatch.player2,
                score: score,
                playoff_type: currentMatch.playoff_type
            };
        } else {
            url = '/api/match/submit';
            payload = {
                player1: currentMatch.player1,
                player2: currentMatch.player2,
                score: score,
                type: 'group'
            };
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showNotification(data.message, 'success');
            matchModal.style.display = 'none';

            // Reload current tab
            if (currentMatch.type === 'playoff') {
                loadPlayoffs();
            } else {
                loadTournamentInfo();
            }
        } else {
            showNotification(data.error || 'Error', 'error');
        }
    } catch (error) {
        showNotification('Error saving result', 'error');
        console.error(error);
    }
}

// Load results
async function loadResults() {
    try {
        const response = await fetch('/api/results');

        if (!response.ok) {
            return;
        }

        const data = await response.json();
        renderResults(data);

    } catch (error) {
        console.error('Error loading results:', error);
    }
}

// Render results
function renderResults(results) {
    const container = document.getElementById('final-results');

    container.innerHTML = `
        <div class="podium-place first">
            <div class="podium-medal">🥇</div>
            <div class="podium-rank">Champion</div>
            <div class="podium-name">${results.champion}</div>
        </div>
        <div class="podium-place second">
            <div class="podium-medal">🥈</div>
            <div class="podium-rank">2nd place</div>
            <div class="podium-name">${results.runner_up}</div>
        </div>
        ${results.third_place ? `
        <div class="podium-place third">
            <div class="podium-medal">🥉</div>
            <div class="podium-rank">3rd place</div>
            <div class="podium-name">${results.third_place}</div>
        </div>
        ` : ''}
        ${results.fourth_place ? `
        <div class="podium-place">
            <div class="podium-medal">4️⃣</div>
            <div class="podium-rank">4th place</div>
            <div class="podium-name">${results.fourth_place}</div>
        </div>
        ` : ''}
    `;
}

// Show notification
function showNotification(message, type = 'success') {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';

    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}
