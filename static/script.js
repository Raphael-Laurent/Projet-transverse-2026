document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const form = document.getElementById('analyze-form');
    const urlInput = document.getElementById('video-url');
    const submitBtn = document.getElementById('submit-btn');
    const resetBtn = document.getElementById('reset-btn');
    
    const inputSection = document.querySelector('.input-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.getElementById('system-status');
    
    // Check API Status on load
    checkStatus();

    async function checkStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            if (data.status === 'ready') {
                statusDot.className = 'status-dot ok';
                statusText.innerHTML = '<span class="status-dot ok"></span> Système opérationnel';
            } else {
                statusDot.className = 'status-dot error';
                statusText.innerHTML = '<span class="status-dot error"></span> Dépendances système manquantes (Ollama/FFmpeg)';
            }
        } catch (e) {
            statusDot.className = 'status-dot error';
            statusText.innerHTML = '<span class="status-dot error"></span> Serveur inaccessible';
        }
    }

    // Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        if (!url) return;

        startLoading();

        try {
            // Fake progression for UI since backend is synchronous right now
            // In a real app we'd use Server Sent Events or Websockets
            const progressInterval = simulateProgress();

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url, use_vision: true })
            });

            clearInterval(progressInterval);
            document.querySelectorAll('.step').forEach(s => s.className = 'step done');

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erreur inconnue lors de l\'analyse');
            }

            displayResults(data);

        } catch (error) {
            showError(error.message);
            stopLoading();
        }
    });

    // Reset Button
    resetBtn.addEventListener('click', () => {
        resultsSection.style.display = 'none';
        inputSection.style.display = 'block';
        urlInput.value = '';
        urlInput.focus();
        
        // Reset classes
        document.body.className = '';
        document.getElementById('score-circle').style.strokeDasharray = '0, 100';
    });

    function startLoading() {
        inputSection.style.display = 'none';
        resultsSection.style.display = 'none';
        loadingSection.style.display = 'block';
        submitBtn.disabled = true;
        
        // Reset steps
        document.querySelectorAll('.step').forEach(s => s.className = 'step');
        document.getElementById('step-download').className = 'step active';
    }

    function stopLoading() {
        loadingSection.style.display = 'none';
        inputSection.style.display = 'block';
        submitBtn.disabled = false;
    }

    function simulateProgress() {
        const steps = ['step-download', 'step-audio', 'step-vision', 'step-final'];
        let currentStep = 0;
        
        return setInterval(() => {
            if (currentStep < steps.length - 1) {
                document.getElementById(steps[currentStep]).className = 'step done';
                currentStep++;
                document.getElementById(steps[currentStep]).className = 'step active';
            }
        }, 5000); // Advance roughly every 5 seconds as a fallback visual
    }

    function displayResults(data) {
        loadingSection.style.display = 'none';
        resultsSection.style.display = 'flex';
        submitBtn.disabled = false;

        // Main Score
        const score = data.combined_score;
        const label = data.label; // true, uncertain, false
        
        // Update Circle Chart
        setTimeout(() => {
            document.getElementById('score-circle').style.strokeDasharray = `${score}, 100`;
            animateValue("score-text", 0, score, 1500);
        }, 100);

        // Update Theme & Texts based on label
        const bodyClass = `status-${label}`;
        document.body.className = bodyClass;
        resultsSection.className = `results-section ${bodyClass}`;

        const titles = {
            'true': 'Probablement Authentique',
            'uncertain': 'Incertain / Suspect',
            'false': 'Probablement Manipulé (IA)'
        };
        const subtitles = {
            'true': 'Cette vidéo ne présente pas de signes évidents de manipulation générée par IA.',
            'uncertain': 'Certains éléments semblent suspects, mais la certitude n\'est pas absolue.',
            'false': 'Forte probabilité que cette vidéo soit un deepfake ou générée par IA.'
        };

        document.getElementById('verdict-title').textContent = titles[label] || 'Inconnu';
        document.getElementById('verdict-subtitle').textContent = subtitles[label] || '';

        // Audio Details
        updateDetailCard('audio', data.audio.result);
        document.getElementById('audio-length').textContent = data.audio.text_length;

        // Visual Details
        updateDetailCard('visual', data.visual.result);
        document.getElementById('visual-frames').textContent = data.visual.frames_analyzed;
    }

    function updateDetailCard(type, resultData) {
        const badge = document.getElementById(`${type}-score-badge`);
        const explanation = document.getElementById(`${type}-explanation`);
        
        badge.textContent = `${resultData.score}/100`;
        
        // Set badge color class
        badge.className = 'badge';
        if (resultData.label === 'true') badge.classList.add('success');
        else if (resultData.label === 'false') badge.classList.add('error');
        else badge.classList.add('warning');

        explanation.textContent = resultData.explanation || 'Aucune explication fournie.';
    }

    function showError(msg) {
        const toast = document.getElementById('error-toast');
        document.getElementById('error-message').textContent = msg;
        
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }

    function animateValue(id, start, end, duration) {
        const obj = document.getElementById(id);
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            obj.innerHTML = Math.floor(easeOutQuart * (end - start) + start) + '%';
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
});
