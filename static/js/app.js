// Global state
let currentCacheKey = null;

// DOM Elements
const form = document.getElementById('analysisForm');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsSection = document.getElementById('resultsSection');
const errorDisplay = document.getElementById('errorDisplay');
const runBtn = document.getElementById('runAnalysisBtn');
const resetBtn = document.getElementById('resetBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupTabs();
    startAutonomousStatusUpdates();
});

// Auto-refresh autonomous status
let statusUpdateInterval = null;

function startAutonomousStatusUpdates() {
    // Update immediately
    updateAutonomousStatus();
    
    // Update every 10 seconds
    statusUpdateInterval = setInterval(updateAutonomousStatus, 10000);
}

async function updateAutonomousStatus() {
    try {
        const response = await fetch('/api/discoveries/status');
        
        // Check if response is ok
        if (!response.ok) {
            console.error(`Status check failed: ${response.status} ${response.statusText}`);
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            const status = data.status || {};
            const health = data.health || {};
            
            // Update status icon
            const icon = document.getElementById('autonomousIcon');
            if (icon) {
                const isHealthy = status.running && (health.heartbeat_healthy !== false);
                icon.textContent = isHealthy ? '🟢' : '🔴';
            }
            
            // Update status text
            const statusText = document.getElementById('autonomousStatus');
            if (statusText) {
                if (status.running) {
                    const healthScore = health.health_score || 0;
                    statusText.textContent = `Running • Health: ${healthScore}/100`;
                } else {
                    statusText.textContent = 'Stopped';
                }
            }
            
            // Update counts
            const countToday = document.getElementById('autonomousCount');
            if (countToday) {
                countToday.textContent = status.discoveries_today || 0;
            }
            
            const countTotal = document.getElementById('autonomousTotal');
            if (countTotal) {
                countTotal.textContent = status.total_discoveries || 0;
            }
        } else {
            console.error('Status update failed:', data.error);
        }
    } catch (error) {
        console.error('Error updating autonomous status:', error);
        // Set offline indicators
        const icon = document.getElementById('autonomousIcon');
        if (icon) {
            icon.textContent = '🔴';
        }
        const statusText = document.getElementById('autonomousStatus');
        if (statusText) {
            statusText.textContent = 'Offline - Retrying...';
        }
    }
}

// Event Listeners
function setupEventListeners() {
    form.addEventListener('submit', handleAnalysis);
    resetBtn.addEventListener('click', resetForm);
    
    document.getElementById('downloadJsonBtn')?.addEventListener('click', downloadJSON);
    document.getElementById('downloadPlotsBtn')?.addEventListener('click', downloadAllPlots);
}

// Tab System
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(`tab-${tabId}`).classList.add('active');
            
            // Load plot if not loaded
            loadPlot(tabId);
        });
    });
}

// Handle Analysis Form Submission
async function handleAnalysis(e) {
    e.preventDefault();
    
    hideError();
    showLoading();
    hideResults();
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Convert numeric values
    data.side = parseFloat(data.side);
    data.angle = parseFloat(data.angle);
    data.max_distance_pairs = parseInt(data.max_distance_pairs);
    data.max_direction_pairs = parseInt(data.max_direction_pairs);
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Analysis failed');
        }
        
        currentCacheKey = result.cache_key;
        displayResults(result.summary);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// Display Results
function displayResults(summary) {
    // Configuration stats
    document.getElementById('statSide').textContent = `${summary.configuration.side_length} units`;
    document.getElementById('statAngle').textContent = `Rotation: ${summary.configuration.rotation_angle_degrees}°`;
    
    // Point counts
    document.getElementById('statPoints').textContent = summary.point_counts.unique_points;
    document.getElementById('statPointBreakdown').textContent = 
        `${summary.point_counts.edge_face_intersections} edge-face, ${summary.point_counts.edge_edge_intersections} edge-edge`;
    
    // Distance stats
    const distStats = summary.distance_stats;
    document.getElementById('statDistRange').textContent = 
        `${distStats.min.toFixed(3)} - ${distStats.max.toFixed(3)}`;
    document.getElementById('statDistMean').textContent = 
        `Mean: ${distStats.mean.toFixed(3)}, σ: ${distStats.std.toFixed(3)}`;
    
    // Golden ratio
    const phi = summary.golden_ratio;
    document.getElementById('statPhi').textContent = `φ ≈ ${phi.phi_value.toFixed(6)}`;
    document.getElementById('statPhiCandidates').textContent = 
        phi.candidate_count > 0 
            ? `${phi.candidate_count} candidate pair${phi.candidate_count !== 1 ? 's' : ''} found`
            : 'No candidates found';
    
    // Directions
    document.getElementById('statDirections').textContent = summary.direction_count;
    document.getElementById('statAngles').textContent = `${summary.angle_count} distinct angles`;
    
    // Icosahedral match
    const ico = summary.icosahedral_check;
    const icoCard = document.getElementById('icoCard');
    const matchQuality = ico.match_quality || 'unknown';
    
    document.getElementById('statIcoMatch').textContent = matchQuality.toUpperCase();
    document.getElementById('statIcoMatch').className = `stat-value match-${matchQuality}`;
    
    if (ico.angle_degrees !== null) {
        document.getElementById('statIcoAngle').textContent = 
            `Angular error: ${ico.angle_degrees.toFixed(2)}°`;
    } else {
        document.getElementById('statIcoAngle').textContent = 'No match data';
    }
    
    // Special angles
    displaySpecialAngles(summary.special_angles);
    
    // Load first plot
    loadPlot('3d');
    
    // Show results
    showResults();
}

// Display Special Angles
function displaySpecialAngles(specialAngles) {
    const grid = document.getElementById('specialAnglesGrid');
    grid.innerHTML = '';
    
    const angleData = [
        { angle: 36, key: '36.0', label: 'Pentagon/Icosahedron' },
        { angle: 60, key: '60.0', label: 'Hexagon/Octahedron' },
        { angle: 72, key: '72.0', label: 'Pentagon/Dodecahedron' },
        { angle: 90, key: '90.0', label: 'Cube/Octahedron' },
        { angle: 120, key: '120.0', label: 'Hexagon' }
    ];
    
    angleData.forEach(item => {
        const data = specialAngles[item.key];
        if (data && data.count > 0) {
            const badge = document.createElement('div');
            badge.className = 'angle-badge';
            badge.innerHTML = `
                <div class="angle-badge-value">${item.angle}°</div>
                <div class="angle-badge-label">${item.label}</div>
                <div class="angle-badge-count">${data.count} occurrences</div>
            `;
            grid.appendChild(badge);
        }
    });
    
    if (grid.children.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No special symmetry angles detected</p>';
    }
}

// Load Plot
async function loadPlot(plotType) {
    if (!currentCacheKey) return;
    
    const imgElement = document.getElementById(`plot${capitalize(plotType)}`);
    
    // Check if already loaded
    if (imgElement.src && imgElement.src.includes(plotType)) {
        return;
    }
    
    try {
        imgElement.src = `/api/plot/${plotType}/${currentCacheKey}?t=${Date.now()}`;
    } catch (error) {
        console.error(`Failed to load ${plotType} plot:`, error);
    }
}

// Download JSON
async function downloadJSON() {
    if (!currentCacheKey) return;
    
    try {
        window.location.href = `/api/download/${currentCacheKey}`;
    } catch (error) {
        showError('Failed to download JSON results');
    }
}

// Download All Plots
async function downloadAllPlots() {
    if (!currentCacheKey) return;
    
    const plots = ['3d', 'distances', 'angles', 'summary'];
    
    for (const plotType of plots) {
        try {
            const link = document.createElement('a');
            link.href = `/api/plot/${plotType}/${currentCacheKey}`;
            link.download = `orion_octave_${plotType}.png`;
            link.click();
            
            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
            console.error(`Failed to download ${plotType} plot:`, error);
        }
    }
}

// Reset Form
function resetForm() {
    form.reset();
    hideResults();
    hideError();
    currentCacheKey = null;
}

// UI State Management
function showLoading() {
    loadingIndicator.style.display = 'block';
    runBtn.disabled = true;
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
    runBtn.disabled = false;
}

function showResults() {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideResults() {
    resultsSection.style.display = 'none';
}

function showError(message) {
    errorDisplay.textContent = `Error: ${message}`;
    errorDisplay.style.display = 'block';
    errorDisplay.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    errorDisplay.style.display = 'none';
}

// Utility Functions
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Modal Functions
function showAbout() {
    alert(`Orion Octave Cubes - Geometry Analysis Dashboard

This interactive tool analyzes the geometric properties of two interpenetrating cubes:
- Cube A: Axis-aligned
- Cube B: Rotated around the z-axis

The analysis detects:
• Golden ratio (φ) relationships in distance patterns
• Icosahedral symmetry in direction vectors
• Special angles associated with Platonic solids
• Complex geometric interference patterns

Developed for computational geometry research and education.

Version 2.0 | December 2025`);
}

function showHelp() {
    alert(`How to Use:

1. Set Parameters:
   • Cube Side Length: Size of the cubes (0.1 - 100)
   • Rotation Angle: How much Cube B is rotated (0 - 360°)
   • Sample Sizes: Higher = more accurate but slower

2. Run Analysis:
   • Click "Run Analysis" to perform calculations
   • Wait for results (may take 5-30 seconds)

3. Explore Results:
   • View summary statistics in the cards
   • Check special angle detections
   • Browse different visualization tabs
   • Download results and plots

Tips:
• Try angles: 30°, 45°, 60°, 72° for interesting patterns
• Increase sample sizes for better accuracy
• Golden ratio detection works best at certain angles
• Watch for "strong" icosahedral matches!`);
}
