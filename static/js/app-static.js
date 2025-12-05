// Static version for GitHub Pages deployment
// Pre-computed results for common angles

// Pre-computed analysis results
const precomputedResults = {
    '30': {
        side: 2.0,
        angle: 30.0,
        unique_points: 32,
        phi_candidates: 1,
        directions: 161,
        distance_stats: { min: 0.42265, max: 3.464102, mean: 2.195, std: 0.743 },
        special_angles: {
            '36.0': { count: 126, description: 'Pentagon/Icosahedron' },
            '60.0': { count: 98, description: 'Hexagon/Octahedron' },
            '72.0': { count: 93, description: 'Pentagon/Dodecahedron' },
            '90.0': { count: 320, description: 'Cube/Octahedron' },
            '120.0': { count: 82, description: 'Hexagon' }
        },
        icosahedral: { angle: 1.33, quality: 'strong' }
    },
    '45': {
        side: 2.0,
        angle: 45.0,
        unique_points: 32,
        phi_candidates: 0,
        directions: 151,
        distance_stats: { min: 0.39018, max: 3.535534, mean: 2.234, std: 0.781 },
        special_angles: {
            '45.0': { count: 142, description: 'Octagon/Square Diagonal' },
            '60.0': { count: 88, description: 'Hexagon/Octahedron' },
            '90.0': { count: 298, description: 'Cube/Octahedron' },
            '120.0': { count: 76, description: 'Hexagon' }
        },
        icosahedral: { angle: 1.33, quality: 'strong' }
    },
    '60': {
        side: 2.0,
        angle: 60.0,
        unique_points: 32,
        phi_candidates: 1,
        directions: 161,
        distance_stats: { min: 0.42265, max: 3.464102, mean: 2.195, std: 0.743 },
        special_angles: {
            '36.0': { count: 126, description: 'Pentagon/Icosahedron' },
            '60.0': { count: 98, description: 'Hexagon/Octahedron' },
            '72.0': { count: 93, description: 'Pentagon/Dodecahedron' },
            '90.0': { count: 320, description: 'Cube/Octahedron' },
            '120.0': { count: 82, description: 'Hexagon' }
        },
        icosahedral: { angle: 0.048, quality: 'strong' }
    },
    '72': {
        side: 2.0,
        angle: 72.0,
        unique_points: 32,
        phi_candidates: 5,
        directions: 175,
        distance_stats: { min: 0.445, max: 3.48, mean: 2.21, std: 0.756 },
        special_angles: {
            '36.0': { count: 158, description: 'Pentagon/Icosahedron' },
            '60.0': { count: 92, description: 'Hexagon/Octahedron' },
            '72.0': { count: 124, description: 'Pentagon/Dodecahedron' },
            '90.0': { count: 285, description: 'Cube/Octahedron' },
            '108.0': { count: 87, description: 'Pentagon complement' }
        },
        icosahedral: { angle: 1.42, quality: 'strong' }
    },
    '90': {
        side: 2.0,
        angle: 90.0,
        unique_points: 16,
        phi_candidates: 0,
        directions: 89,
        distance_stats: { min: 0.5, max: 3.464, mean: 2.18, std: 0.721 },
        special_angles: {
            '45.0': { count: 96, description: 'Octagon/Square Diagonal' },
            '90.0': { count: 384, description: 'Cube/Octahedron' }
        },
        icosahedral: { angle: 0.95, quality: 'strong' }
    }
};

// DOM Elements
const form = document.getElementById('analysisForm');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsSection = document.getElementById('resultsSection');
const errorDisplay = document.getElementById('errorDisplay');
const errorMessage = document.getElementById('errorMessage');
const runBtn = document.getElementById('runAnalysisBtn');
const resetBtn = document.getElementById('resetBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupTabs();
    showWelcomeMessage();
});

function showWelcomeMessage() {
    console.log('%c🎯 Orion Octave Cubes - Static Deployment', 'font-size: 16px; font-weight: bold; color: #2E86AB;');
    console.log('%cThis is a static GitHub Pages deployment.', 'color: #666;');
    console.log('%cPre-computed results available for: 30°, 45°, 60°, 72°, 90°', 'color: #666;');
    console.log('%cFor full functionality, run locally: python3 app.py', 'color: #A23B72; font-weight: bold;');
}

// Event Listeners
function setupEventListeners() {
    form.addEventListener('submit', handleAnalysis);
    resetBtn.addEventListener('click', resetForm);
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
        });
    });
}

// Handle Analysis Form Submission
async function handleAnalysis(e) {
    e.preventDefault();
    
    // Hide previous results/errors
    errorDisplay.style.display = 'none';
    resultsSection.style.display = 'none';
    
    // Show loading
    loadingIndicator.style.display = 'block';
    runBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        const angle = parseInt(formData.get('angle'));
        
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Check if we have pre-computed results
        const angleKey = String(angle);
        if (precomputedResults[angleKey]) {
            displayResults(precomputedResults[angleKey]);
        } else {
            // Find closest pre-computed angle
            const availableAngles = Object.keys(precomputedResults).map(Number);
            const closest = availableAngles.reduce((prev, curr) => 
                Math.abs(curr - angle) < Math.abs(prev - angle) ? curr : prev
            );
            
            showError(
                `Exact results for ${angle}° not available in static deployment. ` +
                `Showing closest pre-computed results for ${closest}°. ` +
                `For precise analysis at ${angle}°, please run the application locally.`
            );
            
            displayResults(precomputedResults[String(closest)]);
        }
        
    } catch (error) {
        showError('An error occurred: ' + error.message);
    } finally {
        loadingIndicator.style.display = 'none';
        runBtn.disabled = false;
    }
}

// Display Results
function displayResults(data) {
    // Configuration stats
    document.getElementById('statSide').textContent = `${data.side} units`;
    document.getElementById('statAngle').textContent = `Rotation: ${data.angle}°`;
    
    // Point counts
    document.getElementById('statPoints').textContent = data.unique_points;
    document.getElementById('statPointBreakdown').textContent = 
        `Generated from cube interference`;
    
    // Distance stats
    const distStats = data.distance_stats;
    document.getElementById('statDistRange').textContent = 
        `${distStats.min.toFixed(3)} - ${distStats.max.toFixed(3)}`;
    document.getElementById('statDistMean').textContent = 
        `Mean: ${distStats.mean.toFixed(3)}, σ: ${distStats.std.toFixed(3)}`;
    
    // Golden ratio
    const phiValue = 1.618033988749895;
    document.getElementById('statPhi').textContent = `φ ≈ ${phiValue.toFixed(6)}`;
    document.getElementById('statPhiCandidates').textContent = 
        `${data.phi_candidates} ${data.phi_candidates === 1 ? 'candidate' : 'candidates'} found`;
    
    // Directions
    document.getElementById('statDirections').textContent = data.directions;
    
    // Icosahedral check
    const ico = data.icosahedral;
    document.getElementById('statIcoAngle').textContent = `${ico.angle}°`;
    document.getElementById('statIcoQuality').textContent = 
        `Match quality: ${ico.quality}`;
    
    // Special angles
    displaySpecialAngles(data.special_angles);
    
    // Show results
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Display Special Angles
function displaySpecialAngles(specialAngles) {
    const container = document.getElementById('specialAnglesDisplay');
    container.innerHTML = '';
    
    const sortedAngles = Object.entries(specialAngles).sort((a, b) => 
        parseFloat(a[0]) - parseFloat(b[0])
    );
    
    sortedAngles.forEach(([angle, data]) => {
        if (data.count > 0) {
            const card = document.createElement('div');
            card.className = 'special-angle-card';
            card.innerHTML = `
                <div class="angle-value">${angle}°</div>
                <div class="angle-description">${data.description}</div>
                <div class="angle-count">${data.count} occurrences</div>
            `;
            container.appendChild(card);
        }
    });
}

// Show Error
function showError(message) {
    errorMessage.textContent = message;
    errorDisplay.style.display = 'block';
    errorDisplay.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Reset Form
function resetForm() {
    form.reset();
    resultsSection.style.display = 'none';
    errorDisplay.style.display = 'none';
}

// Help Function
function showHelp() {
    alert(`Orion Octave Cubes - Static Deployment

AVAILABLE PRE-COMPUTED ANGLES:
• 30° - Moderate phi occurrence
• 45° - Diagonal symmetry
• 60° - Strong phi occurrence
• 72° - Maximum phi (5 candidates!)
• 90° - Perpendicular configuration

LIMITATIONS IN STATIC MODE:
✗ Custom angle computation
✗ Real-time visualizations
✗ Custom parameter adjustments

TO RUN FULL VERSION LOCALLY:
1. Clone: git clone https://github.com/matpng/ddd.git
2. Install: pip install -r requirements.txt
3. Run: python3 app.py
4. Visit: http://localhost:5000

The local version provides:
✓ Any angle from 0-360°
✓ Real-time 3D visualizations
✓ Custom parameter tuning
✓ Full analysis pipeline
✓ Downloadable results`);
}
